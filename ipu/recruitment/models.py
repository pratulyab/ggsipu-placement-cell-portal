from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.utils import IntegrityError
from django.template.loader import render_to_string
from account.tasks import send_mass_mail_task
from college.models import College, Programme, Stream
from company.models import Company
from notification.models import Notification, NotificationData
from student.models import Student, Qualification
from django.utils.translation import ugettext_lazy as _

from decimal import Decimal
import datetime

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
		help_text=_("Salary to be offered in LPA. If it's an internship, leave this as 0, and mention salary in placement details."),
	)
	desc = models.TextField(_('Placement details you\'d want to mention'), blank=True)
	initiator = models.CharField(_('Who initiated it'), max_length=2, choices=SOURCE, default=SOURCE[0][0])
	approved = models.NullBooleanField(default=None)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)
	decline_message = models.CharField(max_length=1024, blank=True, help_text='Reason(s) for declining')

	def __str__(self):
		return self.company.name + " for placement in " + self.college.name

	def get_streams(self):
		return ", ".join([s['name'] for s in self.streams.values('name')])

class SelectionCriteria(models.Model):
	SCHOOL_PERCENTAGE_CHOICES = tuple((("%s" % i, "%s and above" % i) for i in ['60','70','75','80','85','90','95']))
	COLLEGE_PERCENTAGE_CHOICES = tuple((("%s" % i, "%s and above" % i) for i in ['50','60','65','70','75','80','85']))
	years = models.CharField(_('Which year students may apply'), max_length=30, blank=True, help_text="Eg. 1,2,3 (Without spaces anywhere)(In increasing order)", 
			validators = [RegexValidator(r'^([1-6](,[1-6])*)?$')]
		)
		# UPDATE: Changing length to 30. Desperate times, need desperate measures.
		# MAX: 1,2,3,4,5,6(w/o spaces)
		# regex is valid for empty string as well
	is_sub_back = models.BooleanField(_('Are student with any subject back(s) allowed'), default=False)
	tenth = models.CharField(_('Xth Percentage'), max_length=2, blank=True, choices=SCHOOL_PERCENTAGE_CHOICES)
	twelfth = models.CharField(_('XIIth Percentage'), max_length=2, blank=True, choices=SCHOOL_PERCENTAGE_CHOICES)
	graduation = models.CharField(_('Graduation Percentage'), max_length=2, blank=True, choices=COLLEGE_PERCENTAGE_CHOICES)
	post_graduation = models.CharField(_('Post Graduation Percentage'), max_length=2, blank=True, choices=COLLEGE_PERCENTAGE_CHOICES)
	doctorate = models.CharField(_('Doctorate Percentage'), max_length=2, blank=True, choices=COLLEGE_PERCENTAGE_CHOICES)

	def clean(self, *args, **kwargs):
		super(SelectionCriteria, self).clean()
		years = self.years.split(',')
		for each in years:
			if not each and len(years) > 1:
				raise IntegrityError(_('There must not be any spaces in the years.'))
			elif len(each) > 1:
				raise IntegrityError(_('Make sure the year is entered in the proper desired format'))
			elif each.isalpha() and int(each) > 6:
				raise IntegrityError(_('Maximum year value can be 6.'))
#		return self.years

	def save(self, *args, **kwargs):
		self.full_clean()
		criterion = super(SelectionCriteria, self).save()
		return criterion

	def check_eligibility(self, student):
		if not isinstance(student, Student):
			return False
		try:
			report_card = student.qualifications
		except Qualification.DoesNotExist:
			return None
		fields = ['tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']
		if getattr(student, 'current_year') not in getattr(self, 'years'):
			return False
		for f in fields:
			if getattr(self, f) and getattr(report_card, f) and getattr(report_card, f) < int(getattr(self, f)):
				return False
		if not getattr(self, 'is_sub_back') and getattr(student, 'is_sub_back'):
				return False
		return True

class PlacementSession(models.Model):
	association = models.OneToOneField(Association, related_name="session")
	students = models.ManyToManyField(Student, related_name="sessions", blank=True)
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
	last_modified_by = models.CharField(max_length=2, choices=SOURCE, default=SOURCE[0][0])
	selection_criteria = models.ForeignKey(SelectionCriteria, related_name="sessions")
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.association.company.__str__() + ' placement session at ' + self.association.college.__str__()

class Dissociation(models.Model):
	''' Block '''
	company = models.ForeignKey(Company, related_name="dissociations")
	college = models.ForeignKey(College, related_name="dissociations")
	reason = models.CharField(_('Reasons'), blank=True, max_length=1024)
	initiator = models.CharField(_('Who initiated it'), choices=SOURCE, max_length=2, default=SOURCE[0][0])
	created_on = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		""" Returns the name of initiator first, then the other """
		if self.initiator == SOURCE[0][0]:
			return self.college.__str__() + ", " + self.company.__str__()
		else:
			return self.company.__str__() + ", " + self.college.__str__()
	
	class Meta:
		unique_together = ['company', 'college', 'initiator'] # Because both A and B can block each other

