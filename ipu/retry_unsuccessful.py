from account.tasks import *

def resend_failed_email(unsuccessful_email_pk):
	try:
		obj = UnsuccessfulEmail.objects.prefetch_related('users').get(pk=unsuccessful_email_pk)
	except UnsuccessfulEmail.DoesNotExist:
		return
	users = obj.users.all()
	user = users
	if users.exists():
		user = users[0]
	else:
		return
	
	if obj.is_activation_email:
		send_activation_email_task.delay(user.pk, obj.domain, unsuccessful_email_pk=obj.pk)
	elif obj.is_forgot_password_email:
		send_forgot_password_email_task.delay(user.pk, obj.domain, unsuccessful_email_pk=obj.pk)
	else:
		# Mass Mail
		user_pks_list = [u['pk'] for u in users.values('pk')]
		send_mass_mail_task.delay(obj.subject, obj.message, user_pks_list, unsuccessful_email_pk=obj.pk)

def resend_failed_sms(unsuccessful_sms_pk):
	try:
		obj = UnsuccessfulSMS.objects.get(pk=unsuccessful_sms_pk)
	except UnsuccessfulSMS.objects.DoesNotExist:
		return
	to_list = obj.phone_numbers.split(',')
	send_mass_sms_task.delay(obj.message, to_list, unsuccessfull_sms_pk, sender=obj.sender, template_name=obj.template_name, *obj.template_vars.split(','))
