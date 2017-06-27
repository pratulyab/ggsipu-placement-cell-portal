from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.utils.translation import ugettext_lazy as _
from account.models import CustomUser
from college.models import College, Stream
from student.models import Student, Qualification, TechProfile
from urllib.parse import urlparse
import re
from material import *

class StudentLoginForm(forms.Form):
	username = forms.CharField(label=_('Enrollment Number'), max_length=11, widget=forms.TextInput(attrs={'placeholder': _('Enter your enrollment number'), 'auto_focus':''}))
	password = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'placeholder':_('Enter password')}))

	def __init__(self, *args, **kwargs):
		self.user_cache = None
		super(StudentLoginForm, self).__init__(*args, **kwargs)

	def clean(self, *args, **kwargs):
		super(StudentLoginForm, self).clean(*args, **kwargs)
		username = self.cleaned_data.get('username', None)
		password = self.cleaned_data.get('password', None)
		if username and password:
			queryset = CustomUser.objects.filter(type='S').filter(is_superuser=False)
			if '@' in username:
				try:
					student = queryset.get(email=username)
					username = student.username
				except CustomUser.DoesNotExist:
					raise forms.ValidationError(_('Student with this email address does not exist'))
			else:
				try:
					queryset.get(username=username)
				except CustomUser.DoesNotExist:
					raise forms.ValidationError(_('Invalid enrollment number or password'))
			self.user_cache = authenticate(username=username, password=password)
			if self.user_cache is None:
				raise forms.ValidationError(_('Invalid enrollment number or password'))
		return self.cleaned_data
	
	def get_user(self):
		return self.user_cache

class StudentSignupForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(StudentSignupForm, self).__init__(*args, **kwargs)
		self.fields['email'].required = True
		self.fields['username'].widget.attrs['maxlength'] = 11
		self.fields['username'].widget.attrs['placeholder'] = 'Enter your 11 digit enrollment number'
		self.fields['email'].widget.attrs['placeholder'] = 'Enter email address'
		self.fields['username'].validators = [validators.RegexValidator(r'^\d{11}$')]
	
	password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Enter password')}))
	password2 = forms.CharField(label=_('Re-enter Password'), widget=forms.PasswordInput(attrs={'placeholder': _('Confirm password')}))

	def clean_username(self):
		username = self.cleaned_data.get('username', None)
		try:
			roll, coll, strm, year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', username).groups()
		except AttributeError:
			raise forms.ValidationError(_('Enrollment number should contain only digits'))
		except ValueError:
			raise forms.ValidationError(_('Enrollment number should be 11 digits long'))
		if College.objects.filter(code=coll).count() == 0:
			raise forms.ValidationError(_('Institution with code %s does not exist' % coll))
		if Stream.objects.filter(code=strm).count() == 0:
			raise forms.ValidationError(_('Incorrect programme code'))
		if not College.objects.get(code=coll).streams.filter(code=strm).exists():
			raise forms.ValidationError(_('Invalid enrollment number'))
		return username

	def clean_email(self):
		email = self.cleaned_data['email']
		if email:
			domain = '.'.join(email.split('@')[-1].split('.')[:-1]).lower()
			for blacklisted in settings.DISALLOWED_EMAIL_DOMAINS: # Because a few of these provide subdomains. FOOBAR.domainname.com
				if blacklisted in domain:
					raise forms.ValidationError(_('This email domain is not allowed. Please enter email of different domain.'))
		return email

	def clean(self, *args, **kwargs):
		super(StudentSignupForm, self).clean(*args, **kwargs)
		pwd1 = self.cleaned_data.get('password1', None)
		pwd2 = self.cleaned_data.get('password2', None)
		if pwd1 and pwd2:
			if pwd1 != pwd2:
				raise forms.ValidationError(_('Passwords must match.'))
			password_validation.validate_password(pwd1)
		return self.cleaned_data

	def save(self, commit=True, *args, **kwargs):
		student = super(StudentSignupForm, self).save(commit=False)
		student.set_password(self.cleaned_data['password2'])
		student.is_active = False
		student.type = 'S'
		if commit:
			try:
				student.save()
			except IntegrityError:
				raise forms.ValidationError(_('Student already exists'))
			except ValidationError as error:
				raise forms.ValidationError(error)
		return student

	class Meta:
		model = CustomUser
		fields = ['username', 'email']
		labels = {'username': _('Enrollment Number')}
		help_texts = {
			'username': _('Include the zeroes at the beginning of your enrollment number, if any.'),
			'email': _('You\'ll need to verify this email address. Make sure you have access to it.'),
		}

