from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

from account.models import CustomUser
from college.forms import CollegeCreationForm
from college.models import College, Stream
from company.forms import CompanyCreationForm
from company.models import Company
from faculty.forms import FacultyProfileForm
from faculty.models import Faculty
from student.forms import StudentCreationForm
from student.models import Student

import re

#@require_http_methods(['GET','POST'])
#@login_required
def render_profile_creation(request, user_type):
	if user_type == 'C':
		return render(request, 'college/create.html', {'college_creation_form': CollegeCreationForm()})
	elif user_type == 'F':
		return render(request, 'faculty/edit_create.html', {'faculty_edit_create_form': FacultyProfileForm(instance=request.user.faculty)})
	elif user_type == 'S':
		user_profile = request.user
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', user_profile.username).groups()
		except AttributeError:
#			pass
			raise Http404(_('Enrollment number should contain only digits'))
		except ValueError:
#			pass
			raise Http404(_('Enrollment number should be 11 digits long'))
		coll = College.objects.get(code=coll).pk
		strm = Stream.objects.get(code=strm).pk
		return render(request, 'student/create.html', {'student_creation_form': StudentCreationForm(profile=user_profile, coll=coll, strm=strm)})
	else:
		return render(request, 'company/create.html', {'company_creation_form': CompanyCreationForm()})

#@require_http_methods(['GET','POST'])
#@login_required
def redirect_profile_creation(request, user_type):
	return redirect(settings.PROFILE_CREATION_URL[user_type])

#@require_http_methods(['GET','POST'])
#@login_required
def handle_user_type(request, redirect_request=False):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if data:
#		if request.method == 'GET':
#			print(request.GET.get('next'))
#		Yet to be implemented
		return redirect(settings.HOME_URL[user_type])
	else:
		if redirect_request:
			return redirect_profile_creation(request, user_type)
		else:
			return render_profile_creation(request, user_type)

#@require_http_methods(['GET','POST'])
#@login_required
def get_relevant_reversed_url(request):
	data = get_type_created(request.user)
	user_type = data.pop('user_type')
	if data:
		return reverse(settings.HOME_URL[user_type])
	else:
		return reverse(settings.PROFILE_CREATION_URL[user_type])

def get_type_created(user):
	user_type = user.type
	if user_type == 'C':
		try:
			college = user.college
			return ({'profile': college, 'user_type': user_type})
		except College.DoesNotExist:
			return ({'user_type': user_type})
	elif user_type == 'F':
		try:
			faculty = user.faculty
			if not faculty.firstname:
				return ({'user_type': user_type})
			return ({'profile': faculty, 'user_type': user_type})
		except Faculty.DoesNotExist:
			return ({'user_type': user_type})
	elif user_type == 'S':
		try:
			student = user.student
			return ({'profile': student, 'user_type': user_type})
		except Student.DoesNotExist:
			return ({'user_type': user_type})
	else:
		try:
			company = user.company
			return ({'profile': company, 'user_type': user_type})
		except Company.DoesNotExist:
			return ({'user_type': user_type})
