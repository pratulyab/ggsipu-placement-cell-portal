from django.shortcuts import render
from django.http import HttpResponseForbidden , HttpResponse , JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import CreateNotificationForm , SelectStreamsForm
from django.core.exceptions import PermissionDenied
from account.models import CustomUser
from faculty.models import Faculty
from student.models import Student
from college.models import College , Stream
from .models import Notification
from django.core import serializers
from recruitment.models import PlacementSession
from django.contrib.auth.decorators import login_required
import itertools
import json


#from recruitment.forms import SessionInfoForm

# Create your views here.

@require_http_methods(['GET','POST'])
@login_required
def select_streams(request):
	if request.user.type == 'F' or request.user.type == 'C':
		if request.method == 'GET':
			if request.user.type == 'F':
				college = request.user.faculty.college
			else:
				college = request.user.college
			
			form_object = SelectStreamsForm(college = college)
			raw_html = render(request , 'notification/select_streams.html', {'select_streams' : form_object } )
			return HttpResponse(raw_html)
		else:
			form_object = SelectStreamsForm(request.POST)
			if request.user.type == 'F':
				college = request.user.faculty.college
			else:
				college = request.user.college	
			students_of_streams = list()
			streams_selected = request.POST.getlist('stream_list[]')
			indices = request.POST.getlist('indices[]')			
			
			
			for stream in streams_selected:
				stream_object = Stream.objects.get(code = stream)
				student_objects = stream_object.students.all().values('profile' , 'profile__username' )
				students_of_streams.append(student_objects)							
			

			students_of_streams = list(itertools.chain.from_iterable(students_of_streams))
			send_list = list()
			for_list = list()
			for idx , element in enumerate(students_of_streams):
				send_list.append(element['profile__username'])
				for_list.append(idx + 1)
			
			zipped_choices = zip(for_list , send_list)
			form_object = CreateNotificationForm(receive_list = zipped_choices , college = college , initial={ 'stream' : indices })
			raw_html = render(request , 'notification/create_notification.html' , {'create_notification' : form_object})
			
			return HttpResponse(raw_html)
			
	else:
		raise PermissionDenied


@require_http_methods(['GET','POST'])
@login_required
def create_notification(request):
	if request.user.type == 'C' or request.user.type == 'F':
		if request.method == 'POST':
			if request.user.type == 'F':
				college_object = request.user.faculty.college
			else:
				college_object = request.user.college
			students_selected = request.POST.getlist('student_list[]')
			message = request.POST['message']		
			college_customuser_object = college_object.profile
			college_students_queryset = college_object.students.all()
			
			student_objects = college_students_queryset.filter(profile__username__in = students_selected)
			
			for student_object in student_objects:
				student_customeuser_object = student_object.profile
				notification_object = Notification.objects.create(actor = college_customuser_object, target = student_customeuser_object, message = message )
				notification_object.save()


			return HttpResponse(len(students_selected))
		else:
			raise PermissionDenied
 			
	else:
		raise PermissionDenied			


@require_http_methods(['GET','POST'])
@login_required
def get_notifications(request):
	user = request.user
	data_list = list()
	notification_object_queryset = Notification.objects.filter(target = user)
	notifications = serializers.serialize("json", notification_object_queryset, indent = 4)
	for notification_object in notification_object_queryset:
		if notification_object.is_read == False:
			notification_object.is_read = True
#			notification_object.save()
			message = notification_object.message
			if notification_object.actor.type == 'C':
				actor_name = notification_object.actor.college
			elif notification_object.actor.type =='F':
				actor_name = notification_object.actor.faulty.college
			else:
				actor_name = notification_object.actor.company
			data_dict = dict()
			data_dict['message'] = message
			data_dict['actor'] = str(actor_name)
			data_list.append(data_dict)

	return JsonResponse(data_list , safe = False)







@require_http_methods(['GET','POST'])
@login_required
def forward_modified_session_notifications(request):
	if request.user.type == 'F' or request.user.type == 'C':
		return HttpResponse("")











