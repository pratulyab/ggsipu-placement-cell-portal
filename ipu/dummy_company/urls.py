from django.conf.urls import url
from .views import manage_dummy_company, create_dummy_company, get_edit_dcompany_form, edit_dummy_company, get_dummy_session_streams, create_dummy_session, edit_dummy_session, dummy_excel, my_dummy_sessions

urlpatterns = [
	url(r'^manage_dcompany/$', manage_dummy_company, name='manage_dcompany'),
	url(r'^create/$', create_dummy_company, name='create_dcompany'),
	url(r'^edit_dc_form/$', get_edit_dcompany_form, name='edit_dcompany_form'),
	url(r'^edit/(?P<dummy_hashid>\w{7,})/$', edit_dummy_company, name='edit_dcompany'),
	url(r'^dsess_streams/$', get_dummy_session_streams, name='create_dsession_streams'),
	url(r'^create_session/$', create_dummy_session, name='create_dsession'),
	url(r'^edit_dsession/(?P<sess_hashid>\w{9,})/$', edit_dummy_session, name='edit_dsession'),
	url(r'^excel/(?P<dsess>\w{9,})/$', dummy_excel, name='dexcel'),
	url(r'^mydsessions/$', my_dummy_sessions, name='mydsessions'),
]
