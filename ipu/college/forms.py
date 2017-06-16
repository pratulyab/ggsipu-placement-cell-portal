from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from recruitment.fields import ModelMultipleHashidChoiceField
from .models import College, Programme, Stream

from utils import validate_username_for_urls

class CollegeSignupForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(CollegeSignupForm, self).__init__(*args, **kwargs)
		streams_queryset = Stream.objects.all()
		self.fields['streams'] = ModelMultipleHashidChoiceField(streams_queryset, 'HASHID_STREAM', help_text='Please make sure to enter correct streams. This is a highly sensitive and crucial step.')
		self.fields['streams'].choices = self.get_zipped_choices(streams_queryset, 'HASHID_STREAM')
		self.fields['streams'].required = True
	
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append('[' + q.code + '] ' + q.name) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	def clean_username(self):
		username = self.cleaned_data['username']
		if username and not validate_username_for_urls(username):
			raise forms.ValidationError(_('You cannot take this username'))
		return username
	
	def clean_email(self):
		email = self.cleaned_data['email']
		if email:
			domain = '.'.join(email.split('@')[-1].split('.')[:-1]).lower()
			for blacklisted in settings.DISALLOWED_EMAIL_DOMAINS: # Because a few of these provide subdomains. FOOBAR.domainname.com
				if blacklisted in domain:
					raise forms.ValidationError(_('This email domain is not allowed. Please enter email of different domain.'))
		return email

	def save(self, commit=True, *args, **kwargs):
		user = super(CollegeSignupForm, self).save(commit=False, *args, **kwargs)
		user.is_active = False
		user.type = 'C'
		user.set_unusable_password()
		if commit:
			try:
				user.save()
			except:
				raise forms.ValidationError(_('Error occurred while creating account. Please report admin.'))
		self.user_cache = user
		return user
	
	class Meta:
		model = CustomUser
		fields = ['username', 'email']

class CollegeCreationForm(forms.ModelForm):
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sMB)' % (settings.IMAGE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except AttributeError:
				pass
		return photo
	
	def save(self, commit=True, *args, **kwargs):
		college = super(CollegeCreationForm, self).save(commit=False)
		college.profile = kwargs.get('profile', None)
		if commit:
			try:
				college.save()
			except IntegrityError as error:
				raise forms.ValidationError(error)
			except ValidationError as error:
				raise forms.ValidationError(error)
		return college
	
	class Meta:
		model = College
		fields = ['name', 'code', 'address', 'details', 'contact', 'website', 'photo']
		help_texts = {
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}

class CollegeEditForm(forms.ModelForm):
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sMB)' % (settings.IMAGE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except AttributeError:
				pass
		return photo
	
	class Meta:
		model = College
		fields = ['name', 'address', 'details', 'contact', 'website', 'photo']
		help_texts = {
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}
