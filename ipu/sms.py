import requests, re

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
	return r.text

# Send SMS
def send_sms(api_key, receipents_list, msg, sender='GGSIPU'):
	if not isinstance(api_key, str):
		return None
	if len(sender) > 6:
		return None
	if not isinstance(receipents_list, list) or not len(receipents_list):
		return None

	receipents_validator = r'^([7-9]\d{9}(,[7-9]\d{9})*)$'
	try:
		receipents_set = set(receipents_list)
		receipents = ','.join(receipents_set)
	except:
		return None
	if not re.match(receipents, receipents_validator):
		return None
	if not msg:
		return None
	if check_credits_balance(api_key) < len(receipents_list):
		return None
	url = "http://2factor.in/API/V1/%s/ADDON_SERVICES/SEND/TSMS" % api_key
	payload = {
		'From': sender,
		'To': receipents,
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
