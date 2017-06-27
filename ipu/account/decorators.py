from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.core.urlresolvers import reverse
from account.utils import get_relevant_reversed_url, get_type_created, render_profile_creation
import requests

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
		
		CAUTION: Don't use these for creation functions because this decorator redirects the user to creation url if he hasn't created his profile yet.
				 Otherwise, multiple redirects.
	"""
	def decorator(func):
		@wraps(func)
		def inner(request, *args, **kwargs):
			if request.user.is_anonymous():
				return redirect(settings.LOGIN_URL)
			if request.user.type in user_types_list:
				requester = get_type_created(request.user)
				user_type = requester.pop('user_type')
				if not requester:
					url = reverse(settings.PROFILE_CREATION_URL[user_type])
					if request.is_ajax():
						return JsonResponse(status=403, data = {'location': url})
					else:
#						return redirect(url)
						return render_profile_creation(request, user_type)
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



#Recaptcha Verificaion for forms. Defined only for POST requests.
def check_recaptcha(view_func):
	@wraps(view_func)
	def _wrapped_view(request, *args, **kwargs):
		request.recaptcha_is_valid = None
		if request.method == 'POST':
			recaptcha_response = request.POST.get('recaptcha_response' , None)
			data = {
				'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
				'response': recaptcha_response
			}
			recaptcha_verification_url = settings.GOOGLE_RECAPTCHA_VERIFICATION_URL
			r = requests.post(recaptcha_verification_url, data=data)
			result = r.json()
			if result['success']:
				request.recaptcha_is_valid = True
			else:
				request.recaptcha_is_valid = False
		return view_func(request, *args, **kwargs)
	return _wrapped_view



