from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from college.models import College, Programme, Stream
from company.models import Company
from dummy_company.models import DummyCompany, DummySession
from recruitment.models import SelectionCriteria
from student.models import Student
from material import *
import datetime, re

class CreateDummyCompanyForm(forms.ModelForm):
	def save(self, college=None, commit=True, *args, **kwargs):
		if not college:
			raise ValidationError(_('College is required to create dummy company.'))
		dcompany = super(CreateDummyCompanyForm, self).save(commit=False)
		dcompany.college = college
		if commit:
			try:
				dcompany.save()
			except:
				raise forms.ValidationError(_('Error. Dummy Company with same name already exists.'))
		return dcompany

	class Meta:
		model = DummyCompany
		fields = ['name', 'website', 'details']

class ChooseDummyCompanyForm(forms.Form):
	dummy_company = forms.ModelChoiceField(label="Dummy Company", queryset=None , widget=forms.Select(), help_text=_("Choose Dummy Company To Edit"))

	def __init__(self, *args, **kwargs):
		self.college = kwargs.pop('college')
		super(ChooseDummyCompanyForm, self).__init__(*args, **kwargs)
#		self.fields['dummy_company'].queryset = self.college.dummy_companies.all()
		dcompanies = self.college.dummy_companies.values('name', 'pk')
		names_list = []; hashids_list = [];
		for dc in dcompanies:
			names_list.append(dc['name'])
			hashids_list.append(settings.HASHID_DUMMY_COMPANY.encode(dc['pk']))
		self.fields['dummy_company'].widget.choices = zip(hashids_list, names_list)

class EditDummyCompanyForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(EditDummyCompanyForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_DUMMY_COMPANY.encode(self.instance.pk)
		self.fields['name'].widget.attrs['readonly'] = True

	def clean_name(self):
		name = self.cleaned_data.get('name', None)
		if self.instance.name != name:
			raise forms.ValidationError(_('The name of the dummy company can\'t be changed.'))
		return name

	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))

	class Meta:
		model = DummyCompany
		fields = ['name', 'website', 'details']
		help_texts = {
			'name': _('Readonly. Name cannot be changed'),
		}

class CreateDummySessionForm(forms.ModelForm):
	layout = Layout(
		Fieldset('Assocation Details', Row(Span6('dummy_company'), Span6('programme')), Row(Span8('streams'), Span4('type'))),
		Fieldset('Placement Session Details', Row(Span5('salary'), Span7('application_deadline')), Row(Span6('status'), Span6('ended'))),
		Row('desc'),
	)
	def __init__(self, *args, **kwargs):
		self.college = kwargs.pop('college')
		super(CreateDummySessionForm, self).__init__(*args, **kwargs)
		self.fields['dummy_company'].queryset = self.college.dummy_companies.all()
		self.fields['programme'].queryset = self.college.get_programmes_queryset()
		self.fields['streams'].queryset = Stream.objects.none()
		self.fields['streams'].widget.attrs['disabled'] = 'disabled'
		
	def clean_dummy_company(self):
		college_dcompanies = self.college.dummy_companies.all()
		chosen_dcompany = self.cleaned_data.get('dummy_company', None)
		if chosen_dcompany and chosen_dcompany not in college_dcompanies:
			raise forms.ValidationError(_('You must choose a dummy company created by your college'))
		return chosen_dcompany

	def clean_programme(self):
		college_programmes = self.college.get_programmes_queryset()
		chosen_programme = self.cleaned_data.get('programme', None)
		if chosen_programme and chosen_programme not in college_programmes:
			raise ValidationError(_('You must choose a programme offered in your college'))
		return chosen_programme

	def clean_streams(self):
		chosen_programme = self.cleaned_data.get('programme', None)
		college_prog_streams = chosen_programme.streams.all()
		chosen_streams = self.cleaned_data.get('streams', None)
		if not chosen_streams:
			raise forms.ValidationError(_('You must choose a stream'))
		for stream in chosen_streams:
			if stream not in college_prog_streams:
				raise forms.ValidationError(_('Stream %s is not offered in your college. Please choose appropriate streams' % (stream.__str__())))
		return chosen_streams
	
	def clean_application_deadline(self):
		date = self.cleaned_data['application_deadline']
		if date and date <= datetime.date.today():
			raise forms.ValidationError(_('Please choose a date greater than today\'s'))
		return date

	class Meta:
		model = DummySession
		fields = ['dummy_company', 'programme', 'streams', 'type', 'salary', 'desc', 'status', 'application_deadline', 'ended']
		help_texts = {
			'streams': _('Stream options change according to Programme chosen.')
		}

class EditDummySessionForm(forms.ModelForm):
	def __init__(self, college=None, *args, **kwargs):
		super(EditDummySessionForm, self).__init__(*args, **kwargs)
		self.college = college

	def clean_students(self):
		students = self.cleaned_data.get('students', None)
		streams = self.instance.streams.all()
		if students:
			for student in students:
				if student.college != self.college or student.stream not in streams:
					raise forms.ValidationError(_('Student %s can\'t be added to this session.' % (student.profile.username)))
		return students

	class Meta:
		model = DummySession
		fields = ['students', 'application_deadline', 'status', 'desc', 'ended']

class CreateSelectionCriteriaForm(forms.ModelForm):
	
	layout = Layout(
			Fieldset( 'Selection Criteria',
				Row(Span8('years'), Span4('is_sub_back')),
				Row(Span6('tenth'), Span6('twelfth')),
				Row(Span4('graduation'), Span4('post_graduation'), Span4('doctorate')),
			)
		)

	def __init__(self, *args, **kwargs):
		self.max_year = kwargs.pop('max_year', 0)
		super(CreateSelectionCriteriaForm, self).__init__(*args, **kwargs)
		self.fields['years'].widget = forms.SelectMultiple(choices=(tuple(("%s"%i,"%s"%i) for i in range(0))))
		self.fields['years'].widget.attrs['disabled'] = 'disabled'
	
	def clean_years(self):
#		comma_separated_years = ','.join(self.cleaned_data['years'])    Performed in the views before creating form obj
		comma_separated_years = self.cleaned_data['years'].split('\'')[1:-1][0]
		if comma_separated_years == '':
			return ''
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
		
	class Meta:
		model = SelectionCriteria
		fields = ['years', 'is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']
		help_texts = {
			'years': _('Number of years changes according to Programme chosen.'),
		}