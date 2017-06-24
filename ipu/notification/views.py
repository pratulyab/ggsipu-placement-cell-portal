from django.conf import settings
from django.shortcuts import render ,  get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden , HttpResponse , JsonResponse , Http404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.template import Context, Template
from django.core.exceptions import PermissionDenied
from .forms import SelectStreamsForm , CreateNotificationForm , IssueForm , IssueReplyForm
from .models import NotificationData , Notification , Issue , IssueReply
from account.models import CustomUser
from faculty.models import Faculty
from student.models import Student
from college.models import College , Stream
from django.core import serializers
from recruitment.models import PlacementSession
from django.contrib.auth.decorators import login_required
from hashids import Hashids
import requests
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
		if request.method == 'POST':
			form_object = SelectStreamsForm(request.POST)
			if request.user.type == 'F':
				college = request.user.faculty.college
			else:
				college = request.user.college	
			students_of_streams = list()
			streams_selected = request.POST.getlist('stream_list[]')
			indices = request.POST.getlist('indices[]')						
			programme_to_year_list = list()
			for stream in streams_selected:
				stream_object = get_object_or_404(Stream , code = stream)
				if stream_object:	
					full_name = stream_object
					#above stores a string like [128] B.Tech. (Dual Degree) - Electronics and Communication
					year = stream_object.programme.years
					
					programme_to_year = {'name' : full_name,
										 'year' : year,
										 'code' : stream,
										}
					programme_to_year_list.append(programme_to_year)
						
				else:
					pass	
			form_object = CreateNotificationForm(college = college ,programme_to_year = programme_to_year_list, initial={ 'stream' : indices })
			raw_html = render(request , 'notification/create_notification.html' , {'create_notification' : form_object})
						

			return HttpResponse(raw_html)
			
	else:
		raise PermissionDenied


@require_http_methods(['POST'])
@login_required
def select_years(request):
	if request.user.type == 'C' or request.user.type == 'F':
		if request.user.type == 'F':
			college = request.user.faculty.college
		else:
			college = request.user.college	
		students_of_streams = list()
		stream_to_year = request.POST['stream_to_year']
		indices = request.POST.getlist('indices[]')
		stream_to_year = json.loads(stream_to_year)
		stream_codes = list()
		years_selected = list()
		for key ,values in stream_to_year.items():
			stream_codes.append(key)
			years_selected.append(values)
		
		for idx , stream in enumerate(stream_codes):
			try:
				stream_object = Stream.objects.get(code = stream)
			except:
				return JsonResponse(status = 400 , data = {"error" : "Please select the stream again."})
			student_objects = college.students.filter(stream = stream_object , current_year__in = years_selected[idx]).values('profile' , 'profile__username' )
			students_of_streams.append(student_objects)
		
		students_of_streams = list(itertools.chain.from_iterable(students_of_streams))
		
		send_list = list()
		for element in students_of_streams:
			send_list.append(element['profile__username'])
		return JsonResponse(send_list , safe = False)
		
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
			subject = request.POST.get('subject')
			message = request.POST.get('message')
			if_sms = request.POST.get('if_sms')
			if_email = request.POST.get('if_email')
			sms_message = request.POST.get('sms_message')		
			college_customuser_object = college_object.profile
			college_students_queryset = college_object.students.all()
			if not field_length_test(subject , 256):
				return JsonResponse(status = 400 , data = {"error" : "Length Exceeded."})
			student_objects = college_students_queryset.filter(profile__username__in = students_selected)
			notification_data_object = NotificationData.objects.create(subject = subject , message = message , sms_message = sms_message)
			notification_data_object.save()
			for student_object in student_objects:
				student_customeuser_object = student_object.profile
				notification_object = Notification.objects.create(actor = college_customuser_object, target = student_customeuser_object , notification_data = notification_data_object)
				notification_object.save()

			return HttpResponse(len(students_selected))
		else:
			raise PermissionDenied
 			
	else:
		raise PermissionDenied			

@require_GET
@login_required
def truncated_notifications(request):
	user = request.user
	data_list = list()
	notification_object_queryset = Notification.objects.filter(target = user).order_by('-creation_time')[:5]
	for notification_object in notification_object_queryset:
		data_dict = dict()
		if notification_object.notification_data is not None:
			data = notification_object.notification_data
			message = data.subject
		else:
			message = notification_object.message
		message = clean_string(message , 63)
		data_dict['message'] = message
		data_dict['sender'] = str(get_notification_actor_name(notification_object , compact = True))
		date_template = Template('{{ date|date:"d M Y, D" }}')
		date_context = Context({'date': notification_object.creation_time})
		data_dict['date'] = date_template.render(date_context)
		data_list.append(data_dict)
	return JsonResponse(data_list , safe = False)


