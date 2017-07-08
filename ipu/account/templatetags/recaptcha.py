from django import template
from django.conf import settings
register = template.Library()

@register.simple_tag
def recaptcha_site_key():
	return settings.GOOGLE_RECAPTCHA_SITE_KEY