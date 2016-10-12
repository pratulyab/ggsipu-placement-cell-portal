from django.core import validators
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from college.models import (College, Programme, Stream)
from urllib.parse import urlparse

from decimal import Decimal

# Create your models here.

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
	photo = models.ImageField(_('Photo'),upload_to='student/photo', blank=True)
	phone_number = models.CharField(_('Mobile Number'), max_length=10, help_text='Enter 10 Digit IN Mobile Number', 
			validators=[validators.RegexValidator(r'^[7-9]\d{9}$')], 
			error_messages={'invalid_number': _('Invalid IN Phone Number. Don\'t Prefix The Number With +91 or 0.')},
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

# Placement Specific
	SALARY_CHOICES = tuple( ( (i, "%s and above" % i) for i in range(2,14,2) ) )
	resume = models.FileField(_('Resume'), upload_to='student/resume', blank=True)
	is_intern = models.BooleanField(_('Currently Intern'), default=False)
	is_placed = models.BooleanField(_('Currently Placed'), default=False)
	is_barred = models.BooleanField(_('Bar the student from applying to companies'), default=False, help_text="This will prevent the student from applying to companies for jobs as well as for internships.")
	salary_expected = models.PositiveSmallIntegerField(_('Minimum salary expected (Lakhs P.A.)'), blank=False, null=True, choices=SALARY_CHOICES, 
			help_text = _('Caution: You won\'t be able to appear for companies offering salary less than the minimum you choose. Also, you won\'t be able to change this again.'),
		)

	def get_enrollment_no(self):
		return self.profile.username
	
	def get_full_name(self):
		return (self.firstname + " " + self.lastname).title()

	def __str__(self):
		return self.get_full_name()
	
	def get_absolute_url(self):
		return "/%s/" % self.profile.username

class Qualification(models.Model):
	student = models.OneToOneField(Student, related_name="qualifications")
	tenth = models.DecimalField(_('Xth Percentage'), max_digits=4, decimal_places=2, validators=[validators.MinValueValidator(Decimal('33'))])
	twelfth = models.DecimalField(_('XIIth Percentage'), max_digits=4, decimal_places=2, validators=[validators.MinValueValidator(Decimal('33'))])
	graduation = models.DecimalField(_('Graduation Percentage'), max_digits=4, decimal_places=2, blank=True, null=True, validators=[validators.MinValueValidator(Decimal('33'))])
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
