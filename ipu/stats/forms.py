from django import forms
from .models import YearRecord

class StatsForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(StatsForm, self).__init__(*args, **kwargs)
		self.fields['college'].widget.choices = self.get_fullname_choices()
		self.fields['year'] = forms.ChoiceField(choices=(('', '----------'),))
		self.fields['year'].widget.attrs['disabled'] = True

	def get_fullname_choices(self):
		names, values = list(), list()
		names.append('-----------')
		values.append('')
		for college in self.fields['college'].queryset:
			name = college.name.title() + ('' if not college.alias else (' (' + college.alias + ')'))
			names.append(name)
			values.append(college.pk)
		return zip(values, names)
	
	class Meta:
		model = YearRecord
		fields = ['college', 'year']
