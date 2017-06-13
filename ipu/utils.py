''' Common useful utilities '''

from django.utils.crypto import get_random_string
from django.conf import settings

# CAUTION: If you plan to change the file storage directory structure (MEDIA_ROOT/actor/fieldname), then modify this function accordingly.
def get_hashed_filename(instance, filename):
	''' Check filename validity and appends a random hash to the filename '''
	# Then file can be either photo or resume
	filename = instance.photo.storage.get_valid_name(filename) # Get valid filename as per the underlying OS's filename rules
	filename = filename.split('.')
	(filename, ext) = ('.'.join(filename[:-1]), '.'+filename[-1]) if len(filename) > 1 else (filename[0], '')
	field_name = str(instance.photo.field).split('.') # student.Student.resume
	filename = "{}/{}/{}_{}{}".format(field_name[0], field_name[-1], filename, get_random_string(7), ext) # student/resume
	return filename	
