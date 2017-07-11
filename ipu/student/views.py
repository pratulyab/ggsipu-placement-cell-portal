from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.decorators import require_user_types , check_recaptcha
from account.forms import AccountForm, SocialProfileForm
from account.models import CustomUser, SocialProfile
from account.tasks import send_activation_email_task
from account.utils import handle_user_type, get_relevant_reversed_url
from college.models import College, Stream
from dummy_company.models import DummyCompany, DummySession
from faculty.forms import VerifyStudentProfileForm
from notification.models import Notification
from student.forms import StudentLoginForm, StudentSignupForm, StudentCreationForm, StudentEditForm, QualificationForm, TechProfileForm, FileUploadForm, PaygradeForm, ScoreForm, ScoreMarksheetForm, CGPAMarksheetForm, QualForm
from recruitment.models import Association, PlacementSession
from student.models import Student, TechProfile, Qualification, SchoolMarksheet, Score
from . import scrape

import os, re, datetime, logging
from bs4 import BeautifulSoup

facultyLogger = logging.getLogger('faculty')
studentLogger = logging.getLogger('student')

# Create your views here.

@require_POST
def student_login(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	f = StudentLoginForm(request.POST)
	if f.is_valid():
		user = f.get_user()
		if not user.is_active:
			return JsonResponse(data={'success': True, 'render': render_to_string('account/inactive.html', {'user': user})})
		auth_login(request, user)
		return JsonResponse(data = {'success': True, 'location': get_relevant_reversed_url(request)})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@check_recaptcha
@require_POST
def student_signup(request):
	if not request.recaptcha_is_valid:
		return JsonResponse(status = 400 , data={'error' : 'reCAPTCHA authorization failed. Please try again.'})
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	f = StudentSignupForm(request.POST)
	if f.is_valid():
		user = f.save()
		user = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
#		auth_login(request, user)
		send_activation_email_task.delay(user.pk, get_current_site(request).domain)
		context = {'email': user.email, 'profile_creation': request.build_absolute_uri(reverse(settings.PROFILE_CREATION_URL['S']))}
		html = render(request, 'account/post_signup.html', context).content.decode('utf-8')
		return JsonResponse(data = {'success': True, 'render': html})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

#@require_user_types(['S'])
@login_required
@require_http_methods(['GET','POST'])
def create_student(request, **kwargs):
	if request.user.type == 'S':
		username = request.user.username
		user_profile = request.user
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', username).groups()
		except AttributeError:
#			pass
			raise Http404(_('Enrollment number should contain only digits'))
		except ValueError:
#			pass
			raise Http404(_('Enrollment number should be 11 digits long'))
		coll = College.objects.get(code=coll).pk
		strm = Stream.objects.get(code=strm).pk
		if request.method == 'GET':
			f = StudentCreationForm(profile=user_profile, coll=coll, strm=strm)
			try:
				student = request.user.student
				return redirect(settings.HOME_URL['S'])
			except Student.DoesNotExist:
				pass
		else:
			POST = request.POST.copy()
			POST['college'] = coll
			POST['stream'] = strm
			POST['programme'] = Stream.objects.get(pk=strm).programme.pk
			f = StudentCreationForm(POST, request.FILES, profile=user_profile, coll=coll, strm=strm)
			if f.is_valid():
				student = f.save()
				return redirect(settings.HOME_URL['S'])
		return render(request, 'student/create.html', {'student_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['S'])
@login_required
@require_GET
def student_home(request, **kwargs):
##	if request.user.type == 'S':
	context = {}
	user = request.user
	context['user'] = user
	try:
		student = request.user.student
	except Student.DoesNotExist:
		return redirect(settings.PROFILE_CREATION_URL['S'])
	context['student'] = student
	try:
		if student.marksheet or student.qualification:	
			if not student.is_verified and student.verified_by is None:
				# Can't permit to home page, because authenticity of student can't be identified
				if request.is_ajax():
					return JsonResponse(status=403, data={'message': 'Get your profile verified by college', 'refresh': True})
				else:
					try:
						marksheet = student.marksheet
						context['tenth'] = marksheet.cgpa_marksheet.calculate_percentage() if marksheet.cgpa_marksheet else marksheet.marksheet_10.calculate_percentage()
						context['twelfth'] = marksheet.marksheet_12.calculate_percentage()
						context['graduation'] = student.qualifications.graduation
					finally:
						return render(request, 'student/unverified.html', context)
	except:
		# fill qualifications
		context['qual_form'] = QualForm()
		for klass in ['10','12']:
			for number in range(1,7): # 6 subjects
				context['score_form_%s_%d' % (klass,number)] = ScoreForm(number=number, prefix="%s_%d" % (klass, number))
		context['score_marksheet_form_10'] = ScoreMarksheetForm(klass='10', prefix='score_10')
		context['score_marksheet_form_12'] = ScoreMarksheetForm(klass='12', prefix='score_12')
		context['cgpa_marksheet_form'] = CGPAMarksheetForm(prefix='cgpa')
		return render(request, 'student/qualifications.html', context)
	
	context['edit_account_form'] = AccountForm(instance=user)
	context['upload_file_form'] = FileUploadForm(instance=student)
#	if student.is_verified is None:
#		context['edit_profile_form'] = StudentEditForm(instance=student)
#	try:
#		qual = student.qualifications
#		if qual.is_verified is None or (qual.is_verified == False and qual.verified_by is None):
#			context['edit_qual_form'] = QualificationForm(instance=qual)
#	except Qualification.DoesNotExist:
#		context['edit_qual_form'] = QualificationForm()
	try:
		context['social_profile_form'] = SocialProfileForm(instance=user.social)
	except SocialProfile.DoesNotExist:
		context['social_profile_form'] = SocialProfileForm()
	try:
		context['tech_profile_form'] = TechProfileForm(instance=student.tech, student=student)
	except:
		context['tech_profile_form'] = TechProfileForm(student=student)
	if not student.salary_expected:
		context['paygrade_form'] = PaygradeForm()
	context['badge'] = student.profile.notification_target.filter(is_read=False).count()
	return render(request, 'student/home.html', context)
##	else:
##		return handle_user_type(request, redirect_request=True)

@require_user_types(['S', 'F'])
@login_required
@require_POST
def edit_student(request, **kwargs):
	if request.is_ajax():
		if request.user.type == 'S':
			username = request.user.username
			try:
				roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', username).groups()
			except:
				print("KAAABOOOOOOM ~~~~")
				return JsonResponse(status=403, data={'location': get_relevant_reversed_url('S')})
			coll = College.objects.get(code=coll).pk
			strm = Stream.objects.get(code=strm).pk
			try:
				student = request.user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
			POST = request.POST.copy()
			POST['college'] = student.college.pk
			POST['programme'] = student.programme.pk
			POST['stream'] = student.stream.pk
			f = StudentEditForm(POST, request.FILES, instance=student)
			if f.is_valid():
				f.save(verified=False, verifier=student.verified_by)
				# LOG
				studentLogger.info('[%s] - Updated Profile - %s' % (username, ','.join(f.changed_data)))
				###
#			context = {}
#			context['message'] = "Your profile has been updated. Please contact your college's TPC faculty for verification."
#			return JsonResponse(status=200, data={'render': render(request, 'student/home.html', context).content.decode('utf-8')})
				toast_msg = "Your profile has been updated successfully! Contact your college's Training & Placement Cell's faculty for verification."
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['S']), 'toast_msg': toast_msg})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
			
		elif request.user.type == 'F' and request.is_ajax():
			if not request.user.groups.filter(name='Verifier'):
				return JsonResponse(status=403, data={'error': 'Permission Denied. You cannot verify students'})
			enroll = request.session.get('enrollmentno', None)
			if not enroll:
