from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.db.utils import IntegrityError
from college.models import College, Programme, Stream
from company.models import Company
from student.models import Student
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class Association(models.Model):
	SOURCE = (
			('C', _('College')),
			('CO', _('Company')),
		)
	company = models.ForeignKey(Company, related_name="associations")
	college = models.ForeignKey(College, related_name="associations")
	programme = models.ForeignKey(Programme, related_name="associations")
	streams = models.ManyToManyField(Stream, help_text='Choose particular subject(s).', related_name="associations")
	desc = models.TextField(_('Placement details'), 
			help_text='You can add job details, some specific skills you are looking for. Eg. iOS Developer', 
			blank=True
	)
	initiator = models.CharField(_('Who initiated it'), max_length=2, choices=SOURCE, default=SOURCE[0][0])

	def __str__(self):
		return self.company.name + " for placement in " + self.college.name


class PlacementSession(models.Model):
	association = models.OneToOneField(Association, related_name="session")

	students = models.ManyToManyField(Student, related_name="sessions", blank=True)
	status = models.CharField(_('Current status'), 
			help_text="Mention this placement session's current status for shortlisted students' knowledge. Eg. Resume Submission, Final Round, HR Round, Personal Interview Round", 
			blank=True, max_length=256
	)
	
	recent_deadline = models.DateField(_('Deadline'), 
			null=True, blank=False, 
			help_text="Choose the deadline date for an event. Eg. Last date for applying"
	)
	ended = models.BooleanField(
			_('Has the placement session has ended'), 
			help_text='This would mean that the student currently in the session are selected.', 
			default=False
	)

	def __str__(self):
		return self.association.company.__str__() + ' placement session in ' + self.association.college.__str__()


class Dissociation(models.Model):
	SOURCE = (
			('C', 'College'),
			('CO', 'Company'),
		)
	company = models.ForeignKey(Company, related_name="disassociations")
	college = models.ForeignKey(College, related_name="disassociations")
	duration = models.DateField(null=True, blank=True,
			help_text = "Choose the date till when you want to block the associations with this user."
	)
	initiator = models.CharField(_('Who caused it'), choices=SOURCE, max_length=2, default=SOURCE[0][0])

	def __str__(self):
		""" Returns the name of initiator first, then the other """
		if self.initiator == SOURCE[0][0]:
			return self.college.__str__() + ", " + self.company.__str__()
		else:
			return self.company.__str__() + ", " + self.college.__str__()
	
	class Meta:
		unique_together = ['company', 'college']


@receiver(m2m_changed, sender=Association.streams.through)
def verify_assoc_stream_uniqueness(sender, **kwargs):
	association = kwargs.get('instance', None)
	action = kwargs.get('action', None)
	streams = kwargs.get('pk_set', None)

	if action == 'pre_add':
		for stream in streams:
			if Association.objects.filter(company=association.company, college=association.college).filter(streams=stream):
				raise IntegrityError(_('Association between (%s, %s) already exists for stream %s' % (association.college, association.company, stream,)))

