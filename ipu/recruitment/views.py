from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import require_user_types
from account.utils import handle_user_type, get_relevant_reversed_url, get_type_created
from college.models import College
from company.models import Company
from dummy_company.models import DummyCompany, DummySession
from faculty.models import Faculty
from recruitment.forms import AssActorsOnlyForm, AssWithProgrammeForm, AssociationForm, SessionEditForm, DissociationForm, CreateSessionCriteriaForm, CriteriaEditForm
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from recruitment.utils import get_excel_structure
from student.models import Student, Programme, Stream

import openpyxl as excel, time
from hashids import Hashids

@require_user_types(['C', 'CO'])
@login_required
@require_POST
def get_with_prog_form(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['C'])})
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
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['CO'])})
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

##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})

	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C', 'CO'])
@login_required
@require_POST
def get_ass_streams(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['C'])})
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
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['CO'])})
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
		
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C', 'CO'])
@login_required
@require_POST
def associate(request):
	if request.is_ajax():
		if request.user.type == 'C':
			try:
				college = request.user.college
			except College.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['C'])})
			POST = request.POST.copy()
			POST['college'] = college.pk
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			chosen_programme = POST['programme']
			streams_queryset = college.streams.filter(programme__pk=chosen_programme)
			f = AssociationForm(POST, initiator_profile=college, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
			if f.is_valid():
				f.save()
				f.save_m2m()
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['C'])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

		elif request.user.type == 'CO':
			try:
				company = request.user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['CO'])})
			POST = request.POST.copy()
			POST['company'] = company.pk
			college = College.objects.get(pk=POST['college'])
			programme_queryset = Programme.objects.filter(pk__in=list({s.programme.pk for s in college.streams.all()}))
			chosen_programme = POST['programme']
#			streams_queryset = college.streams.filter(programme__in=[programme_queryset[i-1] for i in chosen_programmes_list])
			streams_queryset = college.streams.filter(programme__pk=chosen_programme)
			f = AssociationForm(POST, initiator_profile=company, programme_queryset=programme_queryset, chosen_programme=chosen_programme, streams_queryset=streams_queryset)
			if f.is_valid():
				try:
					f.save()
					f.save_m2m()
				except Exception as e:
					return JsonResponse(status=400, data={'error': str(e)})
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['CO'])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C', 'CO'])
@login_required
@require_http_methods(['GET','POST'])
def create_session(request):
	if request.is_ajax():
		type = request.user.type
##		if type not in ['C', 'CO']:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'GET':
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.GET.get('ass'))[0]
				association = Association.objects.get(pk=association_id)
			except: #To account for both KeyError as well as Association.DoesNotExist
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, association)
			creation = requester.get('creation', False)
			if creation:
				return JsonResponse(status=400, data={'location': creation})
			if not requester.get('authorized', True):
				return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
			f = CreateSessionCriteriaForm(association=association)
			html = render(request, 'recruitment/create_session.html', {'session_creation_form': f}).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, association)
			creation = requester.get('creation', False)
			if creation:
				return JsonResponse(status=400, data={'location': creation})
			if not requester.get('authorized', True):
				return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
			try:
				association.session
				return JsonResponse(status=400, data={'error': 'Session already exists'})
			except PlacementSession.DoesNotExist:
				pass
			# Converting list to string. i.e. somewhat custom to_python
			POST = request.POST.copy()
			POST['years'] = (','.join(POST.getlist('years')))
			f = CreateSessionCriteriaForm(POST, association=association)
			if f.is_valid():
				data = f.cleaned_data
				criterion,created = SelectionCriteria.objects.get_or_create(years=data['years'], is_sub_back=data['is_sub_back'], tenth=data['tenth'], twelfth=data['twelfth'], graduation=data['graduation'], post_graduation=data['post_graduation'], doctorate=data['doctorate'])
				session = PlacementSession.objects.create(association=association,application_deadline=data['application_deadline'],last_modified_by=type, selection_criteria=criterion)
				association.approved = True
				association.save()
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL[type])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C', 'F', 'CO'])
@login_required
@require_http_methods(['GET','POST'])
def edit_session(request, sess):
	if request.is_ajax():
		type = request.user.type
