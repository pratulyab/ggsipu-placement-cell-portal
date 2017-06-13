from django.conf import settings
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
from college.forms import CollegeCreationForm, CollegeEditForm
from college.models import College
from dummy_company.forms import DummySessionFilterForm
from faculty.forms import FacultySignupForm
from notification.forms import NotifySessionStudentsForm
from notification.models import Notification
from recruitment.models import PlacementSession
from recruitment.forms import AssociationForm, SessionFilterForm

import os

# Create your views here.

@require_http_methods(['GET','POST'])
def college_signup(request):
	if request.user.is_anonymous:
		return redirect('landing')
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
#				auth_login(request, college)
				context['email'] = college.email
				context['profile_creation'] = request.build_absolute_uri(reverse(settings.PROFILE_CREATION_URL['C']))
				send_activation_email_task.delay(college.pk, get_current_site(request).domain)
				return render(request, 'account/post_signup.html', context)
	return render(request, 'college/signup.html', {'college_signup_form': f})

@login_required
@require_http_methods(['GET','POST'])
def create_college(request, **kwargs):
	if request.user.type == 'C':
		if request.method == 'GET':
			f = CollegeCreationForm()
			try:
				college = request.user.college
				return redirect(settings.HOME_URL['C'])
			except College.DoesNotExist:
				pass
		else:
			f = CollegeCreationForm(request.POST, request.FILES)
			if f.is_valid():
				college = f.save(profile=request.user)
				f.save_m2m()
				return redirect(settings.HOME_URL['C'])
		return render(request, 'college/create.html', {'college_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C'])
@login_required
@require_GET
def college_home(request, **kwargs):
##	if request.user.type == 'C':
	context = {}
	user = request.user
	try:
		college = request.user.college
	except College.DoesNotExist:
		return redirect(settings.PROFILE_CREATION_URL['C'])
	context['user'] = user
	context['college'] = college
	context['edit_account_form'] = AccountForm(instance=user)
	context['edit_college_form'] = CollegeEditForm(instance=college)
	context['notify_session_students_form'] = NotifySessionStudentsForm()
	context['association_form'] = AssociationForm(profile=college)
	try:
		context['social_profile_form'] = SocialProfileForm(instance=user.social)
	except SocialProfile.DoesNotExist:
		context['social_profile_form'] = SocialProfileForm()
	context['badge'] = college.profile.notification_target.filter(is_read=False).count() 
	context['session_filter_form'] = SessionFilterForm(profile=college)
	context['dsession_filter_form'] = DummySessionFilterForm(college=college)
	return render(request, 'college/home.html', context)
##	else:
##		return handle_user_type(request, redirect_request=True)

@require_user_types(['C'])
@login_required
@require_POST
def edit_college(request, **kwargs):
	if request.is_ajax():
##		if request.user.type == 'C':
		try:
			college = request.user.college
		except College.DoesNotExist:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['C'])})
		f = CollegeEditForm(request.POST, request.FILES, instance=college)
		photo = college.photo
		if f.is_valid():
			f.save()
			if photo and photo != college.photo:
				try:
					os.remove(os.path.join(settings.BASE_DIR, photo.url[1:]))
				except:
					pass
			context = {}
			context['edit_college_form'] = CollegeEditForm(instance=college)
			if f.has_changed():
				context['success_msg'] = "Profile has been updated successfully!"
			return JsonResponse(status=200, data={'render': render(request, 'college/edit.html', context).content.decode('utf-8')})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

def get_college_public_profile(user, requester_type):
	try:
		college = College.objects.get(id = user.college.id)
	except College.DoesNotExist:
		return '<div class="valign-wrapper"><p class="valign">College doesn\'t have a profile yet. Stay tuned!</p></div>'
	context = {'name': college.name.title(), 'streams': college.streams.count(), 'students': college.students.count(), 'website': college.website, 'type': requester_type, 'college': college}
	if college.photo:
		context['photo'] = college.photo.url
	context['associations'] = PlacementSession.objects.filter(association__college=college).count(),
# Add queryset to filter out mass recruiters
	return render_to_string ('college/pub_profile.html', context)
