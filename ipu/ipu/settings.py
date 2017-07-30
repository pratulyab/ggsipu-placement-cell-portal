"""
Django settings for ipu project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import hashids, socket
from .logging import configure_logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'yc55$ws@*mj)q8q&-!bwg6@44ua@7l2^&+!vd$9uje!shpwlxy'

# SECURITY WARNING: don't run with debug turned on in production!
if socket.gethostname() == 'usict-tnp':
	DEBUG = False
	ALLOWED_HOSTS = ['placements.ggsipu.ac.in']
	db_password = 'P30R1024$1089'
	EMAIL_HOST_USER = 'placements.ggsipu'
	EMAIL_HOST_PASSWORD = ''
	GOOGLE_RECAPTCHA_SECRET_KEY = '6LdZOSgUAAAAAFHQTlrB78BkzCJmmItf33kgT46s'
	GOOGLE_RECAPTCHA_SITE_KEY = '6LdZOSgUAAAAAAI4LnXicSdeb5Q4yndIxOkTGq11'
	# SSL
	SESSION_COOKIE_SECURE = True
	CSRF_COOKIE_SECURE = True
	SECURE_SSL_REDIRECT = True
	USE_HTTPS = True # Self defined boolean
	MEDIA_ROOT = '/var/www/ipu/media/'
	
else:
	DEBUG = True
	ALLOWED_HOSTS = []
	db_password = ''
	USE_HTTPS = False
	EMAIL_HOST_USER = 'ggsipu'
	EMAIL_HOST_PASSWORD = 'Whit3Label' # 100 emails / day
	GOOGLE_RECAPTCHA_SECRET_KEY = '6Lf15yUUAAAAAAqiR-42Dd97yqAUqdab0jW3KK4M'
	GOOGLE_RECAPTCHA_SITE_KEY = "6Lf15yUUAAAAAI1ju9iGXNQQQFKhIQU41J5ccaDC"
	MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# LOGGING CONFIGURATION
LOGGING_CONFIG = None
configure_logging(debug=DEBUG)

AUTH_USER_MODEL = 'account.CustomUser'

# Application definition

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'account',
	'college',
	'company',
	'download',
	'dummy_company',
	'faculty',
	'notification',
	'recruitment',
	'stats',
	'student',
	'material',
]

MIDDLEWARE_CLASSES = [
	'django.middleware.security.SecurityMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ipu.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [os.path.join(BASE_DIR, 'templates')],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.debug',
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'ipu.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'ipu',
		'HOST': 'localhost',
		'USER': 'root',
		'PASSWORD': db_password,
		'PORT': 3306
	}
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
	{
		'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
	},
	{
		'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
	},
	{
		'NAME': 'account.validators.CustomPasswordValidator',
	},
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

#Google recaptcha 
GOOGLE_RECAPTCHA_VERIFICATION_URL = 'https://www.google.com/recaptcha/api/siteverify'


#urls.W001 warns against use of '$' in regex of admin; used to override .com/admin lookup in /username url

# urls.W001 warns against use of '$' in regex of admin; used to override .com/admin lookup in /username url
SILENCED_SYSTEM_CHECKS = ["urls.W001",]

MEDIA_URL = '/media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS=[os.path.join(BASE_DIR, 'static')]
#STATIC_ROOT = os.path.join(BASE_DIR, 'static/') Security Flaw
STATIC_ROOT = '/var/www/ipu/static/'

LOGIN_URL = 'auth'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'no-reply@placements.ggsipu.ac.in'

# SMS
TWOFACTOR_API_KEY = '31cce076-19ed-11e7-9462-00163ef91450'

# FILE UPLOAD CONSTRAINTS
FILE_CONTENT_TYPE = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
FILE_MAX_SIZE = 200*1024 #200KB

# IMAGE UPLOAD CONSTRAINTS
IMAGE_CONTENT_TYPE = ['image/jpeg', 'image/png']
IMAGE_MAX_SIZE = 200*1024 #200KB

# HASHIDS
HASHID_ASSOCIATION = hashids.Hashids(salt="Sammelan", min_length=10)
HASHID_DISSOCIATION = hashids.Hashids(salt="Takraar", min_length=11)
HASHID_COLLEGE = hashids.Hashids(salt="mahavidyalya", min_length=8)
HASHID_COMPANY = hashids.Hashids(salt="NoIdea", min_length=8)
HASHID_CUSTOM_USER = hashids.Hashids(salt="ThinkRandomly", min_length=13)
HASHID_DUMMY_COMPANY = hashids.Hashids(salt="NakliComp", min_length=7)
HASHID_DUMMY_SESSION = hashids.Hashids(salt="NakliNakli", min_length=9)
HASHID_FACULTY = hashids.Hashids(salt="Workforce", min_length=8)
HASHID_KLASS = hashids.Hashids(salt="Pathshala", min_length=10)
HASHID_PLACEMENTSESSION = hashids.Hashids(salt="Naukari", min_length=12)
HASHID_PROGRAMME = hashids.Hashids(salt="Something", min_length=3)
HASHID_SCORE = hashids.Hashids(salt="Marksheet", min_length=11) # is used to encode scores like 101 or 123; i.e. 10 klass, subject 1 or 12 klass, subject 3
HASHID_STREAM = hashids.Hashids(salt="Dhaara", min_length=4)
HASHID_STUDENT = hashids.Hashids(salt="Vidyarthi", min_length=8)

# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'India/Kolkata'

# URL NAMES DICTIONARY FOR USER TYPES
HOME_URL = {
	'C': 'college_home',
	'F': 'faculty_home',
	'S': 'student_home',
	'CO': 'company_home'
}

PROFILE_CREATION_URL = {
	'C': 'create_college',
	'F': 'edit_create_faculty',
	'S': 'create_student',
	'CO': 'create_company'
}

# SESSIONS
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1 * (60 * 60 * 24)

# # # 
DISALLOWED_USERNAMES = ['account', 'notification', 'student', 'faculty', 'company', 'college', 'dcompany', 'recruitment', 'stats', 'download']
DISALLOWED_EMAIL_DOMAINS = ['mailinator', 'discard.email', 'thraml', 'mintemail', 'mailcatch']
