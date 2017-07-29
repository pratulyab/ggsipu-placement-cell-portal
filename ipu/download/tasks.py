from account.models import CustomUser
from account.tasks import send_mass_mail_task
from celery.decorators import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from download.models import DLRequest, ZippedFile
from notification.models import Notification, NotificationData
from student.models import Student
from hashids import Hashids

import os, time, zipfile

logger = get_task_logger(__name__)

'''
Not using custom folder because Django raises SuspiciousFileOperation because the path doesn't start with MEDIA_ROOT.
Therefore, reverting to saving the compressed files to a folder in MEDIA_ROOT.
ZIP_FOLDER = '/Users/Pratulya/Desktop/compressed'
try:
	if not os.path.exists(ZIP_FOLDER):
		os.makedirs(ZIP_FOLDER, exist_ok=True)
except PermissionError:
	ZIP_FOLDER = os.path.join(settings.MEDIA_ROOT, 'compressed')
	if not os.path.exists(ZIP_FOLDER):
		os.mkdir(ZIP_FOLDER)
'''
ZIP_FOLDER = os.path.join(settings.MEDIA_ROOT, 'compressed')

@task(name='handle_resume_dl_task')
def handle_resume_dl_task(students, requester_pk, dl_request_pk, link, description):
	''' Zip resumes and notify requester '''
	students_q = students.replace(' ', '').split(',')
	students_q = Student.objects.filter(profile__username__in=students_q)
	try:
		requester = CustomUser.objects.get(pk=requester_pk)
		dl_request = DLRequest.objects.get(pk=dl_request_pk)
		user_hashid = settings.HASHID_CUSTOM_USER.encode(requester.pk)
		'''
		if getattr(getattr(getattr(dl_request, 'zipped_file', None), 'zipped_file', None),'name', ''):
			zipped_file_obj = dl_request.zipped_file
		else:
		# FIXME: Not caching the result because of complex discrepancies. As of now, zipping on every request.
		'''
		zip_file_name = Hashids(salt="AbhiKaSamay", min_length=11).encode(round(time.time()))+ '_' + get_random_string() + '.zip'
		zip_path = os.path.join(ZIP_FOLDER, zip_file_name)
		zfile = zipfile.ZipFile(zip_path, 'w')
		no_resumes_for = []
		# Compressing each student's resume, if uploaded
		for student in students_q:
			if student.resume:
				zfile.write(student.resume.path, student.profile.username + '.' + student.resume.name.split('.')[-1])#, compress_type=zipfile.ZIP_DEFLATED)
			else:
				no_resumes_for.append(student.profile.username)
		if any(no_resumes_for):
				zfile.writestr('missing_resumes_list.txt', '\n'.join(no_resumes_for).encode('utf-8'))
		zfile.close()
		# Creating Django File instance
	
		zfile = open(zip_path, 'rb')
		zipped_file_obj,created = ZippedFile.objects.get_or_create(download_request=dl_request)
		zipped_file_obj.zipped_file = File(zfile, name=zip_file_name)
		zipped_file_obj.save()
		zfile.close()
		os.remove(zip_path) # Removing the zip file because save z_f_obj copies the zip file to a new one <name_randomstr>
		
		link = link + reverse('serve', kwargs={'user_hashid': user_hashid, 'uuid': zipped_file_obj.uuid})
		# Notifying
		
#		notification_data = NotificationData.objects.create(subject=description, message='Your requested resumes for this session are ready to be downloaded <a class="resume-dl" href="%s"><b>here.</b></a>' % (link))
		Notification.objects.create(actor=requester, target=requester, message='Your requested resumes for <b>%s</b> are ready to be downloaded <a class="resume-dl" href="%s"><b>here.</b></a>' % (description, link))
#		message = render_to_string('download/send_link_email.txt', {'link': link, 'user': requester, 'description': description})
#		send_mass_mail_task.delay('Download Students\' Resumes', message, [requester_pk]) # Using mass mail because it's generic
		logger.info('Notified - ZIP[%s] - User[%d]' % (str(zipped_file_obj.uuid), requester_pk))

	except CustomUser.DoesNotExist:
		logger.error('The requester[%d] for resumes for %s doesn\'t exist.' % (requester_pk, dl_request.students))
	except DLRequest.DoesNotExist:
		logger.error('DLRequest[%d] doesn\'t exist - Requested by [%d]' % (dl_request_pk, requester_pk))
	except Exception as e:
		logger.critical('Requester [%d] - Resumes %s - \n%s' % (requester_pk, dl_request.students, e))