#				Http404(_('Cookie has been deleted'))
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			try:
				student = CustomUser.objects.get(username=enroll)
				student = student.student
			except (CustomUser.DoesNotExist, Student.DoesNotExist):
				return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
			POST = request.POST.copy()
			POST['college'] = student.college.pk
			POST['programme'] = student.programme.pk
			POST['stream'] = student.stream.pk
			f = VerifyStudentProfileForm(POST, request.FILES, instance=student)
			'''
			verdict = False
			if 'continue' == request.POST.get('true', ''):
				verdict = True
			elif 'leave' == request.POST.get('none', ''):
				verdict = None
			else:
				# Button names/values changed
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			'''
			if f.is_valid():
#				student = f.save(verifier=request.user, verified=verdict)
				student = f.save()
				# LOG
#				if student.is_verified:
				message = "[%s] - %s updated %s profile - Changed fields [%s]"
#				else:
#					message = "[%s] - %s skipped %s profile - Changed fields [%s]"
				if 'is_barred' in f.changed_data:
					verdict = "BARRED" if student.is_barred else "UNBARRED"
					facultyLogger.warning("%s[%d] %s %s[%d]" % (request.user.username, request.user.pk, verdict,student.profile.username, student.profile.pk))
				facultyLogger.info(message % (kwargs.get('profile').college.code, request.user.username, student.profile.username, ','.join(f.changed_data)))
				# # #
