from celery.decorators import task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator # An instance of PasswordResetTokenGenerator
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from account.models import CustomUser
from account.tokens import account_activation_token_generator  # An instance of AccountActivationTokenGenerator

from sms import send_sms

logger = get_task_logger(__name__)

# Always pass in user's pk and not the user object
# Because celery needs to serialize the arguments for a task

def how_to_greet(user, html=False):
	greeting = ''
	if user.type == 'S':
		greeting =  "For student " + ("<b>%s</b>" if html else "%s") + ","
	else:
		greeting = "Hi " + ("<b>%s</b>" if html else "%s") + "!"
	return (greeting % (user.username))
	
@task(name="send_activation_email_task")
def send_activation_email_task(user_pk, domain):
	user = CustomUser.objects.get(pk=user_pk)
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
	email_message.send()
	logger.info("Account activation email sent to %s" % (user.username))

@task(name="send_forgot_password_email_task")
def send_forgot_password_email_task(user_pk, domain):
	user = CustomUser.objects.get(pk=user_pk)
	email_body_context = {
		'token': default_token_generator.make_token(user),
		'user_hashid' : settings.HASHID_CUSTOM_USER.encode(user.pk),
		'protocol': 'https' if settings.USE_HTTPS else 'http',
		'domain' : domain,
		'days': settings.PASSWORD_RESET_TIMEOUT_DAYS,
		'greeting': ''
	}
	email_body_context.update({'greeting': how_to_greet(user)})
	body = loader.render_to_string('account/forgot_password_email_body_text.html', email_body_context)
	email_body_context.update({'greeting': how_to_greet(user, html=True)})
	html = loader.render_to_string('account/forgot_password_email_body_html.html', email_body_context)
	email_message = EmailMultiAlternatives('Reset Password', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	email_message.attach_alternative(html, 'text/html')
	email_message.send()
	logger.info("Forgot password email sent to %s" % (user.username))

@task(name='send_mass_mail_task')
def send_mass_mail_task(subject, message, to_list, MAX_RETRIES=3):
	unsuccessful = []
	try:
		connection = mail.get_connection()
		connection.open()
		for to in to_list:
			email = mail.EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [to], connection=connection)
			for tries in range(MAX_RETRIES):
				try:
					email.send(fail_silently=False)
					break
				except Exception as e:
					if tries == MAX_RETRIES - 1:
						logger.error(e)
						logger.critical('Failed to send email to %s' % (to))
						unsuccessful.append(to)
					continue
#		UnsuccessfulEmail.objects.create(subject=subject, message=message, emails=unsuccessful)
	except Exception as e:
		logger.error(e)
	finally:
		connection.close()

@task(name='send_mass_sms_task')
def send_mass_sms_task(message, to_list, sender='GGSIPU', template_name='basic', *VAR):
	# To send custom message, pass template_name=''
	send_sms(to_list, message, sender, template_name, *VAR)
