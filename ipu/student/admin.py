from django.contrib import admin
from .models import Student, Qualification, Score, ExaminationBoard, Subject, CGPAMarksheet, ScoreMarksheet, SchoolMarksheet

# Register your models here.

admin.site.register(Student)
admin.site.register(Qualification)
admin.site.register(Score)
admin.site.register(ExaminationBoard)
admin.site.register(Subject)
admin.site.register(CGPAMarksheet)
admin.site.register(ScoreMarksheet)
admin.site.register(SchoolMarksheet)
