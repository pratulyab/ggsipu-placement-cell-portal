from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError, InternalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import require_user_types, require_AJAX
from account.utils import handle_user_type, get_relevant_reversed_url, get_type_created
from college.models import College
from company.models import Company
from dummy_company.forms import CreateDummyCompanyForm, EditDummyCompanyForm, CreateDummySessionForm, EditDummySessionForm, ChooseDummyCompanyForm, CreateSelectionCriteriaForm, ManageDummySessionStudentsForm, EditDummySessionForm, EditDCriteriaForm, DummySessionFilterForm
from dummy_company.models import DummyCompany, DummySession
from faculty.models import Faculty
from notification.forms import NotifySessionStudentsForm
from recruitment.models import SelectionCriteria
from recruitment.tasks import dump_stats_record_task
from recruitment.utils import get_excel_structure
from student.models import Student, Programme, Stream

import openpyxl as excel, datetime, time, logging
from hashids import Hashids

dummyLogger = logging.getLogger('dummy')
studentLogger = logging.getLogger('student')

@require_user_types(['C', 'F'])
@login_required
@require_GET
def manage_dummy_company(request, **kwargs):
	user_type = kwargs.pop('user_type')
	college = kwargs.pop('profile')
	if user_type == 'F':
		college = college.college
	return render(request, 'dummy_company/manage_dummy_company.html', context={'create_dummy_company_form': CreateDummyCompanyForm(), 'choose_dummy_company_form': ChooseDummyCompanyForm(college=college), 'create_dummy_session_form': CreateDummySessionForm(college=college), 'create_selection_criteria_form': CreateSelectionCriteriaForm(), 'college': college, 'notify_session_students_form': NotifySessionStudentsForm()})

@require_user_types(['C', 'F'])
@login_required
@require_GET
def manage_dummy_session(request, dsess_hashid, profile, user_type, **kwargs):
	if user_type == 'F':
		profile = profile.college
	try:
		dsession_pk = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(dummy_company__college=profile, pk=dsession_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, there\'s nothing here to manage.'})
	context = {
		'dcompany': dsession.dummy_company,
		'dsession': dsession,
		'dsess_hashid': dsess_hashid,
		'manage_dsession_students_form': ManageDummySessionStudentsForm(instance=dsession),
		'edit_dcriteria_form': EditDCriteriaForm(instance=dsession.selection_criteria, dsession=dsession),
		'edit_dsession_form': EditDummySessionForm(instance=dsession),
		'home_url': reverse(settings.HOME_URL['C'] if user_type == 'C' else settings.HOME_URL['F']),
	}
	return render(request, 'dummy_company/manage_dummy_session.html', context=context)

@require_user_types(['C', 'F'])
@login_required
@require_POST
def create_dummy_company(request, **kwargs):
	if request.is_ajax():
		requester = get_type_created(request.user)
		user_type = requester.pop('user_type')
		if not requester:
			return JsonResponse(status=403, data={'location': reverse(settings.PROFILE_CREATION_URL[user_type]), 'refresh': True})
		f = CreateDummyCompanyForm(request.POST)
		if f.is_valid():
			college = requester['profile']
			if user_type == 'F':
				college = college.college # college = <Faculty Object>.college
			try:
				dcompany = f.save(college=college)
			except ValidationError as error:
				return JsonResponse(status=400, data={'error': error.__str__()})
			# LOG
			dummyLogger.info('[%s] - [%s : %s] - Created Dummy Company [%s]' % (college.code, user_type, request.user.username, dcompany.name))
			# # #
			return JsonResponse(data = {'refresh': True, 'location': '', 'message': 'Dummy Company %s has been created successfully' % (dcompany.name)})
		return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_GET
