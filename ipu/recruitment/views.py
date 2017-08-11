from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.utils import IntegrityError, InternalError
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import require_user_types, require_AJAX
from account.utils import handle_user_type, get_relevant_reversed_url, get_type_created
from college.models import College
from company.models import Company
from dummy_company.models import DummyCompany, DummySession
from faculty.models import Faculty
from notification.forms import NotifySessionStudentsForm
from notification.models import Notification
from recruitment.forms import AssociationForm, EditSessionForm, DissociationForm, CreateSessionCriteriaForm, EditCriteriaForm, ManageSessionStudentsForm, SessionFilterForm, DeclineForm
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from recruitment.utils import get_excel_structure
from student.models import Student, Programme, Stream

import openpyxl as excel, time, logging
from hashids import Hashids

collegeLogger = logging.getLogger('college')
companyLogger = logging.getLogger('company')
recruitmentLogger = logging.getLogger('recruitment')

@require_user_types(['C', 'CO'])
@require_AJAX
@login_required
@require_POST
def associate(request, **kwargs):
	user_type = kwargs.get('user_type')
	f = AssociationForm(request.POST, profile=kwargs.pop('profile'))

	# Suspicious Activity
	if user_type == 'CO' and not f.can_make_requests():
		recruitmentLogger.warning('Company %s [%d] has reached requests limit' % (f.profile, f.profile.pk))
		return JsonResponse(status=400, data={'message': 'Sorry, you cannot send any more requests until any of your existing requests gets accepted.'})
	# # #

	if f.is_valid():
		try:
			assoc = f.save()
			f.save_m2m()
			# LOG
			if user_type == 'C':
				message = "[%s: %s] -> Sent Association Request -> [%s] - [A: %d]" % \
						   (f.profile.profile.username, f.profile.code, assoc.company.name, assoc.pk)
			else:
				message = "[%s: %s] -> Sent Association Request -> [%s] - [A: %d]" % \
						   (f.profile.profile.username, f.profile.name, assoc.college.code, assoc.pk)
			recruitmentLogger.info(message)
			# # #
		except (ValidationError, IntegrityError) as error:
			return JsonResponse(status=400, data={'error': error.__str__(), 'message': 'Please correct the errors as indicated in the form.'})
		except InternalError:
			return JsonResponse(status=400, data={'error': 'Please ensure that there are no unsupported characters in the details.'})
		return JsonResponse(status=200, data={
				'message': 'Request sent!\nIf you wish to delete the request for any reasons, go to "My Requests" tab and delete the request.',
				'refresh': True
				})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

@require_user_types(['C', 'F', 'CO'])
@login_required
@require_GET
def manage_session(request, sess_hashid, **kwargs):
	profile = kwargs.pop('profile')
	user_type = kwargs.pop('user_type')
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	try:
		session_pk = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_pk)
		else:
			session = PlacementSession.objects.get(association__college=profile, pk=session_pk)
	except:
		raise Http404()
	context = {
		'edit_criteria_form': EditCriteriaForm(instance=session.selection_criteria, session=session),
		'edit_session_form': EditSessionForm(instance=session),
		'manage_session_students_form': ManageSessionStudentsForm(instance=session),
		'association': session.association,
		'session': session,
		'sess_hashid': sess_hashid,
		'home_url': reverse(settings.HOME_URL['CO'] if user_type == 'CO' else settings.HOME_URL['C']),
		'user': profile.profile
	}
	return render(request, 'recruitment/manage_session.html', context)

