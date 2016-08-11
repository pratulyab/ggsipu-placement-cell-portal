from django.conf.urls import url, include
from .views import create_company, company_home, edit_company, company_signup
from recruitment.views import view_association_requests

urlpatterns = [
	url(r'^create/$', create_company, name='create_company'),
	url(r'^home/$', company_home, name='company_home'),
	url(r'^edit/$', edit_company, name='edit_company_profile'),
	url(r'^association_requests/$', view_association_requests, name='company_association_requests'),
	url(r'^signup/$', company_signup, name='company_signup'),
]
