from django.conf.urls import url, include
from .views import create_student, student_home, edit_student, student_login, student_signup, edit_qualifications

urlpatterns = [
	url(r'^create/$', create_student, name='create_student'),
	url(r'^home/$', student_home, name='student_home'),
	url(r'^edit/$', edit_student, name='edit_student_profile'),
	url(r'^login/$', student_login, name='student_login'),
	url(r'^signup/$', student_signup, name='student_signup'),
	url(r'^qualification/$', edit_qualifications, name='student_qual'),
]
