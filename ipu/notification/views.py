from django.shortcuts import render
from django.http import HttpResponseForbidden , HttpResponse , JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import CreateNotificationForm
from django.core.exceptions import PermissionDenied
from faculty.models import Faculty
from student.models import Student
from college.models import College
from .models import Notification
from django.core import serializers
from recruitment.models import PlacementSession
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

#from recruitment.forms import SessionInfoForm

# Create your views here.

@require_http_methods(['GET','POST'])
@login_required
@csrf_exempt
def generate_notifications(request):
	if request.user.type == 'F' or request.user.type == 'C':
		if request.method == 'GET':
			if request.user.type == 'F':
				college = request.user.faculty.college
			else:
				college = request.user.college
			form_object = CreateNotificationForm(college = college)
			raw_html = render(request , 'notification/generate_notification.html', {'generate_notification' : form_object } )
			return HttpResponse(raw_html)
		else:
			print("here")
			form_object = CreateNotificationForm(request.POST)
			print(request.POST["message"])
			return HttpResponse("ok")

			"""
			if form_object.is_valid():
				#students = form.cleanded_data.get('students')
				actor = request.user
				if actor.type == 'F':
					college = actor.faculty.college
				else:
					college = actor
				#message = form.cleanded_data('message')
				message = request.GET.get("message")
				print(college)
				print(message)
				return HttpResponse("Trying")

				#qset = college.students.all()
				#for student in students:
				#student_object = qset.objects.get(student = profile.username)
				#Obj = Notification.objects.create(actor = college.profile, target = student_object, message = message )
				#Obj.save();
			"""
	else:
		raise PermissionDenied


@require_http_methods(['GET','POST'])
@login_required
def get_notifications(request):
	user = request.user
	notifications = serializers.serialize("json", Notification.objects.filter(target = user), indent = 4)
	user.notification_target.is_read = True
	return JsonResponse(notifications)


@require_http_methods(['GET','POST'])
@login_required
def forward_modified_session_notifications(request):
	if request.user.type == 'F' or request.user.type == 'C':
		return HttpResponse("")











