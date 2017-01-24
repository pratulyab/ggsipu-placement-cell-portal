from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from account.utils import get_relevant_reversed_url, get_type_created

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

def new_require_user_types(user_types_list):
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
