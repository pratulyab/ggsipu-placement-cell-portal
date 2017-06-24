from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser

from utils import get_hashed_filename

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
	photo = models.ImageField(_('Photo'), upload_to=get_hashed_filename, blank=True)

	streams = models.ManyToManyField(Stream, related_name="colleges")

	def get_programmes_queryset(self):
		return Programme.objects.filter(pk__in = {s.programme.pk for s in self.streams.all()})

	def __str__(self):
		return "%s (%s)" % (self.name.title(), self.code)

	def get_short_name(self):
		output = ""
		inp = self.name.replace("Of","",1)
		inp = inp.replace("And","",1)
		for i in inp.upper().split():
			output += i[0]	
		return output	

	def get_absolute_url(self):
		return "/user/%s/" % self.profile.username

@receiver(post_delete, sender=College)
def delete_photo(sender, **kwargs):
	college = kwargs['instance']
	try:
		college.photo.delete(False)
	except:
		pass
