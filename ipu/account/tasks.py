from celery.decorators import task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator # An instance of PasswordResetTokenGenerator
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from account.models import CustomUser
from account.tokens import account_activation_token_generator  # An instance of AccountActivationTokenGenerator

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
