
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote
from email_extras.utils import send_mail_template

from forms_builder.forms.forms import FormForForm
from forms_builder.forms.models import Form, FormEntry, Field, FieldEntry, STATUS_DRAFT, STATUS_PUBLIC, STATUS_PRIVATE, STATUS_GROUPS
from forms_builder.forms.settings import SEND_FROM_SUBMITTER, USE_SITES
from forms_builder.forms.signals import form_invalid, form_valid
from forms_builder.forms.utils import split_choices
from forms_builder.forms import fields

from collections import defaultdict

from django.db import IntegrityError

def form_detail(request, slug, template="forms/form_detail.html"):
    """
    Display a built form and handle submission.
    """
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published, slug=slug)
    if not request.user.is_authenticated() and not form.can_view_status == STATUS_PUBLIC:
        return redirect("%s?%s=%s" % (settings.LOGIN_URL, REDIRECT_FIELD_NAME,
                                      urlquote(request.get_full_path())))

    if request.user.is_authenticated():
        if form.can_view_status == STATUS_GROUPS and (
                len(list(set(request.user.groups.all()).intersection(set(form.can_view_groups.all())))) == 0):
            print("No permissions")
            raise Http404

    request_context = RequestContext(request)
    args = (form, request_context, request.POST or None, request.FILES or None)
    form_for_form = FormForForm(*args)
    if request.method == "POST":
        if not form_for_form.is_valid():
            form_invalid.send(sender=request, form=form_for_form)
        else:
            try:
                entry = form_for_form.save(user=request.user)
            except IntegrityError:
                err = "You have already voted for this"
                return redirect(reverse("form_error", kwargs={"slug": form.slug, "error": err}))
            except:
                raise

            subject = form.email_subject
            if not subject:
                subject = "%s - %s" % (form.title, entry.entry_time)
            fields = []
            for (k, v) in form_for_form.fields.items():
                value = form_for_form.cleaned_data[k]
                if isinstance(value, list):
                    value = ", ".join([i.strip() for i in value])
                fields.append((v.label, value))
            context = {
                "fields": fields,
                "message": form.email_message,
                "request": request,
            }
            email_from = form.email_from or settings.DEFAULT_FROM_EMAIL
            email_to = form_for_form.email_to()
            if email_to and form.send_email:
                send_mail_template(subject, "form_response", email_from,
                                   email_to, context=context,
                                   fail_silently=settings.DEBUG)
            email_copies = split_choices(form.email_copies)
            if email_copies:
                if email_to and SEND_FROM_SUBMITTER:
                    # Send from the email entered.
                    email_from = email_to
                attachments = []
                for f in form_for_form.files.values():
                    f.seek(0)
                    attachments.append((f.name, f.read()))
                send_mail_template(subject, "form_response", email_from,
                                   email_copies, context=context,
                                   attachments=attachments,
                                   fail_silently=settings.DEBUG)
            form_valid.send(sender=request, form=form_for_form, entry=entry)
            return redirect(reverse("form_sent", kwargs={"slug": form.slug}))
    context = {"form": form}
    return render_to_response(template, context, request_context)


def form_sent(request, slug, template="forms/form_sent.html"):
    """
    Show the response message.
    """
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published, slug=slug)
    context = {"form": form}
    return render_to_response(template, context, RequestContext(request))

def form_error(request, slug, error, template="forms/form_error.html"):
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published, slug=slug)
    context = {"form": form, "error": error}
    return render_to_response(template, context, RequestContext(request))

def form_responses(request, slug, template="forms/form_responses.html"):
    published = Form.objects.published(for_user=request.user)
    form = get_object_or_404(published,slug=slug)

    all_fields = [f for f in Field.objects.all() if f.form == form]

    entries = [e for e in FormEntry.objects.all() if e.form == form]
    entries = [[c.field_id,c.value] for c in FieldEntry.objects.all() if c.entry in entries]

    entries_dict = defaultdict(list)
    for k,v in entries: entries_dict[k].append(v)
    entries_dict = dict(entries_dict)

    results = list()
    for field in all_fields:
        results.append([field,list()])
        if(field.field_type==fields.RADIO_MULTIPLE):
            for choice in field.get_choices():
                results[-1][-1].append([choice[0],entries_dict[field.id].count(choice[0]),entries_dict[field.id].count(choice[0])/float(len(entries_dict[field.id]))])

    print results

    context = {"form": form, "results": results}
    return render_to_response(template, context, RequestContext(request))
