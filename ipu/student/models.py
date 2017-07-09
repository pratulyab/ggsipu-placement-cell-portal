from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from college.models import (College, Programme, Stream)
from urllib.parse import urlparse

from decimal import Decimal
from utils import get_hashed_filename

# Create your models here.

####################################################################################

class ExaminationBoard(models.Model):
	name = models.CharField(max_length=128, unique=True)
	abbreviation = models.CharField('Abbreviation', max_length=16, blank=True)

	def __str__(self):
		return "%s (%s)" % (self.name, self.abbreviation) if self.abbreviation else self.name

	class Meta:
		ordering = ['name']

class Subject(models.Model):
	name = models.CharField(max_length=128, unique=True)
	code = models.CharField(max_length=10, blank=True)

	def __str__(self):
		return "%s [%s]" % (self.name, self.code)

	def clean(self, *args, **kwargs):
		super(Subject, self).clean()
		self.name = self.name.upper() # Because subject names are always in uppercase in marksheets

	def save(self, *args, **kwargs):
		self.full_clean()
		return super(Subject, self).save()

	class Meta:
		ordering = ['name']

class Score(models.Model):
	subject = models.ForeignKey(Subject, null=True, blank=True, related_name="scores") # Actual subject object
	# But if subject doesn't exist already, add textually
	subject_name = models.CharField(max_length=128, blank=True, help_text='You are mandated to enter the subject name exactly the same as is in marksheet.')
	subject_code = models.CharField(max_length=10, blank=True, help_text='Fill correct subject code, if provided in marksheet.')
	# Save the subject once profile is verified by the faculty
	marks = models.PositiveSmallIntegerField(('Marks out of 100'), null=True, validators=[validators.MinValueValidator(0),validators.MaxValueValidator(100)])

class ScoreMarksheet(models.Model):
	CLASS_OPTS = (
		('10', 'Tenth'),
		('12', 'Twelfth'),
	)
	klass = models.CharField('For Which Class', max_length=2, choices=CLASS_OPTS, default=CLASS_OPTS[0][1])
	board = models.ForeignKey(ExaminationBoard, verbose_name='Examination Board', related_name="marksheets")
	score1 = models.ForeignKey(Score, verbose_name="Subject 1", related_name="marksheets_1")
	score2 = models.ForeignKey(Score, verbose_name="Subject 2", related_name="marksheets_2")
	score3 = models.ForeignKey(Score, verbose_name="Subject 3", related_name="marksheets_3")
	score4 = models.ForeignKey(Score, verbose_name="Subject 4", related_name="marksheets_4")
	score5 = models.ForeignKey(Score, verbose_name="Subject 5", related_name="marksheets_5")
	score6 = models.ForeignKey(Score, verbose_name="Subject 6", related_name="marksheets_6", help_text="Optional", null=True, blank=True)

	def calculate_percentage(self):
		total = 0
		for i in range(1,6):
			total = total + getattr(self, 'score%d'%i).marks
		return total/5

class CGPAMarksheet(models.Model):
	''' Only for 10th class '''
	board = models.ForeignKey(ExaminationBoard, related_name="cgpas")
	cgpa = models.DecimalField('CGPA', max_digits=3, decimal_places=1, default=Decimal(0),\
				validators=[validators.MinValueValidator(Decimal(0)), validators.MaxValueValidator(Decimal(10))]
			)
	conversion_factor = models.DecimalField('Conversion Factor', max_digits=3, decimal_places=1, default=Decimal(0),\
				validators=[validators.MinValueValidator(Decimal(0)), validators.MaxValueValidator(Decimal(10))],\
				help_text = 'CGPA to Percentage conversion factor. Most likely it will be mentioned in your marksheet. Eg. 9.5 for CBSE (10th standard)'
			)

	def calculate_percentage(self):
		return self.cgpa * self.conversion_factor

class SchoolMarksheet(models.Model):
	marksheet_12 = models.OneToOneField(ScoreMarksheet, related_name="school_marksheet_12")
	marksheet_10 = models.OneToOneField(ScoreMarksheet, null=True, blank=True, related_name="school_marksheet_10")
	cgpa_marksheet = models.OneToOneField(CGPAMarksheet, null=True, blank=True)

	def clean(self, *args, **kwargs):
		super(SchoolMarksheet, self).clean()
		if self.marksheet_10 and self.cgpa_marksheet:
			raise ValidationError("There can only be either Scores Marksheet or CGPA Marksheet for 10th class. Not both.")

	def save(self, *args, **kwargs):
		self.full_clean()
		super(SchoolMarksheet, self).save()

####################################################################################

class Student(models.Model):
	
# General Details
	profile = models.OneToOneField(CustomUser, related_name="student")

	firstname = models.CharField(_('First name'), max_length=128)
	lastname = models.CharField(_('Last name'), max_length=128, blank=True)
	GENDER_CHOICES = (
			('M', _('Male')),
			('F', _('Female')),
			('O', _('Other')),
	)
	gender = models.CharField(_('Gender'), choices=GENDER_CHOICES, max_length=1, default=GENDER_CHOICES[0][0])
	dob = models.DateField(_('Date Of Birth'), null=True, blank=False)
	photo = models.ImageField(_('Photo'),upload_to=get_hashed_filename, blank=True)
	phone_number = models.CharField(_('Mobile Number'), max_length=10, help_text='Enter 10 Digit IN Mobile Number', 
			validators=[validators.RegexValidator(
				regex = r'^[7-9]\d{9}$',
				code = 'invalid_number',
			)], 
			error_messages={'invalid_number': _('Invalid IN Phone Number. Make sure you haven\'t prefixed the number with +91 or 0.')},
			unique=True,
			blank=False
		)

