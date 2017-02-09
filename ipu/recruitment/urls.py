from django.conf.urls import url
#from .views import get_with_prog_form, get_ass_streams, associate, create_session, dissociate, mysessions, generate_excel, edit_session, edit_criteria, associate_mofos
from .views import associate, get_programmes, get_streams, create_session, dissociate, mysessions, generate_excel, edit_session, edit_criteria, manage_session_students, manage_session, notify_session

urlpatterns = [
	url(r'^associate/$', associate, name='associate'),
	url(r'^createsession/$', create_session, name='createsession'),
	url(r'^dissociate/$', dissociate, name='dissociate'),
	url(r'^get_prog/$', get_programmes, name='programmes'),
	url(r'^get_streams/$', get_streams, name='streams'),
	url(r'^mysessions/$', mysessions, name='mysessions'),
	url(r'^excel/(?P<sess>\w{12,})/$', generate_excel, name='excel'),
	url(r'^edit_session/(?P<sess_hashid>[a-zA-Z0-9]{12,})/$', edit_session, name='edit_session'),
	url(r'^edit_criteria/(?P<sess_hashid>[a-zA-Z0-9]{12,})/$', edit_criteria, name='edit_criteria'),
	url(r'^manage_session_students/(?P<sess_hashid>[a-zA-Z0-9]{12,})/$', manage_session_students, name='manage_session_students'),
	url(r'^manage_session/(?P<sess_hashid>[a-zA-Z0-9]{12,})/$', manage_session, name='manage_session'),
	url(r'^notify/(?P<sess_hashid>[a-zA-Z0-9]{12,})/$', notify_session, name='notify_session'),
]
