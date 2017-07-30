from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.tasks import send_mass_mail_task
from college.models import College, Programme, Stream
from company.models import Company
from notification.models import Notification
from recruitment.fields import ModelHashidChoiceField, ModelMultipleHashidChoiceField
from recruitment.models import Association, PlacementSession, Dissociation, SelectionCriteria
from student.models import Student
from datetime import date
from decimal import Decimal
from material import *
import datetime, re, logging

collegeLogger = logging.getLogger('college')
companyLogger = logging.getLogger('company')
recruitmentLogger = logging.getLogger('recruitment')

class AssociationForm(forms.ModelForm):
	layout = Layout() # fields vary according to the requester
	
	def __init__(self, *args, **kwargs):
		# The initiator's object should be sent as profile
		self.profile = kwargs.pop('profile')
		self.who = self.profile.__class__.__name__
		super(AssociationForm, self).__init__(*args, **kwargs)
		self.fields['desc'].widget.attrs['placeholder'] = 'Description about the placement. If you want to share some attachments, please contact the respective college.'
		self.fields['salary'].help_text = 'This cannot be changed later. Please be wary of what you enter.'
		if self.who == 'College':
			del self.fields['college']
#			company_queryset = Company.objects.exclude(pk__in = [d.company.pk for d in self.profile.dissociations.filter(duration__gte=datetime.date.today())])
			company_queryset = Company.objects.exclude(pk__in = [d['company__pk'] for d in self.profile.dissociations.filter(initiator='CO').values('company__pk')])
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
#			college_queryset = College.objects.exclude(pk__in = [d.college.pk for d in self.profile.dissociations.filter(duration__gte=datetime.date.today())])
			college_queryset = College.objects.exclude(pk__in = [d['college__pk'] for d in self.profile.dissociations.filter(initiator='C').values('college__pk')])
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

	def can_make_requests(self):
		''' A check to ensure that an unwarranted company doesn't create more than 5 pending requests.
			Given that it has no record of sessions.
			Therefore, a potential troublemaker.
			No need to limit the college's requests, because colleges will always be warranted.
		'''
		if self.who == 'Company':
			associations = self.profile.associations
			if associations.count() >= 5 and not associations.filter(approved=True).exists():
				return False
		return True
	
	def clean(self):
		super(AssociationForm, self).clean()
		college = self.cleaned_data.get('college', None)
		company = self.cleaned_data.get('company', None)
		if self.who == 'College' and company:
#			dissoc = Dissociation.objects.filter(college=self.profile, company=company, duration__gte=datetime.date.today())
			dissoc = Dissociation.objects.filter(college=self.profile, company=company)
			if dissoc:
				if dissoc[0].initiator == 'CO':
					raise ValidationError(_('Sorry, %s has temporarily blocked you from contacting them.' % (company.name.title())))
				else:
					raise ValidationError(_('You have blocked %s from contacting you. To send request, unblock them.' % (company.name.title())))
		elif self.who == 'Company' and college:
#			dissoc = Dissociation.objects.filter(college=college, company=self.profile, duration__gte=datetime.date.today())
			dissoc = Dissociation.objects.filter(college=college, company=self.profile)
			if dissoc:
				if dissoc[0].initiator == 'C':
					raise ValidationError(_('Sorry, %s has temporarily blocked you from contacting them.' % (college.name.title())))
				else:
					raise ValidationError(_('You have blocked %s from contacting you. To send request, unblock them.' % (company.name.title())))
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
			names.append(q.name if not hasattr(q, 'corporate_code') else ("%s [%s]" % (q.name, q.corporate_code))) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	class Meta:
		model = Association
		fields = ['college', 'company', 'type', 'programme', 'streams', 'salary', 'desc']
		'''
			Using help_texts for fields having custom form fields won't work because the custom classes are not powered with Meta functionality.
			The custom's parent class accepts help_text arg in its init method. Hence, making use of that instead of rewriting the whole Meta functionality.
		'''

