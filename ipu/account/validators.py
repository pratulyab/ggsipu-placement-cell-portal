from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import six
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _

import re

@deconstructible
class ASCIIUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.+-]+$'
    message = _(
        'Enter a valid username. This value may contain only English letters, '
        'numbers, and ./+/-/_ characters.'
    )
    flags = re.ASCII if six.PY3 else 0


@deconstructible
class UnicodeUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.+-]+$'
    message = _(
        'Enter a valid username. This value may contain only letters, '
        'numbers, and ./+/-/_ characters.'
    )
    flags = re.UNICODE if six.PY2 else 0


# Custom Password Validators
'''
class CompleteValidators(object):
	# re = r'((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%]).{8,20})'
	# Not implementing this because the other approach would provide more clear error message at each validation failure
	pass
'''

class CustomPasswordValidator(object):
	'''
		Password validator that requires:
		1) Combination of lower and upper characters
		2) Presence of at least one digit
		3) At least one of the special characters @#$%!
		4) Minimum length of 8 characters
	'''
	def validate(self, password, user=None):
#		if not re.match(r'(?=.*[a-z])(?=.*[A-Z])', password):
#			raise ValidationError(_('Password must be a combination of lower and upper characters. Eg. abC'))
		if not re.match(r'(?=.*\d)', password):
			raise ValidationError(_('Password must contain at least one digit (0-9).'))
		if not re.match(r'(?=.*[#!$%&()*+,-./:;<=>?@[\]^_`{|}~])', password):
			raise ValidationError(_('Password must contain at least one special character.'))
		if not re.match(r'.{8,}', password):
			raise ValidationError(_('Password must be at least 8 characters long.'))

	def get_help_text(self):
		return _("Your password must be a combination of letters, digits (0-9) and special characters (@ # $ % . !).")
