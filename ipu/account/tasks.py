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

@task(name="send_activation_email_task")
def send_activation_email_task(user_pk, domain):
	user = CustomUser.objects.get(pk=user_pk)
	email_body_context = {
		'username': user.username,
		'token': account_activation_token_generator.make_token(user),
		'user_hashid': settings.HASHID_CUSTOM_USER.encode(user.pk),
		'protocol': 'http',
		'domain': domain,
		'days': settings.PASSWORD_RESET_TIMEOUT_DAYS
	}
	body = loader.render_to_string('account/activation_email_body.html', email_body_context)
	email_message = EmailMultiAlternatives('Verify Email Address', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	email_message.send()
	logger.info("Account activation email sent to %s" % (user.username))

@task(name="send_forgot_password_email_task")
def send_forgot_password_email_task(user_pk, domain):
	user = CustomUser.objects.get(pk=user_pk)
	email_body_context = {
		'username' : user.username,
		'token': default_token_generator.make_token(user),
		'user_hashid' : settings.HASHID_CUSTOM_USER.encode(user.pk),
		'protocol': 'http',
		'domain' : domain,
		'days': settings.PASSWORD_RESET_TIMEOUT_DAYS
	}
	body = loader.render_to_string('account/forgot_password_email_body_text.html', email_body_context)
	email_message = EmailMultiAlternatives('Reset Password', body, settings.DEFAULT_FROM_EMAIL, [user.email])
	email_message.send()
	logger.info("Forgot password email sent to %s" % (user.username))
