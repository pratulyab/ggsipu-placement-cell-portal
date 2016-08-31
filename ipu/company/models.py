from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from account.models import CustomUser

# Create your models here.

class Company(models.Model):
	profile = models.OneToOneField(CustomUser, related_name="company")

	name = models.CharField(_('Company name'), blank=False, unique=True, max_length=255)
	corporate_code = models.CharField(_('Company registration code'), unique=True, blank=False, validators=[], max_length=11)
	details = models.TextField(_('Details'), blank=True)
	website = models.URLField(_('Company website'), blank=True)
	photo = models.ImageField(_('Photo'), upload_to='company/photo', blank=True)
	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return "/%s/" % self.profile.username

	class Meta:
		verbose_name_plural = _("Companies")

@receiver(post_delete, sender=Company)
def delete_photo(sender, **kwargs):
	company = kwargs['instance']
	try:
		company.photo.delete(False)
	except:
		pass