##		if type not in ['F', 'C', 'CO']:
##			return JsonResponse(status=403, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'POST':
			sess_post = request.POST.get('token', None)
			if sess != sess_post:
				return JsonResponse(status=400, data={'error': 'Invalid session requested'})
			try:
				session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
				session = PlacementSession.objects.get(pk=session_id)
			except:
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			print(request.POST.getlist('students'))
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, session.association)
			creation = requester.get('creation', False)
			if creation:
				return JsonResponse(status=400, data={'location': creation})
			if not requester.get('authorized', True):
				return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
			f = SessionEditForm(request.POST, instance=session)
			if f.is_valid():
				session = f.save(commit=False)
				session.last_modified_by = type
				session.save()
				f.save_m2m()
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL[type])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=405, data={'error': 'Method Not Allowed'})
	else:
		if request.method == 'GET':
			try:
#				sess = request.GET.get('sess') 
				session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
				session = PlacementSession.objects.get(pk=session_id)
			except: #To account for both KeyError as well as PlacementSession.DoesNotExist
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, session.association)
			creation = requester.get('creation', False)
			if creation:
				return redirect(creation)
			if not requester.get('authorized', True):
				return redirect(reverse(settings.HOME_URL[requester['type']]))
			f = SessionEditForm(instance=session)
			return render(request, 'recruitment/edit_session.html', {'session_edit_form': f, 'sessid': sess})
		else:
			return handle_user_type(request)

@require_user_types(['F', 'C', 'CO'])
@login_required
@require_http_methods(['GET','POST'])
def edit_criteria(request, sess):
	if request.is_ajax():
		type = request.user.type
##		if type not in ['F', 'C', 'CO']:
##			return JsonResponse(status=403, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'POST':
			sess_post = request.POST.get('token', None)
			if sess != sess_post:
				return JsonResponse(status=400, data={'error': 'Invalid session requested'})
			try:
				session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
				session = PlacementSession.objects.get(pk=session_id)
			except:
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, session.association)
			creation = requester.get('creation', False)
			if creation:
				return JsonResponse(status=400, data={'location': creation})
			if not requester.get('authorized', True):
				return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
			POST = request.POST.copy()
			POST['years'] = ','.join(POST.getlist('years'))
			f = CriteriaEditForm(POST, session=session, instance=session.selection_criteria)
			if f.is_valid():
				data = f.cleaned_data
				criterion,created = SelectionCriteria.objects.get_or_create(years=data['years'], is_sub_back=data['is_sub_back'], tenth=data['tenth'], twelfth=data['twelfth'], graduation=data['graduation'], post_graduation=data['post_graduation'], doctorate=data['doctorate'])
				session.selection_criteria = criterion
#				session.last_modified_by = type
				session.save()
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL[type])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=405, data={'error': 'Method Not Allowed'})
	else:
		if request.method == 'GET':
			try:
				session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
				session = PlacementSession.objects.get(pk=session_id)
			except: #To account for both KeyError as well as PlacementSession.DoesNotExist
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, session.association)
			creation = requester.get('creation', False)
			if creation:
				return redirect(creation)
			if not requester.get('authorized', True):
				return redirect(reverse(settings.HOME_URL[requester['type']]))
			f = CriteriaEditForm(session=session, instance=session.selection_criteria)
			return render(request, 'recruitment/edit_criteria.html', {'criteria_edit_form': f, 'sessid': sess})
		else:
			return handle_user_type(request)

@login_required
@require_GET
def mysessions(request):
	if request.is_ajax():
		user = request.user
		type = user.type
		sessions = None; html=''
		if type == 'S':
			try:
				student = user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
			sessions = student.sessions.all()
			dsessions = student.dummy_sessions.all()
			sessions_list = []
			for s in sessions:
				assoc = s.association
				data = {}
				data['sessobj'] = s
#				data['sessid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['company'] = assoc.company.name.title()
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.company.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['students'] = s.students.count()
				data['is_dummy'] = False
				sessions_list.append(data)
			for ds in dsessions:
				data['dsessobj'] = ds