@receiver(m2m_changed, sender=PlacementSession.students.through)
def validating_students(sender, **kwargs):
	session = kwargs.get('instance', None)
	action = kwargs.get('action', None)
	reverse = kwargs.get('reverse')
	
	if action == 'pre_add' and not reverse: # Validation when reverse=True, i.e. student has applied using the form, is taken care of in the views
		# Validating if the admin adds incorrectly
			students = kwargs.get('pk_set', None)
			for student in students:
				student = Student.studying.get(pk=student) # Only currently studying students can be addded to a session
				if student.college != session.association.college:
					raise IntegrityError(_('Student %s doesn\'t belong to this college, thus cannot be added to the session.'))
				if not session.association.streams.filter(pk=student.stream.pk).exists():
					raise IntegrityError(_('Student %s doesn\'t belong to this programme, thus cannot be added to the session.'))

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
		message = message + ' Session: %s - {%s}<br>' % (association.programme.__str__(), ', '.join([s.name.title() for s in association.streams.all()]) )
#		usernames = '\n'.join([Student.objects.get(pk=s).profile.username for s in students]) # Haven't used 'studying' manager because list could be changed after students have graduated
		if action == 'post_add':
#			message = '%d student%s added to the session\n%s' % (len(students), '' if len(students)==1 else 's', usernames)
			message += '%d student%s added to the session.<br> Total enrollments = %d.<br>' % \
				(len(students), '' if len(students)==1 else 's', session.students.count())
		else:
#			message = '%d student%s removed from the session\n%s' % (len(students), '' if len(students)==1 else 's', usernames)
			message += '%d student%s removed from the session.<br> %d student%s left in the session.<br>' % \
					  (len(students), '' if len(students)==1 else 's', session.students.count(), '' if session.students.count()==1 else 's')
		message += 'To view the complete list, move to "Sessions" tab and download this session\'s excel sheet.'
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

@receiver(post_save, sender=Association)
def declined_request_notification(sender, **kwargs):
	association = kwargs.get('instance')
#	print('Created: ', kwargs.get('created'))
#	print(association.approved)
	if not kwargs.get('created') and association.approved == False: # Declined a pre-created association
		if association.initiator == 'C':
			actor = association.company
			target = association.college
		else:
			actor = association.college
			target = association.company
		type = dict(Association.PLACEMENT_TYPE)[association.type]
		message = '%s declined your association request for %s session. \
				  To view the declined request, move to "My Requests" tab and look under the "Declined Requests" heading.' % (actor.name.title(), type)
		Notification.objects.create(actor=actor.profile, target=target.profile, message=message)

@receiver(post_save, sender=Association)
def new_request_notification(sender, **kwargs):
	if not kwargs.get('created'):
		return
	association = kwargs.get('instance')
	if association.initiator == 'C':
		actor = association.college
		target = association.company
	else:
		actor = association.company
		target = association.college
	type = dict(Association.PLACEMENT_TYPE)[association.type]
	message = '%s sent you an association request. To view the request, hop on to "Association Requests" tab.' % (actor.name.title())
	Notification.objects.create(actor=actor.profile, target=target.profile, message=message)


@receiver(post_save, sender=PlacementSession)
def notify_students_about_new_posting(sender, **kwargs):
	if not kwargs.get('created'):
		return
	session = kwargs.get('instance')
	association = session.association
	subject = "New %s Posting - %s" % (dict(Association.PLACEMENT_TYPE)[association.type], association.company.name)
	message = render_to_string('recruitment/new_posting.txt', {'association': association, 'company': association.company, 'session': session, 'deadline':session.application_deadline + datetime.timedelta(1)})
	student_pks = []
	customuser_pks = []
	years = session.selection_criteria.years.split(',')
	for stream in association.streams.all():
		students = stream.students(manager='studying').filter(current_year__in=years) # Only currently studying students should be notified about new posting
		student_pks += [s['pk'] for s in students.values('pk')]
		customuser_pks += [u['profile__pk'] for u in students.values('profile__pk')]
#	students = Student.studying.filter(pk__in=student_pks)
#	notification_data = NotificationData.objects.create(message=message, subject=subject)
#	college = association.college
#	for student in students:
#		Notification.objects.create(notification_data=notification_data, actor=college.profile, target=student.profile)
	send_mass_mail_task.delay(subject, message, customuser_pks)

	
# # # # # # # #
# This validation offers a drawback to the required scheme.
# 1) There might be use cases to create multiple association with same attributes.
# 2) Also, to re-associate the same association to a new session, the old session has to be removed because O2O.
# Even though there is a way around for 2), still it is better to not increase complexity.
# way around => (by migrating the ended session to an ArchivedAssociation object). But 1) can creep in anytime. i.e. a need for new session while existing one has not yet been marked ended.
'''
# Enables to validate that only 1 association exists between a college and company for particular stream(s)
@receiver(m2m_changed, sender=Association.streams.through)
def verify_assoc_stream_uniqueness(sender, **kwargs):
	association = kwargs.get('instance', None)
	action = kwargs.get('action', None)
	streams = kwargs.get('pk_set', None)
	if action == 'pre_add':
		association_streams = Association.objects.filter(company=association.company, college=association.college)
		for stream in streams:
			if association_streams.filter(streams=stream):
				raise IntegrityError(_('Association between (%s, %s) already exists for chosen stream' % (association.college, association.company)))
'''
# # # # # # # #
