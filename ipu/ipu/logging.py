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
			'format': '%(asctime)s - [%(module)s][%(name)s] - [%(levelname)s] - %(message)s'
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
			'handlers': ['mail_admins', 'error_log'],
			'level': 'WARNING',
			'propagate': False,
		},
	}
}

def add_apps_config():
	apps = ['student', 'faculty', 'college', 'company', 'recruitment', 'notification']
	for app in apps:
		handler = {
			'level': 'INFO',
			'class': 'logging.handlers.RotatingFileHandler',
			'filename': '/var/log/ipu/%s.log' % (app),
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

def configure_logging():
	logging.config.dictConfig(LOGGING)

add_apps_config()
