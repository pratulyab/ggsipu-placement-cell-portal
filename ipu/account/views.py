from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.forms import AccountForm, ForgotPasswordForm, LoginForm, SetPasswordForm, SignupForm, SocialProfileForm
from account.models import CustomUser, SocialProfile
from college.forms import CollegeCreationForm
from college.models import College, Stream
from company.forms import CompanyCreationForm
from company.models import Company
from faculty.forms import FacultyProfileForm
from faculty.models import Faculty
from student.forms import StudentCreationForm
from student.models import Student
import re

# Create your views here

@require_http_methods(['GET', 'POST'])
def login(request):
	if request.user.is_authenticated():
		return handle_user_type(request)
	if request.method == 'GET':
		f = LoginForm()
	else:
		f = LoginForm(request.POST)
		if f.is_valid():
			user = f.get_user()
			user = auth_login(request, user)
			return handle_user_type(request, redirect_request=True)
		else:
			return render(request, 'account/login.html', {'login_form': f})
	return render(request, 'account/login.html', {'login_form': f})

@require_GET
def activate(request, uid=None, token=None):
	if request.user.is_authenticated():
		data = get_type_created(request.user)
		user_type = data.pop('user_type')
		if request.user.is_active:
			return redirect(get_home_url(user_type))
	
	if uid is None or token is None:
		raise Http404(_('Invalid Request'))

	user = get_object_or_404(CustomUser, id=uid)
	token_username = force_text(urlsafe_base64_decode(token))
	
	if user.is_active:
		return redirect('login')
	
	if user.username == token_username:
		user.is_active = True
		user.save()
		return render(request, 'account/activation_success.html')
	else:
		return render(request, 'account/activation_failure.html')

@require_http_methods(['GET', 'POST'])
def forgot_password(request):
	if request.user.is_authenticated():
		return redirect(get_home_url(request.user.type))
	if request.method == 'GET':
		f = ForgotPasswordForm()
	if request.method == 'POST':
		f = ForgotPasswordForm(request.POST)
		if f.is_valid():
			user = CustomUser.objects.get(email = f.cleaned_data['email'])
			email_body_context = {
				'username' : user.username,
				'token': default_token_generator.make_token(user),
				'uid' : user.id,
				'protocol': 'http',
				'domain' : get_current_site(request).domain
			}
			body = loader.render_to_string('account/forgot_password_email_body_text.html', email_body_context)
			email_message = EmailMultiAlternatives('Reset your password',body, settings.DEFAULT_FROM_EMAIL, [user.email])
			email_message.send()
			context = { 'email' : user.email }
			return render(request, 'account/forgot_password_email_sent.html',context)
	context = {'form' : f}
	return render(request, 'account/forgot_password.html', context)

@require_http_methods(['GET', 'POST'])
def reset_password(request, uid = None, token=None):
	if request.user.is_authenticated():
		return redirect(get_home_url(request.user.type))
	try:
		user = CustomUser.objects.get(id = uid)
	except (CustomUser.DoesNotExist):
		user = None
	if not user or not default_token_generator.check_token(user, token):
		context = { 'validlink' : False}
		return render(request, 'account/set_password.html', context)
	if request.method == 'GET':
		f = SetPasswordForm()
	else:
		f = SetPasswordForm(request.POST)
		if f.is_valid():
			user.set_password(f.cleaned_data['password1'])
			user.save()
			return redirect('login')
	context = { 'validlink' : True, 'form' : f}
	return render(request, 'account/set_password.html', context)

@require_http_methods(['GET','POST'])
@login_required
def edit_account(request):
#	if not request.user.is_active:
	data = get_type_created(request.user)
	if data.get('profile') is None:
		return render_profile_creation(request, data.get('user_type'))
	context = {}
	if request.method == 'GET':
		f = AccountForm(instance=request.user)
	else:
		f = AccountForm(request.POST, instance=request.user)
		if f.is_valid():
			if f.has_changed:
				context['update'] = True
			f.save()
			if f.password_changed:
				user = authenticate(username=f.cleaned_data.get('username'), password=f.cleaned_data.get('new_password'))
				if user:
					auth_login(request, user)
	context['edit_account_form'] = f
	context['url'] = reverse(get_home_url(request.user.type))
	return render(request, 'account/edit.html', context)

@require_GET
@login_required
def home(request):
	return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def logout(request):
	if request.user.type == 'S':
		auth_logout(request)
		return redirect('student_login')
	else:
		auth_logout(request)
		return redirect('login')

