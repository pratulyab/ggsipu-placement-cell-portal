from django.contrib.auth.models import AbstractUser
from django.core import validators
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
