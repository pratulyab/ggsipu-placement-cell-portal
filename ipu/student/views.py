from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.models import CustomUser
from account.views import handle_user_type, send_activation_email
from college.models import College, Stream
from student.forms import StudentLoginForm, StudentSignupForm, StudentCreationForm, StudentEditForm
from student.models import Student

import re

# Create your views here.

@require_http_methods(['GET','POST'])
def student_login(request):
	if request.user.is_authenticated():
		return handle_user_type(request)
	if request.method == 'GET':
		f = StudentLoginForm()
	else:
		f = StudentLoginForm(request.POST)
		if f.is_valid():
			user = f.get_user()
			user = auth_login(request, user)
			return handle_user_type(request)
		else:
			return render(request, 'student/login.html', {'student_login_form': f})
	return render(request, 'student/login.html', {'student_login_form': f})

@require_http_methods(['GET','POST'])
def student_signup(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	if request.method == 'GET':
		f = StudentSignupForm()
	else:
		f = StudentSignupForm(request.POST)
		if f.is_valid():
			student = f.save()
			student = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
			context = {}
			if student:
				auth_login(request, student)
				context['email'] = student.email
				context['profile_creation'] = request.build_absolute_uri(reverse('create_student'))
				send_activation_email(student, get_current_site(request).domain)
				return render(request, 'account/post_signup.html', context)
	return render(request, 'student/signup.html', {'student_signup_form': f})

@require_http_methods(['GET','POST'])
@login_required
def create_student(request):
	if request.user.type == 'S':
		username = request.user.username
		user_profile = request.user
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', username).groups()
		except AttributeError:
#			pass
			raise Http404(_('Enrollment number should contain only digits'))
		except ValueError:
#			pass
			raise Http404(_('Enrollment number should be 11 digits long'))
		coll = College.objects.get(code=coll).pk
		strm = Stream.objects.get(code=strm).pk
		if request.method == 'GET':
			f = StudentCreationForm(profile=user_profile, coll=coll, strm=strm)
			try:
				student = request.user.student
				return redirect('student_home')
			except Student.DoesNotExist:
				pass
		else:
			POST = request.POST.copy()
			POST['college'] = coll
			POST['stream'] = strm
			POST['programme'] = Stream.objects.get(pk=strm).programme.pk
			f = StudentCreationForm(POST, request.FILES, profile=user_profile, coll=coll, strm=strm)
			if f.is_valid():
				student = f.save()
				return redirect('student_home')
		return render(request, 'student/create.html', {'student_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def student_home(request):
	if request.user.type == 'S':
		context = {}
		context['user'] = request.user
		try:
			context['student'] = request.user.student
			return render(request, 'student/home.html', context)
		except Student.DoesNotExist:
			return redirect('create_student')
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_student(request):
	if request.user.type == 'S':
		username = request.user.username
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', username).groups()
		except AttributeError:
#			pass
			raise Http404(_('Enrollment number should contain only digits'))
		except ValueError:
#			pass
			raise Http404(_('Enrollment number should be 11 digits long'))
		coll = College.objects.get(code=coll).pk
		strm = Stream.objects.get(code=strm).pk
		try:
			context = {}
			student = request.user.student
			if student.is_verified == True:
				#Message
				return redirect('student_home')
			elif student.is_verified == False and student.verified_by == None:
				return redirect('student_home')
			
			if request.method == 'GET':
				f = StudentEditForm(coll=coll, strm=strm, instance=student)
			else:
				POST = request.POST.copy()
				POST['college'] = coll
				POST['stream'] = strm
				POST['programme'] = Stream.objects.get(pk=strm).programme.pk
				f = StudentEditForm(POST, request.FILES, coll=coll, strm=strm, instance=student)
				if f.is_valid():
					f.save()
					if f.has_changed():
						context['update'] = True
						# Instead use message
			context['student_edit_form'] = f
			return render(request, 'student/edit.html', context)
		except Student.DoesNotExist:
			user_profile = request.user
			try:
				roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', user_profile.username).groups()
			except AttributeError:
#				pass
				raise Http404(_('Enrollment number should contain only digits'))
			except ValueError:
#				pass
				raise Http404(_('Enrollment number should be 11 digits long'))
			coll = College.objects.get(code=coll).pk
			strm = Stream.objects.get(code=strm).pk
			return render(request, 'student/create.html', {'student_creation_form': StudentCreationForm(profile=user_profile, coll=coll, strm=strm)})
	else:
		return handle_user_type(request)
