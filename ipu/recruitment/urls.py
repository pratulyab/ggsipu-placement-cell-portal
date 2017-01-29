from django.conf.urls import url
#from .views import get_with_prog_form, get_ass_streams, associate, create_session, dissociate, mysessions, generate_excel, edit_session, edit_criteria, associate_mofos
from .views import associate, get_programmes, get_streams, create_session, dissociate, mysessions, generate_excel, edit_session, edit_criteria

urlpatterns = [
	url(r'^associate/$', associate, name='associate'),
	url(r'^createsession/$', create_session, name='createsession'),
	url(r'^dissociate/$', dissociate, name='dissociate'),
	url(r'^get_prog/$', get_programmes, name='programmes'),
	url(r'^get_streams/$', get_streams, name='streams'),
	url(r'^mysessions/$', mysessions, name='mysessions'),
	url(r'^excel/(?P<sess>\w{12,})/$', generate_excel, name='excel'),
	url(r'^edit_session/(?P<sess>\w{12,})/$', edit_session, name='edit_session'),
#	url(r'^edit_criteria/(?P<sess>\w{12,})/$', edit_criteria, name='edit_criteria'),
	url(r'^edit_criteria/(?P<sess>\w{9,})/$', edit_criteria, name='edit_criteria'),
]