class StudentCreationForm(forms.ModelForm):
	layout = Layout(
		Fieldset('Personal Details', 
			Row(Span6('firstname'), Span6('lastname')),
			Row(Span3('gender'), Span4('dob'), Span5('phone_number')),
			Row(Span6('photo'))
		),
		Fieldset('Educational Details', 
			Row('college'),
			Row(Span6('programme'), Span6('stream')),
			Row(Span6('current_year'), Span6('is_sub_back')),
			Row('resume')
		),
	)
	def __init__(self, *args, **kwargs):
		self.user_profile = kwargs.pop('profile', None)
		self.coll = kwargs.pop('coll', None)
		self.strm = kwargs.pop('strm', None)
		super(StudentCreationForm, self).__init__(*args, **kwargs)
		self.fields['phone_number'].required = False
		self.initial['college'] = self.coll
		self.initial['stream'] = self.strm
		self.initial['programme'] = Stream.objects.get(pk=self.strm).programme.pk
		self.fields['college'].widget.attrs['disabled'] = 'disabled'
		self.fields['stream'].widget.attrs['disabled'] = 'disabled'
		self.fields['programme'].widget.attrs['disabled'] = 'disabled'

	def clean_college(self):
		college = self.cleaned_data.get('college', None)
		if college and college.pk != self.coll:
			raise forms.ValidationError(_('Error. College field changed.'))
		return college

	def clean_programme(self):
		programme = self.cleaned_data.get('programme', None)
		if programme and programme.pk != Stream.objects.get(pk=self.strm).programme.pk:
			raise forms.ValidationError(_('Error. Programme field changed.'))
		return programme

	def clean_stream(self):
		stream = self.cleaned_data.get('stream', None)
		if stream and stream.pk != self.strm:
			raise forms.ValidationError(_('Error. Stream field changed.'))
		return stream
	
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', None)
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

	def clean_resume(self):
		cv = self.cleaned_data.get('resume', None)
		if cv:
			try:
				if cv.content_type in settings.FILE_CONTENT_TYPE:
					if cv._size > settings.FILE_MAX_SIZE:
						raise forms.ValidationError(_('Resume too large (>%sMB)' % (settings.FILE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload resume in .pdf, .doc or .docx format'))
			except AttributeError:
				pass
		return cv
	
	def save(self, commit=True, *args, **kwargs):
		student = super(StudentCreationForm, self).save(commit=False)
		student.profile = self.user_profile
		student.is_verified = False
		if commit:
			try:
				student.save()
			except IntegrityError:
				raise forms.ValidationError(_('Couldn\'t retrieve profile'))
			except ValidationError as error:
				raise forms.ValidationError(error)
		return student
	
	class Meta:
		model = Student
		fields = ['firstname', 'lastname', 'gender', 'dob', 'photo', 'phone_number', 'college', 'programme', 'stream', 'is_sub_back', 'current_year', 'resume']
		help_texts = {
			'resume': _('Please upload resume in either pdf, doc or docx format, < %sMB' % str(settings.FILE_MAX_SIZE/(1024*1024))),
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}

class StudentEditForm(forms.ModelForm):
	layout = Layout(
		Fieldset('Personal Details', 
			Row(Span6('firstname'), Span6('lastname')),
			Row(Span3('gender'), Span4('dob'), Span5('phone_number')),
			Row(Span6('photo'))
		),
		Fieldset('Educational Details', 
			Row('college'),
			Row(Span6('programme'), Span6('stream')),
			Row(Span6('current_year'), Span6('is_sub_back')),
			Row('resume')
		),
	)
	def __init__(self, *args, **kwargs):
		super(StudentEditForm, self).__init__(*args, **kwargs)
		self.initial['college'] = self.instance.college.pk
		self.fields['college'].widget.attrs['disabled'] = 'disabled'
		self.initial['programme'] = self.instance.programme.pk
		self.fields['programme'].widget.attrs['disabled'] = 'disabled'
		self.initial['stream'] = self.instance.stream.pk
		self.fields['stream'].widget.attrs['disabled'] = 'disabled'

	def clean_college(self):
		clg = self.cleaned_data.get('college', None)
		if clg and self.instance.college != clg:
			raise forms.ValidationError(_('Error. College has been changed'))
		return clg

	def clean_programme(self):
		prog = self.cleaned_data.get('programme', None)
		if prog and self.instance.programme != prog:
			raise forms.ValidationError(_('Error. Programme has been changed'))
		return prog

	def clean_stream(self):
		strm = self.cleaned_data.get('stream', None)
		if strm and self.instance.stream != strm:
			raise forms.ValidationError(_('Error. Stream has been changed'))
		return strm
	
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', None)
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

	def clean_resume(self):
		cv = self.cleaned_data.get('resume', None)
		if cv:
			try:
				if cv.content_type in settings.FILE_CONTENT_TYPE:
					if cv._size > settings.FILE_MAX_SIZE:
						raise forms.ValidationError(_('Resume too large (>%sMB)' % (settings.FILE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload resume in .pdf, .doc or .docx format'))
			except AttributeError:
				pass
		return cv
	
	def save(self, commit=True, *args, **kwargs):
		student = super(StudentEditForm, self).save(commit=False)
		student.is_verified = kwargs.pop('verified', False)
		student.verified_by = kwargs.pop('verifier', None)
		if commit:
			try:
				student.save()
			except IntegrityError:
				raise forms.ValidationError(_('Verification error.'))
			except ValidationError as error:
				print(error)
				raise forms.ValidationError(_('Error Occcurred'))
		return student

	class Meta:
		model = Student
		fields = ['firstname', 'lastname', 'gender', 'dob', 'photo', 'phone_number', 'college', 'programme', 'stream', 'is_sub_back', 'current_year', 'resume']
		help_texts = {
			'resume': _('Please upload resume in either pdf, doc or docx format, < %sMB' % str(settings.FILE_MAX_SIZE/(1024*1024))),
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}

class QualificationForm(forms.ModelForm):
	"""
	Manipulating this form for both creation as well as editing. If the qualifications are being created for the first time, don\'t forget to pass the student instance to the save method. Updating the student field only if student is passed. Hence, if you don\'t pass the student object while creation, "" NULL not allowed " error will be raised. \m/
	"""
	def __init__(self, *args, **kwargs):
		super(QualificationForm, self).__init__(*args, **kwargs)

	def save(self, commit=True, *args, **kwargs):
		qual = super(QualificationForm, self).save(commit=False)
		student = kwargs.pop('student', None)
		if student:
			qual.student = student
		qual.is_verified = kwargs.pop('verified', False)
		qual.verified_by = kwargs.pop('verifier', None)
		if commit:
			qual.save()
		return qual

	class Meta:
		model = Qualification
		fields = ['tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']
		help_texts = {field: 'in percentage (%), upto 2 places of decimal' for field in fields}
"""
class QualificationEditForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(QualificationEditForm, self).__init__(*args, **kwargs)

	def save(self, commit=True, *args, **kwargs):
		qual = super(QualificationEditForm, self).save(commit=False)
		qual.is_verified = kwargs.pop('verified', None)
		qual.verified_by = kwargs.pop('verifier', None)
		if commit:
			qual.save()
		return qual

	class Meta:
		model = Qualification
		fields = ['tenth', 'twelfth', 'graduation', 'post_graduation', 'doctorate']
"""
class TechProfileForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		self.student_profile = kwargs.pop('student', None)
		super(TechProfileForm, self).__init__(*args, **kwargs)

	def clean_codechef(self):
		codechef = self.cleaned_data.get('codechef', None)
		if codechef:
			if not re.match(r'^[a-z]{1}[a-z0-9_]{3,13}$', codechef):
				raise forms.ValidationError(_('Invalid codechef username'))
		return codechef
	
	def clean(self, *args, **kwargs):
		super(TechProfileForm, self).clean(*args, **kwargs)
		for field in self._meta.fields:
			if self.fields[field].__class__.__name__ == 'URLField' and self.cleaned_data.get(field,None):
				if not field in urlparse( self.cleaned_data[field] ).netloc:
					raise forms.ValidationError({field:_('Please provide correct URL')})
		return self.cleaned_data
	
	def save(self, commit=True, *args, **kwargs):
		tech = super(TechProfileForm, self).save(commit=False)
		tech.student = self.student_profile
		if commit:
			tech.save()
		return tech

	class Meta:
		model = TechProfile
		fields = ['github', 'bitbucket', 'codechef', 'codeforces', 'spoj']
		help_texts = {
			'github': _('Please provide the URL of public profile'),
			'bitbucket': _('Please provide the URL of public profile'),
		}

class FileUploadForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(FileUploadForm, self).__init__(*args, **kwargs)
	
	def clean_photo(self):
		photo = self.cleaned_data.get('photo', None)
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

	def clean_resume(self):
		cv = self.cleaned_data.get('resume', None)
		if cv:
			try:
				print(cv.content_type)
				if cv.content_type in settings.FILE_CONTENT_TYPE:
					print(settings.FILE_CONTENT_TYPE)
					if cv._size > settings.FILE_MAX_SIZE:
						raise forms.ValidationError(_('Resume too large (>%sMB)' % (settings.FILE_MAX_SIZE/(1024*1024))))
				else:
					raise forms.ValidationError(_('Please upload resume in .pdf, .doc or .docx format'))
			except AttributeError:
				pass
		return cv
	
	class Meta:
		model = Student
		fields = ['photo', 'resume']
		help_texts = {
			'resume': _('Please upload resume in either pdf, doc or docx format, < %sMB' % str(settings.FILE_MAX_SIZE/(1024*1024))),
			'photo': _('Please upload image in either jpeg or png format, < %sMB' % str(settings.IMAGE_MAX_SIZE/(1024*1024))),
		}

class PaygradeForm(forms.ModelForm):
	'''
		To make sure that paygrade info is updated only once.
	def save(self, commit=True, *args, **kwargs):
		try:
			self.instance.paygrade
		except:
			if commit:
				super(self, PaygradeForm).save(*args, **kwargs)
		return self.instance.paygrade
	'''
	class Meta:
		model = Student
		fields = ['salary_expected']
