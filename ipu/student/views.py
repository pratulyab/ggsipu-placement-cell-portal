from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from account.models import CustomUser, SocialProfile
from account.forms import AccountForm, SocialProfileForm
from account.views import handle_user_type, send_activation_email, get_relevant_reversed_url, get_creation_url, get_home_url
from college.models import College, Stream
from student.forms import StudentLoginForm, StudentSignupForm, StudentCreationForm, StudentEditForm, QualificationForm, TechProfileForm, FileUploadForm, PaygradeForm
from student.models import Student, TechProfile, Qualification
from . import scrape

import os, re
from bs4 import BeautifulSoup

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

@require_POST
def student_signup(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	f = StudentSignupForm(request.POST)
	if f.is_valid():
		user = f.save()
		user = authenticate(username=f.cleaned_data['username'], password=f.cleaned_data['password2'])
#		auth_login(request, user)
		send_activation_email(user, get_current_site(request).domain)
		context = {'email': user.email, 'profile_creation': request.build_absolute_uri(reverse('create_student'))}
		html = render(request, 'account/post_signup.html', context).content.decode('utf-8')
		return JsonResponse(data = {'success': True, 'render': html})
	else:
		return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_http_methods(['GET','POST'])
@login_required
def create_student(request):
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
				return redirect('student_home')
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
				return redirect('student_home')
		return render(request, 'student/create.html', {'student_creation_form': f})
	else:
		return handle_user_type(request, redirect_request=True)

@require_GET
@login_required
def student_home(request):
	if request.user.type == 'S':
		"""
		import openpyxl as excel
		workbook = excel.Workbook()
		worksheet = workbook.active
		worksheet['A1']='hello';worksheet['A2']='world!'
		response = HttpResponse(content=excel.writer.excel.save_virtual_workbook(workbook), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		response['Content-Disposition'] = 'attachment; filename=myexport.xlsx'
		return response
		"""
		context = {}
		user = request.user
		context['user'] = user
		try:
			student = request.user.student
		except Student.DoesNotExist:
			return redirect('create_student')
		context['student'] = student
		if student.is_verified == False and student.verified_by == None:
			try:
				student.qualifications
			except Qualification.DoesNotExist:
				context['qual_form'] = QualificationForm()
			return render(request, 'student/unverified.html', context)
		context['edit_account_form'] = AccountForm(instance=user)
		context['upload_file_form'] = FileUploadForm(instance=student)
		if student.is_verified is None:
			context['edit_profile_form'] = StudentEditForm(instance=student)
		try:
			qual = student.qualifications
			if qual.is_verified is None:
				context['edit_qual_form'] = QualificationForm(instance=qual)
		except Qualification.DoesNotExist:
			context['edit_qual_form'] = QualificationForm()
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
		return render(request, 'student/home.html', context)
	else:
		return handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def edit_student(request):
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
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('S'))})
			POST = request.POST.copy()
			POST['college'] = student.college.pk
			POST['programme'] = student.programme.pk
			POST['stream'] = student.stream.pk
			f = StudentEditForm(POST, request.FILES, instance=student)
			if f.is_valid():
				f.save(verified=False, verifier=student.verified_by)
#			context = {}
#			context['message'] = "Your profile has been updated. Please contact your college's TPC faculty for verification."
#			return JsonResponse(status=200, data={'render': render(request, 'student/home.html', context).content.decode('utf-8')})
				toast_msg = "Your profile has been updated successfully! Contact your college's TPC faculty for verification."
				return JsonResponse(status=200, data={'location': reverse(get_home_url('S')), 'toast_msg': toast_msg})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
			
		elif request.user.type == 'F' and request.is_ajax():
			enroll = request.session['enrollmentno']
			if not enroll:
#				Http404(_('Cookie has been deleted'))
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			try:
				student = CustomUser.objects.get(username=enroll)
				student = student.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
			POST = request.POST.copy()
			POST['college'] = student.college.pk
			POST['programme'] = student.programme.pk
			POST['stream'] = student.stream.pk
			f = StudentEditForm(POST, request.FILES, instance=student)
			verdict = False
			if 'continue' == request.POST.get('true', ''):
				verdict = True
			elif 'leave' == request.POST.get('none', ''):
				verdict = None
			else:
				# Button names/values changed
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			photo, resume = student.photo, student.resume
			if f.is_valid():
				student = f.save(verifier=request.user, verified=verdict)
				# Removing old files
				delete_old_filefield(photo, student.photo)
				delete_old_filefield(resume, student.resume)
				context = {'profile_form': StudentEditForm(instance=student), 'success_msg': 'Student profile has been updated successfully!'}
				return HttpResponse(render(request, 'faculty/verify_profile_form.html', context).content) # for RequestContext() to set csrf value in form
