from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from .validators import ASCIIUsernameValidator, UnicodeUsernameValidator
import re
from urllib.parse import urlparse

# Create your models here.

class CustomUser(AbstractUser):

	def __init__(self, *args, **kwargs):
		self._meta.get_field('email').blank = False
		self._meta.get_field('email')._unique = True
		self._meta.get_field('username').validators = [UnicodeUsernameValidator() if six.PY3 else ASCIIUsernameValidator()]
		self._meta.get_field('username').help_text = "Required. 30 characters or fewer. Letters, digits and ./+/-/_ only."
		super(CustomUser, self).__init__(*args, **kwargs)
	
	USER_TYPES = (
		('C', _('College')),
		('F', _('Faculty')),
		('S', _('Student')),
		('CO', _('Company')),
	)
	type = models.CharField(_('Type'), choices=USER_TYPES, max_length=2, default=USER_TYPES[2][0])
	'''
		Use 'disabled' field to restrict a user's access to the portal, since 'is_active' is used for different purpose.
		If a student has graduated from college, or block recruiter etc.
	'''
	is_disabled = models.BooleanField(default=False)

	def clean(self, *args, **kwargs):
		super(CustomUser, self).clean()
		roll = bool(re.match(r'^\d{11}$', self.username))
		if roll:
			if self.type != 'S':
				raise ValidationError(_('Sorry! You cannot assume this type of username.'))
		else:
			if self.type == 'S' and not self.is_superuser:
				raise ValidationError(_('As a student you are required to enter your enrollment number as username.'))
	
	def save(self, *args, **kwargs):
		self.full_clean()
		user = super(CustomUser, self).save()
		return user

	def get_absolute_url(self):
		return "/%s/" % self.username
	
	def get_home_url(self):
		return reverse(settings.HOME_URL[self.type])

class SocialProfile(models.Model):
	user = models.OneToOneField(CustomUser, related_name="social")
	facebook = models.URLField(blank=True)
	linkedin = models.URLField(blank=True)
	google = models.URLField(blank=True)

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


# Since these don't involve user interaction, not putting much validations
class UnsuccessfulEmail(models.Model):
	is_activation_email = models.BooleanField(default=False)
	is_forgot_password_email = models.BooleanField(default=False)
	subject = models.CharField(max_length=512, blank=True)
	message = models.TextField(blank=True)
	domain = models.CharField(max_length=64, default='placements.ggsipu.ac.in') # I know it's hard coded. But it's apt. Can't set it nullable because it is required in activation email and forgot password
	users = models.ManyToManyField(CustomUser, related_name='unsuccessful_emails', blank=True)
	created_on = models.DateTimeField(auto_now_add=True)
	reattempt_on = models.DateTimeField(auto_now=True)

class UnsuccessfulSMS(models.Model):
	message = models.CharField(max_length=512, blank=True)
	phone_numbers = models.TextField(validators=[validators.RegexValidator(r'^([7-9]\d{9}(,[7-9]\d{9})*)$')], help_text="Comma Separated") # Store comma separated string
	sender = models.CharField(max_length=6, default='GGSIPU')
	template_name = models.CharField(max_length=100, blank=True)
	created_on = models.DateTimeField(auto_now_add=True)
	reattempt_on = models.DateTimeField(auto_now=True)
	template_vars = models.CharField(max_length=256, blank=True, help_text="Comma Separated") # Comma separated string

class SMSDeliveryReport(models.Model):
	actor = models.ForeignKey(CustomUser, blank=True, null=True, on_delete=models.SET_NULL)
	message = models.CharField(max_length=512)
	recipients = models.TextField()
	status = models.CharField(max_length=20) # Success / Failure
	session_id = models.CharField(max_length=128)
	status_desc = models.CharField(max_length=512, blank=True)
	error_desc = models.CharField(max_length=512, blank=True)
	created_on = models.DateTimeField(auto_now_add=True)
