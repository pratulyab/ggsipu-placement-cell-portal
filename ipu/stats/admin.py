from django.contrib import admin

from .models import College, Company, Placement, YearRecord

# Register your models here.

admin.site.register(Company)
admin.site.register(College)
admin.site.register(YearRecord)

class PlacementAdmin(admin.ModelAdmin):
	list_display = ['record', 'company', 'type', 'total_offers', 'salary', 'salary_comment']
	
	def salary(self, obj):
		return self.salary if self.salary != 0 else self.salary_comment

	def record(self, obj):
		return self.record.__str__()

	record.short_description = 'College'
	salary.short_description = 'Salary (LPA)'

admin.site.register(Placement, PlacementAdmin)