@require_user_types(['C', 'F', 'CO'])
@require_AJAX
@login_required
@require_POST
def edit_criteria(request, sess_hashid, **kwargs):
	profile = kwargs.pop('profile')
	user_type = kwargs.pop('user_type')
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	token = request.POST.get('token', None)
	if token != sess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	try:
		session_pk = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_pk)
		else:
			session = PlacementSession.objects.get(association__college=profile, pk=session_pk)
	except:
		return JsonResponse(status=400, data={'error': 'It\'s not your placement session to manage!'})
	POST = request.POST.copy()
	POST['years'] = ','.join(POST.getlist('years'))
	f = EditCriteriaForm(POST, instance=session.selection_criteria, session=session)
	if f.is_valid():
		criterion = f.save() # Not the typical save. Using get_or_create in form's save w/o calling super save
		session.selection_criteria = criterion
		session.last_modified_by = 'CO' if user_type == 'CO' else 'C'
		session.save()
	# Notifying the other party
		actor, target = (profile, session.association.college) if user_type == 'CO' else (profile, session.association.company)
		link = "%s://%s" % (('https' if settings.USE_HTTPS else 'http'), str(get_current_site(request)) + reverse('manage_session', kwargs={'sess_hashid': sess_hashid}))
		f.notify_other_party(actor=actor.profile, target=target.profile, link=link)
	######
		return JsonResponse(status=200, data={'message': 'Selection Criteria has been updated successfully'})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

@require_user_types(['C', 'F', 'CO'])
@require_AJAX
@login_required
@require_POST
def edit_session(request, sess_hashid, **kwargs):
	profile = kwargs.pop('profile')
	user_type = kwargs.pop('user_type')
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	token = request.POST.get('token', None)
	if token != sess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	try:
		session_pk = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_pk)
		else:
			session = PlacementSession.objects.get(association__college=profile, pk=session_pk)
	except:
		return JsonResponse(status=400, data={'error': 'It\'s not your placement session to manage!'})
	f = EditSessionForm(request.POST, instance=session)
	if f.is_valid():
		session = f.save(commit=False)
		session.last_modified_by = 'CO' if user_type == 'CO' else 'C'
		session.save()
		if 'desc' in f.changed_data:
			association = session.association
#			association.salary = f.cleaned_data['salary']
			association.desc = f.cleaned_data['desc']
			try:
				association.save()
			except InternalError:
				return JsonResponse(status=400, data={'error': 'Please ensure that there are no unsupported characters in the details.'})
	# Notifying the other party
		actor, target = (profile, session.association.college) if user_type == 'CO' else (profile, session.association.company)
		link = "%s://%s" % (('https' if settings.USE_HTTPS else 'http'), str(get_current_site(request)) + reverse('manage_session', kwargs={'sess_hashid': sess_hashid}))
		f.notify_other_party(actor=actor.profile, target=target.profile, link=link)
	########
		message = 'Placement Session has been updated successfully.'
		if f.should_notify_students():
			try:
				f.notify_selected_students(actor=profile.profile)
			except:
				return JsonResponse(status=400, data={'error': 'Sorry, error occurred while notifying students.'})
			message += ' Students have been notified.'
		return JsonResponse(status=200, data={'message': message})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

@require_user_types(['C', 'F', 'CO'])
@require_AJAX
@login_required
@require_POST
def manage_session_students(request, sess_hashid, **kwargs):
	profile = kwargs.pop('profile')
	user_type = kwargs.pop('user_type')
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	token = request.POST.get('token', None)
	if token != sess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	try:
		session_pk = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_pk)
		else:
			session = PlacementSession.objects.get(association__college=profile, pk=session_pk)
	except:
		return JsonResponse(status=400, data={'error': 'It\'s not your placement session to manage!'})
	f = ManageSessionStudentsForm(request.POST, instance=session)
	if f.is_valid():
		session = f.save(commit=False)
		session.last_modified_by = 'CO' if user_type == 'CO' else 'C'
		session.save()
		f.save_m2m()
		f.notify_disqualified_students(actor=profile.profile)
		return JsonResponse(status=200, data={'refresh': True, 'message': "Students' list has been modified successfully"})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

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
		return JsonResponse(status=400, data={'error': 'Invalid college chosen.', 'message': 'Please choose a valid college'})
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
		return JsonResponse(status=400, data={'error': 'Invalid programme chosen.', 'message': 'Please choose a valid programme.'})
	streams = programme.streams.all()
	data = []
	for s in streams:
		data.append({'html': s.name.title(), 'value': settings.HASHID_STREAM.encode(s.pk)})
	return JsonResponse(status=200, data={'streams': data})

