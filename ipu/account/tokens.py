from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
	'''
		Redefining the hash_value to make the link a one-time activity.
	'''
	def _make_hash_value(self, user, timestamp):
		return (
			str(user.pk) + user.username + str(timestamp) + str(user.is_active)
			# Therefore, the token expires as soon as it is clicked or the timestamp expires
		)

account_activation_token_generator = AccountActivationTokenGenerator()
