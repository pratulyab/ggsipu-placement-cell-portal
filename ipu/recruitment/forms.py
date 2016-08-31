from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from college.models import College, Programme, Stream
from company.models import Company
from recruitment.models import Association, PlacementSession, Dissociation
from student.models import Student

class AssActorsOnlyForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.initiator_profile = kwargs.pop('initiator_profile')
		super(AssActorsOnlyForm, self).__init__(*args, **kwargs)
		try:
			self.cname = self.initiator_profile.__class__.__name__
		except:
		 	# i.e. when initiator_profile isn't passed
		 	self.cname = ''
		if self.cname == 'College':
			self.fields['college'].queryset = College.objects.filter(pk=self.initiator_profile.pk)
			self.initial['college'] = self.initiator_profile.pk
			self.fields['college'].widget.attrs['disabled'] = 'disabled'
		elif self.cname == 'Company':
			self.fields['company'].queryset = Company.objects.filter(pk=self.initiator_profile.pk)
			self.initial['company'] = self.initiator_profile.pk
			self.fields['company'].widget.attrs['disabled'] = 'disabled'
		else:
			pass

	def clean_college(self):
		college = self.cleaned_data.get('college', None)
		if self.cname == 'College':
			if college and college != self.initiator_profile:
				raise forms.ValidationError(_('College field changed. You can create associations only for yourself.'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data.get('company', None)
		if self.cname == 'Company':
			if company and company != self.initiator_profile:
				raise forms.ValidationError(_('Company field changed. You can create associations only for yourself.'))
		return company
	
	class Meta:
		model = Association
		fields = ['college', 'company']

class AssWithProgrammeForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.initiator_profile = kwargs.pop('initiator_profile')
		programme_queryset = kwargs.pop('programme_queryset')
		super(AssWithProgrammeForm, self).__init__(*args, **kwargs)
		self.fields['programme'].queryset = programme_queryset
		try:
			self.cname = self.initiator_profile.__class__.__name__
		except:
		 	self.cname = ''
		if self.cname == 'College':
			self.fields['college'].queryset = College.objects.filter(pk=self.initiator_profile.pk)
			self.initial['college'] = self.initiator_profile.pk
			self.fields['college'].widget.attrs['disabled'] = 'disabled'
		elif self.cname == 'Company':
			self.fields['company'].queryset = Company.objects.filter(pk=self.initiator_profile.pk)
			self.initial['company'] = self.initiator_profile.pk
			self.fields['company'].widget.attrs['disabled'] = 'disabled'
		else:
			pass

	def clean_college(self):
		college = self.cleaned_data.get('college', None)
		if self.cname == 'College':
			if college and college != self.initiator_profile:
				raise forms.ValidationError(_('College field changed. You can create associations only for yourself.'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data.get('company', None)
		if self.cname == 'Company':
			if company and company != self.initiator_profile:
				raise forms.ValidationError(_('Company field changed. You can create associations only for yourself.'))
		return company
	
	class Meta:
		model = Association
		fields = ['college', 'company', 'programme']

class AssociationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.initiator_profile = kwargs.pop('initiator_profile')
		self.programme_queryset = kwargs.pop('programme_queryset')
		chosen_programme = kwargs.pop('chosen_programme')
		streams_queryset = kwargs.pop('streams_queryset')
		super(AssociationForm, self).__init__(*args, **kwargs)
		self.fields['programme'].queryset = self.programme_queryset
		self.initial['programme'] = chosen_programme
		self.fields['streams'].queryset = streams_queryset
		try:
			self.cname = self.initiator_profile.__class__.__name__
		except:
		 	self.cname = ''
		if self.cname == 'College':
			self.fields['college'].queryset = College.objects.filter(pk=self.initiator_profile.pk)
			self.initial['college'] = self.initiator_profile.pk
			self.fields['college'].widget.attrs['disabled'] = 'disabled'
		elif self.cname == 'Company':
			self.fields['company'].queryset = Company.objects.filter(pk=self.initiator_profile.pk)
			self.initial['company'] = self.initiator_profile.pk
			self.fields['company'].widget.attrs['disabled'] = 'disabled'
		else:
			pass

	def clean_college(self):
		college = self.cleaned_data.get('college', None)
		if self.cname == 'College':
			if college and college != self.initiator_profile:
				raise forms.ValidationError(_('College field changed. You can create associations only for yourself.'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data.get('company', None)
		if self.cname == 'Company':
			if company and company != self.initiator_profile:
				raise forms.ValidationError(_('Company field changed. You can create associations only for yourself.'))
		return company

	def save(self, commit=True):
		association = super(AssociationForm, self).save(commit=False)
		if self.cname == 'College':
			association.college = self.initiator_profile
			association.initiator = 'C'
		elif self.cname == 'Company':
			association.company = self.initiator_profile
			association.initiator = 'CO'
		
		if commit:
			association.save()
		return association
	
	class Meta:
		model = Association
		fields = ['college', 'company', 'programme', 'streams', 'type', 'salary', 'desc']

class PlacementSessionForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.association = kwargs.pop('association')
		super(PlacementSessionForm, self).__init__(*args, **kwargs)
		self.fields['students'].queryset = Student.objects.filter(college=self.association.college, stream__in=self.association.streams.all())
		self.initial['token'] = settings.HASHID_ASSOCIATION.encode(self.association.pk)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': 'True'}))
	
	def save(self, commit=True):
		session = super(PlacementSessionForm, self).save(commit=False)
		session.association = self.association
		if commit:
			session.save()
		return session
	
	class Meta:
		model = PlacementSession
		fields = ['students', 'status', 'recent_deadline', 'ended']

class DissociationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.association = kwargs.pop('association')
		super(DissociationForm, self).__init__(*args, **kwargs)
		if self.association.initiator == 'CO':
			del self.fields['college']
			self.fields['company'].queryset = Company.objects.filter(pk=self.association.company.pk)
			self.initial['company'] = self.association.company.pk
			self.fields['company'].widget.attrs['disabled'] = 'disabled'
		else:
			del self.fields['company']
			self.fields['college'].queryset = College.objects.filter(pk=self.association.college.pk)
			self.initial['college'] = self.association.college.pk
			self.fields['college'].widget.attrs['disabled'] = 'disabled'
		self.initial['token'] = settings.HASHID_ASSOCIATION.encode(self.association.pk)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': 'True'}))

	def clean_college(self):
		college = self.cleaned_data.get('college', None)
		if college and college != self.association.college:
			raise forms.ValidationError(_('Unexpected error occurred. Request cannot be completed'))
		return college
	
	def clean_company(self):
		company = self.cleaned_data.get('company', None)
		if company and company != self.association.company:
			raise forms.ValidationError(_('Unexpected error occurred. Request cannot be completed'))
		return company

	def save(self, commit=True):
		dissociation = super(DissociationForm, self).save(commit=False)
		dissociation.initiator = self.association.initiator
		if self.association.initiator == 'CO':
			dissociation.college = self.association.college
		else:
			dissociation.company = self.association.company
		if commit:
			dissociation.save()
		return dissociation
	
	class Meta:
		model = Dissociation
		fields = ['company', 'college', 'duration']
