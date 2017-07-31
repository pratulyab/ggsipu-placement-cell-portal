from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from account.models import CustomUser

from utils import get_hashed_photo_name

# Create your models here.

class Company(models.Model):
	profile = models.OneToOneField(CustomUser, related_name="company")

	name = models.CharField(_('Company / LLP name (As authorized by MCA)'), blank=False, unique=True, max_length=255)
	corporate_code = models.CharField(_('LLPIN/CIN/Form 1 Ref. No.'), unique=True, blank=False, validators=[], max_length=64)
	details = models.TextField(_('Details'), blank=True)
	website = models.URLField(_('Company website'), blank=True)
	photo = models.ImageField(_('Photo'), upload_to=get_hashed_photo_name, blank=True)
	def __str__(self):
		return "%s" % self.name

	def get_absolute_url(self):
		return "/user/%s/" % self.profile.username

	def display_name(self):
		return "{} [{}]".format(self.name, self.corporate_code)

	class Meta:
		verbose_name_plural = _("Companies")

@receiver(post_delete, sender=Company)
def delete_photo(sender, **kwargs):
	company = kwargs['instance']
	try:
		company.photo.delete(False)
	except:
		pass
