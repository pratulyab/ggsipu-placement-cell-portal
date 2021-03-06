from django import forms
from notification.models import Issue , IssueReply , Report , Notification , NotificationData
from django.utils.translation import ugettext_lazy as _
from account.tasks import send_mass_mail_task
from material import *
import logging

notificationLogger = logging.getLogger('notification')



class SelectStreamsForm(forms.Form):
	def __init__(self, *args , **kwargs):
		college = kwargs.pop('college',None)
		self.college = college
		super(SelectStreamsForm, self).__init__(*args , **kwargs)
		if college:
			self.fields['stream'].queryset = college.streams.all()

	
	stream = forms.ModelChoiceField(label = "Select Stream of the Students" ,queryset = None , widget=forms.SelectMultiple())
	

	class Meta:
		help_texts = {
			'stream' : _("Please select the Streams required."),
		}


class CreateNotificationForm(forms.Form):
	def __init__(self , *args , **kwargs):
		college = kwargs.pop('college',None)
		programme_to_year = kwargs.pop('programme_to_year' , None)
		self.programme_to_year = programme_to_year
		self.college = college
		super(CreateNotificationForm , self).__init__(*args , **kwargs)
		if college:
			self.fields['stream'].queryset = college.streams.all()

		for_list = list()
		year_list = list()
		year_fields = list()
		for i in range(len(programme_to_year)):
			for j in range(1, (int(programme_to_year[i]['year'])+1)):
				for_list.append(j)
				year_list.append("Year "+str(j))

			choices = zip(for_list,year_list)
			self.fields['select_year_%s' % programme_to_year[i]['code']] = forms.MultipleChoiceField(label = "Select Year For " + str(programme_to_year[i]['name']) , choices = choices, widget = forms.SelectMultiple())
			del for_list[:]
			del year_list[:]
			year_field = Row('select_year_%s' % programme_to_year[i]['code'])
			year_fields.append(year_field)
		
		self.layout = Layout(Fieldset('Selected Streams' , Row('stream')), 
					Fieldset('Select Year',
					*year_fields),
					Fieldset('Select Students' , Row(Span9('students') , Fieldset('', 'if_all'))),
					Fieldset('Message' ,Row('subject') , Row('message')),
					Fieldset('' ,  Row(Span3('if_email') , Span3('if_sms'))),
					Row(Span10('sms_message')))

	options = (
		(None , None),
		)	
	stream = forms.ModelChoiceField(label = "Select Stream of the Students" ,queryset = None , widget=forms.SelectMultiple())
	if_all = forms.BooleanField(label = "Notify All Students" , widget = forms.CheckboxInput())
	students = forms.MultipleChoiceField(label = "Select Students" , choices=options, widget=forms.SelectMultiple())
	subject = forms.CharField(label = "Subject" , max_length = 256 , required = True)
	message = forms.CharField(widget=forms.Textarea)
	if_email = forms.BooleanField(label = "Send E-Mail" , widget = forms.CheckboxInput())
	if_sms = forms.BooleanField(label = "Send SMS" , widget = forms.CheckboxInput())
	sms_message = forms.CharField(label = "Write SMS" , max_length = 155 , required = False , widget=forms.Textarea)

	class Meta:
		help_texts = {
			'message' : _("Message for the students."),
			'if_all' : _('All')
		}
'''

class CreateNotificationForm(forms.Form):	
	def __init__(self , *args , **kwargs):
		list_of_students = kwargs.pop('receive_list' , None)
		college = kwargs.pop('college',None)
		self.college = college
		self.list_of_students = list_of_students
		super(CreateNotificationForm , self).__init__(*args , **kwargs)
		if list_of_students:
			self.fields['students'].choices = list_of_students
		if college:
			self.fields['stream'].queryset = college.streams.all()
		
	

	options = (
		(None , None),
		)
	stream = forms.ModelChoiceField(label = "Select Stream of the Students" ,queryset = None , widget=forms.SelectMultiple())	
	if_all = forms.BooleanField(label = "Notify All Students" , widget = forms.CheckboxInput())
	students = forms.MultipleChoiceField(label = "Select Students" , choices=options, widget=forms.SelectMultiple())
	message = forms.CharField(widget=forms.Textarea)
	if_email = forms.BooleanField(label = "Send E-Mail" , widget = forms.CheckboxInput())
	if_sms = forms.BooleanField(label = "Send SMS" , widget = forms.CheckboxInput())
	class Meta:
		help_texts = {
			'message' : _("Message for the students."),
		}

	layout = Layout(Row('stream'), 
					Fieldset('' , Row(Span3('if_all') , Span9('students'))),
					
					Fieldset('' ,  Row('message'),
					Row(Span3('if_email') , Span3('if_sms')),
					))


	def get_year_fields(self):
		return_string = str()
		ls = []
		for i in range(len(self.programme_to_year)):
			ls.append(("'select_year_" + self.programme_to_year[i]['code'] + "',")[:-1])
		print (','.join(ls))
		return ls
	'''

