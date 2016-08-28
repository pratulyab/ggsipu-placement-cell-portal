from django import forms
from django.utils.translation import ugettext_lazy as _

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
	students = forms.MultipleChoiceField(label = "Select Students" , choices=options, widget=forms.SelectMultiple())
	message = forms.CharField(widget=forms.Textarea)

	class Meta:
		help_texts = {
			'message' : _("Message for the students."),
		}


#choice = forms.ModelChoiceField(queryset=MyChoices.Objects.all())