@require_user_types(['C', 'CO', 'F'])
@login_required
@require_http_methods(['GET','POST'])
def create_session(request, **kwargs):
	if request.is_ajax():
		type = kwargs.pop('user_type')
		if type == 'F' and not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
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
			if association.initiator == type: # Validating that the requester is not the one accepting
				return JsonResponse(status=400, data={'error': 'You cannot make this request.'})
			f = CreateSessionCriteriaForm(association=association)
			context = {'session_creation_form': f}
			context['association'] = association
			context['other_party'] = association.company.name if association.initiator == 'CO' else association.college.name
			context['streams'] = ', '.join([s['name'] for s in association.streams.values('name')])
			context['hashid'] = settings.HASHID_ASSOCIATION.encode(association.pk)
			html = render(request, 'recruitment/create_session.html', context).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			user_type = kwargs.get('user_type')
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.prefetch_related('college', 'company').get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Invalid Request.'})
			# validating whether the college/company is making request for its own association
			requester = validate_associator(request, association)
			creation = requester.get('creation', False)
			if creation:
				return JsonResponse(status=400, data={'location': creation})
			if not requester.get('authorized', True):
				return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
			if association.initiator == type: # Validating that the requester is not the one accepting
				return JsonResponse(status=400, data={'error': 'You cannot make this request.'})
			try:
				association.session
				return JsonResponse(status=400, data={'error': 'Session already exists', 'refresh': True})
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
				# LOG
				if user_type == 'C':
					message = "[%s] -> Created Session (Accepted) -> [%s] - [A/S: %d/%d]" % \
							   (association.college.code, association.company.name, association.pk, session.pk)
				else:
					message = "[%s: %s] -> Created Session (Accepted) -> [%s] - [A/S: %d/%d]" % \
							   (association.company.profile.username, association.company.name, association.college.code, association.pk, session.pk)
				recruitmentLogger.info(message)
				# # #
				message = '%s session has been created successfully. To manage the session, move to "Sessions" tab.'\
						  % (dict(Association.PLACEMENT_TYPE)[association.type])
				return JsonResponse(status=200, data={'refresh': True, 'message': message})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
	
	else:
		return handle_user_type(request, redirect_request=True)

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
			all_sessions_list = []
			for s in sessions:
				assoc = s.association
				data = {}
				data['sessobj'] = s
				data['sessid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['company'] = assoc.company.name.title() if assoc.company.name.islower() else assoc.company.name
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.company.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['programme'] = assoc.programme
				data['years'] = assoc.session.selection_criteria.years
				data['students'] = s.students.count()
				data['status'] = s.status
				data['is_dummy'] = False
				all_sessions_list.append(data)
			for ds in dsessions:
				data = {}
				data['dsessobj'] = ds
				data['dsessid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
				data['salary'] = "%d LPA" % ds.salary
				data['company'] = ds.dummy_company.name.title() if ds.dummy_company.name.islower() else ds.dummy_company.name
				data['type'] = "Internship" if ds.type == 'I' else "Job"
				data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
				data['programme'] = ds.programme
				data['years'] = ds.selection_criteria.years
				data['students'] = ds.students.count()
				data['status'] = ds.status
				data['is_dummy'] = True
				all_sessions_list.append(data)
			html = render(request, 'student/mysessions.html', {'sessions': all_sessions_list}).content.decode('utf-8')
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
				data['sess_hashid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['college'] = assoc.college.name.title()
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.college.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['programme'] = assoc.programme
				data['years'] = assoc.session.selection_criteria.years
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
				if not request.user.groups.filter(name='Placement Handler'):
					return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
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
				data['sess_hashid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
				data['salary'] = "%d LPA" % assoc.salary
				data['company'] = assoc.company.name.title()
				data['type'] = "Internship" if assoc.type == 'I' else "Job"
				data['photo'] = assoc.company.photo
				data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
				data['programme'] = assoc.programme
				data['years'] = assoc.session.selection_criteria.years
				data['students'] = s.students.count()
#				data['is_dummy'] = False
				sessions_list.append(data)
			for ds in dsessions:
				data = {}
				data['dsessobj'] = ds
				data['dsess_hashid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
				data['salary'] = "%d LPA" % ds.salary
				data['dcompany'] = ds.dummy_company.name.title()
				data['type'] = "Internship" if ds.type == 'I' else "Job"
				data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
				data['programme'] = ds.programme
				data['years'] = ds.selection_criteria.years
				data['students'] = ds.students.count()
#				data['is_dummy'] = True
				dsessions_list.append(data)
			html = render(request, 'college/mysessions.html', {'sessions': sessions_list, 'dsessions': dsessions_list}).content.decode('utf-8')
		return JsonResponse(status=200, data={'html': html})
	else:
		return handle_user_type(request)

@require_user_types(['C', 'CO', 'F'])
@login_required
@require_http_methods(['GET','POST'])
def decline(request, **kwargs):
	user_type = kwargs.get('user_type')
	if request.is_ajax():
		if user_type == 'F' and not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		if request.method == 'GET':
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.GET.get('ass'))[0]
				association = Association.objects.prefetch_related('college', 'company').get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = DeclineForm(association=association)
			context = {'decline_form': f}
			context['association'] = association
			context['other_party'] = association.company.name if association.initiator == 'CO' else association.college.name
			context['streams'] = ', '.join([s['name'] for s in association.streams.values('name')])
			context['hashid'] = settings.HASHID_ASSOCIATION.encode(association.pk)
			html = render(request, 'recruitment/decline.html', context).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			POST = request.POST.copy()
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.prefetch_related('college', 'company').get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			POST['college'] = association.college.pk
			POST['company'] = association.company.pk
			f = DeclineForm(POST, association=association)
			if f.is_valid():
				f.save()
				# LOG
				if user_type == 'C':
					message = "[%s: %s] -> Declined Request -> [%s] - [%d]" % \
							   (association.college.profile.username, association.college.code, association.company.name, association.pk)
				else:
					message = "[%s: %s] -> Declined Request -> [%s] - [%d]" % \
							   (association.company.profile.username, association.company.name, association.college.profile.username, association.pk)
				recruitmentLogger.info(message)
				# # #
				message = 'You declined the request.\nIf you wish to stop receiving requests from this user, you can block them.\n Click info to know more.'
				return JsonResponse(status=200, data={'refresh': True, 'message': message})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_AJAX
@require_user_types(['C','CO','F'])
@login_required
@require_GET
def view_my_requests(request, profile, user_type):
	queryset = []
	if user_type == 'F':
		profile = profile.college
	if user_type == 'CO':
		queryset = Association.objects.order_by('-updated_on').filter(company=profile, initiator=user_type).filter(~Q(approved=True))
	else:
		queryset = Association.objects.order_by('-updated_on').filter(college=profile, initiator='C').filter(~Q(approved=True))
	my_requests = {'pending': [], 'declined': []}
	for association in queryset:
		if association.approved is None:
			data = {}
			data['who'] = association.company.name.title() if association.initiator=='C' else association.college.name.title()
			data['hashid'] = settings.HASHID_ASSOCIATION.encode(association.pk)
			data['salary'] = "%d LPA" % association.salary
			data['type'] = "Internship" if association.type == 'I' else "Job"
			data['photo'] = association.company.photo if association.initiator=='C' else association.college.photo
			data['programme'] = association.programme
			data['streams'] = ', '.join([s.name.title() for s in association.streams.all()])
			data['created_on'] = association.created_on
			my_requests['pending'].append(data)
		else:
			data = {}
			data['who'] = association.company.name.title() if association.initiator=='C' else association.college.name.title()
			data['hashid'] = settings.HASHID_ASSOCIATION.encode(association.pk)
			data['salary'] = "%d LPA" % association.salary
			data['type'] = "Internship" if association.type == 'I' else "Job"
			data['photo'] = association.company.photo if association.initiator=='C' else association.college.photo
			data['programme'] = association.programme
			data['streams'] = ', '.join([s.name.title() for s in association.streams.all()])
			data['created_on'] = association.created_on
			data['decline_message'] = association.decline_message
			my_requests['declined'].append(data)
	html = render(request, 'recruitment/my_requests.html', {'requests': my_requests}).content.decode('utf-8')
	return JsonResponse(status=200, data={'html': html})

@require_AJAX
@require_user_types(['C', 'CO'])
@login_required
@require_POST
def delete_request(request, profile, user_type, request_hashid):
	try:
		association_id = settings.HASHID_ASSOCIATION.decode(request_hashid)[0]
		association = profile.associations.get(pk=association_id)
	except:
		return JsonResponse(status=400, data={'error': 'No such association request of yours exist.'})
	association.delete()
	if user_type == 'C':
		collegeLogger.info('[%s: %s] - Deleted Association Request - [A: %d]' % (profile.profile.username, profile.code, association_id))
	else:
		companyLogger.info('[%s: %s] - Deleted Association Request - [A: %d]' % (profile.profile.username, profile.name, association_id))
	return JsonResponse(status=200, data={'message': 'Successfully Deleted!', 'callback': True})
'''

@require_user_types(['C', 'CO'])
@require_AJAX
@login_required
@require_http_methods(['GET', 'POST'])
def dissociate(request, profile, user_type, **kwargs):
	try:
		assoc_pk = settings.HASHID_ASSOCIATION.decode(request.GET.get('token') if request.method=='GET' else request.POST.get('token'))[0]
		if user_type == 'C':
			association = Association.objects.get(pk=assoc_pk, college=profile)
		else:
			association = Association.objects.get(pk=assoc_pk, company=profile)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid Request'})
	if Dissociation.objects.filter(college=association.college, company=association.company).values('pk'):
		return JsonResponse(status=400, data={'error': 'You\'ve already blocked this user'})
	if request.method == 'POST':
		POST = request.POST.copy()
		POST['college'] = association.college.pk
		POST['company'] = association.company.pk
		f = DissociationForm(POST, association=association)
		if f.is_valid():
			f.save()
			if f.cleaned_data['delete_all_association_requests']:
				f.delete_all_association_requests()
			association.approved = False
			association.save()
			return JsonResponse(status=200, data={})
	else:
		html = render(request, 'recruitment/dissociate.html', {'dissociation_form': DissociationForm(association=association)}).content.decode('utf-8')
		return JsonResponse(status=200, data={'html': html})
'''
# # # # # # #
@require_user_types(['C','CO'])
@login_required
@require_GET
def manage_dissociation(request, profile, user_type):
	context = {'dissociations': [], 'create_dissociation_form': DissociationForm(profile=profile, user_type=user_type)}
	context['profile'] = profile
#	context['home_url'] = "%s://%s" % (('https' if settings.USE_HTTPS else 'http'), str(get_current_site(request)) + reverse('manage_session', kwargs={'sess_hashid': sess_hashid}))
	context['home_url'] = reverse(settings.HOME_URL[user_type])
	(context['requester'],context['other'])  = ('college','company') if user_type == 'C' else ('company','college') # (requester, blocked)
	context['other_plural'] = 'colleges' if user_type == 'CO' else 'companies'
	context['default_image'] = 'images/%s.png' % context['requester']
	for dissociation in profile.dissociations.all():
		data = {}
		data['hashid'] = settings.HASHID_DISSOCIATION.encode(dissociation.pk)
		if user_type == 'C':
			data['photo'] = dissociation.company.photo
			data['name'] = dissociation.company.name
			data['reason'] = dissociation.reason
			data['blocked_on'] = dissociation.created_on
		else:
			data['photo'] = dissociation.college.photo
			data['name'] = dissociation.college.name
			data['reason'] = dissociation.reason
			data['blocked_on'] = dissociation.created_on
		context['dissociations'].append(data)
	return render(request, 'recruitment/manage_dissociation.html', context)

@require_AJAX
@require_user_types(['C', 'CO'])
@login_required
@require_POST
def create_dissociation(request, profile, user_type):
	f = DissociationForm(request.POST, profile=profile, user_type=user_type)
	if f.is_valid():
		dissociation = f.save()
		f.delete_all_pending_associations()
		# LOG
		message = '[%s: %s] - Blocked - [%s: %s]'
		if user_type == 'C':
			collegeLogger.info(message % (profile.profile.username, profile.code, dissociation.company.profile.username, dissociation.company.name))
		else:
			companyLogger.info(message % (profile.profile.username, profile.name, dissociation.college.profile.username, dissociation.college.code))
		# # #
		return JsonResponse(status=200, data={'message': 'Successfully Blocked %s!' % (profile.__class__.__name__)})
	return JsonResponse(status=400, data={'error': 'Error Occurred', 'errors': dict(f.errors.items())})

@require_AJAX
@require_user_types(['C', 'CO'])
@login_required
@require_POST
def delete_dissociation(request, profile, user_type, dissociation_hashid):
	try:
		dissociation_id = settings.HASHID_DISSOCIATION.decode(dissociation_hashid)[0]
		dissociation = profile.dissociations.prefetch_related('college', 'company').get(pk=dissociation_id)
	except:
		return JsonResponse(status=400, data={'error': 'You haven\'t blocked any such user.'})
	dissociation.delete()
	# LOG
	message = '[%s: %s] - Unblocked - [%s: %s]'
	if user_type == 'C':
		collegeLogger.info(message % (profile.profile.username, profile.code, dissociation.company.profile.username, dissociation.company.name))
	else:
		companyLogger.info(message % (profile.profile.username, profile.name, dissociation.college.profile.username, dissociation.college.code))
	# # #
	return JsonResponse(status=200, data={'message': 'Successfully Deleted!', 'callback': True})

# # # # # # #
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
			if not request.user.groups.filter(name='Placement Handler'):
				return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
			associations = associations.filter( Q(college=profile.college) & Q(approved=None) )
		else:
			associations = associations.filter( Q(company=profile) & Q(approved=None) )
		associations_list = []
		context = {}
		for ass in associations:
			streams = ', '.join([s['name'] for s in ass.streams.values('name')])
			associations_list.append({'obj':ass, 'hashid':settings.HASHID_ASSOCIATION.encode(ass.pk), 'streams': streams})
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
			if not request.user.groups.filter(name='Placement Handler'):
				return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
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

@require_user_types(['C', 'F', 'CO'])
@require_AJAX
@login_required
@require_POST
def notify_session(request, sess_hashid, user_type, profile):
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	try:
		session_pk = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_pk)
		else:
			session = PlacementSession.objects.get(association__college=profile, pk=session_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	if not session.students.exists():
		return JsonResponse(status=400, data={'error': 'There are no students in the session.'})
	f = NotifySessionStudentsForm(request.POST)
	if f.is_valid():
		f.notify_all(students=session.students.all() , actor = profile.profile)
		return JsonResponse(status=200, data={'success_msg': 'Done.'})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['C', 'F', 'CO'])
@require_AJAX
@login_required
@require_POST
def filter_sessions(request, user_type, profile):
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	f = SessionFilterForm(request.POST, profile=profile)
	if f.is_valid():
		sessions = f.get_filtered_sessions()
		sessions_list = []
		for s in sessions:
			assoc = s.association
			data = {}
			data['sessobj'] = s
			data['sess_hashid'] = settings.HASHID_PLACEMENTSESSION.encode(s.pk)
			data['salary'] = "%d LPA" % assoc.salary
			data['company'] = assoc.company.name.title()
			data['type'] = "Internship" if assoc.type == 'I' else "Job"
			data['photo'] = assoc.company.photo
			data['streams'] = ', '.join([s.name.title() for s in assoc.streams.all()])
			data['programme'] = assoc.programme
			data['years'] = assoc.session.selection_criteria.years
			data['students'] = s.students.count()
			sessions_list.append(data)
		if user_type == 'CO':
			html = render(request, 'company/mysessions.html', {'sessions': sessions_list, 'filtering': True}).content.decode('utf-8')
		else:
			html = render(request, 'college/sessions_snippet.html', {'sessions': sessions_list, 'filtering': True}).content.decode('utf-8')
		return JsonResponse(status=200, data={'html': html})
	else:
		return JsonResponse(status=400, data={})

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