def get_edit_dcompany_form(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile') if user_type == 'C' else kwargs.pop('profile').college
		dc_hashid = request.GET.get('dcompany_hashid', '')
		try:
			dcompany_pk = settings.HASHID_DUMMY_COMPANY.decode(dc_hashid)[0]
			dcompany = DummyCompany.objects.get(college=college, pk=dcompany_pk)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid Request.'})
		f = EditDummyCompanyForm(instance=dcompany, prefix='dc')
		context = {'edit_dcompany_form': f, 'dsess': dc_hashid}
		return JsonResponse(data={'message': 'Success! Proceed to edit.', 'html': render(request, 'dummy_company/edit_dcompany.html', context).content.decode('utf-8')})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_POST
def edit_dummy_company(request, dummy_hashid, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile') if user_type == 'C' else kwargs.pop('profile').college
		post_hashid = request.POST.get('token', None)
		if dummy_hashid != post_hashid:
			return JsonResponse(status=400, data={'error': 'Invalid Request'})
		try:
			dc = settings.HASHID_DUMMY_COMPANY.decode(dummy_hashid)[0]
			dcompany = DummyCompany.objects.get(college=college, pk=dc)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid Request'})
		f = EditDummyCompanyForm(request.POST, instance=dcompany)
		if f.is_valid():
			dcompany = f.save()
			# LOG
			dummyLogger.info('[%s] - [%s : %s] - Edited Dummy Company [%s]' % (college.code, user_type, request.user.username, dcompany.name))
			# # #
			context = {'edit_dcompany_form': EditDummyCompanyForm(instance=dcompany), 'dsess': dummy_hashid, 'success_msg': 'Dummy Company\'s details have been updated.'}
#			return JsonResponse(data={'success': True, 'html': render(request, 'dummy_company/edit_dcompany.html', context).content.decode('utf-8')})
			return JsonResponse(status=200, data={'message': 'Dummy Company %s has been edited successfully' % (dcompany.name)})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_GET
def get_dummy_session_streams(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile')
		if user_type == 'F':
			college = college.college
		try:
			programme_pk = settings.HASHID_PROGRAMME.decode(request.GET['programme'])[0]
			programme = college.get_programmes_queryset().get(pk=programme_pk)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid programme chosen.'})
		streams = programme.streams.all()
		data = []
		years = []
		for s in streams:
			data.append({'html':s.name, 'value': settings.HASHID_STREAM.encode(s.pk)})
		for i in range(1, int(programme.years) + 1):
			years.append({'html': i, 'value': i})
		return JsonResponse(data={'streams':data, 'years': years})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_POST
def create_dummy_session(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile')
		if user_type == 'F':
			college = college.college
		try:
			programme_pk = settings.HASHID_PROGRAMME.decode(request.POST['programme'])[0]
			programme = college.get_programmes_queryset().get(pk=programme_pk)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid programme chosen.'})
		f = CreateDummySessionForm(request.POST, college=college)
		f.fields['streams'].queryset = programme.streams.all()
		f.fields['streams'].widget.attrs['disabled'] = False
		POST = request.POST.copy()
		POST['years'] = (','.join(POST.getlist('years')))
		g = CreateSelectionCriteriaForm(POST, max_year=int(programme.years))
		if f.is_valid() and g.is_valid():
			data = g.cleaned_data
			criterion, created = SelectionCriteria.objects.get_or_create(years=data['years'], is_sub_back=data['is_sub_back'], tenth=data['tenth'], twelfth=data['twelfth'], graduation=data['graduation'], post_graduation=data['post_graduation'], doctorate=data['doctorate'])
			dsession = f.save(commit=False)
			dsession.selection_criteria = criterion
			try:
				dsession.save()
			except InternalError:
				return JsonResponse(status=400, data={'error': 'Please ensure that there are no unsupported characters in the details.'})
			try:
				f.save_m2m()
			except IntegrityError as error:
				return JsonResponse(status=400, data={'error': error.__str__()})
			# LOG
			dummyLogger.info('[%s] - [%s : %s] - Created Dummy Session [%d]' % (college.code, user_type, request.user.username, dsession.pk))
			# # #
			return JsonResponse(data={'refresh': True, 'location': '', 'message': 'Dummy Session has been created successfully. To manage this session, go to "Dummy Sessions" tab.'})
		f = dict(f.errors.items())
		if f:
			g.is_valid()
		g = dict(g.errors.items())
		print(f)
		print(g)
		for key, value in g.items():
			f[key] = value
		return JsonResponse(status=400, data={'errors': f, 'message': 'Please correct the errors as indicated in the form.'})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_GET
def dummy_excel(request, dsess, **kwargs):
	requester = get_type_created(request.user)
	user_type = requester.pop('user_type')
	if not requester:
		return redirect(reverse(settings.PROFILE_CREATION_URL[user_type]))
	college = requester['profile']
	if user_type == 'F':
		if not request.user.groups.filter(name__in=['Placement Handler', 'Notifications Manager']):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		college = college.college
	try:
		dsession_id = settings.HASHID_DUMMY_SESSION.decode(dsess)[0]
		dsession = DummySession.objects.get(dummy_company__college=college, pk=dsession_id)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	title = dict(DummySession.PLACEMENT_TYPE)[dsession.type].__str__() + " opportunity by " + dsession.dummy_company.name.upper()
	streams_title = dsession.programme.name + ' - ' + ', '.join(["%s (%s)" % (s.name, s.code) for s in dsession.streams.all()])
	students_queryset = dsession.students.all()
	workbook = get_excel_structure(title, streams_title, students_queryset)
	response = HttpResponse(content=excel.writer.excel.save_virtual_workbook(workbook), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename=dummy_session_%s.xlsx' % Hashids(salt="AbhiKaSamay").encode(round(time.time()))
	return response


@require_user_types(['S'])
@login_required
@require_GET
def apply_to_dummy_company(request, dsess, **kwargs):
	if request.is_ajax():
		try:
			student = request.user.student
		except Student.DoesNotExist:
			return redirect(reverse(settings.PROFILE_CREATION_URL['S']))
		try:
			dsession_id = settings.HASHID_DUMMY_SESSION.decode(dsess)[0]
			dsession = DummySession.objects.get(dummy_company__college=student.college, pk=dsession_id)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid Request'})
		if student.stream not in dsession.streams.all() or dsession.application_deadline < datetime.date.today():
			return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
		criterion = dsession.selection_criteria
		eligibility = criterion.check_eligibility(student)
		if eligibility is None:
			return JsonResponse(status=400, data={'error': 'You need to fill the qualifications form before applying.'})
		message = 'Please get your %s verified by the placement cell faculty first.'
#		if not student.qualifications.is_verified or not student.qualifications.verified_by: # Qualifications.DoesNotExist has been taken care of by 'eligibility is None' condition
		if not student.is_verified or not student.verified_by:
			message = message % 'qualifications'
			return JsonResponse(status=400, data={'error': message})
#		elif not student.is_verified or not student.verified_by:
#			message = message % 'profile'
#			return JsonResponse(status=400, data={'error': message})
		if eligibility == False:
			return JsonResponse(status=400, data={'error': 'Sorry, you are not eligible for this %s.' % ('job' if dsession.type == 'J' else 'internship')})
		student_dummy_sessions = student.dummy_sessions.all()
		if dsession not in student_dummy_sessions:
			student.dummy_sessions.add(dsession)
			student.dsessions_applied_to.add(dsession)
			return JsonResponse(status=200, data={'enrolled': True})
		else:
			student.dummy_sessions.remove(dsession)
			# LOG
			studentLogger.info('[%s] - Withdrew from %d dummy session [%s]' % (request.user.username, dsession.pk, dsession.type))
			# # #
			return JsonResponse(status=200, data={'enrolled': False})
	else:
		raise PermissionDenied

@require_user_types(['C', 'F'])
@login_required
@require_GET
def my_dummy_sessions(request, **kwargs):
	user_type = kwargs.pop('user_type')
	college = kwargs.pop('profile') if user_type == 'C' else kwargs.pop('profile').college
	dsessions = DummySession.objects.filter(dummy_company__college=college)
	dsessions_list = []
	for ds in dsessions:
		data = {}
		data['dsessobj'] = ds
		data['dsess_hashid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
		data['salary'] = "%d LPA" % ds.salary
		data['dcompany'] = ds.dummy_company.name.title()
		data['type'] = "Internship" if ds.type == 'I' else "Job"
		data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
		data['students'] = ds.students.count()
		dsessions_list.append(data)
	html = render(request, 'dummy_company/dummy_sessions.html', {'dsessions': dsessions_list}).content.decode('utf-8')
	return JsonResponse(status=200, data={'html': html})

@require_user_types(['C', 'F'])
@require_AJAX
@login_required
@require_POST
def manage_dsession_students(request, dsess_hashid, user_type, profile, **kwargs):
	if user_type == 'F':
		profile = profile.college
	token = request.POST.get('token', None)
	if token != dsess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	try:
		dsession_pk = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(pk=dsession_pk, dummy_company__college=profile)
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, you can\'t make this request.'})
	f = ManageDummySessionStudentsForm(request.POST, instance=dsession)
	if f.is_valid():
		f.save()
		f.notify_disqualified_students(actor=profile.profile)
		return JsonResponse(status=200, data={'refresh': True, 'message': "List has been modified successfully"})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
	
@require_user_types(['C', 'F'])
@require_AJAX
@login_required
@require_POST
def edit_dcriteria(request, dsess_hashid, user_type, profile, **kwargs):
	if user_type == 'F':
		profile = profile.college
	token = request.POST.get('token', None)
	if token != dsess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	try:
		dsession_pk = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(pk=dsession_pk, dummy_company__college=profile)
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, you can\'t make this request.'})
	POST = request.POST.copy()
	POST['years'] = ','.join(POST.getlist('years'))
	f = EditDCriteriaForm(POST, instance=dsession.selection_criteria, dsession=dsession)
	if f.is_valid():
		criterion = f.save()
		dsession.selection_criteria = criterion
		dsession.save()
		# LOG
		dummyLogger.info('[%s] - [%s : %s] - Edited Criteria for [%d] - [%s]' % \
				(profile.code, user_type, request.user.username, dsession.pk, ','.join(f.changed_data)))
		# # #
		return JsonResponse(status=200, data={'message': "Selection Criteria has been updated successfully"})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

@require_user_types(['C', 'F'])
@require_AJAX
@login_required
@require_POST
def edit_dummy_session(request, dsess_hashid, user_type, profile, **kwargs):
	if user_type == 'F':
		profile = profile.college
	token = request.POST.get('token', None)
	if token != dsess_hashid:
		return JsonResponse(status=400, data={'error': 'Invalid request.'})
	try:
		dsession_pk = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(pk=dsession_pk, dummy_company__college=profile)
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, you can\'t make this request.'})
	f = EditDummySessionForm(request.POST, instance=dsession)
	if f.is_valid():
		try:
			f.save()
		except InternalError:
			return JsonResponse(status=400, data={'error': 'Please ensure that there are no unsupported characters in the details.'})
		message = 'Session Details have been updated successfully.'
		if f.should_notify_students():
			dump_stats_record_task.delay(dsession_pk, is_dummy=True)
			try:
				f.notify_selected_students(actor=profile.profile)
			except:
				return JsonResponse(status=400, data={'error': 'Sorry, error occurred while notifying students'})
			message += ' Students have been notified.'
		# LOG
		dummyLogger.info('[%s] - [%s : %s] - Edited Session for [%d] - [%s]' % (profile.code, user_type, request.user.username, dsession.pk, ','.join(f.changed_data)))
		# # #
		return JsonResponse(data={'success': True, 'message': message})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})

