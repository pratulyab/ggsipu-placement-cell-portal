from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from faculty.models import Faculty
from student.models import Student
import re
from material import *

class FacultySignupForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(FacultySignupForm, self).__init__(*args, **kwargs)
		self.fields['email'].required = True
		self.fields['groups'].required = True
	
	password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Enter password')}))
	password2 = forms.CharField(label=_('Re-enter Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Confirm password')}))

	def clean(self, *args, **kwargs):
		super(FacultySignupForm, self).clean(*args, **kwargs)
		pwd1 = self.cleaned_data.get('password1', None)
		pwd2 = self.cleaned_data.get('password2', None)
		if pwd1 and pwd2:
			if pwd1 != pwd2:
				raise forms.ValidationError(_('Passwords do not match.'))
			password_validation.validate_password(pwd1)
		return self.cleaned_data

	def save(self, commit=True, *args, **kwargs):
		faculty = super(FacultySignupForm, self).save(commit=False)
		faculty.set_password(self.cleaned_data.get('password2'))
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
			pwd1 = form.cleaned_data.get('password1', None)
			pwd2 = form.cleaned_data.get('password2', None)
			if pwd1 and pwd2 and pwd1!=pwd2:
				raise forms.ValidationError(_('Passwords do not match'))
# save conditions to be added in views
# while saving, create faculty profile and set its profile and college fields
"""
class FacultyProfileForm(forms.ModelForm):
# Serves as both Creation, as well as Edit form
	layout = Layout(
		Row(Span6('firstname'), Span6('lastname')),
		Row(Span6('employee_id'), Span6('phone_number')),
		Row('photo')
	)
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', False)
		if photo:
			try:
				if photo.content_type in settings.IMAGE_CONTENT_TYPE:
					if photo._size > settings.IMAGE_MAX_SIZE:
						raise forms.ValidationError(_('Image file too large (>%sMB)' % (settings.IMAGE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload photo in .jpeg or .png format'))
			except AttributeError:
				pass
		return photo
	
	class Meta:
		model = Faculty
		fields = ['firstname', 'lastname', 'employee_id', 'phone_number', 'photo']
		help_texts = {
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}

class EnrollmentForm(forms.Form):
	enroll = forms.CharField(label=_('Enter Enrollment Number'), widget=forms.TextInput(attrs={'maxlength': 11}), required=True, help_text="The retrieved forms will vanish once you change this field.")

	def __init__(self, *args, **kwargs):
		self.verifier = kwargs.pop('faculty', None)
		super(EnrollmentForm, self).__init__(*args, **kwargs)

	def clean(self, *args, **kwargs):
		super(EnrollmentForm, self).clean(*args, **kwargs)
		enrollno = self.cleaned_data.get('enroll', None)
		if enrollno:
			exp = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', enrollno)
			if not exp:
				raise forms.ValidationError(_('Invalid enrollment number format'))
			coll = exp.groups()[1]
			if self.verifier.college.code != coll:
				raise forms.ValidationError(_('You can verify students of your institution only.'))
			try:
				user = CustomUser.objects.get(username=enrollno)
			except CustomUser.DoesNotExist:
				raise forms.ValidationError(_('Student does not exist'))
			if not user.is_active:
				raise forms.ValidationError(_('Student hasn\'t verified his email address. Ask him to do so.'))
			try:
				student = user.student
			except Student.DoesNotExist:
				raise forms.ValidationError(_('Student hasn\'t created his profile. Ask him to create one by logging in from his account.'))
		return self.cleaned_data
