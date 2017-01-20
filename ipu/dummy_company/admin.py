from django.contrib import admin
from .models import DummyCompany, DummySession

# Register your models here.

admin.site.register(DummyCompany)
admin.site.register(DummySession)
