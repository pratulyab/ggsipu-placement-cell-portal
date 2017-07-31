''' Common useful utilities '''

from django.utils.crypto import get_random_string
from django.conf import settings
import re

# CAUTION: If you plan to change the file storage directory structure (MEDIA_ROOT/actor/fieldname), then modify this function accordingly.
# # # # # # # DONT REMOVE THIS FUNCTION... MIGRATIONS CAUSE ERROR
def get_hashed_filename(instance, filename):
	''' Check filename validity and appends a random hash to the filename '''
	# Then file can be either photo or resume
	filename = instance.photo.storage.get_valid_name(filename) # Get valid filename as per the underlying OS's filename rules
	filename = filename.split('.')
	(filename, ext) = ('.'.join(filename[:-1]), '.'+filename[-1]) if len(filename) > 1 else (filename[0], '')
	field_name = str(instance.photo.field).split('.') # student.Student.resume
	filename = "{}/{}/{}_{}{}".format(field_name[0], field_name[-1], filename, get_random_string(7), ext) # student/resume
	return filename	


def get_hashed_photo_name(instance, filename):
	''' Check filename validity and appends a random hash to the filename '''
	# Then file can be either photo or resume
	filename = instance.photo.storage.get_valid_name(filename) # Get valid filename as per the underlying OS's filename rules
	filename = filename.split('.')
	(filename, ext) = ('.'.join(filename[:-1]), '.'+filename[-1]) if len(filename) > 1 else (filename[0], '')
	field_name = str(instance.photo.field).split('.') # student.Student.resume
	filename = "{}/{}/{}_{}{}".format(field_name[0], field_name[-1], filename, get_random_string(7), ext) # student/resume
	return filename	

def get_hashed_resume_name(instance, filename):
	''' Check filename validity and appends a random hash to the filename '''
	filename = instance.resume.storage.get_valid_name(filename) # Get valid filename as per the underlying OS's filename rules
	filename = filename.split('.')
	(filename, ext) = ('.'.join(filename[:-1]), '.'+filename[-1]) if len(filename) > 1 else (filename[0], '')
	field_name = str(instance.resume.field).split('.') # student.Student.resume
	filename = "{}/{}/{}_{}{}".format(field_name[0], field_name[-1], filename, get_random_string(7), ext) # student/resume
	return filename	


def validate_username_for_urls(username):
	''' allows username that don't clash with ipu.urls
		
		Validates against only the topmost url name i.e. domain.com/top-most/..
		
		Assumption => username has already been cleaned for not allowing slashes
		Invalidates 'admin' as username, but validates 'adminblah' (given there is no url as ^adminblah/$ or ^adminblah/)

		But doesn't check for the validity of username like admin/foobar (nested urls)
		because usernames don't include slashes (assumption)

		Otherwise, all set.

		Make sure to add all the wildcard regex patterns in WILDCARD_REGEX_URL_NAMES.
	'''
	WILDCARD_REGEX_URL_NAMES = ['']
	COMMONLY_DISALLOWED_NAMES = ['admin']
	
	from ipu.urls import urlpatterns # ImportError -.-'
	for each in urlpatterns:
		if getattr(each, 'name', False) and each.name in WILDCARD_REGEX_URL_NAMES:
			continue
		if username in COMMONLY_DISALLOWED_NAMES:
			return False
		try:
			pattern = each.regex.pattern
			patterns = pattern.split('/')
			pattern = patterns[0]
		except:
			continue
		if not pattern.endswith('$'):
			pattern += '$'
		if re.compile(pattern).match(username):
			return False
	return True