@require_http_methods(['GET','POST'])
@login_required
def get_notifications(request):
	user = request.user
	data_list = list()
	notification_object_queryset = Notification.objects.filter(target = user).order_by('-creation_time')
	notifications = serializers.serialize("json", notification_object_queryset, indent = 4)
	for notification_object in notification_object_queryset:
		data_dict = dict()
		data_dict['read'] = notification_object.is_read
		if notification_object.is_read == False:
			notification_object.is_read = True
			notification_object.save()
		if notification_object.notification_data is not None:
			data = notification_object.notification_data
			subject = data.subject
			message = data.message
			data_dict['identifier'] = notification_pk_encoder(notification_object.pk)
			data_dict['subject'] = subject
			data_dict['if_ping'] = False
		else:
			data_dict['message'] = notification_object.message
			data_dict['if_ping'] = True
		data_dict['actor'] = str(get_notification_actor_name(notification_object))
		data_list.append(data_dict)
	return JsonResponse(data_list , safe = False)

@require_GET
@login_required
def notification_detail(request):
	user = request.user
	identifier = request.GET.get('identifier' , None)
	notification_object = notification_pk_decoder(identifier)
	data_dict = dict()
	if notification_object.notification_data is not None:
		data = notification_object.notification_data
		data_dict['subject'] = data.subject
		data_dict['message'] = data.message
		date = render_to_string('notification/date_formatter.html' , {'date' : notification_object.creation_time})
		data_dict['date'] = date
	else:
		raise Http404
	return JsonResponse(data_dict , safe = False)


@require_http_methods(['GET','POST'])
@login_required
def submit_issue(request):
	if request.user.type == 'S':
		if request.method == 'GET':
			form_object = IssueForm()
			raw_html = render(request , 'notification/submit_issue.html' , {'issue_form' : form_object})
			return HttpResponse(raw_html)
		if request.method == 'POST':
			form_object = IssueForm(request.POST , user = request.user.student , college = request.user.student.college)
			recaptcha_response = request.POST.get('recaptcha_response' , None)
			recaptcha_data = {
				'secret' : settings.GOOGLE_RECAPTCHA_SECRET_KEY,
				'response' : recaptcha_response
			}
			recaptcha_verification_url = settings.GOOGLE_RECAPTCHA_VERIFICATION_URL
			request = requests.post(recaptcha_verification_url , recaptcha_data)
			status = request.json()
			if status['success']:
				if form_object.is_valid():
					form_object.save()
					return HttpResponse(status = 201)
				else:
					raise Http404
			else:
				return JsonResponse(status = 403 , data = {'errors' : 'Recaptcha authorization failed. Please try again.'} , safe = False)
	else:
		raise PermissionDenied


@require_GET
@login_required
def display_issue(request):
	if request.user.type == 'F':
		college = request.user.faculty.college
		issue_object_queryset = Issue.objects.filter(college = college).order_by('-marked' , 'solved_by' , '-creation_time')
		data_list = list()
		hashids = Hashids("ALonePinkSpiderInYellowWoods")
		for issue_object in issue_object_queryset:
			data_dict = dict()
			data_dict['actor'] = issue_object.actor.profile.username
			data_dict['issue_type'] = issue_object.issue_type
			data_dict['is_marked'] = issue_object.marked
			if(issue_object.solved_by):
				data_dict['is_solved'] = True
			else:
				data_dict['is_solved'] = False

			pk_id = int(issue_object.pk)
			pk_id = pk_id*1000033
			data_dict['identifier'] = hashids.encode(pk_id)
			data_list.append(data_dict)
		
		return JsonResponse(data_list , safe = False)
	else:
		raise PermissionDenied


@login_required
@require_GET
def mark_issue(request):
	if request.user.type == 'F':
		identifier = request.GET.get('identifier' , None)
		if not identifier:
			raise Http404
		hashids = Hashids("ALonePinkSpiderInYellowWoods")
		pk_tuple = hashids.decode(identifier)
		pk_list = list(pk_tuple)
		possible_pk = pk_list[0]/1000033
		if not possible_pk.is_integer():
			raise Http404
		issue_object = get_object_or_404(Issue , pk = possible_pk)
		if issue_object.marked == True:
			issue_object.marked = False
		else:
			issue_object.marked = True
		issue_object.save()
		return HttpResponse(status = 201)
	else:
		raise PermissionDenied



