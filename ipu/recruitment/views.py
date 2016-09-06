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
from faculty.models import Faculty
from recruitment.forms import AssActorsOnlyForm, AssWithProgrammeForm, AssociationForm, SessionEditForm, DissociationForm, DeadlineForm
from recruitment.models import Association, PlacementSession, Dissociation
from student.models import Student, Programme, Stream

import openpyxl as excel, time
from hashids import Hashids

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
		type = request.user.type
		if type not in ['C', 'CO']:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'GET':
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.GET.get('ass'))[0]
				association = Association.objects.get(pk=association_id)
			except: #To account for both KeyError as well as Association.DoesNotExist
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = DeadlineForm(association=association)
			html = render(request, 'recruitment/create_session.html', {'session_creation_form': f}).content.decode('utf-8')
			return JsonResponse(status=200, data={'html':html})
		
		else:
			try:
				association_id = settings.HASHID_ASSOCIATION.decode(request.POST.get('token'))[0]
				association = Association.objects.get(pk=association_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again'})
			f = DeadlineForm(request.POST, association=association)
			if f.is_valid():
				session = f.save(commit=False)
				session.last_modified_by = type
				session.save()
				association.approved = True
				association.save()
				return JsonResponse(status=200, data={'location': reverse(get_home_url(type))})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
	
	else:
		return handle_user_type(request, redirect_request=True)

@require_http_methods(['GET','POST'])
@login_required
def edit_session(request, sess):
	if request.is_ajax():
		type = request.user.type
		if type not in ['F', 'C', 'CO']:
			return JsonResponse(status=403, data={'location': get_relevant_reversed_url(request)})
		if request.method == 'POST':
			sess_post = request.POST.get('token')
			if sess != sess_post:
				return JsonResponse(status=400, data={'error': 'Invalid placement session'})
			try:
				session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
				session = PlacementSession.objects.get(pk=session_id)
			except:
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again.'})
			pk_changed = request.POST['students']
			old_len = session.objects.count()
			new_len = len(pk_changed)
			f = SessionEditForm(request.POST, instance=session)
			if f.is_valid():
				session = f.save()
				session.last_modified_by = type
				session.save()
				# Notifying other party about change in students' list
				if old_len != new_len:
					changed_students = []
					for s in [Student.objects.get(p) for p in pk_changed if p not in session.students.all().values('pk')]:
						changed_students.append(s)
					message = ''
					if association.type == 'J':
						message = 'Job'
					else:
						message = 'Internship'
					association = session.association
					message = message + ' Session: %s - {%s}\t' % (association.programme.__str__(), ', '.join([s.name.title() for s in association.streams.all()]) )
					usernames = '\n'.join([s.profile.username for s in changed_students])
					if new_len > old_len:
						message = '%d student%s added to the session\n%s' % (len(changed_students), '' if len(changed_students)==1 else 's', usernames)
					else:
						message = '%d student%s removed from the session\n%s' % (len(changed_students), '' if len(changed_students)==1 else 's', usernames)
					actor = association.college if type=='C' else association.company
					target = association.company if type=='C' else association.college
					# Creating notification
					Notification.objects.create(actor=actor.profile, target=target.profile, message=message)
				return JsonResponse(status=200, data={'location': reverse(get_home_url(type))})
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
				return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again.'})
			f = SessionEditForm(instance=session)
			return render(request, 'recruitment/edit_session.html', {'session_edit_form': f, 'sessid': sess})
		else:
			return handle_user_type(request)

@require_GET
@login_required
def mysessions(request):
	if request.is_ajax():
		user = request.user
		type = user.type
		sessions = None; html=''
		if type == 'S':
			try:
				student = user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('S'))})
			sessions = student.sessions.all()
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
				sessions_list.append(data)
			html = render(request, 'student/mysessions.html', {'sessions': sessions_list}).content.decode('utf-8')
		elif type == 'CO':
			try:
				company = user.company
			except Company.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('CO'))})
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
					return JsonResponse(status=400, data={'location': reverse(get_creation_url('F'))})
				college = faculty.college
			elif type == 'C':
				try:
					college = user.college
				except College.DoesNotExist:
					return JsonResponse(status=400, data={'location': reverse(get_creation_url('C'))})
			associations = Association.objects.filter(college=college, approved=True).values('pk')
			sessions = PlacementSession.objects.filter(association__pk__in = associations)
			sessions_list = []
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
				sessions_list.append(data)
			html = render(request, 'college/mysessions.html', {'sessions': sessions_list}).content.decode('utf-8')
		
		return JsonResponse(status=200, data={'html': html})
	else:
		return handle_user_type(request)

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

