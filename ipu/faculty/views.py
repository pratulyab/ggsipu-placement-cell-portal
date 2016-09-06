from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.models import CustomUser, SocialProfile
from account.forms import AccountForm, SocialProfileForm
from account.views import handle_user_type, send_activation_email, get_relevant_reversed_url, get_home_url
from college.models import College
from faculty.forms import FacultySignupForm, FacultyProfileForm, EnrollmentForm
from faculty.models import Faculty
from notification.models import Notification
from student.forms import StudentEditForm, QualificationForm
import re

# Create your views here.

@require_POST
@login_required
def faculty_signup(request):
	user = request.user
	if request.is_ajax():
		if user.type == 'C':
			f = FacultySignupForm(request.POST)
			f.instance.type = 'F'
			if f.is_valid():
				faculty = f.save()
				Faculty.objects.create(profile=faculty, college=user.college)
				faculty = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
				send_activation_email(faculty, get_current_site(request).domain)
				return JsonResponse(status=200, data={'location': reverse(get_home_url('C'))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_create_faculty(request):
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
			context['faculty_edit_create_form'] = f
			return render(request, 'faculty/edit_create.html', context)
		else:
			return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def faculty_home(request):
	if request.user.type == 'F':
		if not request.user.faculty.firstname:
			return redirect('edit_create_faculty')
		user = request.user
		faculty = user.faculty
		context = {}
		context['user'] = user
		context['faculty'] = faculty
		context['edit_account_form'] = AccountForm(instance=user)
		context['edit_faculty_form'] = FacultyProfileForm(instance=faculty)
		context['enrollment_form'] = EnrollmentForm(faculty=faculty)
		try:
			context['social_profile_form'] = SocialProfileForm(instance=user.social)
		except SocialProfile.DoesNotExist:
			context['social_profile_form'] = SocialProfileForm()
		return render(request, 'faculty/home.html', context)
		context['badge'] = (faculty.college.profile.notification_target.filter(is_read=False).count() + faculty.profile.notification_target.filter(is_read=False).count())
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def get_enrollment_number(request):
	if not request.is_ajax():
		return handle_user_type(request)
	if request.user.type == 'F':
		if request.method == 'GET':
			try:
				del request.session['enrollmentno']
			except KeyError:
				pass
			return render(request, 'faculty/verify.html', {'enroll_form': EnrollmentForm(faculty=request.user.faculty)})
			
		else:
			f = EnrollmentForm(request.POST, faculty=request.user.faculty)
			if f.is_valid():
				request.session['enrollmentno'] = f.cleaned_data['enroll']
				student = CustomUser.objects.get(username=request.session['enrollmentno']).student
				profile_form = render(request, 'faculty/verify_profile_form.html', {'profile_form': StudentEditForm(instance=student)}).content.decode('utf-8')
				try:
					q = QualificationForm(instance=student.qualifications)
				except Qualification.DoesNotExist:
					q = QualificationForm()
				qual_form = render(request, 'faculty/verify_qual_form.html', {'qual_form': q}).content.decode('utf-8')
				return HttpResponse(profile_form+"<<<>>>"+qual_form)
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