@require_user_types(['C', 'F'])
@require_AJAX
@login_required
@require_POST
def notify_dsession(request, dsess_hashid, user_type, profile):
	if user_type == 'F':
		if not request.user.groups.filter(name__in=['Placement Handler', 'Notifications Manager']):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	try:
		dsession_pk = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(dummy_company__college=profile, pk=dsession_pk)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})
	if not dsession.students.exists():
		return JsonResponse(status=400, data={'error': 'There are no students in the session.'})
	f = NotifySessionStudentsForm(request.POST)
	if f.is_valid():
		f.notify_all(students=dsession.students.all() , actor = profile.profile)
		return JsonResponse(status=200, data={'success_msg': 'Done.'})
	return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_user_types(['C', 'F'])
@require_AJAX
@login_required
@require_POST
def filter_dsessions(request, user_type, profile):
	if user_type == 'F':
		if not request.user.groups.filter(name__in=['Placement Handler', 'Notifications Manager']):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		profile = profile.college
	f = DummySessionFilterForm(request.POST, college=profile)
	if f.is_valid():
		dsessions = f.get_filtered_dsessions()
		dsessions_list = []
		for ds in dsessions:
			data = {}
			data['dsessobj'] = ds
			data['dsess_hashid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
			data['salary'] = "%d LPA" % ds.salary
			data['dcompany'] = ds.dummy_company.name.title()
			data['type'] = "Internship" if ds.type == 'I' else "Job"
			data['programme'] = ds.programme
			data['years'] = ds.selection_criteria.years
			data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
			data['students'] = ds.students.count()
			dsessions_list.append(data)
		html = render(request, 'college/dsessions_snippet.html', {'dsessions': dsessions_list, 'filtering': True}).content.decode('utf-8')
		return JsonResponse(status=200, data={'html': html})
	else:
		return JsonResponse(status=400, data={})

