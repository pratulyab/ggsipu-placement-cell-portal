from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.views import get_type_created, handle_user_type, get_home_url
from college.models import College, Programme, Stream
from student.models import Student
from .models import Association, Dissociation, PlacementSession
from .forms import AssociationForm, DissociationForm, PlacementSessionForm
import base64

# Create your views here.

@require_http_methods(['GET','POST'])
@login_required
def associate(request):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return handle_user_type(request)
	profile = data.pop('profile')
	if user_type not in ['C', 'CO']:
		raise Http404(_('Perhaps, you\'re lost.'))
	else:
		context = {}
		if request.method == 'GET':
			f = AssociationForm(profile=profile)
		else:
			POST = request.POST.copy()
			if user_type == 'C':
				POST['college'] = profile.pk
			else:
				POST['company'] = profile.pk
			f = AssociationForm(POST, profile=profile)
			if f.is_valid():
				f.save()
				f.save_m2m()
				return redirect(get_home_url(user_type))
		context['association_form'] = f
		return render(request, 'recruitment/associate.html', context)

@require_GET
@login_required
def view_association_requests(request):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return handle_user_type(request)
	profile = data.pop('profile')
	if user_type not in ['C', 'CO']:
		raise Http404(_('Winter has come. Go home!'))
	else:
		context = {}
		associations = Association.objects.filter( ~Q(initiator=user_type) )
		if user_type=='C':
			associations = associations.filter( Q(college=profile) & Q(approved=None) )
		else:
			associations = associations.filter( Q(company=profile) & Q(approved=None) )
		associations_list = []
		for ass in associations:
			session_url = request.build_absolute_uri(reverse('createsession'))
			session_url = session_url + "?ass=" + base64.b64encode(str(ass.pk).encode('utf-8')).decode('utf-8')
			print(session_url)
			dissoci_url = request.build_absolute_uri(reverse('dissociate'))
			dissoci_url = dissoci_url + "?ass=" + base64.b64encode(str(ass.pk).encode('utf-8')).decode('utf-8')
			print(dissoci_url)
			urls = {'session_url': session_url, 'dissoci_url':dissoci_url}
			associations_list.append({'obj':ass, 'url':urls})
		context['associations'] = associations_list
		if user_type=='C':
			return render(request, 'college/association_requests.html', context)
		else:
			return render(request, 'company/association_requests.html', context)

@require_http_methods(['GET','POST'])
@login_required
def create_session(request):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return handle_user_type(request)
	profile = data.pop('profile')
	if user_type not in ['C', 'CO']:
		raise Http404(_('Winter has come. Go home!'))
	else:
		context = {}
		if request.method == 'GET':
			try:
				association_id = int(base64.b64decode(request.GET.get('ass').encode('utf-8')).decode('utf-8'))
				association = get_object_or_404(Association, pk=association_id)
				f = PlacementSessionForm(association=association)
			except:
				raise Http404(_('Invalid request'))
		else:
			association = get_object_or_404(Association, pk=int(base64.b64decode(request.POST.get('token').encode('utf-8')).decode('utf-8')))
			f = PlacementSessionForm(request.POST, association=association)
			if f.is_valid():
				f.save()
				f.save_m2m()
				association.approved = True
				association.save()
				if user_type=='C':
					return redirect('college_association_requests')
				else:
					return redirect('company_association_requests')
		context['session_creation_form'] = f
		return render(request, 'recruitment/create_session.html', context)

@require_http_methods(['GET','POST'])
@login_required
def dissociate(request):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if not data:
		return handle_user_type(request)
	profile = data.pop('profile')
	if user_type not in ['C', 'CO']:
		raise Http404(_('Winter has come. Go home!'))
	else:
		context = {}
		if request.method == 'GET':
			try:
				association_id = int(base64.b64decode(request.GET.get('ass').encode('utf-8')).decode('utf-8'))
				association = get_object_or_404(Association, pk=association_id)
				f = DissociationForm(association=association)
			except:
				raise Http404(_('404 error code isn\'t correct. But still..'))
		else:
			POST = request.POST.copy()
			association = get_object_or_404(Association, pk=int(base64.b64decode(POST.get('token').encode('utf-8')).decode('utf-8')))
			POST['college'] = association.college.pk
			POST['company'] = association.company.pk
			f = DissociationForm(POST, association=association)
			if f.is_valid():
				f.save()
				association.approved = False
				association.save()
				if user_type=='C':
					return redirect('college_association_requests')
				else:
					return redirect('company_association_requests')
		context['dissociation_form'] = f
		return render(request, 'recruitment/dissociate.html', context)
