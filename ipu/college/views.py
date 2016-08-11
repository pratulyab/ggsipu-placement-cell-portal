from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.forms import SignupForm
from account.views import handle_user_type, send_activation_email
from college.forms import CollegeCreationForm, CollegeEditForm
from college.models import College

# Create your views here.

@require_http_methods(['GET','POST'])
def college_signup(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_response=True)
	if request.method == 'GET':
		f = SignupForm()
	else:
		f = SignupForm(request.POST)
		f.instance.type = 'C'
		if f.is_valid():
			college = f.save(user_type='C')
			college = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
			context = {}
			if college:
				auth_login(request, college)
				context['email'] = college.email
				context['profile_creation'] = request.build_absolute_uri(reverse('create_college'))
				send_activation_email(college, get_current_site(request).domain)
				return render(request, 'account/post_signup.html', context)
	return render(request, 'college/signup.html', {'college_signup_form': f})

@require_http_methods(['GET','POST'])
@login_required
def create_college(request):
	if request.user.type == 'C':
		if request.method == 'GET':
			f = CollegeCreationForm()
			try:
				college = request.user.college
				return redirect('college_home')
			except College.DoesNotExist:
				pass
		else:
			f = CollegeCreationForm(request.POST, request.FILES)
			if f.is_valid():
				college = f.save(profile=request.user)
				f.save_m2m()
				return redirect('college_home')
		return render(request, 'college/create.html', {'college_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def college_home(request):
	if request.user.type == 'C':
		context = {}
		context['user'] = request.user
		try:
			context['college'] = request.user.college
			return render(request, 'college/home.html', context)
		except College.DoesNotExist:
			return redirect('create_college')
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_college(request):
	if request.user.type == 'C':
		try:
			context = {}
			college = request.user.college
			if request.method == 'GET':
				f = CollegeEditForm(instance = college)
			else:
				f = CollegeEditForm(request.POST, request.FILES, instance=college)
				if f.is_valid():
					f.save()
					f.save_m2m()
					if f.has_changed():
						context['update'] = True
			context['college_edit_form'] = f
			return render(request, 'college/edit.html', context)
		except College.DoesNotExist:
			return render(request, 'college/create.html', {'college_creation_form': CollegeCreationForm()})
	else:
		return handle_user_type(request)
