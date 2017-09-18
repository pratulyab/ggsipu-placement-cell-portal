from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.tasks import send_mass_mail_task
from college.models import College, Programme, Stream
from company.models import Company
from dummy_company.models import DummyCompany, DummySession
from notification.models import Notification
from recruitment.fields import ModelHashidChoiceField, ModelMultipleHashidChoiceField
from recruitment.models import SelectionCriteria
from student.models import Student
from material import *
import datetime, re, logging

dummyLogger = logging.getLogger('dummy')

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
#		self.fields['dummy_company'].queryset = self.college.dummy_companies.all()
		dcompany_queryset = self.college.dummy_companies.all()
		self.fields['dummy_company'] = ModelHashidChoiceField(dcompany_queryset, 'HASHID_DUMMY_COMPANY')
		self.fields['dummy_company'].widget.choices = self.get_zipped_choices(dcompany_queryset, 'HASHID_DUMMY_COMPANY')
		programmes_queryset = self.college.get_programmes_queryset()
		self.fields['programme'] = ModelHashidChoiceField(programmes_queryset, 'HASHID_PROGRAMME')
		self.fields['programme'].choices = self.get_zipped_choices(programmes_queryset, 'HASHID_PROGRAMME')
		self.fields['streams'] = ModelMultipleHashidChoiceField(Stream.objects.all(), 'HASHID_STREAM', help_text='Changes according to the Programme chosen')
		self.fields['streams'].choices = ()
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
	
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.name) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)

	class Meta:
		model = DummySession
		fields = ['dummy_company', 'programme', 'streams', 'type', 'salary', 'desc', 'status', 'application_deadline', 'ended']
		help_texts = {
			'streams': _('Stream options change according to Programme chosen.')
		}
'''
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
'''
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


class ManageDummySessionStudentsForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.students_queryset = kwargs.get('instance').students.all()
		self.choices = self.get_zipped_choices(self.students_queryset, 'HASHID_STUDENT')
		kwargs.update(initial={'students': [c[0] for i,c in enumerate(self.choices) if i]})
		super(ManageDummySessionStudentsForm, self).__init__(*args, **kwargs)
		self.fields['students'] = ModelMultipleHashidChoiceField(self.students_queryset, 'HASHID_STUDENT', help_text=_('CAUTION: Students can only be removed from the list. Removed students will be notified.'), required=False)
		self.fields['students'].choices = self.get_zipped_choices(self.students_queryset, 'HASHID_STUDENT')
		self.initial['token'] = settings.HASHID_DUMMY_SESSION.encode(self.instance.pk)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))

	def notify_disqualified_students(self, actor):
		shortlisted_pks = [s['pk'] for s in self.cleaned_data['students'].values('pk')]
#		disqualified = self.students_queryset.exclude(pk__in=shortlisted_pks) Somehow this doesn't work _._
		original_students_pks = [s.pk for s in self.students_queryset]
		disqualified_pks = set(original_students_pks).difference(set(shortlisted_pks))
		disqualified = Student.objects.filter(pk__in=disqualified_pks)
		self.disqualified = disqualified
		student_disq_usernames = ','.join([s['profile__username'] for s in disqualified.values('profile__username')])
		message = "Sorry, your involvement in the %s session by %s was till here only!\
					\nThanks for showing your interest.\
					\nBest of luck for your future." % ("job" if self.instance.type == 'J' else "internship", self.instance.dummy_company.name)
		for student in disqualified:
			Notification.objects.create(actor=actor, target=student.profile, message=message)
		# send mass email
		subject = '%s session with %s' % ('Internship' if self.instance.type == 'I' else 'Job', self.instance.dummy_company.name)

		disqualified_user_pks = [u['profile__pk'] for u in disqualified.values('profile__pk')]
		send_mass_mail_task.delay(subject, message, disqualified_user_pks)
#		send_mass_mail_task.delay(subject, message, list(disqualified_pks))
		# LOG
		dummyLogger.info('%s - Students disqualified %s - [DS: %d]' % (actor.username, student_disq_usernames, self.instance.pk))
		# # #
		
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append("%s (%s)" % (q.get_full_name(), q.profile.username)) # for STUDENT
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	class Meta:
		model = DummySession
		fields = ['students']


