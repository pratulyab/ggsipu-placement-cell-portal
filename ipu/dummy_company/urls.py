from django.conf.urls import url
from .views import manage_dummy_company, create_dummy_company, get_edit_dcompany_form, edit_dummy_company, get_dummy_session_streams, create_dummy_session, edit_dummy_session, dummy_excel, my_dummy_sessions, manage_dummy_session, manage_dsession_students, edit_dcriteria, notify_dsession, filter_dsessions

urlpatterns = [
	url(r'^manage_dcompany/$', manage_dummy_company, name='manage_dcompany'),
	url(r'^create/$', create_dummy_company, name='create_dcompany'),
	url(r'^edit_dc_form/$', get_edit_dcompany_form, name='edit_dcompany_form'),
	url(r'^edit/(?P<dummy_hashid>[a-zA-Z0-9]{7,})/$', edit_dummy_company, name='edit_dcompany'),
	url(r'^dsess_streams/$', get_dummy_session_streams, name='create_dsession_streams'),
	url(r'^create_session/$', create_dummy_session, name='create_dsession'),
	url(r'^edit_dsession/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', edit_dummy_session, name='edit_dsession'),
	url(r'^excel/(?P<dsess>[a-zA-Z0-9]{9,})/$', dummy_excel, name='dexcel'),
	url(r'^mydsessions/$', my_dummy_sessions, name='mydsessions'),
	url(r'^manage_dsession/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', manage_dummy_session, name='manage_dsession'),
	url(r'^manage_dsession_students/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', manage_dsession_students, name='manage_dsession_students'),
	url(r'^edit_criteria/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', edit_dcriteria, name='edit_dcriteria'),
	url(r'^notify/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', notify_dsession, name='notify_dsession'),
	url(r'^filter_dsessions/$', filter_dsessions, name='filter_dsessions'),
]
