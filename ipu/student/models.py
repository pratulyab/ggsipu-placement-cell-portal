from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from college.models import (College, Programme, Stream)
from urllib.parse import urlparse

# Create your models here.

class Student(models.Model):
	"""
	def __init__(self, *args, **kwargs):
		self._meta.get_field('username').validators = [validators.RegexValidator(r'^\d{11}$')]
		super(Student, self).__init__(*args, **kwargs)
	"""
	
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
	verified_by = models.ForeignKey(CustomUser, blank=True, related_name="profiles_verified")

# Placement Specific
	resume = models.FileField(upload_to='student/resume', blank=True)
	
	def get_full_name(self):
		return (self.firstname + " " + self.lastname).title()

	def __str__(self):
		return get_full_name()
	
	def get_absolute_url(self):
		return "/%s/" % self.profile.username


class Qualification(models.Model):
	student = models.OneToOneField(Student, related_name="qualifications")
	tenth = models.DecimalField(_('Xth Percentage'), max_digits=4, decimal_places=2)
	twelfth = models.DecimalField(_('XIIth Percentage'), max_digits=4, decimal_places=2)
	graduation = models.DecimalField(_('Graduation Percentage'), max_digits=4, decimal_places=2)
	post_graduation = models.DecimalField(_('Post Graduation Percentage'), max_digits=4, decimal_places=2)
	doctorate = models.DecimalField(_('Doctorate Percentage'), max_digits=4, decimal_places=2)


class TechProfile(models.Model):
	student = models.OneToOneField(Student, related_name="tech")
	github = models.URLField(blank=True)
	bitbucket = models.URLField(blank=True)
	coding = models.TextField(_('Miscellaneous Profile Links'), help_text="Eg. Code Chef, SPOJ, Code Forces, Hacker Earth", blank=True)

	def clean(self, *args, **kwargs):
		super(SocialProfile, self).clean()
		for field in self._meta.fields:
			if field.__class__.__name__ == 'URLField' and getattr(self, field.name):
				if not field.name in urlparse( getattr(self, field.name) ).netloc:
					raise ValidationError( {field.name: _('Domain name error. Please provide the correct URL.')} )
	
	def save(self, *args, **kwargs):
		self.full_clean()
		profile = super(SocialProfile, self).save()
		return profile