class EditDummySessionForm(forms.ModelForm):
	layout = Layout(
			Row(Span6('application_deadline'), Span6('salary')),
			Row(Span8('status'), Span4('ended')),
			Row('desc')
		)
	def __init__(self, *args, **kwargs):
		super(EditDummySessionForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_DUMMY_SESSION.encode(self.instance.pk)
		self.initial['salary'] = self.instance.salary
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
#	salary = forms.DecimalField(max_digits=4, decimal_places=2, min_value=Decimal('0'), help_text=_('The other party will be notified about the changes made.'))
	
	def clean_application_deadline(self):
		date = self.cleaned_data['application_deadline']
		if date and date <= datetime.date.today() and 'application_deadline' in self.changed_data:
			raise forms.ValidationError(_('Please choose a date greater than today\'s'))
		return date

	def should_notify_students(self):
		if 'ended' in self.changed_data and self.cleaned_data['ended'] and self.cleaned_data['application_deadline'] < datetime.date.today():
			return True
		return False

	def notify_selected_students(self, actor):
		if not self.instance.students.exists():
			return
		dsession = self.instance
		message = "Congratulations! "
		if dsession.type == 'J':
			message += "You have been placed at %s. " % (dsession.dummy_company.name.title())
		else:
			message += "You have grabbed the internship at %s. " % (dsession.dummy_company.name.title())
		students = self.instance.students.all()
		student_usernames = ','.join([s['profile__username'] for s in students.values('profile__username')])
		for student in students:
			Notification.objects.create(actor=actor, target=student.profile, message=message)
		send_mass_mail_task.delay("Congratulations!", message, [s['profile__pk'] for s in students.values('profile__pk')])
		# Log
		dummyLogger.info('%s - Students selected %s - [DS: %d]' % (actor.username, student_usernames, self.instance.pk))
		# # #
	
	class Meta:
		model = DummySession
		fields = ['salary', 'application_deadline', 'status', 'desc', 'ended']
		help_texts = {
			'salary': _('The other party will be notified about the changes made.'),
		}


class EditDCriteriaForm(forms.ModelForm):
	layout = Layout(
			Row(Span8('years'), Span4('is_sub_back')),
			Row(Span6('tenth'), Span6('twelfth')),
			Row(Span4('graduation'), Span4('post_graduation'), Span4('doctorate')),
	)

	def __init__(self, *args, **kwargs):
		self.dsession = kwargs.pop('dsession') # Required because instance will be SelectionCriteria
		super(EditDCriteriaForm, self).__init__(*args, **kwargs)
		self.max_year = int(self.dsession.programme.years)
		self.initial['token'] = settings.HASHID_DUMMY_SESSION.encode(self.dsession.pk)
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
	
	def save(self, commit=True, *args, **kwargs):
		# Won't be calling model form's save method
		data = self.cleaned_data
		criterion, created = SelectionCriteria.objects.get_or_create(years=data['years'], is_sub_back=data['is_sub_back'], tenth=data['tenth'], twelfth=data['twelfth'], graduation=data['graduation'], post_graduation=data['post_graduation'], doctorate=data['doctorate'])
		return criterion
	
	class Meta:
		model = SelectionCriteria
		fields = ['is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']

class DummySessionFilterForm(forms.Form):
	def __init__(self, *args, **kwargs):
		self.college = kwargs.pop('college')
		super(DummySessionFilterForm, self).__init__(*args, **kwargs)
		dcompany_queryset = self.college.dummy_companies.all()
		self.fields['dummy_company'] = ModelMultipleHashidChoiceField(dcompany_queryset, 'HASHID_DUMMY_COMPANY', required=False)
		self.fields['dummy_company'].choices = self.get_zipped_choices(dcompany_queryset, 'HASHID_DUMMY_COMPANY')
		TYPE_CHOICES = (('', 'Choose one'), DummySession.PLACEMENT_TYPE[0], DummySession.PLACEMENT_TYPE[1])
		self.fields['type'] = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
		self.fields['ended'] = forms.BooleanField(required=False)
		self.fields['ended'].label = 'Has ended'

	def get_filtered_dsessions(self):
		dcompany = self.cleaned_data.get('dummy_company', None)
		type =  self.cleaned_data.get('type', '')
		dsessions = DummySession.objects.filter(dummy_company__college=self.college)
		if type:
			dsessions = dsessions.filter(type=type)
		if dcompany:
			dsessions = dsessions.filter(dummy_company__pk__in=[c.pk for c in dcompany])
		dsessions = dsessions.filter(ended=self.cleaned_data.get('ended', False))
		return dsessions
			
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.name) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
