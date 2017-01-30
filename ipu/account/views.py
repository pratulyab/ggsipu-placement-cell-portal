from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import require_AJAX
from account.forms import AccountForm, ForgotPasswordForm, LoginForm, SetPasswordForm, SignupForm, SocialProfileForm
from account.models import CustomUser, SocialProfile
from account.tasks import send_forgot_password_email_task
from account.tokens import account_activation_token_generator
from account.utils import *
from college.forms import CollegeCreationForm
from college.models import College, Stream
from company.forms import CompanyCreationForm
from company.models import Company
from faculty.forms import FacultyProfileForm
from faculty.models import Faculty
from recruitment.models import Association
from student.forms import StudentCreationForm, StudentSignupForm, StudentLoginForm
from student.models import Student
import re
from college.views import get_college_public_profile
from company.views import get_company_public_profile
from student.views import get_student_public_profile

# Create your views here
@require_GET
def landing(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	return render(request, 'account/landing.html', {})

@require_GET
def procedures(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	return render(request, 'account/procedures.html', {})

@require_GET
def stats(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	return render(request, 'account/stats.html', {})

@require_GET
def intro(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	return render(request, 'account/intro.html', {})			

@require_GET
def auth(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	context = {'login_form': LoginForm(prefix='l'), 'signup_form': SignupForm(prefix='s'), 'student_login_form': StudentLoginForm(prefix='sl'), 'student_signup_form': StudentSignupForm(prefix='ss')}
	return render(request, 'account/auth.html', context)

@require_POST
def login(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	f = LoginForm(request.POST)
	if f.is_valid():
		user = f.get_user()
		if not user.is_active:
			return JsonResponse(data={'success': True, 'render': loader.render_to_string('account/inactive.html', {'user': user})})
		auth_login(request, user)
		return JsonResponse(data = {'success': True, 'location': get_relevant_reversed_url(request)})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_GET
def activate(request, user_hashid='', token=''):
	if request.user.is_authenticated():
		data = get_type_created(request.user)
		user_type = data.pop('user_type')
		if request.user.is_active:
			return redirect(settings.HOME_URL[user_type])
		else:
			auth_logout(request)
			return redirect('auth')
	
	if not user_hashid or not token:
		raise Http404(_('Invalid Request'))
	
	try:
		uid = settings.HASHID_CUSTOM_USER.decode(user_hashid)[0]
	except IndexError:
		raise Http404(_('Invalid Request'))

	user = get_object_or_404(CustomUser, pk=uid)
	
	# Validating Token
	if not account_activation_token_generator.check_token(user, token):
		return render(request, 'account/activation_failure.html')
	
	if user.is_active:
		return redirect('login')

	try:
		user.is_active = True
		user.save()
	except:
		return render(request, 'account/500.html')
	return render(request, 'account/activation_success.html')

@require_http_methods(['GET', 'POST'])
def forgot_password(request):
	if request.user.is_authenticated():
		return redirect(settings.HOME_URL[request.user.type])
	if request.method == 'GET':
		f = ForgotPasswordForm()
	if request.method == 'POST':
		f = ForgotPasswordForm(request.POST)
		if f.is_valid():
			user = CustomUser.objects.get(email = f.cleaned_data['email'])
			send_forgot_password_email_task.delay(user.pk, get_current_site(request).domain)
			context = { 'email' : user.email }
			return render(request, 'account/forgot_password_email_sent.html',context)
	context = {'forgot_password_form' : f}
	return render(request, 'account/forgot_password.html', context)

@require_http_methods(['GET', 'POST'])
def reset_password(request, user_hashid='', token=''):
	if request.user.is_authenticated():
		return redirect(settings.HOME_URL[request.user.type])
	try:
		uid = settings.HASHID_CUSTOM_USER.decode(user_hashid)[0]
	except IndexError:
		return render(request, '404.html')
	try:
		user = CustomUser.objects.get(pk=uid)
	except CustomUser.DoesNotExist:
		return render(request, '404.html')
	if not default_token_generator.check_token(user, token):
		context = {'validlink': False}
		return render(request, 'account/set_password.html', context)
	if request.method == 'GET':
		f = SetPasswordForm()
	else:
		f = SetPasswordForm(request.POST)
		if f.is_valid():
			user.set_password(f.cleaned_data['password1'])
			user.save()
#			return redirect('login')
			return render(request, 'account/set_password.html', {'successful': True})
	context = { 'validlink': True, 'password_reset_form': f, 'user_hashid': user_hashid, 'token': token}
	return render(request, 'account/set_password.html', context)

@login_required
@require_http_methods(['GET', 'POST'])
def edit_account(request):
	if request.is_ajax():
		if request.method == 'GET':
			f = AccountForm(instance=request.user)
			return HttpResponse(render(request, 'account/edit_account.html', {'edit_account_form': f}).content.decode('utf-8'))
		else:
			f = AccountForm(request.POST, instance=request.user)
			if f.is_valid():
				f.save()
				if f.password_changed:
					user = authenticate(username=f.cleaned_data.get('username'), password=f.cleaned_data.get('new_password2'))
					if user:
						auth_login(request, user)
				context = {}
				context['edit_account_form'] = f
				context['success_msg'] = "Your account has been updated successfully"
				return JsonResponse(status=200, data={'render': render(request, 'account/edit_account.html', context).content.decode('utf-8')})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		return handle_user_type(request, redirect_request=True)

@login_required
@require_GET
def search(request):
	if not request.is_ajax():
		return render(request, '404.html')
	
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return JsonResponse({ 'location': reverse(settings.PROFILE_CREATION_URL[user_type]) })
	profile = data.pop('profile')
	query = request.GET.get('query')
# If 'location' key is not passed in JSON, then 'username' and 'name' of the relevant results will be passed
# If no matching queries, then success will be false and 'message' will be provided. Otherwise, success will be True
	if not query:
		return JsonResponse({'success': False, 'message': "No results found."})
	result = []
	space_separated_query = query.split(' ')
	first = ' '.join(space_separated_query[:-1]) if len(space_separated_query)-1 else space_separated_query[0]
	students = Student.objects.filter( Q(firstname__istartswith=first) | Q(lastname__istartswith=space_separated_query[-1]) )
	if user_type == 'CO':
		associated_colleges = list({a.college for a in Association.objects.filter(company=profile, approved=True)})
		students = students.filter(college__in = associated_colleges)
	for s in students:
		result.append({'name': s.get_full_name(), 'url': request.build_absolute_uri(s.get_absolute_url())})
		
	colleges = College.objects.filter(name__icontains=query)
	for c in colleges:
		result.append({'name': c.name.title(), 'url': request.build_absolute_uri(c.get_absolute_url())})
	companies = Company.objects.filter(name__icontains=query)
	for co in companies:
		result.append({'name': co.name.title(), 'url': request.build_absolute_uri(co.get_absolute_url())})
	result = result[:12]
	if result:
		return JsonResponse({'success': True, 'result': result})
	else:
		return JsonResponse({'success': False, 'message': 'No results found.'})

@login_required
@require_http_methods(['GET', 'POST'])
def social_profile(request):
	if request.is_ajax():
		if request.method == 'GET':
			try:
				f = SocialProfileForm(instance=request.user.social)
			except SocialProfile.DoesNotExist:
				f = SocialProfileForm()
			return HttpResponse(render(request, 'account/social_profile.html', {'social_profile_form': f}).content.decode('utf-8'))
		else:
			try:
				f = SocialProfileForm(request.POST, instance=request.user.social)
			except SocialProfile.DoesNotExist:
				f = SocialProfileForm(request.POST)
			if f.is_valid():
				f.save(user=request.user)
				context = {}
				context['social_profile_form'] = f
				context['success_msg'] = "Your profile has been successfully updated"
				return JsonResponse(status=200, data={'render': render(request, 'account/social_profile.html', context).content.decode('utf-8')})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		return handle_user_type(request, redirect_request=True)

@login_required
@require_GET
def home(request):
	return handle_user_type(request, redirect_request=True)

@login_required
@require_GET
def logout(request):
	auth_logout(request)
	return redirect('auth')

@login_required
@require_GET
def view_profile(request, username):
	if not request.is_ajax() or not CustomUser.objects.filter(username=username).exists():
		print('-----------')
		print('Received hit at view_profile')
		print('-----------')
		return render(request, '404.html')
	
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return JsonResponse({ 'location': reverse(settings.PROFILE_CREATION_URL[user_type]) })
#	if request.user.username == username:
#		return redirect(get_home_url(user_type))
	user = CustomUser.objects.get(username=username)
	requested_data = get_type_created(user)
	requested_user_type = requested_data.pop('user_type')
	if not requested_data:
		return JsonResponse({'success':False, 'message': 'User hasn\'t created profile. Stay tuned!'})
	if requested_user_type == 'C':
		return JsonResponse({'success':True, 'card-html':get_college_public_profile(user, user_type)})
	elif requested_user_type == 'S':
		return JsonResponse({'success':True, 'card-html':get_student_public_profile(user, user_type)})
	else:
		return JsonResponse({'success':True, 'card-html':get_company_public_profile(user, user_type)})