#				data['dsessid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
				data['salary'] = "%d LPA" % ds.salary
				data['company'] = ds.dummy_company.name.title()
				data['type'] = "Internship" if ds.type == 'I' else "Job"
				data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
				data['students'] = ds.students.count()
				data['is_dummy'] = True
			html = render(request, 'student/mysessions.html', {'sessions': sessions_list}).content.decode('utf-8')
		elif type == 'CO':
			try:
				company = user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['CO'])})
			associations = Association.objects.filter(company=company, approved=True).values('pk')
			sessions = PlacementSession.objects.filter(association__pk__in = associations)
			sessions_list = []
			for s in sessions:
				assoc = s.association
				data = {}
				data['sessobj'] = s
				data['sessid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['college'] = assoc.company.name.title()
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.college.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['students'] = s.students.count()
				sessions_list.append(data)
			html = render(request, 'company/mysessions.html', {'sessions': sessions_list}).content.decode('utf-8')
		else:
			college = None
			if type == 'F':
				verdict = False
				try:
					faculty = user.faculty
				except Faculty.DoesNotExist:
					verdict = True
				if not faculty.firstname:
					verdict = True
				if verdict:
					return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['F'])})
				college = faculty.college
			elif type == 'C':
				try:
					college = user.college
				except College.DoesNotExist:
					return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['C'])})
			associations = Association.objects.filter(college=college, approved=True).values('pk')
			sessions = PlacementSession.objects.filter(association__pk__in = associations)
			dsessions = DummySession.objects.filter(dummy_company__college=college)
			sessions_list = []
			dsessions_list = []
			for s in sessions:
				assoc = s.association
				data = {}
				data['sessobj'] = s
				data['sessid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['company'] = assoc.company.name.title()
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.company.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['students'] = s.students.count()
#				data['is_dummy'] = False
				sessions_list.append(data)
			for ds in dsessions:
				data = {}
				data['dsessobj'] = ds
				data['dsessid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
				data['salary'] = "%d LPA" % ds.salary
				data['dcompany'] = ds.dummy_company.name.title()
				data['type'] = "Internship" if ds.type == 'I' else "Job"
				data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
				data['students'] = ds.students.count()
#				data['is_dummy'] = True
				dsessions_list.append(data)
			html = render(request, 'college/mysessions.html', {'sessions': sessions_list, 'dsessions': dsessions_list}).content.decode('utf-8')
		return JsonResponse(status=200, data={'html': html})
	else:
		return handle_user_type(request)

@require_user_types(['C', 'CO'])
@login_required
@require_http_methods(['GET','POST'])
def dissociate(request):
	if request.is_ajax():
##		if request.user.type not in ['C', 'CO']:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
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
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL[request.user.type])})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['C', 'F', 'CO'])
@login_required
@require_GET
def view_association_requests(request):
	if request.is_ajax():
##		if request.user.type not in ['C', 'CO', 'F']:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
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


@require_user_types(['C', 'F', 'CO'])
@login_required
@require_GET
def generate_excel(request, sess):
#	if request.is_ajax() and request.user.type in ['F', 'C', 'CO']:
##	if request.user.type in ['F', 'C', 'CO']:
	requester = get_type_created(request.user)
	user_type = requester.pop(user_type)
	if not requester:
		return redirect(reverse(settings.PROFILE_CREATION_URL[user_type]))
	profile = requester['profile']
	try:
#			sess = request.GET.get('sess')
		session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_id)
		elif user_type == 'C':
			session = PlacementSession.objects.get(association__college=profile, pk=session_id)
		else:
			session = PlacementSession.objects.get(association__college=profile.college, pk=session_id)
	except: #To account for both KeyError as well as PlacementSession.DoesNotExist
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	title = ''
	if user_type == 'CO':
		title = dict(Association.PLACEMENT_TYPE)[session.association.type].__str__() + " session at " + session.association.college.name.upper()
	else:
		title = dict(Association.PLACEMENT_TYPE)[session.association.type].__str__() + " opportunity by " + session.association.company.name.upper()
	streams_title = session.association.programme.name + ' - ' + ', '.join(["%s (%s)" % (s.name, s.code) for s in session.association.streams.all()])
	students_queryset = session.students.all()
	workbook = get_excel_structure(title, streams_title, students_queryset)
	response = HttpResponse(content=excel.writer.excel.save_virtual_workbook(workbook), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename=session_%s.xlsx' % Hashids(salt="AbhiKaSamay").encode(round(time.time()))
	return response
#	else:
#		return HttpResponse('')


# -------------------------------
def validate_associator(request, association):
	data = {}
	requester = get_type_created(request.user)
	type = requester.pop('user_type')
	data['type'] = type
	if not requester: # requester dict empty i.e. no profile
		data['creation'] = reverse(settings.PROFILE_CREATION_URL[type])
		return data
	if type == 'CO':
		company = requester.pop('profile')
		if company != association.company:
			data['authorized'] = False
	elif type in ['F','C']:
		college = None
		if type == 'F':
			faculty = requester.pop('profile')
			college = faculty.college
		else:
			college = requester.pop('profile')
		if college != association.college:
			data['authorized'] = False
	else:
		data['authorized'] = False
	return data
