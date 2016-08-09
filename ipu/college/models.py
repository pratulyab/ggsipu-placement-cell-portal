from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser

# Create your models here.


class Programme(models.Model):
	YEAR_CHOICES = (
			('1', 1),
			('2', 2),
			('3', 3),
			('4', 4),
			('5', 5),
			('6', 6),
		)
	name = models.CharField(_('Stream name'), blank=False, max_length=32, unique=True)
	desc = models.TextField(_('Description'), blank=True)
	years = models.CharField(_('Number of years'), choices=YEAR_CHOICES, max_length=1, default=YEAR_CHOICES[3][0])

	def __str__(self):
		return self.name


class Stream(models.Model):
	programme = models.ForeignKey(Programme, related_name='streams')

	name = models.CharField(_('Stream name'), blank=False, max_length=64)
	code = models.CharField(_('Stream code'), blank = False, unique=True, max_length=3, validators=[RegexValidator(r'\d{3}')])
	desc = models.TextField(_('Description'), blank=True)

	class Meta:
		unique_together = ['programme', 'code']
	
	def __str__(self):
		return "[%s] %s - %s" % (self.code, self.programme.__str__(), self.name)


class College(models.Model):
	profile = models.OneToOneField(CustomUser, related_name="college")
	
	name = models.CharField(_('College name'), blank=False, max_length=255, unique=True)
	code = models.CharField(_('College code'), blank = False, unique=True, max_length=3, validators=[RegexValidator(r'\d{3}')])
	address = models.TextField(_('College address'), blank=True)
	details = models.TextField(_('Other details'), blank=True)
	contact = models.TextField(_('Contact details'), blank=True)
	website = models.URLField(_('College website'), blank=True)
	photo = models.ImageField(_('Photo'), upload_to='college/photo', blank=True)

#	programmes = models.ManyToManyField(Programme, related_name="colleges")
	streams = models.ManyToManyField(Stream, related_name="colleges")

	def __str__(self):
		return "%s (%s)" % (self.name.title(), self.code)

	def get_absolute_url(self):
		return "/%s/" % self.profile.username
