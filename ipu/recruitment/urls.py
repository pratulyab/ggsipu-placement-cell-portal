from django.conf.urls import url
from .views import get_with_prog_form, get_ass_streams, associate, create_session, dissociate

urlpatterns = [
	url(r'^associate/$', associate, name='associate'),
	url(r'^createsession/$', create_session, name='createsession'),
	url(r'^dissociate/$', dissociate, name='dissociate'),
	url(r'^get_with_prog/$', get_with_prog_form, name='with_prog'),
	url(r'^get_with_streams/$', get_ass_streams, name='with_streams'),
]
