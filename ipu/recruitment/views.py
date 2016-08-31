from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.views import handle_user_type, get_relevant_reversed_url, get_creation_url, get_home_url
from college.models import College
from company.models import Company
from recruitment.forms import AssActorsOnlyForm, AssWithProgrammeForm, AssociationForm, PlacementSessionForm, DissociationForm
from recruitment.models import Association, PlacementSession, Dissociation
from student.models import Student, Programme, Stream

@require_POST
@login_required
def get_with_prog_form(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('C'))})
			POST = request.POST.copy()
			POST['college'] = college.pk
			f = AssActorsOnlyForm(POST, initiator_profile=college)
			if f.is_valid():
				programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
				
				prog_form = AssWithProgrammeForm(initial={'company': POST['company']}, initiator_profile=college, programme_queryset=programme_queryset)
				html = render(request, 'recruitment/with_programme.html', {'prog_form': prog_form}).content.decode('utf-8')
				return JsonResponse(status=200, data={'render': html})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

		elif request.user.type == 'CO':
			try:
				company = request.user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('CO'))})
			POST = request.POST.copy()
			POST['company'] = company.pk
			f = AssActorsOnlyForm(POST, initiator_profile=company)
			if f.is_valid():
				college = f.cleaned_data['college']
				programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
				
				prog_form = AssWithProgrammeForm(initial={'college': POST['college']}, initiator_profile=company, programme_queryset=programme_queryset)
				html = render(request, 'recruitment/with_programme.html', {'prog_form': prog_form}).content.decode('utf-8')
				return JsonResponse(status=200, data={'render': html})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})

	
	else:
		return handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def get_ass_streams(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('C'))})
			POST = request.POST.copy()
			POST['college'] = college.pk
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			f = AssWithProgrammeForm(POST, initiator_profile=college, programme_queryset=programme_queryset)
			if f.is_valid():
				chosen_programme = POST['programme']
				streams_queryset = college.streams.filter(programme=f.cleaned_data['programme'])
				ass_form = AssociationForm(initial={'company': POST['company']}, initiator_profile=college, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
				html = render(request, 'recruitment/associate.html', {'ass_form': ass_form}).content.decode('utf-8')
				return JsonResponse(status=200, data={'render': html})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		
		elif request.user.type == 'CO':
			try:
				company = request.user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('CO'))})
			POST = request.POST.copy()
			POST['company'] = company.pk
			college = College.objects.get(pk=POST['college'])
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			f = AssWithProgrammeForm(POST, initiator_profile=company, programme_queryset=programme_queryset)
			if f.is_valid():
				chosen_programme = POST['programme']
				streams_queryset = college.streams.filter(programme=f.cleaned_data['programme'])
				ass_form = AssociationForm(initial={'college': POST['college']}, initiator_profile=company, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
				html = render(request, 'recruitment/associate.html', {'ass_form': ass_form}).content.decode('utf-8')
				return JsonResponse(status=200, data={'render': html})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def associate(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('C'))})
			POST = request.POST.copy()
			POST['college'] = college.pk
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			chosen_programme = POST['programme']
			streams_queryset = college.streams.filter(programme__pk=chosen_programme)
			f = AssociationForm(POST, initiator_profile=college, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
			if f.is_valid():
				f.save()
				f.save_m2m()
				return JsonResponse(status=200, data={'location': reverse(get_home_url('C'))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

		elif request.user.type == 'CO':
			try:
				company = request.user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('CO'))})
			POST = request.POST.copy()
			POST['company'] = company.pk
			college = College.objects.get(pk=POST['college'])
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			chosen_programme = POST['programme']
#			streams_queryset = college.streams.filter(programme__in=[programme_queryset[i-1] for i in chosen_programmes_list])
			streams_queryset = college.streams.filter(programme__pk=chosen_programme)
			f = AssociationForm(POST, initiator_profile=company, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
			if f.is_valid():
				f.save()
				f.save_m2m()
				return JsonResponse(status=200, data={'location': reverse(get_home_url('CO'))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def create_session(request):
	if request.is_ajax():
		if request.user.type not in ['C', 'CO']:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'GET':
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.GET.get('ass'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = PlacementSessionForm(association=association)
			html = render(request, 'recruitment/create_session.html', {'session_creation_form': f}).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = PlacementSessionForm(request.POST, association=association)
			if f.is_valid():
				f.save()
				association.approved = True
				association.save()
				return JsonResponse(status=200, data={'location': reverse(get_home_url(request.user.type))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def dissociate(request):
	if request.is_ajax():
		if request.user.type not in ['C', 'CO']:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'GET':
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.GET.get('ass'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = DissociationForm(association=association)
			html = render(request, 'recruitment/dissociate.html', {'dissociation_form': f}).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			POST = request.POST.copy()
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			POST['college'] = association.college.pk
			POST['company'] = association.company.pk
			f = DissociationForm(POST, association=association)
			if f.is_valid():
				f.save()
				association.approved = False
				association.save()
				return JsonResponse(status=200, data={'location': reverse(get_home_url(request.user.type))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def view_association_requests(request):
	if request.is_ajax():
		if request.user.type not in ['C', 'CO', 'F']:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
		associations = Association.objects.filter( ~Q(initiator=request.user.type) )
		if request.user.type == 'C':
			associations = associations.filter( Q(college=request.user.college) & Q(approved=None) )
		elif request.user.type == 'F':
			associations = associations.filter( Q(college=request.user.faculty.college) & Q(approved=None) )
		else:
			associations = associations.filter( Q(company=request.user.company) & Q(approved=None) )
		associations_list = []
		context = {}
		for ass in associations:
			session_url = request.build_absolute_uri(reverse('createsession'))
			session_url = session_url + "?ass=" + settings.HASHID_ASSOCIATION.encode(ass.pk)
			dissoci_url = request.build_absolute_uri(reverse('dissociate'))
			dissoci_url = dissoci_url + "?ass=" + settings.HASHID_ASSOCIATION.encode(ass.pk)
			urls = {'session_url': session_url, 'dissoci_url':dissoci_url}
			associations_list.append({'obj':ass, 'url':urls})
		context['associations'] = associations_list
		if request.user.type in ['C','F']:
			html = render(request, 'college/association_requests.html', context).content.decode('utf-8')
			return JsonResponse(status=200, data={'html': html})
		else:
			html = render(request, 'company/association_requests.html', context).content.decode('utf-8')
			return JsonResponse(status=200, data={'html': html})
	else:
		return handle_user_type(request, redirect_request=True)
