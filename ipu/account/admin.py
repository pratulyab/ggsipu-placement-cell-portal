from django.contrib import admin
from .models import CustomUser, SocialProfile

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(SocialProfile)
