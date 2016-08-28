from django.conf.urls import url, include
from .views import get_notifications , select_streams , create_notification

urlpatterns = [
	url(r'^get_notifications/$', get_notifications, name='get_notifications'),
	url(r'^select_streams/$' , select_streams , name = 'select_streams'),
	url(r'^create_notification/$' , create_notification , name = 'create_notification'),
]