@require_GET
@login_required
def generate_excel(request, sess):
#	if request.is_ajax() and request.user.type in ['F', 'C', 'CO']:
	if request.user.type in ['F', 'C', 'CO']:
		try:
#			sess = request.GET.get('sess')
			session_id = settings.HASHID_PLACEMENTSESSION.decode(sess)[0]
			session = PlacementSession.objects.get(pk=session_id)
		except: #To account for both KeyError as well as PlacementSession.DoesNotExist
			return JsonResponse(status=400, data={'error': 'Unexpected error occurred. Please refresh the page and try again.'})
		workbook = excel.Workbook()
		worksheet = workbook.active
		worksheet.title = "Placement Session"
		worksheet['A1'].font = excel.styles.Font(name='Times New Roman', size=20, bold=True)
		worksheet.merge_cells("A1:I2");worksheet.merge_cells("A3:I3")
		if request.user.type == 'CO':
			text = dict(Association.PLACEMENT_TYPE)[session.association.type].__str__() + " session at "
			worksheet['A1'] = text + session.association.college.name.upper()
		else:
			text = dict(Association.PLACEMENT_TYPE)[session.association.type].__str__() + " opportunity by "
			worksheet['A1'] = text + session.association.company.name.upper()
		worksheet['A3'] = session.association.programme.name + ' - ' + ', '.join(["%s (%s)" % (s.name, s.code) for s in session.association.streams.all()])
		worksheet.freeze_panes = 'A5'
		
		# S.No. | Enrollment No. | First Name | Last Name | Gender | Email | Stream | Year
		worksheet['A4'] = 'S.No.'; worksheet['B4'] = 'Enrollment No.'; worksheet['C4'] = 'First Name'; worksheet['D4'] = 'Last Name';
		worksheet['E4'] = 'Sex';worksheet['F4'] = 'Email'; worksheet['G4'] = 'Stream'; worksheet['H4'] = 'Year';
		
		bold = excel.styles.Font(bold=True)
		for i in range(1,9):
			worksheet.cell(row=4, column=i).font = bold
		
		students = session.students.all()
		GENDER = dict(Student.GENDER_CHOICES)
		for i, student in enumerate(students, 1):
			row = worksheet.max_row+1
			worksheet.cell(row=row, column=1).value = i
			worksheet.cell(row=row, column=2).value = student.profile.username
			worksheet.cell(row=row, column=3).value = student.firstname.title()
			worksheet.cell(row=row, column=4).value = student.lastname.title()
			worksheet.cell(row=row, column=5).value = GENDER[student.gender].__str__()
			worksheet.cell(row=row, column=6).value = student.profile.email
			worksheet.cell(row=row, column=7).value = student.stream.name.title()
			worksheet.cell(row=row, column=8).value = student.current_year
		
		to_letter = excel.cell.get_column_letter
		for col in [1,5,8]:
			worksheet.column_dimensions[to_letter(col)].width = 5
		for col in [2,3,4]:
			worksheet.column_dimensions[to_letter(col)].width = 12
		for col in [6,7]:
			worksheet.column_dimensions[to_letter(col)].width = 20
		response = HttpResponse(content=excel.writer.excel.save_virtual_workbook(workbook), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename=session_%s.xlsx' % Hashids(salt="AbhiKaSamay").encode(round(time.time()))
		return response
#	else:
#		return HttpResponse('')
