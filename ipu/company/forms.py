from django import forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from company.models import Company
import re

class CompanyCreationForm(forms.ModelForm):
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sKB)' % (settings.IMAGE_MAX_SIZE/(1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except AttributeError:
				pass
		return photo
	
	def save(self, commit=True, *args, **kwargs):
		company = super(CompanyCreationForm, self).save(commit=False)
		company.profile = kwargs.pop('profile', None)
		if commit:
			try:
				company.save()
			except IntegrityError as error:
				raise forms.ValidationError(error)
			except ValidationError as error:
				raise forms.ValidationError(error)
		return company

	def clean_corporate_code(self, *args, **kwargs):
		ccode = self.cleaned_data.get('corporate_code')
		if ccode and len(ccode) < 5:
			raise forms.ValidationError('Invalid code')
		return ccode
	
	class Meta:
		model = Company
		fields = ['name', 'corporate_code', 'details', 'website', 'photo']
		help_texts = {
			'name': _('Please fill in company name as authorized by the Ministry of Corporate Affairs (MCA).'),
			'corporate_code': _('This is required only once during registration process.'),
			'photo': _('Please upload image in either jpeg or png format, < %sKB' % str(settings.IMAGE_MAX_SIZE/(1024))),
		}

class CompanyEditForm(forms.ModelForm):
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sKB)' % (settings.IMAGE_MAX_SIZE/(1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except AttributeError:
				pass
		return photo
	
	class Meta:
		model = Company
		fields = ['name', 'details', 'website', 'photo']
		help_texts = {
			'photo': _('Please upload image in either jpeg or png format, < %sKB' % str(settings.IMAGE_MAX_SIZE/(1024))),
		}
