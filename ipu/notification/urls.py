from django.conf.urls import url, include
from .views import get_notifications , generate_notifications

urlpatterns = [
	url(r'^get_notifications/$', get_notifications, name='get_notifications'),
	url(r'^generate_notifications/$' , generate_notifications , name = 'generate_notifications'),
]