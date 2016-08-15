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
from account.views import login, view_profile, logout

urlpatterns = [
    url(r'^admin/', admin.site.urls),
	url(r'^admin$', admin.site.urls),
	url(r'^$', login, name='login'),
	url(r'^account/', include('account.urls')),
	url(r'^college/', include('college.urls')),
	url(r'^company/', include('company.urls')),
	url(r'^faculty/', include('faculty.urls')),
	url(r'^recruitment/', include('recruitment.urls')),
	url(r'^student/', include('student.urls')),
	url(r'^logout/$', logout, name='logout'),
#	url(r'^(?P<username>[\w.+=]+)/$', view_profile, name='view_profile'),
] + static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
