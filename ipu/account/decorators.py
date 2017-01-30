from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from account.utils import get_relevant_reversed_url, get_type_created
'''
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
'''
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
		This also sets the user_type and profile of the user. If profile hasn't been created, user is automatically redirected to creation page.
	"""
	def decorator(func):
		@wraps(func)
		def inner(request, *args, **kwargs):
			if request.user.type in user_types_list:
				requester = get_type_created(request.user)
				user_type = requester.pop('user_type')
				if not requester:
					url = reverse(settings.PROFILE_CREATION_URL[user_type])
					if request.is_ajax():
						return JsonResponse(status=403, data = {'location': url})
					else:
						return redirect(url)
				profile = requester['profile']
				return func(request, user_type=user_type, profile=profile, *args, **kwargs)
			if request.is_ajax():
				return JsonResponse(status=400, data={'location': get_relevant_reversed_url(request)})
			else:
				return redirect(get_relevant_reversed_url(request))
		return inner
	return decorator

def require_AJAX_redirect(redirect_appropriately=True):
	"""
		Decorator to allow only asynchronous requests.
		It accepts a boolean param which decides whether to redirect the user to a relevant url,
		or raise Permission Denied (403) error, for synchronous requests made.
	
		Careful on usage with anonymous users.
		In such cases, place this decorator above login_required.
	
	"""
	def decorator(func):
		@wraps(func)
		def inner(request, *args, **kwargs):
			if not request.is_ajax():
				if redirect_appropriately:
					return redirect(get_relevant_reversed_url(request))
				raise PermissionDenied
			return func(request, *args, **kwargs)
		return inner
	return decorator

require_AJAX = require_AJAX_redirect(False)
require_AJAX.__doc__ = 'Decorator to allow only asynchronous request and raise Permission Denied (403) error otherwise.'