# College Specific
	college = models.ForeignKey(College, related_name="students")
	programme = models.ForeignKey(Programme, related_name="students")
	stream = models.ForeignKey(Stream, related_name="students")
	current_year = models.CharField(_('Current Year'), max_length=1, validators=[validators.RegexValidator(r'[1-6]')])
	is_sub_back = models.BooleanField(_('Any Subject Back(s)'), default=False)
	is_verified = models.NullBooleanField(default=None)
	verified_by = models.ForeignKey(CustomUser, blank=True, null=True, related_name="profiles_verified")
	'''
		is_verified
		None -> initial, skipped by faculty
		False -> unverified, waiting for re-evaluation
		True -> verified
		
		verified_by
		Object -> faculty
		None -> verification process not yet initiated. Therefore, it's not known whether the student is a valid one.
		Thus, unverified page is shown until student is not verified_by some faculty. i.e. not None
	'''

# Placement Specific
	SALARY_CHOICES = tuple( ( (i, "%s and above" % i) for i in range(2,14,2) ) )
	resume = models.FileField(_('Resume'), upload_to=get_hashed_filename, blank=True)
	is_intern = models.BooleanField(_('Currently Intern'), default=False)
	is_placed = models.BooleanField(_('Currently Placed'), default=False)
	is_barred = models.BooleanField(_('Bar the student from applying to companies'), default=False, help_text="This will prevent the student from applying to companies for jobs as well as for internships.")
	salary_expected = models.PositiveSmallIntegerField(_('Minimum salary expected (Lakhs P.A.)'), blank=False, null=True, choices=SALARY_CHOICES, 
			help_text = _('Caution: You won\'t be able to appear for companies offering salary less than the minimum you choose. Also, you won\'t be able to change this again.'),
		)
	sessions_applied_to = models.ManyToManyField('recruitment.PlacementSession', blank=True, related_name="applications")
	dsessions_applied_to = models.ManyToManyField('dummy_company.DummySession', blank=True, related_name="applications")

	### School (10 and 12th) marksheet ###
	marksheet = models.OneToOneField(SchoolMarksheet, null=True, blank=True)

	def get_enrollment_no(self):
		return self.profile.username
	
	def get_full_name(self):
		return (self.firstname + " " + self.lastname).title()

	def __str__(self):
		return self.get_full_name()
	
	def get_absolute_url(self):
		return "/user/%s/" % self.profile.username

	def is_not_interested(self):
		return not bool(sessions_applied_to.count() or dsessions_applied_to.count()) # Whether the student ever applied for an opportunity

class Qualification(models.Model):
	student = models.OneToOneField(Student, related_name="qualifications")
	tenth = models.DecimalField(_('Xth Percentage'), max_digits=4, decimal_places=2, validators=[validators.MinValueValidator(Decimal('33'))], default=Decimal(33))
	twelfth = models.DecimalField(_('XIIth Percentage'), max_digits=4, decimal_places=2, validators=[validators.MinValueValidator(Decimal('33'))], default=Decimal(33))
	graduation = models.DecimalField(_('Graduation Percentage'), max_digits=4, decimal_places=2, default=Decimal(33), validators=[validators.MinValueValidator(Decimal('33'))])
	post_graduation = models.DecimalField(_('Post Graduation Percentage'), max_digits=4, decimal_places=2, blank=True, null=True, validators=[validators.MinValueValidator(Decimal('33'))])
	doctorate = models.DecimalField(_('Doctorate Percentage'), max_digits=4, decimal_places=2, blank=True, null=True, validators=[validators.MinValueValidator(Decimal('33'))])
	is_verified = models.NullBooleanField(default=None)
	verified_by = models.ForeignKey(CustomUser, blank=True, null=True, related_name="qualifications_verified")

	def __str__(self):
		return self.student.get_full_name()

class TechProfile(models.Model):
	student = models.OneToOneField(Student, related_name="tech")
	github = models.URLField(blank=True)
	bitbucket = models.URLField(blank=True)
	codechef = models.CharField(max_length=14, blank=True, help_text='Please provide your Codechef username.', validators=[validators.RegexValidator(r'^[a-z]{1}[a-z0-9_]{3,13}$')])
	codeforces = models.CharField(max_length=24, blank=True, help_text='Please provide your Codeforces username.')
	spoj = models.CharField(max_length=14, blank=True, help_text='Please provide your SPOJ username.')
#	coding = models.TextField(_('Miscellaneous Coding Platform Links'), help_text="Eg. Hacker Earth", blank=True)

	def clean(self, *args, **kwargs):
		super(TechProfile, self).clean()
		for field in self._meta.fields:
			if field.__class__.__name__ == 'URLField' and getattr(self, field.name):
				if not field.name in urlparse( getattr(self, field.name) ).netloc:
					raise ValidationError( {field.name: _('Domain name error. Please provide the correct URL.')} )
	
	def save(self, *args, **kwargs):
#		self.full_clean()
		profile = super(TechProfile, self).save()
		return profile

	def __str__(self):
		return self.student.get_full_name()

@receiver(post_delete, sender=Student)
def delete_photo_resume(sender, **kwargs):
	student = kwargs['instance']
	try:
		student.photo.delete(False)
	except:
		pass
	try:
		student.resume.delete(False)
	except:
		pass
