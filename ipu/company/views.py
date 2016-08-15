from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.forms import SignupForm
from account.views import handle_user_type, send_activation_email
from company.forms import CompanyCreationForm, CompanyEditForm
from company.models import Company

# Create your views here.

@require_POST
def company_signup(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	f = SignupForm(request.POST)
	f.instance.type = 'CO'
	if f.is_valid():
		user = f.save(user_type='CO')
		user = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
		auth_login(request, user)
		send_activation_email(user, get_current_site(request).domain)
		context = {'email': user.email, 'profile_creation': request.build_absolute_uri(reverse('create_student'))}
		html = render(request, 'account/post_signup.html', context).content.decode('utf-8')
		return JsonResponse(data = {'success': True, 'render': html})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_http_methods(['GET','POST'])
@login_required
def create_company(request):
	if request.user.type == 'CO':
		if request.method == 'GET':
			f = CompanyCreationForm()
			try:
				company = request.user.company
				return redirect('company_home')
			except Company.DoesNotExist:
				pass
		else:
			f = CompanyCreationForm(request.POST, request.FILES)
			if f.is_valid():
				company = f.save(profile=request.user)
				return redirect('company_home')
		return render(request, 'company/create.html', {'company_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def company_home(request):
	if request.user.type == 'CO':
		context = {}
		context['user'] = request.user
		try:
			context['company'] = request.user.company
			return render(request, 'company/home.html', context)
		except Company.DoesNotExist:
			return redirect('create_company')
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_company(request):
	if request.user.type == 'CO':
		try:
			context = {}
			company = request.user.company
			if request.method == 'GET':
				f = CompanyEditForm(instance = company)
			else:
				f = CompanyEditForm(request.POST, request.FILES, instance=company)
				if f.is_valid():
					f.save()
					if f.has_changed():
						context['update'] = True
			context['company_edit_form'] = f
			return render(request, 'company/edit.html', context)
		except Company.DoesNotExist:
			return render(request, 'company/create.html', {'company_creation_form': CompanyCreationForm()})
	else:
		return handle_user_type(request)
