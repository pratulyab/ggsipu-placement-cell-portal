from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from account.decorators import new_require_user_types
from account.utils import handle_user_type, get_relevant_reversed_url, get_type_created
from college.models import College
from company.models import Company
from dummy_company.forms import CreateDummyCompanyForm, EditDummyCompanyForm, CreateDummySessionForm, EditDummySessionForm, ChooseDummyCompanyForm, CreateSelectionCriteriaForm
from dummy_company.models import DummyCompany, DummySession
from faculty.models import Faculty
from recruitment.models import SelectionCriteria
from recruitment.utils import get_excel_structure
from student.models import Student, Programme, Stream

import openpyxl as excel, datetime, time
from hashids import Hashids

@new_require_user_types(['C', 'F'])
@login_required
@require_GET
def manage_dummy_home(request, **kwargs):
	user_type = kwargs.pop('user_type')
	college = kwargs.pop('profile')
	if user_type == 'F':
		college = college.college
	return render(request, 'dummy_company/manage_dummy_home.html', context={'create_dummy_company_form': CreateDummyCompanyForm(), 'choose_dummy_company_form': ChooseDummyCompanyForm(college=college), 'create_dummy_session_form': CreateDummySessionForm(college=college), 'create_selection_criteria_form': CreateSelectionCriteriaForm()})

@new_require_user_types(['C', 'F'])
@login_required
@require_POST
def create_dummy_company(request, **kwargs):
	if request.is_ajax():
		requester = get_type_created(request.user)
		user_type = requester.pop('user_type')
		if not requester:
			return JsonResponse(status=403, data={'location': reverse(settings.PROFILE_CREATION_URL[user_type])})
		f = CreateDummyCompanyForm(request.POST)
		if f.is_valid():
			college = requester['profile']
			if user_type == 'F':
				college = college.college # college = <Faculty Object>.college
			try:
				dcompany = f.save(college=college)
			except ValidationError as error:
				return JsonResponse(status=400, data={'error': error.__str__()})
			return JsonResponse(data = {'success': True, 'location': '/'})
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
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
		return JsonResponse(data={'success': True, 'html': render(request, 'dummy_company/edit_dcompany.html', context).content.decode('utf-8')})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
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
			context = {'edit_dcompany_form': EditDummyCompanyForm(instance=dcompany), 'dsess': dummy_hashid, 'success_msg': 'Dummy Company\'s details have been updated.'}
			return JsonResponse(data={'success': True, 'html': render(request, 'dummy_company/edit_dcompany.html', context).content.decode('utf-8')})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
@login_required
@require_GET
def get_dummy_session_streams(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile')
		if user_type == 'F':
			college = college.college
		try:
			programme_pk = request.GET['programme']
			programme = college.get_programmes_queryset().get(pk=programme_pk)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid programme chosen.'})
		streams = programme.streams.all()
		data = []
		years = []
		for s in streams:
			data.append({'html':s.name, 'value': s.pk})
		for i in range(1, int(programme.years) + 1):
			years.append({'html': i, 'value': i})
		return JsonResponse(data={'streams':data, 'years': years})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
@login_required
@require_POST
def create_dummy_session(request, **kwargs):
	if request.is_ajax():
		user_type = kwargs.pop('user_type')
		college = kwargs.pop('profile')
		if user_type == 'F':
			college = college.college
		try:
			programme_pk = request.POST['programme']
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
			dsession.save()
			try:
				f.save_m2m()
			except IntegrityError as error:
				return JsonResponse(status=400, data={'error': error.__str__()})
			return JsonResponse(data={'success': True, 'location': '/'})
		f = dict(f.errors.items())
		if f:
			g.is_valid()
		g = dict(g.errors.items())
		print(f)
		print(g)
		for key, value in g.items():
			f[key] = value
		return JsonResponse(status=400, data={'errors': f})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
@login_required
@require_http_methods(['GET', 'POST'])
def edit_dummy_session(request, sess_hashid, **kwargs):
	if request.is_ajax():
		requester = get_type_created(request.user)
		user_type = requester.pop('user_type')
		if not requester:
			return JsonResponse(status=403, data={'location': reverse(settings.PROFILE_CREATION_URL[user_type])})
		post_hashid = request.POST.get('token', None)
		if post_hashid != sess_hashid:
			return JsonResponse(status=400, data={'error': 'Invalid request.'})
		college = requester['profile']
		if user_type == 'F':
			college = college.college
		try:
			dsession_pk = settings.HASHID_DUMMY_SESSION.decode(sess_hashid)[0]
			dsession = DummySession.objects.get(dummy_company__college=college, pk=dsession_pk)
		except:
			return JsonResponse(status=400, data={'error': 'Invalid request.'})
		if request.method == 'POST':
			f = EditDummySessionForm(request.POST, instance=dsession, college=college)
			if f.is_valid():
				f.save()
				try:
					f.save_m2m()
				except IntegrityError as error:
					return JsonResponse(status=400, data={'error': error.__str__()})
				return JsonResponse(data={'success': True, 'location': '/'})
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			f = EditDummySessionForm(instance=dsession, college=college)
			context = {'edit_dsession_form': f}
			return JsonResponse(data = {'success': True, 'html': render(request, 'dummy_company/edit_dsession.html', context).content.decode('utf-8')})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
@login_required
@require_GET
def dummy_excel(request, dsess, **kwargs):
	requester = get_type_created(request.user)
	user_type = requester.pop('user_type')
	if not requester:
		return redirect(reverse(settings.PROFILE_CREATION_URL[user_type]))
	college = requester['profile']
	if user_type == 'F':
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


@new_require_user_types(['S'])
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
		if not criterion.check_eligibility(student):
			return JsonResponse(status=400, data={'error': 'Sorry, you are not eligible for this %s.' % 'job' if dsession.type == 'J' else 'internship'})
		student_dummy_sessions = student.dummy_sessions.all()
		if dsession not in student_dummy_sessions:
			student.dummy_sessions.add(dsession)
			return JsonResponse(status=200, data={'enrolled': True})
		else:
			student.dummy_sessions.remove(dsession)
			return JsonResponse(status=200, data={'enrolled': False})
	else:
		raise PermissionDenied

@new_require_user_types(['C', 'F'])
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
		data['dsessid'] = settings.HASHID_DUMMY_SESSION.encode(ds.pk)
		data['salary'] = "%d LPA" % ds.salary
		data['dcompany'] = ds.dummy_company.name.title()
		data['type'] = "Internship" if ds.type == 'I' else "Job"
		data['streams'] = ', '.join([s.name.title() for s in ds.streams.all()])
		data['students'] = ds.students.count()
		dsessions_list.append(data)
	html = render(request, 'dummy_company/dummy_sessions.html', {'dsessions': dsessions_list}).content.decode('utf-8')
	return JsonResponse(status=200, data={'html': html})