class IssueForm(forms.ModelForm):
	def __init__(self , *args , **kwargs):
		self.user = kwargs.pop('user' , None)
		self.college = kwargs.pop('college' , None)
		super(IssueForm, self).__init__(*args, **kwargs)

	def clean_subject(self):
		subject = self.cleaned_data['subject']
		if subject and '\n' in subject:
			raise forms.ValidationError(_('New line is not allowed in subject field.'))
		return subject
		

	def save(self):
		form_instance = super(IssueForm, self).save(commit=False)
		form_instance.actor = self.user
		form_instance.college = self.college
		form_instance.save()
		return form_instance


	class Meta:
		model = Issue
		fields = ['issue_type', 'subject',  'message']
		widgets = {
		'message' : forms.Textarea,
		}


class IssueReplyForm(forms.ModelForm):
	def __init__(self , *args , **kwargs):
		self.faculty = kwargs.pop('faculty' , None)
		self.root_issue = kwargs.pop('root_issue' , None)
		super(IssueReplyForm , self).__init__(*args , **kwargs)

	def clean(self):
		super(IssueReplyForm , self).clean()
		reply = self.cleaned_data.get('reply' , None)
		return self.cleaned_data

	def save(self):
		form_instance = super(IssueReplyForm , self).save(commit = False)
		form_instance.root_issue = self.root_issue
		form_instance.solved_by = self.faculty.get_full_name()
		form_instance.solver_username = self.faculty.profile.username
		form_instance.save()
		return form_instance

	if_email = forms.BooleanField(label = "Send E-Mail" , widget = forms.CheckboxInput() , initial = False ,  required = False)
	class Meta:
		model = IssueReply
		fields = ['reply']
		widgets = {
		'reply' : forms.Textarea,
		}
		help_texts = {
		'reply' : "Your reply for the Issue."
		}

class NotifySessionStudentsForm(forms.Form):
	layout = Layout(
			Row('subject'),
			Row('message'),
			Fieldset('Choose at least one', Span6('notification'), Span6('mail')),#, Span4('sms')),
		)
	
	def __init__(self, *args, **kwargs):
		super(NotifySessionStudentsForm, self).__init__(*args, **kwargs)
		self.initial['notification'] = True
	
	subject = forms.CharField(max_length=256, required=True)
	message = forms.CharField(widget=forms.Textarea, required=True)
	notification = forms.BooleanField(label="Send Notification" , widget=forms.CheckboxInput(), required=False)
	mail = forms.BooleanField(label="Send e-mail" , widget=forms.CheckboxInput(), required=False)
	#sms = forms.BooleanField(label="Send SMS" , widget=forms.CheckboxInput(), required=False)

	def clean_subject(self):
		subject = self.cleaned_data['subject']
		if subject and '\n' in subject:
			raise forms.ValidationError(_('New line is not allowed in subject field.'))
		return subject

	def clean(self):
		data = self.cleaned_data
#		notification, mail, sms = data.get('notification', False), data.get('mail', False), data.get('sms', False)
		notification, mail = data.get('notification', False), data.get('mail', False)
		if not (notification or mail):# or sms):
			raise forms.ValidationError(_('You must choose at least one of the delivery methods'))
		return self.cleaned_data

	def notify_all(self, students , actor):
		if self.cleaned_data.get('mail'):
			student_pks = self.querysets_to_values(students.values('profile__pk') , 'profile__pk')
			student_enrolls = self.querysets_to_values(students.values('profile__username') , 'profile__username')
			subject = self.cleaned_data.get('subject' , None)
			message = self.cleaned_data.get('message' , None)
			send_mass_mail_task.delay(subject , message , student_pks)
			notificationLogger.info('Session E-Mail sent to %s' % (student_enrolls))

		if self.cleaned_data.get('notification'):
			subject = self.cleaned_data.get('subject' , None)
			message = self.cleaned_data.get('message' , None)
			student_enrolls = self.querysets_to_values(students.values('profile__username') , 'profile__username')
			notification_data_object = NotificationData.objects.create(subject = subject , message = message)
			for student in students:
				student_customeuser_object = student.profile
				Notification.objects.create(actor = actor, target = student_customeuser_object , notification_data = notification_data_object)
			notificationLogger.info('Session notification created for %s' % (student_enrolls))


	def querysets_to_values(self, queryset , key):
		result_list = list()
		for modal_instance in queryset:
			result_list.append(modal_instance[key])
		return result_list
#choice = forms.ModelChoiceField(queryset=MyChoices.Objects.all())

class ReportBugForm(forms.ModelForm):
	def __init__(self , *args , **kwargs):
		self.user = kwargs.pop('user' , None)
		super(ReportBugForm , self).__init__(*args , **kwargs)
		
	def save(self):
		form_instance = super(ReportBugForm , self).save(commit = False)
		if self.user.is_authenticated():
			form_instance.reported_by = self.user
		form_instance.save()
		return form_instance

	class Meta:
		model = Report
		fields = ('type' , 'message' , )
		widgets = {
				'message' : forms.Textarea,
			}