class CreateSessionCriteriaForm(forms.ModelForm):
	layout = Layout(
			Row('application_deadline'),
#			Row(Span8('current_year'), Span4('is_sub_back')),
			Row(Span8('years'), Span4('is_sub_back')),
			Row(Span6('tenth'), Span6('twelfth')),
			Row(Span4('graduation'), Span4('post_graduation'), Span4('doctorate')),
		)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
	application_deadline = forms.DateField(label=_('Application Deadline'), help_text=_("This can be changed later. If no event is scheduled for now, choose an arbitrary future date."),input_formats=['%d %B, %Y','%d %B %Y','%d %b %Y','%d %b, %Y'])
	years = forms.CharField(label=_('Which year students may apply'), max_length=30) # Max length is 30 because "['1', '2', '3', '4', '5', '6']" is passed
	
	def __init__(self, *args, **kwargs):
		self.association = kwargs.pop('association')
		self.max_year = int(self.association.programme.years)
		super(CreateSessionCriteriaForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_ASSOCIATION.encode(self.association.pk)
		self.fields['years'].widget = forms.SelectMultiple(choices=(tuple(("%s"%i,"%s"%i) for i in range(1,self.max_year+1))))
		self.fields['application_deadline'].widget.attrs['placeholder'] = 'Choose last date for students to apply'

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
		
	class Meta:
		model = SelectionCriteria
		fields = ['is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']


class EditCriteriaForm(forms.ModelForm):
	FIELDS_VERBOSE_NAME = {
		'is_sub_back': 'whether students with subject back(s) are allowed',
		'years': 'which year students are allowed',
	}

	layout = Layout(
			Row(Span8('years'), Span4('is_sub_back')),
			Row(Span6('tenth'), Span6('twelfth')),
			Row(Span4('graduation'), Span4('post_graduation'), Span4('doctorate')),
	)

	def __init__(self, *args, **kwargs):
		self.session = kwargs.pop('session') # Required because instance will be SelectionCriteria
		super(EditCriteriaForm, self).__init__(*args, **kwargs)
		self.max_year = int(self.session.association.programme.years)
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

	def notify_other_party(self, actor, target, link):
		if self.changed_data:
			# Log
			recruitmentLogger.info('%s updated %s [Session: %d]' % (actor.username, ','.join(self.changed_data), self.session.pk))
			# # #
			changed_fields = []
			marks_fields = []
			for field in self.changed_data:
				if field in self.FIELDS_VERBOSE_NAME:
					changed_fields.insert(0, self.FIELDS_VERBOSE_NAME[field])
				else:
					marks_fields.append(field)
			if marks_fields:
				changed_fields.append('marks requirements for %s' % (','.join(marks_fields)))
			message = '%s updated %s for <a href="%s">this </a> placement session.' % (actor, ', '.join(changed_fields), link)
			Notification.objects.create(actor=actor, target=target, message=message)
	
	def save(self, commit=True, *args, **kwargs):
		# Won't be calling model form's save method
		data = self.cleaned_data
		criterion, created = SelectionCriteria.objects.get_or_create(years=data['years'], is_sub_back=data['is_sub_back'], tenth=data['tenth'], twelfth=data['twelfth'], graduation=data['graduation'], post_graduation=data['post_graduation'], doctorate=data['doctorate'])
		return criterion
	
	class Meta:
		model = SelectionCriteria
		fields = ['is_sub_back','tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']


class EditSessionForm(forms.ModelForm):
	FIELDS_VERBOSE_NAME = {
		'ended': 'whether the session has ended',
		'application_deadline': 'Application Deadline',
		'status': 'Status',
		'salary': 'Salary Offered',
		'desc': 'Placement Details'
	}
	layout = Layout(
			Row(Span6('application_deadline')), #Span6('salary')),
			Row(Span8('status'), Span4('ended')),
			Row('desc')
		)

	def __init__(self, *args, **kwargs):
		super(EditSessionForm, self).__init__(*args, **kwargs)
		self.initial['token'] = settings.HASHID_PLACEMENTSESSION.encode(self.instance.pk)
		self.initial['salary'] = self.instance.association.salary
		self.fields['desc'].widget.attrs['placeholder'] = 'Description about the placement. If you want to share some attachments, please contact the respective college.'
		self.initial['desc'] = self.instance.association.desc
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))
	desc = forms.CharField(label='Placement Details',widget=forms.Textarea, required=False)
