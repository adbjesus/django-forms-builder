
from django.conf.urls import *
from forms_builder.forms import views

urlpatterns = patterns("forms_builder.forms.views",
    #url(r"(?P<slug>.*)/error/(?P<error>.*)$", "form_error", name="form_error"),
    #url(r"(?P<slug>.*)/sent/$", "form_sent", name="form_sent"),
    #url(r"(?P<slug>.*)/responses/$", "form_responses", name="form_responses"),
    url(r"(?P<slug>.*)/$",
        view=views.FormDetailView.as_view(),
        name="form_detail",
        ),
)
