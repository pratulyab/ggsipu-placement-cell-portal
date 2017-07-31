from django.core import validators
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from college.models import College

from utils import get_hashed_photo_name

# Create your models here.

class Faculty(models.Model):
	profile = models.OneToOneField(CustomUser, related_name="faculty")
	firstname = models.CharField(_('First name'), max_length=128)
	lastname = models.CharField(_('Last name'), max_length=128, blank=True)
	employee_id = models.CharField(_('Employee ID'), max_length=64, blank=True)
	college = models.ForeignKey(College, related_name="faculties")
	phone_number = models.CharField(_('Mobile Number'), max_length=10, help_text='Enter 10 Digit IN Mobile Number', 
			validators=[validators.RegexValidator(r'[7-9]\d{9}')], 
			error_messages={'invalid_number': _('Invalid IN Phone Number. Don\'t Prefix The Number With +91 or 0.')},
			null=True
	)
	photo = models.ImageField(_('Photo'),upload_to=get_hashed_photo_name, blank=True)

	def get_full_name(self):
		try:
			return (self.firstname + " " + self.lastname).title()
		except:
			return ("<%s>" % self.profile.username)

	def __str__(self):
		return self.get_full_name()

	def get_absolute_url(self):
		return "/user/%s/" % self.profile.username
	
	class Meta:
		verbose_name_plural = _('Faculties')

@receiver(post_delete, sender=Faculty)
def delete_photo(sender, **kwargs):
	faculty = kwargs['instance']
	try:
		faculty.photo.delete(False)
	except:
		pass