#			return HttpResponse(render_to_string('faculty/verify_profile_form.html', context))
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request)

@require_POST
@login_required
def edit_qualifications(request):
	if request.is_ajax():
		if request.user.type == 'S':
			try:
				student = request.user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('S'))})
			try:
				qual = student.qualifications
				f = QualificationForm(request.POST, instance=qual)
			except Qualification.DoesNotExist:
				f = QualificationForm(request.POST)
			if f.is_valid():
				f.save(student=student, verified=False, verifier=student.verified_by)
				toast_msg = "Qualifications have been updated successfully! Contact your college's TPC faculty for verification."
				return JsonResponse(status=200, data={'location': reverse(get_home_url('S')), 'toast_msg': toast_msg})
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		
		elif request.user.type == 'F' and request.is_ajax():
			enroll = request.session['enrollmentno']
			if not enroll:
#				Http404(_('Cookie has been deleted'))
				return JsonResponse(status=400, data={'error': 'Unexpected changes have been made. Refresh page and continue.'})
			try:
				student = CustomUser.objects.get(username=enroll)
				student = student.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
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
			if f.is_valid():
				verifier = request.user
				verified = verdict
				if qual:
					student = f.save(verifier=verifier, verified=verified)
				else:
					student = f.save(student=student, verifier=verifier, verified=verified)
				context = {'qual_form': f, 'success_msg': 'Student profile has been updated successfully!'}
				form_html = render(request, 'faculty/verify_qual_form.html', context).content.decode('utf-8')
				return HttpResponse(form_html)
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def delete_student(request):
	if request.user.type == 'F' and request.is_ajax():
		try:
			faculty = request.user.faculty
		except Faculty.DoesNotExist:
			return redirect('edit_create_faculty')
		enroll = request.session['enrollmentno']
		if not enroll:
			return JsonResponse(status=403, data={'error': 'Cookie Error. Couldn\'t complete request'})
		try:
			user = CustomUser.objects.get(username=enroll)
		except CustomUser.DoesNotExist:
			return JsonResponse(status=400, data={'error': 'Student with this enrollment number does not exist'})
		try:
			user.delete()
			return redirect('verify')
		except:
			return JsonResponse(status=500, data={'error': 'Error occurred while deleting student'})
	else:
		return handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def paygrade(request):
	if request.is_ajax() and request.user.type == 'S':
		try:
			student = request.user.student
		except:
			return JsonResponse(status=400, data={'location': reverse('create_student')})
		f = PaygradeForm(request.POST, instance=student)
		if f.is_valid():
			f.save()
			return JsonResponse(status=200, data={'location': reverse('student_home')})
		else:
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})

@require_GET
@login_required
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

@require_POST
@login_required
def tech_profile(request):
	if request.is_ajax():
		if request.user.type == 'S':
			student = request.user.student
			try:
				f = TechProfileForm(request.POST, student=student, instance=student.tech)
			except:
				f = TechProfileForm(request.POST, student=student)
			if f.is_valid():
				f.save()
				context = {}
				context['tech_profile_form'] = f
				context['success_msg'] = "Your profile has been updated successfully!"
				return JsonResponse(status=200, data={ 'render': render(request, 'student/tech_profile.html', context).content.decode('utf-8') })
			else:
				return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
	else:
		return handle_user_type(request, redirect_request=True)

@require_POST
@login_required
def upload_file(request):
	if request.is_ajax():
		if request.user.type == 'S':
			try:
				student = request.user.student
			except Student.DoesNotExist:
				return JsonResponse(status=400, data={'location': reverse(get_creation_url('S'))})
			f = FileUploadForm(request.POST, request.FILES, instance=student)
			photo, resume = student.photo, student.resume
			if f.is_valid():
				f.save()
				# Removing old files
				delete_old_filefield(photo, student.photo)
				delete_old_filefield(resume, student.resume)
				context = {}
				context['upload_file_form'] = FileUploadForm(instance=student)
				context['success_msg'] = "Upload success!"
				return JsonResponse(status=200, data={'location': reverse(get_home_url('S'))})
			return JsonResponse(status=400, data={'errors': dict(f.errors.items())})
		else:
			return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
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
