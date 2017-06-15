from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.decorators import require_user_types, require_AJAX
from account.forms import AccountForm, SocialProfileForm, SetPasswordForm
from account.models import CustomUser, SocialProfile
from account.tasks import send_activation_email_task
from account.tokens import faculty_activation_token_generator
from account.utils import handle_user_type, get_relevant_reversed_url
from college.models import College
from dummy_company.forms import DummySessionFilterForm
from faculty.forms import FacultySignupForm, FacultyProfileForm, EnrollmentForm, EditGroupsForm, ChooseFacultyForm, VerifyStudentProfileForm
from faculty.models import Faculty
from notification.models import Notification
from recruitment.forms import SessionFilterForm
from student.models import Qualification
from student.forms import QualificationForm
import re

# Create your views here.

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
				#faculty = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
				send_activation_email_task.delay(faculty.pk, get_current_site(request).domain)
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['C'])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
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
		return handle_user_type(request)
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
			profile_form = render(request, 'faculty/verify_profile_form.html', {'profile_form': VerifyStudentProfileForm(instance=student)}).content.decode('utf-8')
			try:
				q = QualificationForm(instance=student.qualifications)
			except Qualification.DoesNotExist:
				q = QualificationForm()
			qual_form = render(request, 'faculty/verify_qual_form.html', {'qual_form': q}).content.decode('utf-8')
			return HttpResponse(profile_form+"<<<>>>"+qual_form)
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['C'])
@require_AJAX
@login_required
@require_POST
def delete_faculty(request, f_hashid, user_type, profile):
	try:
		faculty_pk = settings.HASHID_FACULTY.decode(f_hashid)[0]
		faculty = profile.faculties.get(pk=faculty_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	try:
		faculty.profile.delete()
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
		faculty = profile.faculties.get(pk=faculty_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	if request.method == 'POST':
		f = EditGroupsForm(request.POST, instance=faculty.profile)
		if f.is_valid():
			f.save()
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

@require_http_methods(['GET','POST'])
def activate(request, user_hashid, token):
	''' Activates faculty by allowing to set a usable password '''
	if request.user.is_authenticated():
		return redirect(settings.HOME_URL[request.user.type])
	try:
		user = CustomUser.objects.get(pk=settings.HASHID_CUSTOM_USER.decode(user_hashid)[0])
	except (IndexError, CustomUser.DoesNotExist):
		return render(request, 'faculty/activation.html', {'invalid': True})
	if user.has_usable_password() or not faculty_activation_token_generator.check_token(user, token):
		''' This means that the activation link for the faculty has already been used. '''
		return render(request, 'faculty/activation.html', {'invalid': True})
	if request.method == 'GET':
		f = SetPasswordForm()
	else:
		f = SetPasswordForm(request.POST)
		if f.is_valid():
			user.set_password(f.cleaned_data['password2'])
			user.is_active = True
			user.save()
			return render(request, 'faculty/activation.html', {'successful': True})
	return render(request, 'faculty/activation.html', {'set_password_form': f, 'user_hashid': user_hashid, 'token': token})
