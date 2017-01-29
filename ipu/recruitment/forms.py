from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from college.models import College, Programme, Stream
from company.models import Company
from recruitment.fields import ModelHashidChoiceField, ModelMultipleHashidChoiceField
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from student.models import Student
from material import *
import datetime, re

class AssociationForm(forms.ModelForm):
	layout = Layout() # fields vary according to the requester
	
	def __init__(self, *args, **kwargs):
		# The initiator's object should be sent as profile
		self.profile = kwargs.pop('profile')
		self.who = self.profile.__class__.__name__
		super(AssociationForm, self).__init__(*args, **kwargs)
		
		if self.who == 'College':
			del self.fields['college']
			company_queryset = Company.objects.exclude(pk__in = [d.company.pk for d in self.profile.dissociations.filter(duration__gte=datetime.date.today())])
			programmes_queryset = self.profile.get_programmes_queryset()
			self.fields['company'] = ModelHashidChoiceField(company_queryset, 'HASHID_COMPANY')
			self.fields['company'].widget.choices = self.get_zipped_choices(company_queryset, 'HASHID_COMPANY')
			# queryset argument can't be none because the object of chosen pk is retreived by filtering this qs in to_python
			# providing choices overwrites the choices
			
			self.fields['programme'] = ModelHashidChoiceField(programmes_queryset, 'HASHID_PROGRAMME') # I.
			# Could've used the below one also. Case Study:
			# I. Probably better as the filtering of Programme object is from the restricted domain of the college's programmes qs.
			# 	 i.e. clean_programme logic is automatically handled in this case
			# II. The to_python method will filter from all the Programmes. Thus, even if a programme not offered by the college is chosen,
			# 	  a legit programme object will be returned (although logically incorrect)
			#	  Therefore, the clean method's logic is a must in this case
#II			self.fields['programme'] = ModelHashidChoiceField(Programme.objects.all(), 'HASHID_PROGRAMME')
			
			self.fields['programme'].choices = self.get_zipped_choices(programmes_queryset, 'HASHID_PROGRAMME')
			self.fields['streams'] = ModelMultipleHashidChoiceField(Stream.objects.all(), 'HASHID_STREAM', help_text='Changes according to the Programme chosen')
			self.fields['streams'].choices = ()
			# Providing both choices as well as queryset because:
			# Queryset is required by to_python to filter the object of chosen pk from
			# Choices is required to render empty select list in html, otherwise by default select field values are rendered using the queryset given
			# Other option is to give empty queryset and no choices, but that would require you to pass
			# in the relevant qs in views.. But, it's highly error prone if forgetten
			self.fields['streams'].widget.attrs['disabled'] = 'disabled'
			self.layout = Layout(
				Fieldset('Association Details',
				Row('company'),
				Row('programme'),
				Row('streams'),
				Row(Span4('type'), Span8('salary')),
				Row('desc')
			))
		
		elif self.who == 'Company':
			del self.fields['company']
			college_queryset = College.objects.exclude(pk__in = [d.college.pk for d in self.profile.dissociations.filter(duration__gte=datetime.date.today())])
			self.fields['college'] = ModelHashidChoiceField(college_queryset, 'HASHID_COLLEGE')
			self.fields['college'].widget.choices = self.get_zipped_choices(college_queryset, 'HASHID_COLLEGE')
			self.fields['programme'].choices= ()
			self.fields['programme'] = ModelHashidChoiceField(Programme.objects.all(), 'HASHID_PROGRAMME')
			self.fields['programme'].widget.attrs['disabled'] = 'disabled'
			self.fields['streams'].choices= ()
			self.fields['streams'] = ModelMultipleHashidChoiceField(Stream.objects.all(), 'HASHID_STREAM')
			self.fields['streams'].widget.attrs['disabled'] = 'disabled'
			self.layout = Layout(
				Fieldset('Association Details',
				Row('college'),
				Row('programme'),
				Row('streams'),
				Row(Span4('type'), Span8('salary')),
				Row('desc')
			))
		
		else:
			raise ValidationError(_('Permission Denied. Only college or company can initiate association.'))

	def clean_streams(self):
		streams = self.cleaned_data['streams']
		if streams:
			college = self.profile if self.who == 'College' else self.cleaned_data['college']
			programme = self.cleaned_data.get('programme', None)
			if college and programme:
				for stream in streams:
					if not college.streams.filter(pk=stream.pk):
						raise forms.ValidationError(_('Stream %s is not offered by the college.' % (stream.name.__str__())))
					if not programme.streams.filter(pk=stream.pk):
						raise forms.ValidationError(_('Selected stream does not belong to the chosen programme.'))
		return self.cleaned_data['streams']
	
	def clean_programme(self):
		programme = self.cleaned_data.get('programme', None)
		college = self.profile if self.who == 'College' else self.cleaned_data.get('college', None)
		if programme and college and not college.get_programmes_queryset().filter(pk=programme.pk):
			raise forms.ValidationError(_('The selected programme is not offered by the college.'))
		return self.cleaned_data['programme']
	
	def clean(self):
		super(AssociationForm, self).clean()
		college = self.cleaned_data.get('college', None)
		company = self.cleaned_data.get('company', None)
		if self.who == 'College' and company:
			dissoc = Dissociation.objects.filter(college=self.profile, company=company, duration__gte=datetime.date.today())
			if dissoc:
				if dissoc[0].initiator == 'CO':
					raise ValidationError(_('Sorry, %s has temporarily blocked you from contacting it.' % (company.name.title())))
				else:
					raise ValidationError(_('You have blocked %s from contacting you. To unblock it, delete the dissociation.' % (company.name.title())))
		elif self.who == 'Company' and college:
			dissoc = Dissociation.objects.filter(college=college, company=self.profile, duration__gte=datetime.date.today())
			if dissoc:
				if dissoc[0].initiator == 'C':
					raise ValidationError(_('Sorry, %s has temporarily blocked you from contacting it.' % (college.name.title())))
				else:
					raise ValidationError(_('You have blocked %s from contacting you. To unblock it, delete the dissociation.' % (company.name.title())))
		return self.cleaned_data
	
	def save(self, commit=True, *args, **kwargs):
		association = super(AssociationForm, self).save(commit=False)
		if self.who == 'College':
			association.college = self.profile
			association.initiator = 'C'
		elif self.who == 'Company':
			association.company = self.profile
			association.initiator = 'CO'
		
		if commit:
			try:
				association.save()
			except IntegrityError as error:
				raise forms.ValidationError(_(error.__str__()))
			except ValidationError as error:
				raise forms.ValidationError(_('The desired association already exists.'))
		return association
		
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.name) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	class Meta:
		model = Association
		fields = ['college', 'company', 'type', 'programme', 'streams', 'salary', 'desc']
		'''
			Using help_texts for fields having custom form fields won't work because the custom classes are not powered with Meta functionality.
			The custom's parent class accepts help_text arg in its init method. Hence, making use of that instead of rewriting the whole Meta functionality.
		'''

class NewAssociationForm(forms.ModelForm):
	layout = Layout(
		Row('college'),
		Row('company'),
		Row('programme'),
		Row('streams'),
		Row(Span4('type'), Span8('salary')),
		Row('desc')
	)

	def __init__(self, *args, **kwargs):
		super(NewAssociationForm, self).__init__(*args, **kwargs)
		self.fields['streams'].widget.attrs['disabled'] = 'disabled'
		self.fields['streams'].queryset = Stream.objects.none()
#		self.fields['college'].queryset = College.objects.get(pk=1)
		self.fields['college'].widget.attrs['disabled'] = 'disabled'

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
