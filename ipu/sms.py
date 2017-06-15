import requests, re, json
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ipu.settings")
from django.core.management import execute_from_command_line

from django.conf import settings
from django.core.mail import mail_admins

# Check SMS Credits Balance
def check_credits_balance():
	api_key = settings.TWOFACTOR_API_KEY
	if not isinstance(api_key, str):
		return None
	url = "http://2factor.in/API/V1/%s/ADDON_SERVICES/BAL/TRANSACTIONAL_SMS" % api_key
	try:
		r = requests.get(url)
	except:
		# Log
		return None
	if r.status_code != 200:
		return False
	r = json.loads(r.text)
	return int(r['Details'])

def pull_delivery_report(session_id):
	url = "http://2factor.in/API/V1/{}/ADDON_SERVICES/RPT/TSMS/{}".format(settings.TWOFACTOR_API_KEY, session_id)
	try:
		r = requests.get(url, data="{}")
		return r.text
	except:
		return None

# Send SMS
def send_sms(recipients_list, msg='', sender='GGSIPU', template_name='basic', *VAR):
	''' Returns dict {"Status": "Success/Failure", "Details": "session_id"}'''
	api_key = settings.TWOFACTOR_API_KEY
	if not isinstance(api_key, str):
		return None
	if len(sender) > 6:
		return None
	if not isinstance(recipients_list, list) or not len(recipients_list):
		return None

	recipients_validator = r'^([7-9]\d{9}(,[7-9]\d{9})*)$'
	try:
		recipients_set = set(recipients_list)
		recipients = ','.join(recipients_set)
	except:
		return None
	if not re.match(recipients_validator, recipients):
		return None
	if not msg and not template_name:
		return None
	balance = check_credits_balance()
	tobesent = len(recipients_list)
	if balance < tobesent:
		mail_admins('URGENT: 2Factor SMS Balance insufficient', 'No. of recipients: %s\nBalance SMS: %s' % (str(tobesent), str(balance)))
		return None
	url = "http://2factor.in/API/V1/%s/ADDON_SERVICES/SEND/TSMS" % api_key
	payload = {
		'From': sender,
		'To': recipients,
		'TemplateName': template_name,
		'Msg': msg
	}
	if not template_name:
		payload.pop('TemplateName')
	[payload.__setitem__('VAR'+str(i+1), var) for i,var in enumerate(VAR) if i<12] # Max 12 VARS are allowed
	try:
		r = requests.post(url, data=payload)
	except:
		return None
	if r.status_code != 200:
		print(r.text)
		return False
	return json.loads(r.text)
