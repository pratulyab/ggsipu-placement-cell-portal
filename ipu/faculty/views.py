from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.decorators import require_user_types, require_AJAX
from account.forms import AccountForm, SocialProfileForm, SetPasswordForm
from account.models import CustomUser, SocialProfile
from account.tasks import send_activation_email_task
from account.tokens import time_unbounded_activation_token_generator
from account.utils import handle_user_type, get_relevant_reversed_url
from college.models import College
from dummy_company.forms import DummySessionFilterForm
from faculty.forms import FacultySignupForm, FacultyProfileForm, EnrollmentForm, EditGroupsForm, ChooseFacultyForm, VerifyStudentProfileForm
from faculty.models import Faculty
from notification.models import Notification
from notification.forms import NotifySessionStudentsForm
from recruitment.forms import SessionFilterForm
from student.models import Qualification, Student
from student.forms import QualificationForm, ScoreMarksheetForm, CGPAMarksheetForm, ScoreForm, QualForm
import re

# Create your views here.
import logging
collegeLogger = logging.getLogger('college')
facultyLogger = logging.getLogger('faculty')

@login_required
@require_POST
def faculty_signup(request):
	user = request.user
	if request.is_ajax():
		if user.type == 'C':
			f = FacultySignupForm(request.POST)
			f.instance.type = 'F'
			if f.is_valid():
				faculty = f.save()
				f.save_m2m()
				Faculty.objects.create(profile=faculty, college=user.college)
				collegeLogger.info('[%s] - %s added faculty %s' % (user.college.code, user.username, faculty.username))
				send_activation_email_task.delay(faculty.pk, get_current_site(request).domain)
				message = 'Faculty %s has been added.' % (faculty.username)
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['C']), 'refresh': True, message: message})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request), 'refresh': True})
	else:
		return handle_user_type(request, redirect_request=True)

@login_required
@require_http_methods(['GET','POST'])
def edit_create_faculty(request, **kwargs):
	if request.is_ajax():
		if request.user.type == 'F' and request.method == 'POST':
			faculty = request.user.faculty
			f = FacultyProfileForm(request.POST, request.FILES, instance=faculty)
			photo = faculty.photo
			if f.is_valid():
				f.save()
				if photo and photo != faculty.photo:
					try:
						os.remove(os.path.join(settings.BASE_DIR, photo.url[1:]))
					except:
						pass
				context = {}
				context['faculty_edit_form'] = FacultyProfileForm(instance=faculty)
				if f.has_changed():
					context['success_msg'] = "Profile has been updated successfully!"
				return JsonResponse(status=200, data={'render': render(request, 'faculty/profile_form.html', context).content.decode('utf-8')})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
# To handle initial creation form
		if request.user.type == 'F':
			context = {}
			if request.method == 'GET':
				f = FacultyProfileForm(instance=request.user.faculty)
			else:
				f = FacultyProfileForm(request.POST, request.FILES, instance=request.user.faculty)
				if f.is_valid():
					f.save()
					if f.has_changed():
						context['update'] = True
					return redirect(settings.HOME_URL['F'])
			context['faculty_edit_create_form'] = f
			return render(request, 'faculty/edit_create.html', context)
		else:
			return handle_user_type(request, redirect_request=True)

@require_user_types(['F'])
@login_required
@require_GET
def faculty_home(request, **kwargs):
##	if request.user.type == 'F':
	if not request.user.faculty.firstname:
		return redirect(settings.PROFILE_CREATION_URL['F'])
	user = request.user
	faculty = user.faculty
	context = {}
	context['user'] = user
	context['faculty'] = faculty
	context['edit_account_form'] = AccountForm(instance=user)
	context['edit_faculty_form'] = FacultyProfileForm(instance=faculty)
	context['enrollment_form'] = EnrollmentForm(faculty=faculty)
	context['notify_session_students_form'] = NotifySessionStudentsForm()
	context['session_filter_form'] = SessionFilterForm(profile=faculty.college)
	context['dsession_filter_form'] = DummySessionFilterForm(college=faculty.college)
	try:
		context['social_profile_form'] = SocialProfileForm(instance=user.social)
	except SocialProfile.DoesNotExist:
		context['social_profile_form'] = SocialProfileForm()
	context['badge'] = (faculty.college.profile.notification_target.filter(is_read=False).count() + faculty.profile.notification_target.filter(is_read=False).count())
	return render(request, 'faculty/home.html', context)
##	else:
##		return handle_user_type(request, redirect_request=True)

#@user_passes_test(lambda u: u.groups.filter(name='Verifier')) cant use this because need to return Jsonresp
@require_user_types(['F'])
@login_required
@require_http_methods(['GET','POST'])
def get_enrollment_number(request, profile, user_type):
	if not request.is_ajax():
