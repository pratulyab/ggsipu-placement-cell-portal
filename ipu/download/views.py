from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET
from account.decorators import require_user_types, require_AJAX
from dummy_company.models import DummySession
from recruitment.models import PlacementSession
from .models import *
from .tasks import handle_resume_dl_task
from datetime import datetime

# Create your views here.

@require_AJAX
@require_GET
@login_required
@require_user_types(['C', 'F', 'CO'])
def download_resume(request, sess_hashid, user_type, profile, **kwargs):
	try:
		session_id = settings.HASHID_PLACEMENTSESSION.decode(sess_hashid)[0]
		session = None
		if user_type == 'CO':
			session = PlacementSession.objects.get(association__company=profile, pk=session_id)
			description = " session at " + session.association.college.name.title()
		elif user_type == 'C':
			session = PlacementSession.objects.get(association__college=profile, pk=session_id)
			description = " session by " + session.association.company.name
		else:
			if not request.user.groups.filter(name='Placement Handler'):
				return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
			session = PlacementSession.objects.get(association__college=profile.college, pk=session_id)
			description = " session by " + session.association.company.name
		description = ("Internship" if session.association.type == 'I' else "Job") + description
		return handle_resume_downloads(request, session.students.all(), description)
	except Exception as e:
		print(e)
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})

@require_AJAX
@require_GET
@login_required
@require_user_types(['C','F'])
def download_resume_dummy(request, dsess_hashid, user_type, profile, **kwargs):
	college = profile
	if user_type == 'F':
		if not request.user.groups.filter(name='Placement Handler'):
			return JsonResponse(status=403, data={'error': 'Permission Denied. You are not authorized to handle college\'s placements.'})
		college = college.college
	try:
		dsession_id = settings.HASHID_DUMMY_SESSION.decode(dsess_hashid)[0]
		dsession = DummySession.objects.get(dummy_company__college=college, pk=dsession_id)
		description = ("Internship" if dsession.type == 'I' else "Job") + " session by " + dsession.dummy_company.name
		return handle_resume_downloads(request, dsession.students.all(), description)
	except:
		return JsonResponse(status=400, data={'error': 'Invalid Request.'})

@require_GET
@login_required
def serve_zipped_file(request, user_hashid, uuid):
	try:
		is_ajax = request.is_ajax()
		user_pk = settings.HASHID_CUSTOM_USER.decode(user_hashid)[0]
		if request.user.pk != user_pk:
			if is_ajax:
				return JsonResponse(status=403, data={'error': 'You did not request this link.'})
			else:
				raise PermissionDenied
		zipped_file = get_object_or_404(ZippedFile, pk=uuid)
		dl_request = zipped_file.download_request
		if not dl_request.requesters.filter(pk=user_pk).exists():
			if is_ajax:
				return JsonResponse(status=403, data={'error': 'You did not request this link.'})
			else:
				raise PermissionDenied
		user_request = dl_request.requests.get(requester=request.user)
		if user_request.downloaded_on and (datetime.utcnow() - user_request.downloaded_on.replace(tzinfo=None)).total_seconds() < 300:# and user_request.downloaded:
			# User has already downloaded it once. Requesting for another creation within 5min only.
			if is_ajax:
				return JsonResponse(status=400, data={'error': 'You have already downloaded the requested resumes. You must wait at least 5 min from your last download. Thanks for cooperating with our limitation.'})
			else:
				raise Http404('You need to wait for atleast 5 minutes since your last download.')
		if not is_ajax:
			user_request.downloaded_on = datetime.now()
			user_request.save()
		if is_ajax:
			return JsonResponse(status=200, data={'message': 'Proceed to download'})
		else:
			response = HttpResponse(zipped_file.zipped_file, content_type="application/x-zip-compressed")
			response['Content-Disposition'] = 'attachment; filename=%s' % (zipped_file.zipped_file.name.split('/')[-1].split('.')[0] + get_random_string(6) + '.zip')
			return response
	except Exception as e:
		print(e)
		raise Http404('Link has expired.')


def handle_resume_downloads(request, students_queryset, description):
	''' Utility function '''
	if not students_queryset.exists():
		return JsonResponse(status=400, data={'error': 'There are no students enrolled in the session.'})
	link = "%s://%s" % (('https' if settings.USE_HTTPS else 'http'), get_current_site(request).domain)
	user_requests = Requester.objects.filter(requester=request.user).order_by('-requested_on')
	if user_requests.exists() and user_requests.first().requested_on and (datetime.utcnow() - user_requests.first().requested_on.replace(tzinfo=None)).total_seconds() < 300:
		# Limiting the request issuing because of server limitations
		return JsonResponse(status=400, data={'error': 'You are required to wait at least 10min before issuing a new download request.\
														Thanks for cooperating with us.'})
	dl_request = None
	for ur in DLRequest.objects.all():
		if not ur.is_different(students_queryset):
			# Checking if already a dl_request exists, which has the same set of students' zipped resumes. i.e. no difference
			dl_request = ur
			break
	if dl_request is not None:
		# A pre-existing dl request has been found.
		user_request, created = Requester.objects.get_or_create(requester=request.user, requested=dl_request)
		if not created:
			# This user has requested this again.
			if user_request.downloaded_on and (datetime.utcnow() - user_request.downloaded_on.replace(tzinfo=None)).total_seconds() < 1200 and user_request.downloaded:
				# User has already downloaded it once. Requesting for another creation within 20min only.
				return JsonResponse(status=400, data={'error': 'You have already downloaded the requested data. You must wait at least 20 min from your last download.'})
			else:
				# Update requested_on
				user_request.requested_on = datetime.now()
				user_request.save()
		handle_resume_dl_task.delay(dl_request.students, request.user.pk, dl_request.pk, link, description)
	else:
		# A new DLRequest has to be created.
		student = students_queryset.first() # Because a session contains homogeneous students (same batch)
		batch,created = Batch.objects.get_or_create(college=student.college, stream=student.stream, year=student.get_year())
		students = ','.join(s['profile__username'] for s in students_queryset.values('profile__username').order_by('profile__username'))
		dlr = DLRequest.objects.create(batch=batch, students=students)
		# Create new Requester. This user is asking for this, for the first time.
		Requester.objects.create(requester=request.user, requested=dlr)
		handle_resume_dl_task.delay(students, request.user.pk, dlr.pk, link, description)
	return JsonResponse(status=200, data={'message': 'Compressed files successfully'})
