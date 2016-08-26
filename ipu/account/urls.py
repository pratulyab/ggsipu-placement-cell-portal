from django.conf.urls import url, include
from .views import home, logout, edit_account, activate, reset_password, forgot_password, social_profile

urlpatterns = [
		url(r'^home/$', home, name='home'),
#		url(r'^logout/$', logout, name='logout'),
		url(r'^edit_account/$', edit_account, name='edit_account'),
		url(r'^activate/(?P<uid>\d+)/(?P<token>[0-9A-Za-z_\-]+)/$', activate, name='activate'),
		url(r'^reset_password/(?P<uid>\d+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', reset_password, name='reset_password'),
		url(r'^forgot_password/$', forgot_password, name='forgot_password'),
		url(r'^social_profile/$', social_profile, name='social_profile'),
]