#		return handle_user_type(request)
		raise PermissionDenied('')
	if not request.user.groups.filter(name='Verifier'):
		return JsonResponse(status=403, data={'error': 'Permission Denied. You cannot verify students'})
	if request.method == 'GET':
		try:
			del request.session['enrollmentno']
		except KeyError:
			pass
		return render(request, 'faculty/verify.html', {'enroll_form': EnrollmentForm(faculty=profile)})
		
	else:
		f = EnrollmentForm(request.POST, faculty=profile)
		if f.is_valid():
			request.session['enrollmentno'] = f.cleaned_data['enroll']
			student = CustomUser.objects.get(username=request.session['enrollmentno']).student
#			profile_form = render(request, 'faculty/verify_profile_form.html', {'profile_form': VerifyStudentProfileForm(instance=student)}).content.decode('utf-8')
			profile_form = render(request, 'faculty/verify_profile.html', {'profile_form':VerifyStudentProfileForm(instance=student)}).content.decode('utf-8')
			'''
			try:
				q = QualificationForm(instance=student.qualifications)
			except Qualification.DoesNotExist:
				q = QualificationForm()
			grad_form = render(request, 'faculty/verify_qual_form.html', {'qual_form': q}).content.decode('utf-8')
			'''
			q = QualForm(instance=student.qualifications)
			grad_form = render(request, 'faculty/verify_grad_form.html', {'grad_form': q}).content.decode('utf-8')
# # # Tenth # # # 
			tenth_form = None
			if student.marksheet.marksheet_10:
				marksheet_10 = student.marksheet.marksheet_10
				tenth_form = ScoreMarksheetForm(klass='10', instance=marksheet_10, prefix='10') # Board
				scores = []
				for i in range(1,7):
					score = getattr(marksheet_10, 'score%d'%(i))
					subject = score.subject.__str__() if score.subject else "%s" % (score.subject_name or '-')
					marks = score.marks
					key = int("%s%d" % ('10',i)) # 103 => 10klass, score3
					hashid = settings.HASHID_SCORE.encode(key)
					scores.append({'subject': subject, 'marks': marks, 'hashid': hashid})
				klass_hashid = settings.HASHID_KLASS.encode(10)
				tenth_form = render(request, 'faculty/verify_scores.html',{'board_form': tenth_form, 'scores': scores, 'hashid':klass_hashid}).content.decode('utf-8')
			else:
				tenth_form = CGPAMarksheetForm(instance=student.marksheet.cgpa_marksheet, prefix="cgpa")
				hashid = settings.HASHID_KLASS.encode(10)
				tenth_form = render(request, 'faculty/verify_cgpa_form.html', {'cgpa_form': tenth_form, 'hashid': hashid}).content.decode('utf-8')
# # # Twelfth # # # 
			twelfth_form = ScoreMarksheetForm(klass='12', instance=student.marksheet.marksheet_12, prefix='12')
			scores = []
			for i in range(1,7):
				score = getattr(student.marksheet.marksheet_12, 'score%d'%(i))
				subject = score.subject.__str__() if score.subject else "%s" % (score.subject_name or '-')
				marks = score.marks
				key = int("%s%d" % ('12',i)) # 126 => 12klass, score6
				hashid = settings.HASHID_SCORE.encode(key)
				scores.append({'subject': subject, 'marks': marks, 'hashid': hashid})
			klass_hashid = settings.HASHID_KLASS.encode(12)
			twelfth_form = render(request, 'faculty/verify_scores.html',{'board_form': twelfth_form, 'scores': scores, 'hashid':klass_hashid}).content.decode('utf-8')
# # # # # # # # # #
			return JsonResponse(status=200, data={'tenth': tenth_form, 'twelfth': twelfth_form, 'profile': profile_form, 'grad': grad_form})
#			return HttpResponse(profile_form+"<<<>>>"+qual_form)
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['C'])
@require_AJAX
@login_required
@require_POST
def delete_faculty(request, f_hashid, user_type, profile):
	try:
		faculty_pk = settings.HASHID_FACULTY.decode(f_hashid)[0]
		faculty = profile.faculties.prefetch_related('profile').get(pk=faculty_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	try:
		faculty.profile.delete()
		collegeLogger.info('[%s] - %s deleted faculty %s' % (profile.code, request.user.username, faculty.profile.username))
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, couldn\'t complete the deletion request. Please try again after some time.'})
	return JsonResponse(status=200, data={'success_msg': 'Deletion request successful'})