#				context = {'profile_form': VerifyStudentProfileForm(instance=student), 'success_msg': 'Student profile has been updated successfully!'}
#				return HttpResponse(render(request, 'faculty/verify_profile_form.html', context).content) # for RequestContext() to set csrf value in form
#			return HttpResponse(render_to_string('faculty/verify_profile_form.html', context))
				return JsonResponse(status=200, data={'message': 'Student profile has been saved.\nProceed to "Tenth Qualifications".'})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'error': 'Please correct the errors as indicated in the form.'})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request)

@require_user_types(['S', 'F'])
@login_required
@require_POST
def edit_qualifications(request, **kwargs):
	if request.is_ajax():
		if request.user.type == 'S':
			try:
				student = request.user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
			try:
				qual = student.qualifications
				f = QualificationForm(request.POST, instance=qual)
			except Qualification.DoesNotExist:
				f = QualificationForm(request.POST)
			if f.is_valid():
				f.save(student=student, verified=False, verifier=student.verified_by)
				# LOG
				studentLogger.info('[%s] - Updated Qualifications - %s' % (student.profile.username, ','.join(f.changed_data)))
				# # #
				toast_msg = "Qualifications have been updated successfully! Contact your college's TPC faculty for verification."
				return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['S']), 'toast_msg': toast_msg})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		
		elif request.user.type == 'F' and request.is_ajax():
			if not request.user.groups.filter(name='Verifier'):
				return JsonResponse(status=403, data={'error': 'Permission Denied. You cannot verify students'})
			enroll = request.session.get('enrollmentno', None)
			if not enroll:
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			try:
				student = CustomUser.objects.get(username=enroll)
				student = student.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
			'''
			verdict = False
			if 'continue' == request.POST.get('true', ''):
				verdict = True
			elif 'leave' == request.POST.get('none', ''):
				verdict = None
			else:
				# Button names/values changed
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			try:
				qual = student.qualifications
				f = QualificationForm(request.POST, instance=qual)
			except Qualification.DoesNotExist:
				qual = None
				f = QualificationForm(request.POST)
			'''
			qual = student.qualifications
			f = QualForm(request.POST, instance=qual)
			if f.is_valid():
#				verifier = request.user
#				verified = verdict
				'''
				if qual:
					qualifications = f.save(verifier=verifier, verified=verified)
				else:
					qualifications = f.save(student=student, verifier=verifier, verified=verified)
				'''
				marksheet_10 = student.marksheet.cgpa_marksheet if student.marksheet.cgpa_marksheet else student.marksheet.marksheet_10
				marksheet_12 = student.marksheet.marksheet_12
				qualifications = f.save(student=student, tenth=marksheet_10.calculate_percentage(), twelfth=marksheet_12.calculate_percentage())
				# LOG
#				if qualifications.is_verified:
				student.is_verified = True
				student.verified_by = request.user
				student.save()
				message = "[%s] - %s VERIFIED %s  - Changed fields [%s]"
#				else:
#					message = "[%s] - %s skipped %s qualifications - Changed fields [%s]"
				facultyLogger.info(message % (kwargs.get('profile').college.code, request.user.username, student.profile.username, ','.join(f.changed_data)))
				# # #
#				context = {'qual_form': f, 'success_msg': 'Student profile has been updated successfully!'}
#				form_html = render(request, 'faculty/verify_qual_form.html', context).content.decode('utf-8')
#				return HttpResponse(form_html)
				return JsonResponse(status=200, data={'message': 'Student has been verified.\nTo verify another student, go to "Get Student".'})
			return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'error': 'Please correct the errors as indicated in the form.'})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		handle_user_type(request, redirect_request=True)

