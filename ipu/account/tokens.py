from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int, int_to_base36

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
	'''
		Redefining the hash_value to make the link a one-time activity.
	'''
	def _make_hash_value(self, user, timestamp):
		return (
			str(user.pk) + user.username + str(timestamp) + str(user.is_active)
			# Therefore, the token expires as soon as it is clicked or the timestamp expires
		)

class TimeUnboundedActivationTokenGenerator(AccountActivationTokenGenerator):
	'''
		Same as account activation token, but without the no of days constraint while checking validity
	'''
	def check_token(self, user, token):
		if not (user and token):
			return False
		
		# Parse the token
		try:
			ts_b36, hash = token.split("-")
		except ValueError:
			return False
		
		try:
			ts = base36_to_int(ts_b36)
		except ValueError:
			return False
		
		# Check that the timestamp/uid has not been tampered with
		if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
			return False
		'''
		# Check the timestamp is within limit. Commenting this constraint
		if (self._num_days(self._today()) - ts) > settings.PASSWORD_RESET_TIMEOUT_DAYS:
			return False
		'''
		return True

account_activation_token_generator = AccountActivationTokenGenerator()
time_unbounded_activation_token_generator = TimeUnboundedActivationTokenGenerator()