@require_http_methods(['GET','POST'])
@login_required
def solve_issue(request):
	if request.user.type == 'F':
		if request.method == 'GET':
			identifier = request.GET.get('identifier' , None)
			if not identifier:
				raise Http404
			hashids = Hashids("ALonePinkSpiderInYellowWoods")
			pk_tuple = hashids.decode(identifier)
			pk_list = list(pk_tuple)
			possible_pk = pk_list[0]/1000033
			if not possible_pk.is_integer():
				raise Http404
			issue_object = get_object_or_404(Issue , pk = possible_pk)
			context = dict()
			context['student'] = issue_object.actor
			context['issue_object'] = issue_object
			context['identifier'] = identifier
			context['issue_type'] = get_issue_name(issue_object.issue_type)
			form_object = IssueReplyForm()
			context['solve_issue_form'] = form_object
			raw_html = render(request , 'notification/submit_solution.html' , context =  context)
			return HttpResponse(raw_html)
		if request.method == 'POST':
			identifier = request.POST.get('identifier' , None)
			if not identifier:
				raise Http404
			hashids = Hashids("ALonePinkSpiderInYellowWoods")
			pk_tuple = hashids.decode(identifier)
			pk_list = list(pk_tuple)
			possible_pk = pk_list[0]/1000033
			if not possible_pk.is_integer():
				raise Http404
			issue_object = get_object_or_404(Issue , pk = possible_pk)
			form_object = IssueReplyForm(request.POST , faculty = request.user.faculty , root_issue = issue_object)
			if form_object.is_valid():
				form_object.save()
				notification_message = "Your issue with subject : " + issue_object.subject + " has been solved."
				notification_object = Notification.objects.create(actor = request.user, target = issue_object.actor.profile, message = notification_message )
				notification_object.save()
				issue_object.solved_by = request.user.faculty
				issue_object.save()

				return HttpResponse(status = 201)
			else:
				raise Http404

	else:
		raise PermissionDenied

@require_GET
@login_required
def display_solution_list(request):
	if request.user.type == 'S':
		student = request.user.student
		issue_object_queryset = Issue.objects.filter(actor = student).order_by('creation_time').reverse()
		data_list = list()
		hashids = Hashids("ALonePinkSpiderInYellowWoods")
		for issue_object in issue_object_queryset:
			data_dict = dict()
			data_dict['issue_type'] = issue_object.issue_type
			data_dict['subject'] = issue_object.subject
			try:
				issue_reply_object = issue_object.issue_reply
				data_dict['is_solved'] = True
			except IssueReply.DoesNotExist:
				data_dict['is_solved'] = False
			pk_id = int(issue_object.pk)
			pk_id = pk_id*1000033
			data_dict['identifier'] = hashids.encode(pk_id)
			data_list.append(data_dict)
		return JsonResponse(data_list , safe = False)
	else:
		PermissionDenied

@require_GET
@login_required
def display_solution(request):
	if request.user.type == 'S':
		identifier = request.GET.get('identifier' , None)
		if not identifier:
			raise Http404
		hashids = Hashids("ALonePinkSpiderInYellowWoods")
		pk_tuple = hashids.decode(identifier)
		pk_list = list(pk_tuple)
		possible_pk = pk_list[0]/1000033
		if not possible_pk.is_integer():
			raise Http404
		issue_object = get_object_or_404(Issue , pk = possible_pk)
		try:
			issue_reply_object = issue_object.issue_reply
		except IssueReply.DoesNotExist:
			raise Http404
		context = dict()
		context['issue_object'] = issue_object
		context['issue_reply_object'] = issue_reply_object
		context['issue_type'] = get_issue_name(issue_object.issue_type)
		raw_html = render(request , 'notification/view_solution.html' , context =  context)
		return HttpResponse(raw_html)
	else:
		raise PermissionDenied

#===============================Utility Functions=====================================#

def get_issue_name(issue_symbol):
	if issue_symbol == 'V':
		return "Verification"
	if issue_symbol == 'P':
		return "Placement"
	if issue_symbol == 'G':
		return "General"
	else:
		raise Http404


def field_length_test(field , length):
	if not field:
		return False
	if len(field) <= length:
		return True
	else:
		return False


def get_notification_actor_name(notification_object , compact = False):
	if not compact:
		if notification_object.actor.type == 'C':
			actor_name = notification_object.actor.college.name
		if notification_object.actor.type == 'F':
			actor_name = notification_object.actor.faculty.college.name
		if	notification_object.actor.type == 'CO':
			actor_name = notification_object.actor.company
	else:
		if notification_object.actor.type == 'C':
			actor_name = notification_object.actor.college.get_short_name()
		if notification_object.actor.type == 'F':
			actor_name = notification_object.actor.faculty.college.get_short_name()
		if	notification_object.actor.type == 'CO':
			actor_name = notification_object.actor.company
			actor_name_template = Template('{{ actor_name|truncatechars:13 }}')
			actor_name_context = Context({'actor_name': actor_name})
			actor_name = actor_name_template.render(actor_name_context)
			return actor_name
	return actor_name


def notification_pk_encoder(pk):
	int_pk = int(pk)
	hashids = Hashids("MysteryTomato")
	pk_id = int_pk*5754853343
	pk_id = hashids.encode(pk_id)
	return pk_id

def notification_pk_decoder(identifier):
	hashids = Hashids("MysteryTomato")
	pk_tuple = hashids.decode(identifier)
	pk_list = list(pk_tuple)		
	possible_pk = pk_list[0]/5754853343
	if not possible_pk.is_integer():
		raise Http404
	notification_object = get_object_or_404(Notification , pk = possible_pk)
	return notification_object		


def clean_string(message , length = 20):
	if len(message) > length:
		message = message[:length]
		message += "..."
	else:
		if len(message) < 1:
			message = "No Details Available"
	return message

