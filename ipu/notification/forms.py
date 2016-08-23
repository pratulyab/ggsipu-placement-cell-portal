from django import forms
from django.utils.translation import ugettext_lazy as _

class CreateNotificationForm(forms.Form):
	def __init__(self, *args , **kwargs):
		college = kwargs.pop('college',None)
		self.college = college
		super(CreateNotificationForm, self).__init__(*args , **kwargs)
		if college:
			self.fields['stream'].queryset = college.streams.all()

	options = (
		("None" , "None"),
		)

	stream = forms.ModelChoiceField(label = "Select Stream" ,queryset = None , widget=forms.CheckboxSelectMultiple())
	students = forms.MultipleChoiceField(label = "Select Students" , choices=options, widget=forms.CheckboxSelectMultiple())
	message = forms.CharField(widget=forms.Textarea)

	class Meta:
		help_texts = {
			'stream' : _("Please select the Streams required."),
			'message' : _("Message for the students.")
		}



#choice = forms.ModelChoiceField(queryset=MyChoices.Objects.all())