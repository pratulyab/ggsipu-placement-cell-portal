from django.conf.urls import url, include
from .views import create_student, student_home, edit_student, student_login, student_signup, edit_qualifications, delete_student, tech_profile, upload_file, paygrade, coder, companies_in_my_college, apply_to_company, qualifications, update_score, download_master_excel
from dummy_company.views import apply_to_dummy_company

urlpatterns = [
	url(r'^create/$', create_student, name='create_student'),
	url(r'^home/$', student_home, name='student_home'),
	url(r'^edit/$', edit_student, name='edit_student_profile'),
	url(r'^login/$', student_login, name='student_login'),
	url(r'^signup/$', student_signup, name='student_signup'),
	url(r'^qualification/$', edit_qualifications, name='student_qual'),
	url(r'^delete/$', delete_student, name='delete_student'),
	url(r'^tech_profile/$', tech_profile, name='tech_profile'),
	url(r'^upload_file/$', upload_file, name='upload_file'),
	url(r'^paygrade/$', paygrade, name='paygrade'),
	url(r'^coder/$', coder, name='coder'),
	url(r'^view_companies/$', companies_in_my_college, name='view_companies'),
	url(r'^apply/(?P<sess>\w{12,})/$', apply_to_company, name='apply'),
	url(r'^applyd/(?P<dsess>\w{9,})/$', apply_to_dummy_company, name='applyd'),
	url(r'^qualifications/$', qualifications, name='qual'),
	url(r'^update_score/(?P<score_hashid>\w{11,})/$', update_score, name='update_score'),
	url(r'^download_master_excel/$', download_master_excel, name='master_excel'),
]
