from django.db import models
from account.models import CustomUser
from django.utils.translation import ugettext_lazy as _
from faculty.models import Faculty
from student.models import Student
from college.models import College
# Create your models here.

class NotificationData(models.Model):
	message = models.TextField(_("Message"), max_length = 4096 , blank = True)
	subject = models.CharField(_('Subject') , max_length = 256 , blank = False)
	sms_message = models.CharField(_('SMS Message') , max_length = 128 , blank = True, null = True)
	def __str__(self):
		return self.subject + "at : " + self.creation_time

class Notification(models.Model):
	actor = models.ForeignKey(CustomUser, related_name="notification_actor")
	target = models.ForeignKey(CustomUser, related_name="notification_target")
	is_read = models.BooleanField(_("Seen?"), default = False)
	notification_data = models.ForeignKey(NotificationData , related_name = "notification_data" , blank = True , null = True)
	message = models.CharField(_('Message') , max_length = 128 , blank = True)
	creation_time = models.DateTimeField(auto_now=False, auto_now_add=True)
	def __str__(self):
		return (" To " + self.target.username + "  From  " + self.actor.username)

	class Meta:
		verbose_name_plural = _("Notifications")


class Issue(models.Model):
	ISSUE_TYPE = (
			('V', _('Verification')),
			('P', _('Placement')),
			('G', _('General')),
		)
	actor = models.ForeignKey(Student, related_name="issue")
	college = models.ForeignKey(College , related_name = "issue")
	issue_type = models.CharField(_('Issue Type'), max_length=1, choices=ISSUE_TYPE, default = None)
	subject = models.CharField(_('Subject') , max_length = 256 , blank = False)
	message = models.CharField(_('Message') , max_length = 4096 , blank = False)
	#solved_by = models.ForeignKey(Faculty , related_name = "issue" , null = True)
	creation_time = models.DateTimeField(auto_now=False, auto_now_add=True, null = False)
	marked = models.BooleanField(_('Marked Important') , default = False)
	solved_by = models.CharField(_('Answered By') , max_length = 64 , blank = True)
	solver_username = models.CharField(_('Solver') , max_length = 32 , blank = True)

	def __str__(self):
		return ("By" + self.actor.profile.username)


class IssueReply(models.Model):
	root_issue = models.OneToOneField(Issue , related_name = "issue_reply")
	reply = models.CharField(_("Reply") , max_length = 4096 , blank = False)
	creation_time = models.DateTimeField(auto_now=False, auto_now_add=True, null = False)
	

	def __str__(self):
		return (self.root_issue.actor.username + "Solved by" + self.actor.firstname)

class Report(models.Model):
	reported_by = models.ForeignKey(CustomUser , related_name = "bug")
	REPORT_TYPE = (
			('FDBK' , _('Feedback')),
			('RQFR' , _('Request Feature')),
			('REBG' , _('Report Bug')),
		)
	type = models.CharField(_('Report Type') , max_length = 4 , choices = REPORT_TYPE , default = None)
	message = models.CharField(_('Message') , max_length = 4096 , blank = False)
	creation_time = models.DateTimeField(auto_now=False, auto_now_add=True, null = False)

	def __str__(self):
		return ("Reported By" + self.reported_by.profile.username)