@require_user_types(['C'])
@require_AJAX
@login_required
@require_http_methods(['GET', 'POST'])
def edit_perms(request, f_hashid, user_type, profile):
	try:
		faculty_pk = settings.HASHID_FACULTY.decode(f_hashid)[0]
		faculty = profile.faculties.prefetch_related('profile').get(pk=faculty_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	if request.method == 'POST':
		f = EditGroupsForm(request.POST, instance=faculty.profile)
		if f.is_valid():
			f.save()
			if f.changed_data:
				collegeLogger.info('[%s] - %s changed perms of faculty %s to: %s' % (profile.code, request.user.username, faculty.profile.username, ','.join(f.changed_data)))
			return JsonResponse(status=200, data={'success_msg': 'Permissions have been updated successfully.'})
	else:
		context = {'edit_faculty_perms_form': EditGroupsForm(instance=faculty.profile), 'f_hashid': f_hashid}
		return JsonResponse(status=200, data={'html': render(request, 'faculty/edit_perms.html', context).content.decode('utf-8')})

@require_user_types(['C'])
@login_required
@require_GET
def manage(request, user_type, profile):
	faculties = []
	for faculty in profile.faculties.all():
		faculties.append({'faculty': faculty, 'f_hashid': settings.HASHID_FACULTY.encode(faculty.pk)})
	context = {
		'create_faculty_form': FacultySignupForm(),
		'choose_faculty_form': ChooseFacultyForm(college=profile),
		'college': profile,
		'faculties': faculties
	}
	return render(request, 'faculty/manage_faculty.html', context)

@require_user_types(['F'])
@login_required
@require_POST
def verify_cgpa(request, klass_hashid, user_type, profile, **kwargs):
	if not request.is_ajax():
		raise PermissionDenied('')
	if not request.user.groups.filter(name='Verifier'):
		return JsonResponse(status=403, data={'error': 'Permission Denied. You cannot verify students'})
	try:
		klass = str(settings.HASHID_KLASS.decode(klass_hashid)[0])
		if klass not in ['10','12']:
			raise TypeError
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request'})
	try:
		student = Student.objects.get(profile__username=request.session['enrollmentno'])
		marksheet = student.marksheet
		cgpa_marksheet = marksheet.cgpa_marksheet
		if not cgpa_marksheet:
			return JsonResponse(status=400, data={'error': 'Student hasn\'t added CGPA qualifications'})
	except:
		return JsonResponse(status=400, data={'error': 'Your session has expired. Please refresh and continue'})
	if student.college != profile.college:
		return JsonResponse(status=403, data={'error': 'Permission Denied. You can verify students of your college only'})
	f = CGPAMarksheetForm(request.POST, instance=cgpa_marksheet, prefix='cgpa')
	if f.is_valid():
		f.save()
		if f.changed_data:
			facultyLogger.info("CGPA: %s[%d] updated %s for %s[%d]" % (profile.profile.username, profile.profile.pk, ','.join(f.changed_data),\
						student.profile.username, student.profile.pk))
		return JsonResponse(status=200, data={'message': 'CGPA changes have been updated.\nProceed to "Twelfth Qualifications".'})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'error': 'Please correct the errors as indicated in the form', 'prefix':f.prefix+'-'})

@require_user_types(['F'])
@login_required
@require_POST
def verify_board(request, klass_hashid, user_type, profile, **kwargs):
	if not request.is_ajax():
		raise PermissionDenied('')
	if not request.user.groups.filter(name='Verifier'):
		return JsonResponse(status=403, data={'error': 'Permission Denied. You cannot verify students'})
	try:
		klass = str(settings.HASHID_KLASS.decode(klass_hashid)[0])
		if klass not in ['10','12']:
			raise TypeError
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request'})
	try:
		student = Student.objects.get(profile__username=request.session['enrollmentno'])
		marksheet = getattr(student.marksheet, 'marksheet_%s'%klass)
		if not marksheet:
			return JsonResponse(status=400, data={'error': 'Student hasn\'t added %sth marksheet' % klass})
	except:
		return JsonResponse(status=400, data={'error': 'Your session has expired. Please refresh and continue'})
	if student.college != profile.college:
		return JsonResponse(status=403, data={'error': 'Permission Denied. You can verify students of your college only'})
	f = ScoreMarksheetForm(request.POST, klass=klass, instance=marksheet, prefix=klass)
	if f.is_valid():
		f.save()
		if f.changed_data:
			facultyLogger.info("Board: %s[%d] updated %s for %s[%d]" % (profile.profile.username, profile.profile.pk, ','.join(f.changed_data),\
						student.profile.username, student.profile.pk))
		return JsonResponse(status=200, data={'message': 'Examination Board changes have been updated.'})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'error': 'Please correct the errors as indicated in the form', 'prefix':f.prefix+'-'})


