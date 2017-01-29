from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

class ModelHashidChoiceField(forms.ModelChoiceField):
	def __init__(self, queryset, hashid_name, *args, **kwargs):
		self.hashid = getattr(settings, hashid_name)
		super(ModelHashidChoiceField, self).__init__(queryset, *args, **kwargs)
	
	def to_python(self, value):
		try:
			if value:
				value = self.hashid.decode(value)[0]
		except:
			raise ValidationError(_('Error. Select a valid choice.'))
		value = super(ModelHashidChoiceField, self).to_python(value)
		return value

class ModelMultipleHashidChoiceField(forms.ModelMultipleChoiceField):
	def __init__(self, queryset, hashid_name, *args, **kwargs):
		self.hashid = getattr(settings, hashid_name)
		super(ModelMultipleHashidChoiceField, self).__init__(queryset, *args, **kwargs)
	# No need to overwrite to_python, but clean. Because MMCF calls custom run_validators
	# which in turn call clean method first, instead of to_python.
	"""
	def to_python(self, value):
		...
	"""
	def clean(self, value):
		if value:
			try:
				value = [self.hashid.decode(each)[0] for each in value]
			except:
				raise ValidationError(_('Error. Select a valid choice.'))
		return super(ModelMultipleHashidChoiceField, self).clean(value)
