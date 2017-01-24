from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from .models import College, Programme, Stream

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