#@user_passes_test(lambda u: u.groups.filter(name='Verifier With Student Deletion Privilege')) cant use this because need to return jsonresponse
@require_user_types(['F'])
@login_required
@require_POST
def delete_student(request, **kwargs):
##	if request.user.type == 'F' and request.is_ajax():
	if request.is_ajax():
		try:
			faculty = request.user.faculty
		except Faculty.DoesNotExist:
			return redirect(settings.PROFILE_CREATION_URL['F'])
		if not request.user.groups.filter(name='Verifier With Student Deletion Privilege'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You don\'t have permission to delete students.'})
		enroll = request.session['enrollmentno']
		if not enroll:
			return JsonResponse(status=403, data={'error': 'Cookie Error. Couldn\'t complete request'})
		try:
			user = CustomUser.objects.get(username=enroll)
		except CustomUser.DoesNotExist:
			return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
		try:
			user.delete()
			# LOG
			facultyLogger.info('[%s] - %s deleted %s - %s' % (faculty.college.code, faculty.profile.username, user.username, request.POST.get('reason', 'No reasons given')))
			# # #
			return redirect('verify')
		except:
			return JsonResponse(status=500, data={'error': 'Error occurred while deleting student'})
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['S'])
@login_required
@require_POST
def paygrade(request, **kwargs):
##	if request.is_ajax() and request.user.type == 'S':
	if request.is_ajax():
		try:
			student = request.user.student
		except:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
		f = PaygradeForm(request.POST, instance=student)
		if f.is_valid():
			f.save()
			if f.changed_data:
				studentLogger.info('[%s] - Paygrade - %d LPA' % (student.profile.username, student.salary_expected))
			return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['S'])})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@login_required
@require_GET
def coder(request):
	try:
		platform = request.GET.get('platform').strip().lower()
		username = request.GET.get('username').strip()
		username = getattr(Student.objects.get(profile__username=username).tech,platform)
		data = {}
		result = getattr(scrape, platform)(username)
		for k,v in result.items():
			newkey = k.strip().lower().replace(' ','')
			if newkey != k:
				result[newkey] = result.pop(k)
		result['username'] = username
		html = render_to_string('student/%s.html'%(platform), result)
		return JsonResponse(status=200, data={'html': html})
	except:
		return JsonResponse(status=400, data={})

@require_user_types(['S'])
@login_required
@require_GET
def companies_in_my_college(request, **kwargs):
	if request.is_ajax():
