from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from faculty.models import Faculty

class FacultySignupForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(FacultySignupForm, self).__init__(*args, **kwargs)
		self.fields['email'].required = True
		self.fields['groups'].required = True
	
	password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Enter password')}))
	password2 = forms.CharField(label=_('Re-enter Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Confirm password')}))

	def clean(self, *args, **kwargs):
		super(FacultySignupForm, self).clean(*args, **kwargs)
		pwd1 = self.cleaned_data.get('password1')
		pwd2 = self.cleaned_data.get('password2')
		if pwd1 and pwd2 and pwd1!=pwd2:
			raise forms.ValidationError(_('Passwords do not match.'))
		return self.cleaned_data

	def save(self, commit=True, *args, **kwargs):
		faculty = super(FacultySignupForm, self).save(commit=False)
		faculty.set_password(self.cleaned_data['password2'])
		faculty.is_active = False
		faculty.type = 'F'
		if commit:
			try:
				faculty.save()
			except IntegrityError:
				raise forms.ValidationError(_('Faculty already exists'))
			except ValidationError as error:
				raise forms.ValidationError(error)
		return faculty

	class Meta:
		model = CustomUser
		fields = ['username', 'email', 'groups']
		help_texts = {
			'username': _('Required. 30 characters or fewer. Letters, digits and ./+/-/_ only.'),
			'groups': _('Faculty may belong to one or more groups.'),
		}

"""
class FacultyFormset(forms.BaseModelFormSet):
# for Faculty Account  model = CustomUser
	def clean(self):
		super(FacultyFormset, self).clean()

		for form in self.forms:
			pwd1 = form.cleaned_data['password1']
			pwd2 = form.cleaned_data['password2']
			if pwd1 and pwd2 and pwd1!=pwd2:
				raise forms.ValidationError(_('Passwords do not match'))
# save conditions to be added in views
# while saving, create faculty profile and set its profile and college fields
"""
class FacultyProfileForm(forms.ModelForm):
# Serves as both Creation, as well as Edit form
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sMB)' % (settings.IMAGE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except:
				pass
		return photo
	
	class Meta:
		model = Faculty
		exclude = ['profile', 'college']
		help_texts = {
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}
