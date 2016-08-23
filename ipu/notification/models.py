from django.db import models
from account.models import CustomUser
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class Notification(models.Model):
	actor = models.ForeignKey(CustomUser, related_name="notification_actor")
	target = models.ForeignKey(CustomUser, related_name="notification_target")
	message = models.CharField(_("Message"), max_length = 128 , blank = True , null = True)
	is_read = models.BooleanField(_("Seen?"), default = False)
	creation_time = models.DateTimeField(auto_now=False, auto_now_add=True, null = False)

	def __str__(self):
		return (self.target + "to" + self.actor)


	class Meta:
		verbose_name_plural = _("Notifications")