##		if request.user.type == 'S':
		try:
			student = request.user.student
		except Student.DoesNotExist:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
		if not student.salary_expected:
			html = render(request, 'student/paygrade.html', {'paygrade_form': PaygradeForm()}).content.decode('utf-8')
			return JsonResponse(status=200, data={'form': html})

		if student.is_barred:
			return JsonResponse(status=200, data={'barred': 'Sorry, you have been barred by your college. You cannot view/apply to various job and internship opportunities.'})
		# Recruitment
		associations = Association.objects.filter(college=student.college, approved=True, streams__pk__in=[student.stream.pk]).filter(~Q(session=None)).filter(salary__gte=student.salary_expected).filter(session__application_deadline__gte=datetime.date.today())
		associations = associations.order_by('session__application_deadline')
		placement_sessions_assoc = [a['association'] for a in student.sessions.filter( Q(application_deadline__lt=datetime.date.today()) | Q(ended=True)).values('association')]
		associations = associations.exclude(pk__in=placement_sessions_assoc)
		# Dummy
		dsessions = DummySession.objects.filter(dummy_company__college=student.college, streams__pk__in=[student.stream.pk]).filter(salary__gte=student.salary_expected).filter(application_deadline__gte=datetime.date.today())
		dsessions = dsessions.order_by('application_deadline')
		dsessions = dsessions.exclude(pk__in=[ds.pk for ds in student.dummy_sessions.filter(Q(application_deadline__lt=datetime.date.today()) | Q(ended=True))])
		# Eligibility
		'''
		eligible_criteria = set()
		only_eligible_assoc = list()
		for a in associations:
			criterion = a.session.selection_criteria
			if criterion in eligible_criteria:
				only_eligible_assoc.append(a.pk)
			else:
				if criterion.check_eligibility(student):
					eligible_criteria.add(criterion)
					only_eligible_assoc.append(a.pk)
		associations = associations.filter(pk__in=only_eligible_assoc)
		'''
		# Actual
		jobs = associations.filter(type='J')
		enrolled_jobs = jobs.filter(session__students__pk__in = [student.pk])
		unenrolled_jobs = jobs.exclude(pk__in = enrolled_jobs.values('pk'))
		internships = associations.filter(type='I')
		enrolled_internships = internships.filter(session__students__pk__in = [student.pk])
		unenrolled_internships = internships.exclude(pk__in = enrolled_internships.values('pk'))
		# Dummy
		djobs = dsessions.filter(type='J')
		enrolled_djobs = djobs.filter(students__pk__in = [student.pk])
		unenrolled_djobs = djobs.exclude(pk__in = enrolled_djobs.values('pk'))
		dinternships = dsessions.filter(type='I')
		enrolled_dinternships = dinternships.filter(students__pk__in = [student.pk])
		unenrolled_dinternships = dinternships.exclude(pk__in = enrolled_dinternships.values('pk'))
		# # #
		render_data = {}; context = {}
		context['datecomp'] = datetime.date.today() + datetime.timedelta(1)
		context['htmlid'] = 'jobs'
		data = []
		for j in enrolled_jobs:
			sess = settings.HASHID_PLACEMENTSESSION.encode(j.session.pk)
			data.append({'sessid':sess, 'assoc':j, 'date':j.session.application_deadline + datetime.timedelta(1), 'is_dummy': False})
		for j in enrolled_djobs:
			dsess = settings.HASHID_DUMMY_SESSION.encode(j.pk)
			data.append({'dsessid': dsess, 'dsess': j, 'date': j.application_deadline + datetime.timedelta(1), 'is_dummy': True})
		data = sorted(data, key=lambda x: x['date'])
		context['on'] = data
		data = []
		for j in unenrolled_jobs:
			sess = settings.HASHID_PLACEMENTSESSION.encode(j.session.pk)
			data.append({'sessid':sess, 'assoc':j, 'date':j.session.application_deadline + datetime.timedelta(1), 'is_dummy': False})
		for j in unenrolled_djobs:
			dsess = settings.HASHID_DUMMY_SESSION.encode(j.pk)
			data.append({'dsessid': dsess, 'dsess': j, 'date': j.application_deadline + datetime.timedelta(1), 'is_dummy': True})
		data = sorted(data, key=lambda x: x['date'])
		context['off'] = data
		render_data['jobs'] = render(request, 'student/companies_in_my_college.html', context).content.decode('utf-8')
		context['htmlid'] = 'internships'
		data = []
		for i in enrolled_internships:
			sess = settings.HASHID_PLACEMENTSESSION.encode(i.session.pk)
			data.append({'sessid':sess, 'assoc':i, 'date':i.session.application_deadline + datetime.timedelta(1)})
		for i in enrolled_dinternships:
			dsess = settings.HASHID_DUMMY_SESSION.encode(i.pk)
			data.append({'dsessid': dsess, 'dsess': i, 'date': i.application_deadline + datetime.timedelta(1), 'is_dummy': True})
		data = sorted(data, key=lambda x: x['date'])
		context['on'] = data
		data = []
		for i in unenrolled_internships:
			sess = settings.HASHID_PLACEMENTSESSION.encode(i.session.pk)
			data.append({'sessid':sess, 'assoc':i, 'date':i.session.application_deadline + datetime.timedelta(1)})
		for i in unenrolled_dinternships:
			dsess = settings.HASHID_DUMMY_SESSION.encode(i.pk)
			data.append({'dsessid': dsess, 'dsess': i, 'date': i.application_deadline + datetime.timedelta(1), 'is_dummy': True})
		data = sorted(data, key=lambda x: x['date'])
		context['off'] = data
		render_data['internships'] = render(request, 'student/companies_in_my_college.html', context).content.decode('utf-8')
		return JsonResponse(status=200, data=render_data)
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['S'])
@login_required
@require_GET
def apply_to_company(request, sess, **kwargs): # handling withdrawl as well
	if request.is_ajax():
