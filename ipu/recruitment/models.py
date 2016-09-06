from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.utils import IntegrityError
from college.models import College, Programme, Stream
from company.models import Company
from notification.models import Notification
from student.models import Student
from django.utils.translation import ugettext_lazy as _

from decimal import Decimal

# Create your models here.

SOURCE = (
		('C', ('College')),
		('CO', ('Company')),
	)

class Association(models.Model):
	PLACEMENT_TYPE = (
			('I', _('Internship')),
			('J', _('Job')),
		)
	company = models.ForeignKey(Company, related_name="associations")
	college = models.ForeignKey(College, related_name="associations")
	programme = models.ForeignKey(Programme, related_name="associations")
	streams = models.ManyToManyField(Stream, help_text='Choose particular stream(s).', related_name="associations")
	type = models.CharField(_('Type'), max_length=1, choices=PLACEMENT_TYPE, default=PLACEMENT_TYPE[1][0])
	salary = models.DecimalField(_('Salary (Lakhs P.A.)'), max_digits=4, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], 
		help_text=_("Salary to be offered in LPA."),
	)
	desc = models.TextField(_('Placement details you\'d want to mention'),
			blank=True
	)
	initiator = models.CharField(_('Who initiated it'), max_length=2, choices=SOURCE, default=SOURCE[0][0])
	approved = models.NullBooleanField(default=None)

	def __str__(self):
		return self.company.name + " for placement in " + self.college.name


class PlacementSession(models.Model):
	association = models.OneToOneField(Association, related_name="session")

	students = models.ManyToManyField(Student, related_name="sessions", blank=True)
	status = models.CharField(_('Current status'), 
			help_text="Mention this placement session's current status for shortlisted students' knowledge. Eg. Resume Submission, Final Round, HR Round, Personal Interview Round", 
			blank=True, max_length=256
	)
	
	application_deadline = models.DateField(_('Application Deadline (Due By Midnight)'), 
			null=True, blank=False, 
			help_text=_("Choose last date before which students can apply. If no event is scheduled for now, choose an arbitrary future date.")
	)
	ended = models.BooleanField(
			_('Has the placement session ended'), 
			help_text=_('Setting it to true would mean that the students currently in the session are selected.'), 
			default=False
	)
	last_modified_by = models.CharField(max_length=2, choices=SOURCE, default=SOURCE[0][0])

	def __str__(self):
		return self.association.company.__str__() + ' placement session in ' + self.association.college.__str__()


class Dissociation(models.Model):
	company = models.ForeignKey(Company, related_name="dissociations")
	college = models.ForeignKey(College, related_name="dissociations")
	duration = models.DateField(null=True, blank=True,
			help_text = "Choose the date till when you want to block this user from contacting you."
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

@receiver(m2m_changed, sender=PlacementSession.students.through)
def notify_college_student_list_changed(sender, **kwargs):
	session = kwargs.get('instance', None)
	action = kwargs.get('action', None)
	students = kwargs.get('pk_set', None)
	reverse = kwargs.get('reverse', True) # don't want the parties to be notified  when reverse = True i.e. Reverse relation, when student is applying or withdrawing; Otherwise, Forward relation
	if action in ['post_add', 'post_remove'] and not reverse:
		association = session.association
		message = ''
		if association.type == 'J':
			message = 'Job'
		else:
			message = 'Internship'
		message = message + ' Session: %s - {%s}\t' % (association.programme.__str__(), ', '.join([s.name.title() for s in association.streams.all()]) )
		usernames = '\n'.join([Student.objects.get(pk=s).profile.username for s in students])
		if action == 'post_add':
			message = '%d student%s added to the session\n%s' % (len(students), '' if len(students)==1 else 's', usernames)
		else:
			message = '%d student%s removed from the session\n%s' % (len(students), '' if len(students)==1 else 's', usernames)
		actor = association.college if session.last_modified_by == 'C' else association.company
		target = association.company if session.last_modified_by == 'C' else association.college
		# Creating notification
		Notification.objects.create(actor=actor.profile, target=target.profile, message=message)

@receiver(post_save, sender=PlacementSession)
def request_accepted_notification(sender, **kwargs):
	if not kwargs.get('created'):
		return
	session = kwargs.get('instance')
	association = session.association
	college = association.college
	company = association.company
	initiator = association.initiator
	actor = company if initiator == 'C' else college
	target = college if initiator == 'C' else company
	type = "Job" if association.type == 'J' else "Internship"
	streams = '%s - {%s}\t' % (association.programme.__str__(), ', '.join([s.__str__() for s in association.streams.all()]) )
	message = ''
	if initiator == 'C':
		message = "%s accepted your association request for %s session.\n%s" % (company.name.title(), type, streams)
	else:
		message = "%s accepted your association request for %s session.\n%s" % (college.name.title(), type, streams)
	Notification.objects.create(actor=actor.profile, target=target.profile, message=message)
