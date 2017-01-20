from django.conf.urls import url
from .views import manage_dummy_home, create_dummy_company, edit_dummy_company, create_dummy_sessionI, create_dummy_sessionII, edit_dummy_session, dummy_excel

urlpatterns = [
	url(r'^manage/$', manage_dummy_home, name='manage_dummy'),
	url(r'^create/$', create_dummy_company, name='create_dcompany'),
	url(r'^edit/$', edit_dummy_company, name='edit_dcompany'),
	url(r'^get_with_prog/$', create_dummy_sessionI, name='create_dsessI'),
	url(r'^get_with_streams/$', create_dummy_sessionII, name='create_dsessII'),
	url(r'^edit_dsession/(?P<sess_hashid>\w{9,})/$', edit_dummy_session, name='edit_dsession'),
	url(r'^excel/(?P<dsess>\w{9,})/$', dummy_excel, name='dexcel'),
]
