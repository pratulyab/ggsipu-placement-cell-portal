from django.conf.urls import url
from .views import get_with_prog_form, get_ass_streams, associate, create_session, dissociate, mysessions, generate_excel, edit_session, edit_criteria

urlpatterns = [
	url(r'^associate/$', associate, name='associate'),
	url(r'^createsession/$', create_session, name='createsession'),
	url(r'^dissociate/$', dissociate, name='dissociate'),
	url(r'^get_with_prog/$', get_with_prog_form, name='with_prog'),
	url(r'^get_with_streams/$', get_ass_streams, name='with_streams'),
	url(r'^mysessions/$', mysessions, name='mysessions'),
	url(r'^excel/(?P<sess>\w{12,})/$', generate_excel, name='excel'),
	url(r'^edit_session/(?P<sess>\w{12,})/$', edit_session, name='edit_session'),
	url(r'^edit_criteria/(?P<sess>\w{12,})/$', edit_criteria, name='edit_criteria'),
]