# Methods that aren't mapped to any URL

@require_http_methods(['GET','POST'])
@login_required
def handle_user_type(request, redirect_request=False):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if data:
#		if request.method == 'GET':
#			print(request.GET.get('next'))
#		Yet to implemented
		return redirect(get_home_url(user_type))
	else:
		if redirect_request:
			return redirect_profile_creation(request, user_type)
		else:
			return render_profile_creation(request, user_type)

@require_http_methods(['GET','POST'])
@login_required
def render_profile_creation(request, user_type):
	if user_type == 'C':
		return render(request, 'college/create.html', {'college_creation_form': CollegeCreationForm()})
	elif user_type == 'F':
		return render(request, 'faculty/edit_create.html', {'faculty_edit_create_form': FacultyProfileForm(instance=request.user.faculty)})
	elif user_type == 'S':
		user_profile = request.user
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', user_profile.username).groups()
		except AttributeError:
#			pass
			raise Http404(_('Enrollment number should contain only digits'))
		except ValueError:
#			pass
			raise Http404(_('Enrollment number should be 11 digits long'))
		coll = College.objects.get(code=coll).pk
		strm = Stream.objects.get(code=strm).pk
		return render(request, 'student/create.html', {'student_creation_form': StudentCreationForm(profile=user_profile, coll=coll, strm=strm)})
	else:
		return render(request, 'company/create.html', {'company_creation_form': CompanyCreationForm()})

@require_http_methods(['GET','POST'])
@login_required
def redirect_profile_creation(request, user_type):
	if user_type == 'C':
		return redirect('create_college')
	elif user_type == 'F':
		return redirect('edit_create_faculty')
	elif user_type == 'S':
		return redirect('create_student')
	else:
		return redirect('create_company')

@require_GET
@login_required
def view_profile(request, username):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return render_profile_creation(request, user_type)
	if request.user.username == username:
		return redirect(get_home_url(user_type))
	user = get_object_or_404(CustomUser, username=username)
	
	requested_data = get_type_created(user)
	requested_user_type = requested_data.pop('user_type')
	if not requested_data:
		raise Http404(_('User hasn\'t created the profile yet. Stay tuned.'))
	else:
		context = {}
		profile = requested_data.pop('profile')
		context['url'] = reverse(get_home_url(user_type))
		print(context['url'])
		if requested_user_type == 'C':
			context['college'] = profile
			return render(request, 'college/pub_profile.html', context)
		elif requested_user_type == 'F':
			context['faculty'] = profile
			return render(request, 'faculty/pub_profile.html', context)
		elif requested_user_type == 'S':
			context['student'] = profile
			return render(request, 'student/pub_profile.html', context)
		else:
			context['company'] = profile
			return render(request, 'company/pub_profile.html', context)

# Methods for facilitation. No 'request' requirement

def send_activation_email(user, domain):

	email_body_context = {
		'username': user.username,
		'token': urlsafe_base64_encode(force_bytes(user.username)),
		'uid': user.id,
		'protocol': 'http',
		'domain': domain
	}
	body = loader.render_to_string('account/activation_email_body.html', email_body_context)
	email_message = EmailMultiAlternatives('Activate Account', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	print(settings.DEFAULT_FROM_EMAIL)
	email_message.send()


def get_type_created(user):
	user_type = user.type
	if user_type == 'C':
		try:
			college = CustomUser.objects.get(username = user.username).college
			return ({'profile': college, 'user_type': user_type})
		except:
			return ({'user_type': user_type})
	elif user_type == 'F':
		try:
			faculty = CustomUser.objects.get(username = user.username).faculty
			if not faculty.firstname:
				return ({'user_type': user_type})
			return ({'profile': faculty, 'user_type': user_type})
		except:
			return ({'user_type': user_type})
	elif user_type == 'S':
		try:
			student = CustomUser.objects.get(username = user.username).student
			return ({'profile': student, 'user_type': user_type})
		except:
			return ({'user_type': user_type})
	else:
		try:
			company = CustomUser.objects.get(username = user.username).company
			return ({'profile': company, 'user_type': user_type})
		except:
			return ({'user_type': user_type})

def get_home_url(user_type):
	if user_type == 'C':
		return 'college_home'
	elif user_type == 'F':
		return 'faculty_home'
	elif user_type == 'S':
		return 'student_home'
	else:
		return 'company_home'
