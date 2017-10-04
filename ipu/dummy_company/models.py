from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.utils import IntegrityError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from account.tasks import send_mass_mail_task
from college.models import College, Programme, Stream
from company.models import Company
from recruitment.models import SelectionCriteria
from student.models import Student
from decimal import Decimal
import datetime

# Create your models here.

class DummyCompany(models.Model):
	name = models.CharField(_('Company name'), blank=False, max_length=255)
	details = models.TextField(_('Details'), blank=True)
	website = models.URLField(_('Company website'), blank=True)
	college = models.ForeignKey(College, related_name="dummy_companies") # Created By/For
	
	def __str__(self):
		return '[Dummy] ' + self.name

	class Meta:
		unique_together = ['name', 'college']
		verbose_name_plural = _("Dummy Companies")

class DummySession(models.Model):
	PLACEMENT_TYPE = (
			('I', _('Internship')),
			('J', _('Job')),
		)
	dummy_company = models.ForeignKey(DummyCompany, related_name="dummy_sessions")
	programme = models.ForeignKey(Programme, related_name="dummy_sessions")
	streams = models.ManyToManyField(Stream, help_text='Choose particular stream(s).', related_name="dummy_sessions")
	type = models.CharField(_('Type'), max_length=1, choices=PLACEMENT_TYPE, default=PLACEMENT_TYPE[1][0])
	salary = models.DecimalField(_('Salary (Lakhs P.A.)'), max_digits=4, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], help_text=_("Salary to be offered in LPA. If it's an internship, leave this as 0, and mention salary in placement details."))
	desc = models.TextField(_('Placement details you\'d want to mention'), blank=True)

	students = models.ManyToManyField(Student, related_name="dummy_sessions", blank=True)
	selection_criteria = models.ForeignKey(SelectionCriteria, related_name="dummy_sessions")
	status = models.CharField(_('Current status'),
			help_text="Mention this placement session's current status for shortlisted students' knowledge. Eg. Resume Submission, Final Round, HR Round, Personal Interview Round", 
			blank=True, max_length=256
	)
	
	application_deadline = models.DateField(_('Application Deadline'), 
			null=True, blank=False, 
			help_text=_("Choose last date for students to apply. If no event is scheduled for now, choose an arbitrary future date.")
	)
	
	ended = models.BooleanField(
			_('Has the placement session ended'), 
			help_text=_('Setting it to true would mean that the students currently in the session are selected.'), 
			default=False
	)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.dummy_company.__str__() + ' placement session in ' + self.dummy_company.college.__str__()

	def get_streams(self):
		return ", ".join([s['name'] for s in self.streams.values('name')])

'''
@receiver(m2m_changed, sender=DummySession.streams.through)
def verify_assoc_stream_uniqueness(sender, **kwargs):
	dsession = kwargs.get('instance', None)
	action = kwargs.get('action', None)
	streams = kwargs.get('pk_set', None)
	dsession_streams = DummySession.objects.filter(dummy_company=dsession.dummy_company)
	if action == 'pre_add':
		for stream in streams:
			if dsession_streams.filter(streams=stream):
				raise IntegrityError(_('Association between (%s, %s) already exists for stream %s' % (dsession.dummy_company.college, dsession.dummy_company, stream,)))
'''

@receiver(m2m_changed, sender=DummySession.students.through)
def validating_students(sender, **kwargs):
	action = kwargs.get('action')
	reverse = kwargs.get('reverse')
	
	if action == 'pre_add':
		if reverse:
			student = kwargs.get('instance')
			dsessions = kwargs.get('pk_set')
			college = student.college
			for dsession in dsessions:
				dsession = DummySession.objects.get(pk=dsession)
				if dsession.dummy_company.college != college:
					raise IntegrityError(_('Student doesn\'t belong to this college, thus cannot be added to the session.'))
		else:
			dsession = kwargs.get('instance')
			students = kwargs.get('pk_set')
			college = dsession.dummy_company.college
			for student in students:
				student = Student.objects.get(pk=student)
				if student.college != college:
					raise IntegrityError(_('Student %s doesn\'t belong to this college, thus cannot be added to the session.'%(student.profile.username)))


# m2m_changed instead of post_save because M2Ms are added after instance is saved.
@receiver(m2m_changed, sender=DummySession.streams.through)
def notify_students_about_new_posting(sender, **kwargs):
	dsession = kwargs.get('instance')
	action = kwargs.get('action')
	reverse = kwargs.get('reverse')

	if action == 'post_add' and not reverse:
#		streams = Stream.objects.filter(pk__in=kwargs.get('pk_set'))
		subject = "New %s Posting - %s" % (dict(DummySession.PLACEMENT_TYPE)[dsession.type], dsession.dummy_company.name)
		message = render_to_string('dummy_company/new_posting.txt', {'dcompany': dsession.dummy_company, 'dsession': dsession, 'deadline':dsession.application_deadline + datetime.timedelta(1)})
		student_pks = []
		customuser_pks = []
		years = dsession.selection_criteria.years.split(',')
		for stream in dsession.streams.all():
			students = stream.students.filter(current_year__in=years)
			student_pks += [s['pk'] for s in students.values('pk')]
			customuser_pks += [u['profile__pk'] for u in students.values('profile__pk')]
#		students = Student.objects.filter(pk__in=student_pks)
#		notification_data = NotificationData.objects.create(message=message, subject=subject) IMPORT ME
#		college = association.college
#		for student in students:
#			Notification.objects.create(notification_data=notification_data, actor=college.profile, target=student.profile)
		send_mass_mail_task.delay(subject, message, customuser_pks)