#	salary = forms.DecimalField(max_digits=4, decimal_places=2, min_value=Decimal('0'), help_text=_('The other party will be notified about the changes made.'))
	
	def clean_application_deadline(self):
		date = self.cleaned_data['application_deadline']
		if date and date <= datetime.date.today() and 'application_deadline' in self.changed_data:
			raise forms.ValidationError(_('Please choose a date greater than today\'s'))
		return date

	def notify_other_party(self, actor, target, link):
		if self.changed_data:
			# Log
			recruitmentLogger.info('%s updated %s [Session: %d]' % (actor.username, ','.join(self.changed_data), self.instance.pk))
			# # #
			changed_fields = []
			for field in self.changed_data:
				if field == 'ended':
					changed_fields.insert(0, (self.FIELDS_VERBOSE_NAME[field]))
				else:
					changed_fields.append(self.FIELDS_VERBOSE_NAME[field])
			message = '%s updated %s for <a href="%s">this</a> placement session.' % (actor, ', '.join(changed_fields), link)
			Notification.objects.create(actor=actor, target=target, message=message)

	def should_notify_students(self):
		if 'ended' in self.changed_data and self.cleaned_data['ended'] and self.cleaned_data['application_deadline'] < date.today():
			return True
		return False

	def notify_selected_students(self, actor):
		association = self.instance.association
		message = "Congratulations! "
		if association.type == 'J':
			message += "You have been placed at %s. " % (association.company.name.title())
		else:
			message += "You have grabbed the internship at %s. " % (association.company.name.title())
		students = self.instance.students.all()
		student_usernames = ','.join([s['profile__username'] for s in students.values('profile__username')])
		for student in students:
			Notification.objects.create(actor=actor, target=student.profile, message=message)
		send_mass_mail_task.delay("Congratulations!", message, [s['profile__pk'] for s in students.values('profile__pk')])
		# Log
		recruitmentLogger.info('%s - Students selected %s - [S: %d]' % (actor.username, student_usernames, self.instance.pk))
		# # #
	
	class Meta:
		model = PlacementSession
		fields = ['application_deadline', 'status', 'ended']


class ManageSessionStudentsForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.students_queryset = kwargs.get('instance').students.all()
		self.choices = self.get_zipped_choices(self.students_queryset, 'HASHID_STUDENT')
		kwargs.update(initial={'students': [c[0] for i,c in enumerate(self.choices) if i]})
		super(ManageSessionStudentsForm, self).__init__(*args, **kwargs)
		self.fields['students'] = ModelMultipleHashidChoiceField(self.students_queryset, 'HASHID_STUDENT', help_text=_('CAUTION: Students can only be removed from the list. Removed students will be notified.'))
		self.fields['students'].choices = self.get_zipped_choices(self.students_queryset, 'HASHID_STUDENT')
#		self.fields['students'].initial = (settings.HASHID_STUDENT.encode(s.pk) for s in self.students_queryset)
#		Why wouldn't this work? Passing initial to MMHC's super isn't working either
		self.initial['token'] = settings.HASHID_PLACEMENTSESSION.encode(self.instance.pk)
	
	token = forms.CharField(widget=forms.HiddenInput(attrs={'name': 'token', 'readonly': True}))

	def notify_disqualified_students(self, actor):
		students = self.cleaned_data['students'].values('pk')
		shortlisted_pks = [s['pk'] for s in students]
		original_students_pks = [s.pk for s in self.students_queryset]
		disqualified_pks = set(original_students_pks).difference(set(shortlisted_pks))
#		disqualified = self.students_queryset.exclude(pk__in=shortlisted_pks) Somehow this isn't working __-__
		disqualified = Student.objects.filter(pk__in=disqualified_pks)
		self.disqualified = disqualified
		student_disq_usernames = ','.join([s['profile__username'] for s in disqualified.values('profile__username')])
		message = "Sorry, your involvement in the placement session with %s was till here only!\
					\nThanks for showing your interest.\
					\nBest of luck for your future endeavours." % (self.instance.association.company.name)
		for student in disqualified:
			Notification.objects.create(actor=actor, target=student.profile, message=message)
		
		# send mass email
		association = self.instance.association
		subject = '%s session with %s' % ('Internship' if association.type == 'I' else 'Job', self.association.company.name)
		
		send_mass_mail_task.delay(subject, message, disqualified_pks)

		# Log
		recruitmentLogger.info('%s - Students disqualified %s - [S: %d]' % (actor.username, student_disq_usernames, self.instance.pk))
		# # #
		
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.profile.username) # for STUDENT
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	class Meta:
		model = PlacementSession
		fields = ['students']

