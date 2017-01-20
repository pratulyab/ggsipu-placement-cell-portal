from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from account.utils import get_relevant_reversed_url

def require_user_types(user_types_list):
	"""
		This decorator allows the logged in users of particular types, provided in the list.
		It doesn't check for user authentication. Therefore, if authentication is required,
		you MUST call this decorator after the login_required. (place above login_required)
		Eg. 
			@require_user_types(['C', 'F'])
			@login_required
			def foo:
				...
	"""
	def decorator(func):
		@wraps(func)
		def inner(request, *args, **kwargs):
			if request.user.type in user_types_list:
				return func(request, *args, **kwargs)
			return redirect(get_relevant_reversed_url(request))
		return inner
	return decorator
