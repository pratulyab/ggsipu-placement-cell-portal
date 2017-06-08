import requests, re, json

# Check SMS Credits Balance
def check_credits_balance(api_key):
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
	print(r.text)
	r = json.loads(r.text)
	return int(r['Details'])

# Send SMS
def send_sms(api_key, recipients_list, msg, sender='GGSIPU'):
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
	if not msg:
		return None
	if check_credits_balance(api_key) < len(recipients_list):
		return None
	url = "http://2factor.in/API/V1/%s/ADDON_SERVICES/SEND/TSMS" % api_key
	payload = {
		'From': sender,
		'To': recipients,
		'Msg': msg
	}
	try:
		r = requests.POST(url, data=payload)
	except:
		return None
	if r.status_code != 200:
		return False
	print(r.text)
	return r.text
