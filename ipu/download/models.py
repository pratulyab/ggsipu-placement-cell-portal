from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.db.utils import IntegrityError
from django.dispatch import receiver
from account.models import CustomUser
from college.models import College, Stream
from student.models import Student
import re, uuid

# Create your models here.

class Batch(models.Model):
	YEAR_CHOICES = tuple(((str(y),str(y)) for y in range(2008, 2020)))
	college = models.ForeignKey(College, related_name="batches")
	stream = models.ForeignKey(Stream, related_name="batches")
	year = models.CharField(max_length=4, choices=YEAR_CHOICES)

	def __str__(self):
		return "%s%s%s" % (self.college.code, self.stream.code, self.year[2:])

	class Meta:
		verbose_name_plural = "Batches"
		unique_together = ['college', 'stream', 'year']


class DLRequest(models.Model):
	''' Download Request '''
	requesters = models.ManyToManyField(CustomUser, through='Requester', related_name="download_requests", blank=True)
	batch = models.ForeignKey(Batch, related_name="download_requests")
	students = models.TextField(validators=[validate_comma_separated_integer_list]) # Stores student enrollment numbers

	def get_students(self):
		students = self.students.split(',')
		return Student.objects.filter(profile__username__in=students)

	def is_different(self, student_queryset):
		''' Boolean to check if there is difference between currently Zipped and a student_queryset '''
		students = set(self.students.split(','))
		student_queryset = [s['profile__username'] for s in student_queryset.values('profile__username')]
		return bool(students.difference(set(student_queryset)))

	def clean(self, *args, **kwargs):
		super(DLRequest, self).clean(*args, **kwargs)
		batch = self.batch.__str__()
		batch = batch[:-2] # Because session can contain students of only same prog and coll. No restriction on year.
		pattern = r'^(\d{3}%s\d{2}(,\d{3}%s\d{2})*)$' % (batch,batch)
		if not re.match(pattern, self.students):
			raise ValidationError('The students of a session must belong to the same college and programme.')

	def save(self, *args, **kwargs):
		self.full_clean()
		return super(DLRequest, self).save(*args, **kwargs)


class Requester(models.Model):
	requester = models.ForeignKey(CustomUser, related_name="requests")
	requested = models.ForeignKey(DLRequest, related_name="requests")
	requested_on = models.DateTimeField(null=True)
	downloaded = models.BooleanField(default=False)
	downloaded_on = models.DateTimeField(null=True)


class ZippedFile(models.Model):
	uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	download_request = models.OneToOneField(DLRequest, related_name="zipped_file")
	zipped_file = models.FileField(upload_to='compressed/', blank=True)


@receiver(pre_save, sender=Requester)
def validate_requester(sender, **kwargs):
	requester = kwargs.get('instance')
	user = requester.requester
	if user.type not in ['C', 'CO', 'F']:
		raise IntegrityError('This user type is not allowed to create download requestes')
	batch = requester.requested.batch
	if user.type == 'CO':
		if not user.associations.filter(college=batch.college, approved=True).exists():
			raise IntegrityError('The company requesting doesn\'t have any session with requested college')

@receiver(post_delete, sender=ZippedFile)
def delete_zip(sender, **kwargs):
	zipped_file = kwargs['instance']
	try:
		print(zipped_file.zipped_file.path)
		zipped_file.zipped_file.delete(False)
	except Exception as e:
		print('---', e, '---')
		pass
