# Migrate excel data to db
import openpyxl as excel
import os, re, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ipu.settings")
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
from account.models import CustomUser
from student.models import Student, College, Programme, Stream

workbook = excel.load_workbook('abc.xlsx')
sheet = workbook.active
max_row = sheet.max_row
password = 'pbkdf2_sha256$24000$cW9GaQxskQzH$RpXd6CRU78akuFboDI3QX//KbhjrcPRR/9NA4gBmFRY='
for row in range(2, max_row+1):
	firstname = sheet['A'+str(row)].value
	lastname = sheet['B'+str(row)].value
	gender = sheet['C'+str(row)].value.title()[0]
	email = sheet['D'+str(row)].value
	phone_number = str(sheet['E'+str(row)].value)
	enrollment = str(sheet['F'+str(row)].value)
	if len(enrollment) == 9:
		enrollment = '00'+enrollment
	elif len(enrollment) == 10:
		enrollment = '0'+enrollment
	try:
		user = CustomUser.objects.create(username=enrollment, password=password, email=email, type='S', is_active=True)
		user.save()
		user.set_password(password)
	except:
		print("Error occurred creating CustomUser for %s" % enrollment)
		continue
	roll,coll,stream,year = re.match(r'^(\d{3})(\d{3})(\d{3})(\d{2})$', enrollment).groups()
	coll = College.objects.get(code=coll).pk
	stream = Stream.objects.get(code=stream)
	prog = stream.programme.pk
	stream = stream.pk
	try:
		Student.objects.create(profile=user, firstname=firstname, lastname=lastname, gender=gender, phone_number=phone_number, college_id=coll, programme_id=prog, stream_id=stream)
	except:
		print("Error occurred creating Student obj for %s %s" % (firstname,lastname))
