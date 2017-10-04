from django.conf import settings
from django.shortcuts import render ,  get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponseForbidden , HttpResponse , JsonResponse , Http404
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.template import Context, Template
from django.core.exceptions import PermissionDenied
from .forms import SelectStreamsForm , CreateNotificationForm , IssueForm , IssueReplyForm , ReportBugForm
from .models import NotificationData , Notification , Issue , IssueReply
from account.models import CustomUser
from account.decorators import check_recaptcha
from account.tasks import send_mass_mail_task , send_mass_sms_task
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
import logging

notificationLogger = logging.getLogger('notification')

#notificationLogger.info('%s created a notification for %s' % (faculty.username, ','.join(list_student_usernames))
#send_mass_mail_task.delay(Subject, message, [reciever_pks])
#from recruitment.forms import SessionInfoForm
#def send_mass_sms_task(actor_pk, message, reciever_list;phone number, template_name='')


# Create your views here.
@login_required
@require_http_methods(['GET','POST'])
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


@login_required
@require_http_methods(['POST'])
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

@login_required
@require_http_methods(['GET','POST'])
def create_notification(request):
	if request.user.type == 'C' or request.user.type == 'F':
		if request.method == 'POST':
			if request.user.type == 'F':
				college_object = request.user.faculty.college
				faculty_object = request.user.faculty
			else:
				college_object = request.user.college 
			students_selected = request.POST.getlist('student_list[]')
			if not any(students_selected):
				return JsonResponse(status = 400 , data = {'errors' : 'Please select at least 1 Student. Check if Select Year field is not blank.'})
			subject = request.POST.get('subject')
			if '\n' in subject or len(subject) < 1:
				return JsonResponse(status = 400 , data = {'errors' : 'Please enter the Subject Properly.'})
			message = request.POST.get('message')
			if_sms = js_to_django_boolean(request.POST.get('if_sms'))
			if_email = js_to_django_boolean(request.POST.get('if_email'))
			if if_email:
				if len(subject) < 5:
					return JsonResponse(status = 400 , data = {'errors' : 'For E-Mails to be sent, please make sure the subject has at least 5 characters.'})
			sms_message = request.POST.get('sms_message')
			if if_sms:
				if len(sms_message) < 30 or len(sms_message) > 160:
					return JsonResponse(status = 400 , data = {'errors' : 'Please keep the length of SMS Message between 30 and 160 Characters.'})		
			college_customuser_object = college_object.profile
			college_students_queryset = college_object.students.all()
			if not field_length_test(subject , 256):
				return JsonResponse(status = 400 , data = {"error" : "Length Exceeded."})
			student_objects = college_students_queryset.filter(profile__username__in = students_selected)
			student_enrolls = querysets_to_values(student_objects.values('profile__username') , 'profile__username')
			student_phone_numbers = querysets_to_values(student_objects.values('phone_number') , 'phone_number')
			student_pks = querysets_to_values(student_objects.values('profile__pk') , 'profile__pk')
			if if_email:
				send_mass_mail_task.delay(subject , message , student_pks)
				if request.user.type == 'F':
					notificationLogger.info('%s sent E-Mail to %s' % (faculty_object, student_enrolls))
				else:
					notificationLogger.info('%s sent E-Mail to %s' % (college_object, student_enrolls))
			if if_sms:
				send_mass_sms_task.delay(college_object.pk , sms_message , student_phone_numbers , template_name='')
				if request.user.type == 'F':
					notificationLogger.info('%s sent SMS Message to %s' % (faculty_object, student_enrolls))
				else:
					notificationLogger.info('%s sent SMS Message to %s' % (college_object, student_enrolls))
			notification_data_object = NotificationData.objects.create(subject = subject , message = message , sms_message = sms_message)
			if request.user.type == 'F':
				notificationLogger.info('%s created a notification for %s' % (faculty_object, student_enrolls))
			else:
				notificationLogger.info('%s created a notification for %s' % (college_object, student_enrolls))
			for student_object in student_objects:
				student_customeuser_object = student_object.profile
				notification_object = Notification.objects.create(actor = college_customuser_object, target = student_customeuser_object , notification_data = notification_data_object)
				notification_object.save()
			
			#sending it to all the faculties as well. 5th October, 2017
			faculties = college_object.faculties.all()
			for faculty in faculties:
				faculty_customuser_object = faculty.profile
				notification_object = Notification.objects.create(actor = college_customuser_object, target = faculty_customuser_object , notification_data = notification_data_object)
				notification_object.save()
				notificationLogger.info('Winded up faculty. Done all notifications. Bye.') 
			
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

