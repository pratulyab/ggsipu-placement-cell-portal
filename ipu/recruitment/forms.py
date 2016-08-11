from django import forms
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from .models import Association, Dissociation, PlacementSession
from college.models import College, Programme, Stream
from student.models import Student
import base64

class AssociationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		profile = kwargs.pop('profile')
		self.profile = profile
		super(AssociationForm, self).__init__(*args, **kwargs)
		if profile:
			if profile.__class__.__name__ == 'College':
				self.initial['college'] = profile.pk
				self.fields['college'].widget.attrs['disabled'] = 'disabled'
			elif profile.__class__.__name__ == 'Company':
				self.initial['company'] = profile.pk
				self.fields['company'].widget.attrs['disabled'] ='disabled'
			else:
				pass
	
	def clean_college(self):
		college = self.cleaned_data['college']
		if self.profile:
			if self.profile.__class__.__name__ == 'College':
				if college and college!=self.profile:
					raise forms.ValidationError(_('College field changed. You can create associations only for yourself as a college.'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data['company']
		if self.profile:
			if self.profile.__class__.__name__ == 'Company':
				if company and company!=self.profile:
					raise forms.ValidationError(_('Company field changed. You can create associations only for yourself as a company'))
		return company
	
	def save(self, commit=True):
		association = super(AssociationForm, self).save(commit=False)
		if self.profile:
			if self.profile.__class__.__name__ == 'Company':
				association.company = self.profile
				association.initiator = 'CO'
			else:
				association.college = self.profile
				association.initiator = 'C'
		if commit:
			try:
				association.save()
			except IntegrityError as error:
				raise forms.ValidationError(error)
			except ValidationError as error:
				raise forms.ValidationError(error)
		return association
	
	class Meta:
		model = Association
		fields = ['company', 'college', 'programme', 'streams', 'desc']

class PlacementSessionForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		association = kwargs.pop('association', None)
		super(PlacementSessionForm, self).__init__(*args, **kwargs)
		self.association = association
		self.fields['students'].queryset = Student.objects.filter(college=association.college, stream__in=association.streams)
		self.initial['token'] = base64.b64encode(str(association.pk).encode('utf-8')).decode('utf-8')
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly':'True'}))
	
	def save(self, commit=True):
		session = super(PlacementSessionForm, self).save(commit=False)
		session.association = self.association
		if commit:
			try:
				session.save()
			except IntegrityError as error:
				raise forms.ValidationError(error)
			except ValidationError as error:
				raise forms.ValidationError(error)
		return session
	
	class Meta:
		model = PlacementSession
		fields = ['students', 'status', 'recent_deadline', 'ended']

class DissociationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		association = kwargs.pop('association', None)
		super(DissociationForm, self).__init__(*args, **kwargs)
		self.association = association
		self.initial['college'] = association.college.pk
		self.initial['company'] = association.company.pk
		self.fields['college'].widget.attrs['disabled'] = 'disabled'
		self.fields['company'].widget.attrs['disabled'] = 'disabled'
		self.initial['token'] = base64.b64encode(str(association.pk).encode('utf-8')).decode('utf-8')
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly':'True'}))
	
	def clean_college(self):
		college = self.cleaned_data['college']
		if college and college!=self.association.college:
			raise forms.ValidationError(_('College must be the one with whom association was made.'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data['company']
		if company and company!=self.association.company:
			raise forms.ValidationError(_('Company must be the one with whom association was made.'))
		return company
	
	def save(self, commit=True):
		dissociation = super(DissociationForm, self).save(commit=False)
		dissociation.initiator = self.association.initiator
		if commit:
			try:
				dissociation.save()
			except IntegrityError as error:
				raise forms.ValidationError(error)
		return dissociation
	
	class Meta:
		model = Dissociation
		fields = ['company', 'college', 'duration']
