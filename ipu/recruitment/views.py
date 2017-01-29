from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import require_user_types, require_AJAX
from account.utils import handle_user_type, get_relevant_reversed_url, get_type_created
from college.models import College
from company.models import Company
from dummy_company.models import DummyCompany, DummySession
from faculty.models import Faculty
#from recruitment.forms import Associate, AssActorsOnlyForm, AssWithProgrammeForm, AssociationForm, SessionEditForm, DissociationForm, CreateSessionCriteriaForm, CriteriaEditForm
from recruitment.forms import AssociationForm, SessionEditForm, DissociationForm, CreateSessionCriteriaForm, CriteriaEditForm
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from recruitment.utils import get_excel_structure
from student.models import Student, Programme, Stream

import openpyxl as excel, time
from hashids import Hashids

@require_user_types(['C', 'CO'])
@require_AJAX
@login_required
@require_POST
def associate(request, **kwargs):
	f = AssociationForm(request.POST, profile=kwargs.pop('profile'))
	if f.is_valid():
		try:
			f.save()
			f.save_m2m()
		except (ValidationError, IntegrityError) as error:
			return JsonResponse(status=400, data={'error': error.__str__()})
		return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['C'])})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['CO'])
@require_AJAX
@login_required
@require_GET
def get_programmes(request, **kwargs):
	user_type = kwargs.pop('user_type')
	profile = kwargs.pop('profile')
	try:
		college = request.GET.get('college', '')
		college = settings.HASHID_COLLEGE.decode(college)[0]
		college = College.objects.get(pk=college)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid college chosen.'})
	data = []
	for p in college.get_programmes_queryset():
		data.append({'html': p.name.title(), 'value': settings.HASHID_PROGRAMME.encode(p.pk)})
	return JsonResponse(status=200, data={'programmes': data})

@require_user_types(['C', 'CO'])
@require_AJAX
@login_required
@require_GET
def get_streams(request, **kwargs):
	user_type = kwargs.pop('user_type')
	profile = kwargs.pop('profile')
	try:
		programme = request.GET.get('programme', '')
		programme = settings.HASHID_PROGRAMME.decode(programme)[0]
		programme = Programme.objects.get(pk=programme)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid programme chosen.'})
	streams = programme.streams.all()
	data = []
	for s in streams:
		data.append({'html': s.name.title(), 'value': settings.HASHID_STREAM.encode(s.pk)})
	return JsonResponse(status=200, data={'streams': data})

@require_user_types(['C', 'CO'])
@login_required
@require_http_methods(['GET','POST'])
def create_session(request, **kwargs):
	if request.is_ajax():
		type = kwargs.pop('user_type')
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
def edit_session(request, sess, **kwargs):
	if request.is_ajax():
		type = kwargs.pop('user_type')
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
def edit_criteria(request, sess, **kwargs):
	if request.is_ajax():
		type = kwargs.pop('user_type')
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
def dissociate(request, **kwargs):
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
def view_association_requests(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		profile = kwargs.pop('profile')
		associations = Association.objects.filter( ~Q(initiator=user_type) )
		if user_type == 'C':
			associations = associations.filter( Q(college=profile) & Q(approved=None) )
		elif user_type == 'F':
			associations = associations.filter( Q(college=profile.college) & Q(approved=None) )
		else:
			associations = associations.filter( Q(company=profile) & Q(approved=None) )
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
		if user_type in ['C','F']:
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
def generate_excel(request, sess, **kwargs):
#	if request.is_ajax() and request.user.type in ['F', 'C', 'CO']:
	user_type = kwargs.pop('user_type')
	profile = kwargs.pop('profile')
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
