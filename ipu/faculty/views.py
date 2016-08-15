from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.models import CustomUser
from account.views import handle_user_type, send_activation_email
from college.models import College
from faculty.forms import FacultySignupForm, FacultyProfileForm, EnrollmentForm
from faculty.models import Faculty
from student.forms import StudentEditForm, QualificationForm
import re

# Create your views here.

@require_http_methods(['GET','POST'])
@login_required
def faculty_signup(request):
	if request.user.type == 'C':
		try:
			request.user.college
		except College.DoesNotExist:
			return redirect('create_college')
		if request.method == 'GET':
			f = FacultySignupForm()
		else:
			f = FacultySignupForm(request.POST)
			f.instance.type = 'F'
			if f.is_valid():
				faculty = f.save()
				f.save_m2m()
				try:
					Faculty.objects.create(profile=faculty, college=request.user.college)
				except ValidationError:
					raise Http404(_('Faculty couldn\'t be created.'))
				faculty = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
				send_activation_email(faculty, get_current_site(request).domain)
				return redirect('college_home')
		return render(request, 'faculty/signup.html', {'faculty_signup_form':f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_create_faculty(request):
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
		context = {}
		context['user'] = request.user
		context['faculty'] = request.user.faculty
		return render(request, 'faculty/home.html', context)
	else:
		return handle_user_type(request, redirect_request=True)

#@require_http_methods(['GET','POST','DELETE'])
#def cookies_enabled(request):
#	if request.session.test_cookie_worked():
#		request.session.delete_test_cookie()
#		return True
#	else:
#		return False

@require_http_methods(['GET','POST'])
@login_required
def get_enrollment_number(request):
	if request.user.type == 'F':
		if request.method == 'GET':
#		request.session.set_test_cookie()
			try:
				del request.session['enrollmentno']
			except KeyError:
				pass
			return render(request, 'faculty/verify.html', {'enroll_form': EnrollmentForm(faculty=request.user.faculty)})
			
		else:
#		if not cookies_enabled(request):
#			messages.error(request, 'Cookies are disabled in your browser. Please enable cookies and try again.')
#			return HttpResponse('')
#		
			f = EnrollmentForm(request.POST, faculty=request.user.faculty)
			if f.is_valid():
				request.session['enrollmentno'] = f.cleaned_data['enroll']
				student = CustomUser.objects.get(username=request.session['enrollmentno']).student
#				profile_form = render_to_string('faculty/verify_profile_form.html', {'profile_form': StudentEditForm(instance=student)})
#				qual_form = render_to_string('faculty/verify_qual_form.html', {'qual_form': QualificationEditForm(instance=student)})
				profile_form = render(request, 'faculty/verify_profile_form.html', {'profile_form': StudentEditForm(instance=student)}).content.decode('utf-8')
				try:
					q = QualificationForm(instance=student.qualifications)
				except:
					q = QualificationForm()
				qual_form = render(request, 'faculty/verify_qual_form.html', {'qual_form': q}).content.decode('utf-8')
				return HttpResponse(profile_form+"<<<>>>"+qual_form)
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		return handle_user_type(request, redirect_request = True)

@require_http_methods(['GET', 'POST'])
@login_required
def verify(request, enroll=None, verified=None):
	return render(request, 'faculty/verify.html', {'enroll_form': EnrollmentForm()})
	"""
	if request.user.type == 'F':
		if not request.user.faculty.firstname:
			return redirect('edit_create_faculty')
		if not enroll:
			return render(request, 'faculty/verify.html')
		user = get_object_or_404(CustomUser, username=enroll)
		context = {}
		if request.method == 'GET':
			f = StudentEditForm(instance=user.student)
		else:
			f = StudentEditForm(request.POST, request.FILES, instance=user.student)
			if f.is_valid():
				student = f.save()
				student.is_verified = verified
				student.verified_by = request.user
				return redirect('verify')
		context['student_edit_form'] = f
		context['enroll'] = enroll
		return render(request, 'faculty/verify.html', context)
	"""