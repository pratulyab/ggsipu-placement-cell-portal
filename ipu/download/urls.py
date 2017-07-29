from django.conf.urls import url
from .views import download_resume, download_resume_dummy, serve_zipped_file

urlpatterns = [
	url(r'^resume/(?P<sess_hashid>\w{12,})/$', download_resume, name='dl_resume'),
	url(r'^dresume/(?P<dsess_hashid>[a-zA-Z0-9]{9,})/$', download_resume_dummy, name='dl_dresume'),
	url(r'^serve/(?P<user_hashid>[a-zA-Z0-9]{13,})/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', serve_zipped_file, name='serve'),
#(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/
]
