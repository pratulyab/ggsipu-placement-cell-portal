from django.conf.urls import url, include
from .views import create_college, college_home, edit_college, college_signup
from recruitment.views import view_association_requests

urlpatterns = [
	url(r'^create/$', create_college, name='create_college'),
	url(r'^home/$', college_home, name='college_home'),
	url(r'^edit/$', edit_college, name='edit_college_profile'),
	url(r'^association_requests/$', view_association_requests, name='college_association_requests'),
	url(r'^signup/$', college_signup, name='college_signup'),
]
