
from django.conf.urls import *
from forms_builder.forms import views

urlpatterns = patterns("forms_builder.forms.views",

    url(r"(?P<slug>.*)/responses/$",
        view=views.FormResponsesView.as_view(),
        name="form_responses"
        ),

    url(r"(?P<slug>.*)/success/$",
        view=views.FormSuccessView.as_view(),
        name="form_success",
        ),

    url(r"(?P<slug>.*)/error/$",
        view=views.FormErrorView.as_view(),
        name="form_error",
        ),

    url(r"(?P<slug>.*)/$",
        view=views.FormDetailView.as_view(),
        name="form_detail",
        ),
)
