from celery.decorators import task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator # An instance of PasswordResetTokenGenerator
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from account.models import CustomUser, UnsuccessfulEmail, UnsuccessfulSMS, SMSDeliveryReport
from account.tokens import account_activation_token_generator  # An instance of AccountActivationTokenGenerator

from sms import send_sms
from datetime import datetime

logger = get_task_logger(__name__)

MAX_RETRIES = 3

# Always pass in user's pk and not the user object
# Because celery needs to serialize the arguments for a task

def how_to_greet(user, html=False):
	greeting = ''
	if user.type == 'S':
		greeting =  "For student " + ("<b>%s</b>" if html else "%s") + ","
	else:
		greeting = "Hi " + ("<b>%s</b>" if html else "%s") + "!"
	return (greeting % (user.username))

def send_email_message(user, email_message, unsuccessful_email_pk, domain, is_activation_email=False, is_forgot_password_email=False):
	email_type = 'Account activation' if is_activation_email else 'Forgot password'

	for tries in range(MAX_RETRIES):
		try:
			email_message.send(fail_silently=False)
			logger.info("%s email sent to %s" % (email_type, user.username))
			if unsuccessful_email_pk:
				try:
					UnsuccessfulEmail.objects.get(pk=unsuccessful_email_pk).delete()
				except:
					pass
			break # Break if successful
		except:
			# Error thrown on the last retry. Therefore, unsuccessful.
			if tries == MAX_RETRIES-1:
				logger.error("%s email could not be sent to %s" % (email_type, user.username))
				if unsuccessful_email_pk:
					try:
						unsuccessful_email = UnsuccessfulEmail.objects.get(pk=unsuccessful_email_pk)
						unsuccessful_email.save() # Saving in order to update the modified_on field
						return
					except:
						unsuccessful_obj = UnsuccessfulEmail.objects.create(is_activation_email=is_activation_email, is_forgot_password_email=is_forgot_password_email, domain=domain)
						unsuccessful_obj.users.add(user)
			# Continue with the loop if tries still in range
	return

