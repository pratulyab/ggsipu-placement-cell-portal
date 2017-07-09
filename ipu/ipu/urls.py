"""ipu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include, static
from django.contrib import admin
from notification.views import report
from account.views import auth, landing, login, view_profile, logout, search, team, intro, sms_callback, procedure
from stats.views import stats, past_recruiters

urlpatterns = [
#    url(r'^LrY4pRNMnQXvOK3vWeODJaP15jbKkV$' if not settings.DEBUG else r'admin$', admin.site.urls),
	url(r'^LrY4pRNMnQXvOK3vWeODJaP15jbKkV/' if not settings.DEBUG else r'admin/', admin.site.urls),
	url(r'^$', landing, name='landing'),
	url(r'^auth/$', auth, name='auth'),
	url(r'^team/$', team, name='team'),
	url(r'^procedure/$', procedure, name='procedure'),
	url(r'^stats/$', stats, name='stats'),
	url(r'^past_recruiters/$', past_recruiters, name='past_recruiters'),
	url(r'^intro/$', intro, name='intro'),
	url(r'^login/$', login, name='login'),
	url(r'^account/', include('account.urls')),
	url(r'^college/', include('college.urls')),
	url(r'^notification/', include('notification.urls')),
	url(r'^company/', include('company.urls')),
	url(r'^dcompany/', include('dummy_company.urls')),
	url(r'^faculty/', include('faculty.urls')),
	url(r'^recruitment/', include('recruitment.urls')),
	url(r'^student/', include('student.urls')),
	url(r'^logout/$', logout, name='logout'),
	url(r'^search/$', search, name='search'),
	url(r'^twofactor/cb2e22ea-80a6-45e8-ab27-6d101350a73d/$', sms_callback),
	url(r'^user/(?P<username>[\w.+=]+)/$', view_profile, name='view_profile'),
    url(r'^report/$', report, name='report'),

] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static.static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
