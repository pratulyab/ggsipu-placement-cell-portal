import os, logging.config

LOGGING = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'verbose': {
			'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
		},
		'simple': {
			'format': '%(levelname)s %(message)s'
		},
		'standard': {
			'format': '%(asctime)s - [%(name)s.%(module)s] - [%(levelname)s] - %(message)s'
		},
	},
	'filters': {
		'require_debug_true': {
			'()': 'django.utils.log.RequireDebugTrue',
		},
	},
	'handlers': {
		'console': {
			'level': 'INFO',
			'filters': ['require_debug_true'],
			'class': 'logging.StreamHandler',
			'formatter': 'simple'
		},
		'mail_admins': {
			'level': 'ERROR',
			'class': 'django.utils.log.AdminEmailHandler',
		},
		'error_log': {
			'level': 'ERROR',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': '/var/log/ipu/error.log',
			'maxBytes': 5 * 1024 * 1024, # 5 MB
			'backupCount': 5,
			'formatter': 'standard'
		},
	},
	'loggers': {
		'django': {
			'handlers': ['console'],
			'level': 'INFO',
			'propagate': True,
		},
		'django.request': {
			'handlers': ['mail_admins', 'error_log', 'console'],
			'level': 'WARNING',
			'propagate': False,
		},
	}
}

def add_apps_config(log_file_path):
	apps = ['student', 'faculty', 'college', 'company', 'recruitment', 'notification', 'account', 'dummy', 'download']
	for app in apps:
		handler = {
			'level': 'INFO',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': log_file_path % (app),
			'maxBytes': 5 * 1024 * 1024, # 5 MB
			'backupCount': 5,
			'formatter': 'standard',
		}
		logger = {
			'handlers': ['%s' % app],
			'level': 'INFO',
			'propagate': False,
		}
		LOGGING['handlers'][app] = handler
		LOGGING['loggers'][app] = logger
	
	# Mofifying error.log file path
	LOGGING['handlers']['error_log']['filename'] = log_file_path % ('error')

def configure_logging(debug=False):
	BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	log_file_path = ''
	if not debug: # Prod
		log_file_path = '/var/log/ipu/%s.log'
	
	else: # Dev
		if not os.path.exists(os.path.join(BASE_DIR, '.log')):
			os.mkdir(os.path.join(BASE_DIR, '.log'))
		log_file_path = os.path.join(BASE_DIR, '.log', '%s.log')
	add_apps_config(log_file_path)
	logging.config.dictConfig(LOGGING)

