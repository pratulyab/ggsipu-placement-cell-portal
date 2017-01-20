from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from college.models import College, Programme, Stream
from company.models import Company
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from student.models import Student
from material import *
import datetime, re

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
	layout = Layout(
		Row('college'),
		Row('company'),
		Row('programme'),
		Row('streams'),
		Row(Span4('type'), Span8('salary')),
		Row('desc')
	)

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
	
	def clean_streams(self):
		streams = self.cleaned_data['streams']
		company, college, type = self.cleaned_data['company'], self.cleaned_data['college'], self.cleaned_data['type']
		for stream in streams:
			if Association.objects.filter(company=company, college=college, type=type).filter(streams=stream):
				raise forms.ValidationError(_('Association already exists for stream %s' % (stream)))
		return self.cleaned_data['streams']

	def save(self, commit=True):
		association = super(AssociationForm, self).save(commit=False)
		if self.cname == 'College':
			association.college = self.initiator_profile
			association.initiator = 'C'
		elif self.cname == 'Company':
			association.company = self.initiator_profile
			association.initiator = 'CO'
		
		if commit:
			try:
				association.save()
			except IntegrityError as error:
				raise forms.ValidationError(_('The desired association already exists.'))
			except ValidationError as error:
				raise forms.ValidationError(_('The desired association already exists.'))
		return association
	
	class Meta:
		model = Association
		fields = ['college', 'company', 'type', 'programme', 'streams', 'salary', 'desc']

class SessionEditForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(SessionEditForm, self).__init__(*args, **kwargs)
		self.fields['students'].queryset = Student.objects.filter(college=self.instance.association.college, stream__in=self.instance.association.streams.all())
		self.initial['token'] = settings.HASHID_PLACEMENTSESSION.encode(self.instance.pk)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
	
	def clean_application_deadline(self):
		date = self.cleaned_data['application_deadline']
		if date and date <= datetime.date.today():
			raise forms.ValidationError(_('Please choose a date greater than today\'s'))
		return date
	
	class Meta:
		model = PlacementSession
		fields = ['students', 'status', 'application_deadline', 'ended']
	
class CreateSessionCriteriaForm(forms.ModelForm):
	layout = Layout(
			Row('application_deadline'),
#			Row(Span8('current_year'), Span4('is_sub_back')),
			Row(Span8('years'), Span4('is_sub_back')),
			Row(Span6('tenth'), Span6('twelfth')),
			Row(Span4('graduation'), Span4('post_graduation'), Span4('doctorate')),
		)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
	application_deadline = forms.DateField(label=_('Application Deadline'), help_text=_("Choose last date for students to apply. If no event is scheduled for now, choose an arbitrary future date."),input_formats=['%d %B, %Y','%d %B %Y','%d %b %Y','%d %b, %Y'])
	years = forms.CharField(label=_('Which year students may apply'), max_length=30) # Max length is 30 because "['1', '2', '3', '4', '5', '6']" is passed
	
	def __init__(self, *args, **kwargs):
		self.association = kwargs.pop('association')
		self.max_year = int(self.association.programme.years)
		super(CreateSessionCriteriaForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_ASSOCIATION.encode(self.association.pk)
		self.fields['years'].widget = forms.SelectMultiple(choices=(tuple(("%s"%i,"%s"%i) for i in range(1,self.max_year+1))))

	def clean_application_deadline(self):
		date = self.cleaned_data['application_deadline']
		if date and date <= datetime.date.today():
			raise forms.ValidationError(_('Please choose a date greater than today\'s'))
		return date
	
	def clean_years(self):
#		comma_separated_years = ','.join(self.cleaned_data['years'])    Performed in the views before creating form obj
		comma_separated_years = self.cleaned_data['years'].split('\'')[1:-1][0]
		if not re.match(r'^([1-6](,[1-6])*)?$', comma_separated_years):
			raise forms.ValidationError(_('Invalid years provided.'))
#		To validate against the maximum year of the programme
		try:
			chosen_years = [int(y) for y in comma_separated_years.split(',')]
		except: # To handle NameError, TypeError in case of invalid int type conversion
			raise forms.ValidationError(_('Please provide valid years.'))
		if max(chosen_years) > self.max_year:
			raise forms.ValidationError(_('Please choose valid year(s). Maximum year value for this programme is %s.' % self.max_year))
		return comma_separated_years
		
	"""
# Not overriding the save method because get_or_create has to be used in views instead of saving here and then catching IntegrityError (Duplicate Entry)
	"""

	class Meta:
		model = SelectionCriteria
		fields = ['is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']

class CriteriaEditForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.session = kwargs.pop('session')
		self.association = self.session.association
		self.max_year = int(self.association.programme.years)
		super(CriteriaEditForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_PLACEMENTSESSION.encode(self.session.pk)
		self.fields['years'].widget = forms.SelectMultiple(choices=(tuple(("%s"%i,"%s"%i) for i in range(1,self.max_year+1))))
		self.initial['years'] = self.instance.years.split(',')
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
	years = forms.CharField(label=_('Which year students may apply'), max_length=30) # # # # # #
	
	def clean_years(self):
		comma_separated_years = self.cleaned_data['years'].split('\'')[1:-1][0]
		if not re.match(r'^([1-6](,[1-6])*)?$', comma_separated_years):
			raise forms.ValidationError(_('Invalid years provided.'))
		try:
			chosen_years = [int(y) for y in comma_separated_years.split(',')]
		except:
			raise forms.ValidationError(_('Please provide valid years.'))
		if max(chosen_years) > self.max_year:
			raise forms.ValidationError(_('Please choose valid year(s). Maximum year value for this programme is %s.' % self.max_year))
		return comma_separated_years
		
	class Meta:
		model = SelectionCriteria
		fields = ['is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']

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
			try:
				dissociation.save()
			except IntegrityError as error:
				raise forms.ValidationError(_('Error occurred.'))
			except ValidationError as error:
				raise forms.ValidationError(_('Error occurred.'))
		return dissociation
	
	class Meta:
		model = Dissociation
		fields = ['company', 'college', 'duration']
