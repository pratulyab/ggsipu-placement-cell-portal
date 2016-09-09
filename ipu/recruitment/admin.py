from django.contrib import admin
from .models import Association, Dissociation, PlacementSession, SelectionCriteria

# Register your models here.

admin.site.register(Association)
admin.site.register(Dissociation)
admin.site.register(PlacementSession)
admin.site.register(SelectionCriteria)
