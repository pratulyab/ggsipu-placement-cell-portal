from django.conf.urls import url, include
from .views import faculty_signup, edit_create_faculty, faculty_home, get_enrollment_number, delete_faculty, edit_perms, manage, activate
urlpatterns = [
	url(r'^home/$', faculty_home, name='faculty_home'),
	url(r'^profile/$', edit_create_faculty, name='edit_create_faculty'),
	url(r'^signup/$', faculty_signup, name='faculty_signup'),
	url(r'verify/$', get_enrollment_number, name='verify'),
	url(r'delete/(?P<f_hashid>[a-zA-Z0-9]{8,})/$', delete_faculty, name='delete_faculty'),
	url(r'edit_perms/(?P<f_hashid>[a-zA-Z0-9]{8,})/$', edit_perms, name='edit_faculty_perms'), # Hard coded this url in faculty/manage_faculty.html
	url(r'manage/$', manage, name='manage_faculty'),
	url(r'activate/(?P<user_hashid>[a-zA-Z0-9]{13,})/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', activate, name='faculty_activation'),
]