@task(name="send_activation_email_task")
def send_activation_email_task(user_pk, domain, unsuccessful_email_pk=None):
	try:
		user = CustomUser.objects.get(pk=user_pk)
	except CustomUser.DoesNotExist:
		return
	email_body_context = {
		'type': user.type,
		'token': account_activation_token_generator.make_token(user),
		'user_hashid': settings.HASHID_CUSTOM_USER.encode(user.pk),
		'protocol': 'https' if settings.USE_HTTPS else 'http',
		'domain': domain,
		'days': settings.PASSWORD_RESET_TIMEOUT_DAYS,
		'greeting': ''
	}
	email_body_context.update({'greeting': how_to_greet(user)})
	body = loader.render_to_string('account/activation_email_text.html', email_body_context)
	email_body_context.update({'greeting': how_to_greet(user, html=True)})
	html = loader.render_to_string('account/activation_email_html.html', email_body_context)
	email_message = EmailMultiAlternatives('Verify Email Address', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	email_message.attach_alternative(html, 'text/html')
	send_email_message(user, email_message, unsuccessful_email_pk, domain, is_activation_email=True)

@task(name="send_forgot_password_email_task")
def send_forgot_password_email_task(user_pk, domain, unsuccessful_email_pk=None):
	try:
		user = CustomUser.objects.get(pk=user_pk)
	except CustomUser.DoesNotExist:
		return
	email_body_context = {
		'token': default_token_generator.make_token(user),
		'user_hashid' : settings.HASHID_CUSTOM_USER.encode(user.pk),
		'protocol': 'https' if settings.USE_HTTPS else 'http',
		'domain' : domain,
		'days': settings.PASSWORD_RESET_TIMEOUT_DAYS,
		'greeting': ''
	}
	if not settings.DEBUG and settings.ALLOWED_HOSTS: # Prod
		# Just in case an unsuccessful email is executed with an obsolete host (domain)
		for host in settings.ALLOWED_HOSTS:
			if domain.startswith(host) or host.startswith(domain): # 'domain.com/ and domain.com'
				break
		domain = settings.ALLOWED_HOSTS[0]
	
	email_body_context.update({'greeting': how_to_greet(user)})
	body = loader.render_to_string('account/forgot_password_email_body_text.html', email_body_context)
	email_body_context.update({'greeting': how_to_greet(user, html=True)})
	html = loader.render_to_string('account/forgot_password_email_body_html.html', email_body_context)
	email_message = EmailMultiAlternatives('Reset Password', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	email_message.attach_alternative(html, 'text/html')
	send_email_message(user, email_message, unsuccessful_email_pk, domain, is_forgot_password_email=True)

@task(name='send_mass_mail_task')
def send_mass_mail_task(subject, message, user_pks_list, unsuccessful_email_pk=None):
# # # # #
	users = CustomUser.objects.filter(pk__in=user_pks_list)
	if not users:
		return
	unsuccessful_users = []
# # # # #
	unsuccessful_email = None
	if unsuccessful_email_pk:
		try:
			unsuccessful_email = UnsuccessfulEmail.objects.get(pk=unsuccessful_email_pk)
		except:
			pass
# # # # #
	try:
		connection = mail.get_connection()
		opened = connection.open()
		if not opened:
			raise Exception('Connection could not be opened')
		for user in users:
			email = mail.EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], connection=connection)
			for tries in range(MAX_RETRIES):
				try:
					email.send(fail_silently=False)
					if unsuccessful_email: # i.e. UnsuccessfulEmail object or this function call is a reattempt to send UnsuccessfulEmail
						unsuccessful_email.users.remove(user)
					break
				except Exception as e:
					if tries == MAX_RETRIES-1:
						logger.error(e)
						logger.critical('Failed to send email to %s' % (user.email))
						unsuccessful_users.append(user)
					# Continue with the loop
		# Loop ends

		if unsuccessful_users and not unsuccessful_email: # i.e. failed attempts for a new task i.e. not a reattempt
			unsuccessful_obj = UnsuccessfulEmail.objects.create(subject=subject, message=message)
			for user in unsuccessful_users:
				unsuccessful_obj.users.add(user)
		elif unsuccessful_email:
			count =  unsuccessful_email.users.count() # or len(unsuccessful_users) is also same
			if count == 0:
				unsucessful_email.delete()
			else:
				unsuccessful_email.save() # i.e. still failed attempts. Therefore, Update modification time 

	except Exception as e:
		logger.error(e) # Maybe ConnectionError/SMTPError or connection is not avilable.. whatever
		obj = UnsuccessfulEmail.objects.create(subject=subject, message=message)
		for user in users:
			obj.users.add(user)
	finally:
		connection.close()

@task(name='send_mass_sms_task')
def send_mass_sms_task(actor_pk, message, to_list, unsuccessful_sms_pk=None, sender='GGSIPU', template_name='basic', *VAR):
	# To send custom message, pass template_name=''
	# Send VAR args as string.
# # # # #
	report = None
	if VAR:
		try:
			VAR = [str(i) for i in VAR]
		except:
			VAR = []
# # # # #
	for tries in range(MAX_RETRIES):
		report = send_sms(to_list, message, sender, template_name, *VAR)
		if not report:
			if tries == MAX_RETRIES-1:
				if unsuccessful_sms_pk:
					try:
						unsuccessful_sms = UnsuccessfulSMS.objects.get(pk=unsuccessful_sms_pk)
						unsuccessful_sms.save()
					except:
						UnsuccessfulSMS.objects.create(message=message, phone_numbers=','.join(set(to_list)), template_name=template_name, sender=sender, template_vars=(','.join(VAR)))
#			Continue with the loop
		else:
			try:
				SMSDeliveryReport.objects.create(actor=CustomUser.objects.get(actor_pk), message=message, recipients=','.join(set(to_list)), status=report['Status'], session_id=report['Details'])
			except:
				pass
			# It was a success. Atleast, the request was sent to the API. Not concerned with the Status of session_id.
			# That is a concern of callback url.
			if unsuccessful_sms_pk:
				try:
					unsuccessful_sms = UnsuccessfulSMS.objects.get(pk=unsuccessful_sms_pk).delete()
				except:
					pass
			break
