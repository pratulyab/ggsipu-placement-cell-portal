from django.contrib import admin
from .models import Association, Dissociation, PlacementSession

# Register your models here.

admin.site.register(Association)
admin.site.register(Dissociation)
admin.site.register(PlacementSession)
