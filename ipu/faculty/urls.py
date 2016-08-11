from django.conf.urls import url, include
from .views import faculty_signup, edit_create_faculty, faculty_home
urlpatterns = [
	url(r'^home/$', faculty_home, name='faculty_home'),
	url(r'^profile/$', edit_create_faculty, name='edit_create_faculty'),
	url(r'^signup/$', faculty_signup, name='faculty_signup'),
]