class SessionFilterForm(forms.Form):

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		self.who = self.profile.__class__.__name__
		super(SessionFilterForm, self).__init__(*args, **kwargs)
		
		if self.who == 'College':
			company_queryset = Company.objects.filter(pk__in = [a['company__pk'] for a in self.profile.associations.values('company__pk')])
			self.fields['company'] = ModelMultipleHashidChoiceField(company_queryset, 'HASHID_COMPANY', required=False)
			self.fields['company'].choices = self.get_zipped_choices(company_queryset, 'HASHID_COMPANY')
		elif self.who == 'Company':
			college_queryset = College.objects.filter(pk__in = [a['college__pk'] for a in self.profile.associations.values('college__pk')])
			self.fields['college'] = ModelMultipleHashidChoiceField(college_queryset, 'HASHID_COLLEGE', required=False)
			self.fields['college'].choices = self.get_zipped_choices(college_queryset, 'HASHID_COLLEGE')
		else:
			raise ValidationError(_('Permission Denied.'))
		
		TYPE_CHOICES = (('', 'Choose one'), Association.PLACEMENT_TYPE[0], Association.PLACEMENT_TYPE[1])
		self.fields['type'] = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
		self.fields['has_ended'] = forms.BooleanField(required=False)

	def get_filtered_sessions(self):
		company = self.cleaned_data.get('company', None)
		college = self.cleaned_data.get('college', None)
		associations = self.profile.associations.all()
		type =  self.cleaned_data.get('type', '')
		if type:
			associations = associations.filter(type=type)
		if self.who == 'College':
			company = self.cleaned_data.get('company', None)
			if company:
				associations = associations.filter(company__pk__in=[c.pk for c in company])
		else:
			college = self.cleaned_data.get('college', None)
			if college:
				associations = associations.filter(college__pk__in=[c.pk for c in college])
		sessions = PlacementSession.objects.filter(association__pk__in=[a.pk for a in associations], ended=self.cleaned_data.get('has_ended', False))
		return sessions
			
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.name) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)

class DeclineForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.association = kwargs.pop('association')
		super(DeclineForm, self).__init__(*args, **kwargs)
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
		# no super save call because association already exists in db
		association = self.association
		association.initiator = self.association.initiator
		if self.association.initiator == 'CO':
			association.college = self.association.college
		else:
			association.company = self.association.company
		association.approved = False
		association.decline_message = self.cleaned_data.get('decline_message', '')
		if commit:
			try:
				association.save()
			except IntegrityError as error:
				raise forms.ValidationError(_('Error occurred.'))
			except ValidationError as error:
				raise forms.ValidationError(_('Error occurred.'))
		return association
	
	class Meta:
		model = Association
		fields = ['company', 'college', 'decline_message']
		help_texts = {
			'college': 'Readonly. Cannot be edited',
			'company': 'Readonly. Cannot be edited',
		}

class DissociationForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		self.profile = kwargs.pop('profile')
		self.initiator = kwargs.pop('user_type')
		super(DissociationForm, self).__init__(*args, **kwargs)
		if self.initiator == 'C':
			del self.fields['college']
			company_queryset = Company.objects.exclude(pk__in=[d['company__pk'] for d in self.profile.dissociations.values('company__pk')])
			self.fields['company'] = ModelHashidChoiceField(company_queryset, 'HASHID_COMPANY')
			self.fields['company'].widget.choices = self.get_zipped_choices(company_queryset, 'HASHID_COMPANY')
		else:
			del self.fields['company']
			college_queryset = College.objects.exclude(pk__in=[d['college__pk'] for d in self.profile.dissociations.values('college__pk')])
			self.fields['college'] = ModelHashidChoiceField(college_queryset, 'HASHID_COLLEGE')
			self.fields['college'].widget.choices = self.get_zipped_choices(college_queryset, 'HASHID_COLLEGE')
	
	def save(self, commit=True):
		dissociation = super(DissociationForm, self).save(commit=False)
		dissociation.initiator = self.initiator
		if self.initiator == 'CO':
			dissociation.company = self.profile
		else:
			dissociation.college = self.profile
		if commit:
			try:
				dissociation.save()
			except (IntegrityError,ValidationError) as error:
				raise forms.ValidationError(_('You have already blocked the user.'))
		return dissociation

	def delete_all_pending_associations(self):
		dissociation = self.instance
		associations = Association.objects.filter(college=dissociation.college, company=dissociation.company).filter(~Q(approved=True))
		associations_pks = ','.join([str(a.pk) for a in associations])
		associations.delete()
		# LOG
		recruitmentLogger.info('%s Pending Associations Deleted %s - [D: %d]' % \
				((self.instance.college.name if self.instance.initiator == 'C' else self.instance.company.name), associations_pks, self.instance.pk))
		# # #
	
	@staticmethod
	def get_zipped_choices(queryset, hashid_name):
		names, hashids = list(), list()
		names.append('---------'); hashids.append('') # default
		for q in queryset:
			names.append(q.name if not hasattr(q, 'corporate_code') else ("%s [%s]" % (q.name, q.corporate_code))) # COLLEGE, COMPANY, PROGRAMME, STREAM use 'name'
			hashids.append(getattr(settings, hashid_name).encode(q.pk))
		return zip(hashids, names)
	
	class Meta:
		model = Dissociation
		fields = ['company', 'college', 'reason']
