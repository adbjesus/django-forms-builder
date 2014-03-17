
from django.conf.urls import *

urlpatterns = patterns("forms_builder.forms.views",
	url(r"(?P<slug>.*)/error/(?P<error>.*)$", "form_error", name="form_error"),
    url(r"(?P<slug>.*)/sent/$", "form_sent", name="form_sent"),
    url(r"(?P<slug>.*)/responses/$", "form_responses", name="form_responses"),
    url(r"(?P<slug>.*)/$", "form_detail", name="form_detail"),
)