##		if request.user.type == 'S':
		try:
			student = request.user.student
		except Student.DoesNotExist:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
		try:
			session = PlacementSession.objects.get(pk=settings.HASHID_PLACEMENTSESSION.decode(sess)[0])
		except:
			return JsonResponse(status=400, data={'error': 'Invalid request'})
		if student.is_barred:
			return JsonResponse(status=403, data={'error': 'Sorry, you have been barred by your college from placements.'})
		if student.college != session.association.college or student.stream not in session.association.streams.all() or session.application_deadline < datetime.date.today():
			return JsonResponse(status=403, data={'error': 'You cannot make this request.'})
		association = session.association
		criterion = session.selection_criteria
		eligibility = criterion.check_eligibility(student)
		if eligibility is None:
			return JsonResponse(status=400, data={'error': 'You need to fill the qualifications form before applying.'})
		message = 'Please get your %s verified by the placement cell faculty first.'
		if not student.qualifications.is_verified or not student.qualifications.verified_by: # Qualifications.DoesNotExist has been taken care of by 'eligibility is None' condition
			message = message % 'qualifications'
			return JsonResponse(status=400, data={'error': message})
		elif not student.is_verified or not student.verified_by:
			message = message % 'profile'
			return JsonResponse(status=400, data={'error': message})
		if eligibility == False:
			return JsonResponse(status=400, data={'error': 'Sorry, you are not eligible for this %s.' % ('job' if association.type == 'J' else 'internship')})
		"""
		if (association.type == 'J' and student.is_placed) or (association.type == 'I' and student.is_intern):
			type = dict(association.PLACEMENT_TYPE)[association.type]
#				msg = "Sorry, you cannot apply to more companies for %s as you are already selected for %s at %s" % (type,type,student.sessions.get().association.company.name.title())
			msg = "Sorry, you cannot apply to more companies for %s as you are already selected for %s." % (type,type)
			return JsonResponse(status=400, data={'error': msg})
		"""
		students_sessions = student.sessions.all()
		"""
		sessions_students = session.students.all()
		if student not in sessions_students:
			session.students.add(student)
			return JsonResponse(status=200, data={'enrolled': True})
		else:
			session.students.remove(student)
			return JsonResponse(status=200, data={'enrolled': False})
#				return JsonResponse(status=400, data={'error': 'You have already applied to this company'})
		"""
#			Better! => 1. Complexity 2. m2m changed signal discrepancy handled because implementing below code will cause reverse=True :D
		if session not in students_sessions:
			student.sessions.add(session)
			student.sessions_applied_to.add(session) # stores sessions the student had applied to
			return JsonResponse(status=200, data={'enrolled': True})
		else:
			student.sessions.remove(session)
			# LOG
			studentLogger.info('[%s] - Withdrew from %s session [%s]' % (request.user.username, str(session), session.association.type))
			# # #
			return JsonResponse(status=200, data={'enrolled': False})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request)

# ----+----=----+----=----+----=----+----=----+----=----+---- #
def get_student_public_profile(user, requester_type):
	try:
		student = Student.objects.get(id=user.student.id)
	except Student.DoesNotExist:
		return '<div class="valign-wrapper"><p class="valign">Student hasn\'t created his/her profile. Stay tuned!</p></div>'

	context = {'name': student.get_full_name(), 'college': student.college.name.title(), 'stream': '%s - %s'%(student.programme.name,student.stream.name), 'year': student.current_year, 'type': requester_type, 'student': student}
	try:
		social = user.social
		for field in social._meta.get_fields():
			if not field.__class__.__name__ == 'URLField':
				continue
			field = field.name
			if getattr(social, field):
				context[field] = getattr(social, field)
	except SocialProfile.DoesNotExist:
		pass
	
	try:
		tech = student.tech
		for field in tech._meta.get_fields():
			if not field.__class__.__name__ == 'URLField':
				continue
			field = field.name
			if getattr(tech, field):
				context[field] = getattr(tech, field)
	except TechProfile.DoesNotExist:
		pass
	
	sessions = student.sessions.all()
	associations = [s.association for s in sessions[:3]]
	companies = ', '.join([ass.company.name.title() for ass in associations])
	context['sessions'] = sessions.count()
	if len(sessions) > 3:
		companies = companies + ' and others'
	context['companies'] = companies
	return render_to_string('student/pub_profile.html', context)

@require_user_types(['S'])
@login_required
@require_POST
def tech_profile(request, **kwargs):
	if request.is_ajax():
##		if request.user.type == 'S':
		student = request.user.student
		try:
			f = TechProfileForm(request.POST, student=student, instance=student.tech)
		except:
			f = TechProfileForm(request.POST, student=student)
		if f.is_valid():
			f.save()
