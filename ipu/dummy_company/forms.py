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

class CreateDummySessionFormI(forms.ModelForm):
	def __init__(self, college=None, *args, **kwargs):
		super(CreateDummySessionFormI, self).__init__(*args, **kwargs)
		self.college = college
		self.fields['dummy_company'].queryset = college.dummy_companies.all()
		self.fields['programme'].queryset = college.get_programmes_queryset()
		self.fields['streams'].queryset = college.streams.all()
		
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

	class Meta:
		model = DummySession
		fields = ['dummy_company', 'programme', 'streams', 'type', 'salary', 'desc', 'status', 'application_deadline', 'ended']


class CreateDummySessionFormII(forms.ModelForm):
	def __init__(self, college=None, *args, **kwargs):
		super(CreateDummySessionFormII, self).__init__(*args, **kwargs)
		self.college = college
		self.fields['dummy_company'].queryset = college.dummy_companies.all()
		self.fields['programme'].queryset = college.get_programmes_queryset()
		self.fields['streams'].queryset = programme.streams.all()
		
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
		chosen_programme = self.cleaned_data('programme', None)
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

	def save(self, criterion, commit=True, *args, **kwargs):
		dsession = super(CreateDummySessionFormII, self).save(commit=False)
		dsession.selection_criteria = criterion
		if commit:
			dsession.save()
		return dsession

	class Meta:
		model = DummySession
		fields = ['dummy_company', 'programme', 'streams', 'type', 'salary', 'desc', 'status', 'application_deadline', 'ended']

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
