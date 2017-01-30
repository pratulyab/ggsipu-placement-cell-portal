from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.decorators import require_user_types
from account.forms import SignupForm, AccountForm, SocialProfileForm
from account.models import CustomUser, SocialProfile
from account.tasks import send_activation_email_task
from account.utils import handle_user_type, get_relevant_reversed_url
from company.forms import CompanyCreationForm, CompanyEditForm
from company.models import Company
from notification.models import Notification
from recruitment.models import PlacementSession
from recruitment.forms import AssociationForm

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
#		auth_login(request, user)
		send_activation_email_task.delay(user.pk, get_current_site(request).domain)
		context = {'email': user.email, 'profile_creation': request.build_absolute_uri(reverse(settings.PROFILE_CREATION_URL['CO']))}
		html = render(request, 'account/post_signup.html', context).content.decode('utf-8')
		return JsonResponse(data = {'success': True, 'render': html})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['CO'])
@login_required
@require_http_methods(['GET','POST'])
def create_company(request, **kwargs):
##	if request.user.type == 'CO':
	if request.method == 'GET':
		f = CompanyCreationForm()
		try:
			company = request.user.company
			return redirect(settings.HOME_URL['CO'])
		except Company.DoesNotExist:
			pass
	else:
		f = CompanyCreationForm(request.POST, request.FILES)
		if f.is_valid():
			company = f.save(profile=request.user)
			return redirect(settings.HOME_URL['CO'])
	return render(request, 'company/create.html', {'company_creation_form': f})
##	else:
##		return handle_user_type(request, redirect_request=True)

@require_user_types(['CO'])
@login_required
@require_GET
def company_home(request, **kwargs):
##	if request.user.type == 'CO':
	context = {}
	user = request.user
	try:
		company = request.user.company
	except Company.DoesNotExist:
		return redirect(settings.PROFILE_CREATION_URL['CO'])
	context['user'] = user
	context['company'] = company
	context['edit_account_form'] = AccountForm(instance=user)
	context['edit_company_form'] = CompanyEditForm(instance=company)
	context['association_form'] = AssociationForm(profile=company)
	try:
		context['social_profile_form'] = SocialProfileForm(instance=user.social)
	except SocialProfile.DoesNotExist:
		context['social_profile_form'] = SocialProfileForm()
	context['badge'] = company.profile.notification_target.filter(is_read=False).count()
	return render(request, 'company/home.html', context)
##	else:
##		return handle_user_type(request, redirect_request=True)

@require_user_types(['CO'])
@login_required
@require_POST
def edit_company(request, **kwargs):
	if request.is_ajax():
##		if request.user.type == 'CO':
		try:
			company = request.user.company
		except Company.DoesNotExist:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['CO'])})
		f = CompanyEditForm(request.POST, request.FILES, instance=company)
		photo = company.photo
		if f.is_valid():
			f.save()
			if photo and photo != company.photo:
				try:
					os.remove(os.path.join(settings.BASE_DIR, photo.url[1:]))
				except:
					pass
			context = {}
			context['company_edit_form'] = CompanyEditForm(instance=company)
			if f.has_changed():
				context['success_msg'] = "Profile has been updated successfully!"
			return JsonResponse(status=200, data={'render': render(request, 'company/edit.html', context).content.decode('utf-8')})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

def get_company_public_profile(user, requester_type):
	try:
		company = Company.objects.get(id=user.company.id)
	except Company.DoesNotExist:
		return '<div class="valign-wrapper"><p class="valign">Company doesn\'t have a profile yet. Stay tuned!</p></div>'
	context = {'name': company.name.title(), 'associations': PlacementSession.objects.filter(association__company=company).count(), 'website': company.website, 'type': requester_type, 'company': company}
	if company.photo:
		context['photo'] = company.photo.url
	print(context)
	return render_to_string('company/pub_profile.html', context)
