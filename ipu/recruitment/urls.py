from django.conf.urls import url
from .views import associate, create_session, dissociate

urlpatterns = [
	url(r'^associate/$', associate, name='associate'),
	url(r'^createsession/$', create_session, name='createsession'),
	url(r'^dissociate/$', dissociate, name='dissociate'),
]
