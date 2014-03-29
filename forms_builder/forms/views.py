from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from forms_builder.forms import settings
from forms_builder.forms.forms import FormForForm
from forms_builder.forms.signals import form_invalid, form_valid
from forms_builder.forms.models import Form


class FormDetailView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'forms/form_detail.html'

    def get(self, request, slug):
        published = Form.objects.published(for_user=request.user)
        form = get_object_or_404(published, slug=slug)

        if not form.is_user_permitted(request.user, 'view'):
            raise Http404

        context = self.get_context_data(form=form, can_submit=form.is_user_permitted(request.user, 'submit'))
        return self.render_to_response(context)

    def post(self, request, slug):
        published = Form.objects.published(for_user=request.user)
        form = get_object_or_404(published, slug=slug)

        if not form.is_user_permitted(request.user, 'submit'):
            raise Http404

        request_context = RequestContext(request)
        args = (form, request_context, request.POST or None, request.FILES or None)
        form_for_form = FormForForm(*args)

        if not form_for_form.is_valid():
            form_invalid.send(sender=request, form=form_for_form)
        else:
            try:
                entry = form_for_form.save(user=request.user)
            except IntegrityError:
                err = "You have already voted for this"
                request.session['form_submitted'] = True
                #request.session['form_error'] = err
                return redirect(reverse("form_error", kwargs={"slug": form.slug}))
            except:
                raise

            form_valid.send(sender=request, form=form_for_form, entry=entry)
            request.session['form_submitted'] = True;
            return redirect(reverse("form_success", kwargs={"slug": form.slug}))

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class FormSuccessView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'forms/form_success.html'

    def get(self, request, slug):
        if not request.session.pop('form_submitted', False):
            raise Http404
        published = Form.objects.published(for_user=request.user)
        form = get_object_or_404(published, slug=slug)

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class FormErrorView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'forms/form_error.html'

    def get(self, request, slug):
        if not request.session.pop('form_submitted', False) or not request.session.pop('form_error', False):
            raise Http404
        published = Form.objects.published(for_user=request.user)
        form = get_object_or_404(published, slug=slug)

        context = self.get_context_data(form=form, error=request.session.pop('form_error'))
        return self.render_to_response(context)

class FormResponsesView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'forms/form_responses.html'

    def get(self, request, slug):
        published = Form.objects.published(for_user=request.user)
        form = get_object_or_404(published, slug=slug)

        if not form.is_user_permitted(request.user, 'responses'):
            raise Http404

        context = self.get_context_data(form=form)
        return self.render_to_response(context)