@login_required
@require_http_methods(['GET','POST'])
def get_notifications(request):
	user = request.user
	data_list = list()
	notification_object_queryset = user.notification_target.all().order_by('-creation_time')
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

@check_recaptcha
@login_required
@require_http_methods(['GET','POST'])
def submit_issue(request):
	if request.user.type == 'S':
		if request.method == 'GET':
			form_object = IssueForm()
			raw_html = render(request , 'notification/submit_issue.html' , {'issue_form' : form_object})
			return HttpResponse(raw_html)
		if request.method == 'POST':
			form_object = IssueForm(request.POST , user = request.user.student , college = request.user.student.college)
			if request.recaptcha_is_valid:
				if form_object.is_valid():
					issue = form_object.save()
					notificationLogger.info('%s created an ISSUE %d' % (request.user.username , issue.pk))
					return HttpResponse(status = 201)
				else:
					return JsonResponse(status = 400 , data = {'erros' : form_object._errors})
			else:
				return JsonResponse(status = 403 , data = {'errors' : 'reCAPTCHA authorization failed. Please try again.'} , safe = False)
	else:
		raise PermissionDenied


@require_GET
@login_required
def display_issue(request):
	if request.user.type == 'F':
		college = request.user.faculty.college
		issue_object_queryset = Issue.objects.filter(college = college).filter(issue_reply__isnull = True).order_by('-marked' , '-creation_time')
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



@require_GET
@login_required
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


@login_required
@require_http_methods(['GET','POST'])
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
			if_email = js_to_django_boolean(request.POST.get('if_email'))
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
				issue_object.solved_by = request.user.faculty.get_full_name()
				issue_object.save()
				if if_email:
					send_mass_mail_task.delay('Reply for your Issue' , issue_object.issue_reply.reply , issue_object.actor.pk)
					notificationLogger.info('%s solved an issue; issue pk %d' % (request.user.username, issue_object.pk))
				return HttpResponse(status = 201)
			else:
				return JsonResponse(status = 400 , data = {'errors' : form_object._errors})

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

@require_http_methods(['GET','POST'])
@check_recaptcha
def report(request):
	if request.method == 'GET':
		form_object = ReportBugForm()
		raw_html = render(request , 'notification/report_bug.html' , {'report_form' : form_object})
		return HttpResponse(raw_html)
	if request.method == 'POST':
		if not request.recaptcha_is_valid:
			return JsonResponse(status = 400 , data={'errors' : 'reCAPTCHA authorization failed. Please try again.'})
		form_object = ReportBugForm(request.POST , user = request.user)
		if form_object.is_valid():
			report = form_object.save()
			notificationLogger.info('%s created a report; pk  %d' % (request.user.username , report.pk))
			return JsonResponse(status = 201 , data = {'success' : 'Thanks for your feedback.'})
		else:
			return JsonResponse(status = 400 , data = {'errors' : 'Seems to be a problem with your form. Please fill it again.'})

@require_http_methods(['GET' , 'POST'])
@check_recaptcha
def anonymous_report(request):
	if request.method == 'GET':
		form_object = ReportBugForm()
		raw_html = render(request , 'account/report_bug.html' , {'report_form' : form_object})
		return HttpResponse(raw_html)
	if request.method == 'POST':
		context = dict()
		context['redirect'] = True
		if not request.recaptcha_is_valid:
			context['error'] = True
			context['message'] = 'reCAPTCHA authorization failed. Please try again.'
			form_object = ReportBugForm()
			context['report_form'] = form_object
			raw_html = render(request , 'account/report_bug.html' , context)
			return HttpResponse(raw_html)
		form_object = ReportBugForm(request.POST , user = request.user)
		if form_object.is_valid():
			form_object.save()
			context['error'] = False
			context['message'] = 'Thanks for your feedback.'
			form_object = ReportBugForm()
			context['report_form'] = form_object
			raw_html = render(request , 'account/report_bug.html' , context)
			return HttpResponse(raw_html)
		else:
			context['error'] = True
			context['message'] = 'Seems to be a problem with your form. Please fill it again..'
			form_object = ReportBugForm()
			context['report_form'] = form_object
			raw_html = render(request , 'account/report_bug.html' , context)
			return HttpResponse(raw_html)

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
		anchor_index = message.find('<a')
		if anchor_index != -1:
			message = message[:anchor_index]
		else:
			message = message[:length]
		message += "..."
	else:
		if len(message) < 1:
			message = "No Details Available"
	return message


def querysets_to_values(queryset , key):
	result_list = list()
	for modal_instance in queryset:
		result_list.append(modal_instance[key])
	return result_list

def js_to_django_boolean(input):
    if input.lower() == 'false':
        return False
    elif input.lower() == 'true':
        return True
    else:
        return False