#			context = {}
#			context['tech_profile_form'] = f
#			context['success_msg'] = "Your profile has been updated successfully!"
#			return JsonResponse(status=200, data={ 'render': render(request, 'student/tech_profile.html', context).content.decode('utf-8') })
			return JsonResponse(status=200, data={'message': 'Technical Profile settings have been updated.'})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

@require_user_types(['S'])
@login_required
@require_POST
def upload_file(request, **kwargs):
	if request.is_ajax():
##		if request.user.type == 'S':
		try:
			student = request.user.student
		except Student.DoesNotExist:
			return JsonResponse(status=400, data={'location': reverse(settings.PROFILE_CREATION_URL['S'])})
		f = FileUploadForm(request.POST, request.FILES, instance=student)
		photo, resume = student.photo, student.resume
		if f.is_valid():
			f.save()
			# Removing old files
			delete_old_filefield(photo, student.photo)
			delete_old_filefield(resume, student.resume)
#			context = {}
#			context['upload_file_form'] = FileUploadForm(instance=student)
#			context['success_msg'] = "Upload success!"
#			return JsonResponse(status=200, data={'location': reverse(settings.HOME_URL['S'])})
			if f.changed_data:
				message = 'Files have been uploaded successfully.'
				refresh = True
			else:
				message = 'Nothing to upload.'
				refresh = False
			return JsonResponse(status=200, data={'message': message, 'refresh': refresh})
		return JsonResponse(status=400, data={'errors': dict(f.errors.items()), 'message': 'Please correct the errors as indicated in the form.'})
##		else:
##			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request)

""""""
def delete_old_filefield(old, new):
	# old and new are FileField objects
	if old and old != new:
		try:
			os.remove(os.path.join(settings.BASE_DIR, old.url[1:])) #[1:] to avoid //
		except:
			pass






################################
@require_user_types(['S'])
@login_required
@require_http_methods(['GET','POST'])
def qualifications(request, profile, user_type,  **kwargs):
	if not request.is_ajax():
		return render(request, '405.html', {})
	student = profile
	try:
		if student.marksheet or student.qualification:
			if request.is_ajax():
				return JsonResponse(status=400, data={'message':'Your qualifications have already been created. For any discrepancies, contact your college', 'refresh':True})
			else:
				return redirect(settings.HOME_URL['S'])
	except:
		pass
	is_cgpa = bool(request.POST.get('is_cgpa'))
	tenth_scores = []
	twelfth_scores = []
# Tenth
	form10 = None
	if is_cgpa:
		form10 = CGPAMarksheetForm(request.POST, prefix='cgpa')
		if not form10.is_valid():
			return JsonResponse(status=400, data={'errors': form10.get_humanized_errors(), 'type': 'cgpa', 'prefix': form10.prefix})
	else:
		form10 = ScoreMarksheetForm(request.POST, klass='10', prefix='score_10') # Form is used for only examinationboard input
		if not form10.is_valid():
			return JsonResponse(status=400, data={'errors': form10.get_humanized_errors(), 'type': 'board', 'prefix': form10.prefix})
		for i in range(1,7):
			tenth_scores.append(ScoreForm(request.POST, number=i, prefix=('10_%d' % (i))))
# # #
# Twelfth
	form12 = ScoreMarksheetForm(request.POST, klass='12', prefix='score_12')
	if not form12.is_valid():
		return JsonResponse(status=400, data={'errors': form12.get_humanized_errors(), 'type': 'board', 'prefix': form12.prefix})
	for i in range(1,7):
		twelfth_scores.append(ScoreForm(request.POST, number=i, prefix=('12_%d' % (i))))
# # #
	errors = {'twelfth': [], 'tenth': []}
	for score_form in tenth_scores:
		if not score_form.is_valid():
			errors['tenth'].append(score_form.get_humanized_errors())

	for score_form in twelfth_scores:
		if not score_form.is_valid():
			errors['twelfth'].append(score_form.get_humanized_errors())

	if errors['tenth'] or errors['twelfth']:
		return JsonResponse(status=400, data={'errors': errors, 'type': 'score'})

# Graduation
	qual_form = QualForm(request.POST)
	if not qual_form.is_valid():
		return JsonResponse(status=400, data={'errors': qual_form.get_humanized_errors(), 'type': 'qual'})
# # #

