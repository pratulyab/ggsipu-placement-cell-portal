from celery.decorators import task
from celery.utils.log import get_task_logger

from account.views import send_activation_email

logger = get_task_logger(__name__)

@task(name="send_activation_email_task")
def send_activation_email_task(uid, domain):
	logger.info("Sent activation email")
	return send_activation_email(uid, domain)