# No errors; Start saving
# Save scores
	for i,score_form in enumerate(tenth_scores):
		tenth_scores[i] = score_form.save()
	for i,score_form in enumerate(twelfth_scores):
		twelfth_scores[i] = score_form.save()
# Save marksheets
	marksheet_10 = None
	marksheet_12 = None
	if is_cgpa:
		marksheet_10 = form10.save()
	else:
		marksheet_10 = form10.save(tenth_scores)
	marksheet_12 = form12.save(twelfth_scores)
	school_marksheet = SchoolMarksheet.objects.create(marksheet_12=marksheet_12, cgpa_marksheet=marksheet_10) if is_cgpa else SchoolMarksheet.objects.create(marksheet_12=marksheet_12, marksheet_10=marksheet_10)
	student.marksheet = school_marksheet
	student.save()
	qual = qual_form.save(student=student, tenth=marksheet_10.calculate_percentage(), twelfth=marksheet_12.calculate_percentage())
	studentLogger.info("%s[%d] created qualifications [SM: %d] [Q: %d]" % (student.profile.username, student.profile.pk, school_marksheet.pk, qual.pk))
	return JsonResponse(status=200, data={'message': 'Qualifications have been saved.', 'refresh': True})

@require_user_types(['F'])
@login_required
@require_http_methods(['GET','POST'])
def update_score(request, score_hashid, profile, **kwargs):
	try:
		score = str(settings.HASHID_SCORE.decode(score_hashid)[0])
		klass = score[:2]
		number = int(score[2])
		if klass not in ['10','12'] or number not in range(1,7):
			return JsonResponse(status=400, data={'error': 'Invalid score'})
	except:
		return JsonResponse(status=400, data={'error': 'Invalid score'})
	try:
		student = Student.objects.get(profile__username = request.session['enrollmentno'])
		if student.college != profile.college:
			return JsonResponse(status=403, data={'error': 'Permission Denied. You can verify students of your college only.'})
	except KeyError:
		return JsonResponse(status=400, data={'error': 'Your session has expired. Please refresh the page and continue.'})
	except:
		return JsonResponse(status=400, data={'error': 'Sorry, error occurred while retrieving student. Try again later.'})
	if not student.marksheet:
		return JsonResponse(status=400, data={'error': 'Student hasn\'t added their qualifications.'})
	if request.method == 'GET':
		marksheet = getattr(student.marksheet, 'marksheet_%s'%(klass))
		score = getattr(marksheet, 'score%d'%(number))
		score_form = ScoreForm(number=number, instance=score)
		html = render(request, 'student/score_form.html', {'score_form': score_form}).content.decode('utf-8')
		return JsonResponse(status=200, data={'form':html})
	else:
		marksheet = getattr(student.marksheet, 'marksheet_%s'%(klass))
		board_form = ScoreMarksheetForm(klass=klass, instance=marksheet, prefix=klass)
		score = getattr(marksheet, 'score%d'%(number))
		score_form = ScoreForm(request.POST, number=number, instance=score)
		if score_form.is_valid():
			score_form.save()
			scores = []
			for i in range(1,7):
				score = getattr(marksheet, 'score%d'%(i))
				subject = score.subject.__str__() if score.subject else "%s" % (score.subject_name or '-')
				marks = score.marks
				key = int("%s%d" % (klass,i)) # 126 => 12klass, score6
				hashid = settings.HASHID_SCORE.encode(key)
				scores.append({'subject': subject, 'marks': marks, 'hashid': hashid})
			klass_hashid = settings.HASHID_KLASS.encode(int(klass))
			html = render(request, 'faculty/verify_scores.html',{'board_form': board_form, 'scores': scores, 'hashid': klass_hashid}).content.decode('utf-8')
			facultyLogger.info("SCORE: %s[%d] updated %s of %s[%d]: %s class,sub %d"\
					% (profile.profile.username, profile.profile.pk, ','.join(score_form.changed_data),\
						student.profile.username, student.profile.pk, klass, number))
			return JsonResponse(status=200, data={'message':'Subject %d has been updated.'%number, 'form':html})
		else:
			message = score_form.get_humanized_errors()
			message = '. '.join(message['Subject %d: '%(number)])
			return JsonResponse(status=400, data={'error': message})
#			return JsonResponse(status=400, data={'errors': dict(score_form.errors.items())})
#	q = QualificationForm(request.POST)
#	return JsonResponse(status=200, data={})
