from django.core.management.base import BaseCommand, CommandError
from django.core.mail import mail_admins

from account.models import CustomUser
from student.models import Student

import getpass, datetime, logging

accountLogger = logging.getLogger('account')
studentLogger = logging.getLogger('student')

class Command(BaseCommand):
	help = 'Increments Academic Year: Graduates Final Year Students; Increments current_year of students still studying'

	def add_arguments(self, parser):
#		parser.add_argument('username', nargs='?', type=str)
		parser.add_argument('--college', action='append', help="College (Codes) whose academic cal needs to be incremented", required=True, dest='college_codes')
		parser.add_argument('--override', action='store_true', help="Increment Academic Year Irrespective of whether the command is run in July", dest='override')

	def handle(self, *args, **options):
		

		# AUTHENTICATION
		college_codes = options['college_codes']
		
		print('College Codes: %s' % college_codes)
		
		username = input('Enter Username: ')
		pwd = getpass.getpass()
		user = CustomUser.objects.get(username=username)
		if not user.is_superuser:
			raise CommandError("Not Authorized")
		if not user.check_password(pwd):
			raise CommandError("Incorrect Password. Try again.")

		# WARNINGS
		if not datetime.datetime.today().month == 7:
			if options.get('override'):
				self.stdout.write(self.style.WARNING('You are not running this script in July. It will surely BREAK things.\nConsult this script writer before running the script.'))
				self.stdout.write(self.style.WARNING('\nStill want to run the script? (y/N)'), ending=' ')
				if not input().lower().startswith('y'):
					self.stdout.write(self.style.SUCCESS('Command Withdrawn Successfully'))
					return
			else:
				raise CommandError('Academic Calendar should not be updated in any month other than July. Try python manage.py <command> \'help\'')
		else:
			self.stdout.write(self.style.WARNING('Are you sure you want to run the script? (y/N)'), ending=' ')
			if not input().lower().startswith('y'):
				self.stdout.write(self.style.SUCCESS('Command Withdrawn Successfully'))
				return


		# Graduating students after 1st July (i.e. completion of their last sem)

		students = Student.studying.filter(college__code__in=college_codes) # Returns only current students who are studying i.e. not alumni
		print("Total Students", students.count())
		
		graduated_pks = []
		incremented_pks = []

		for student in students:
			programme = student.programme
			stream = student.stream

			# Strictly assuming that the command is run in July
			admission_year = '20' + student.profile.username[-2:]
			diff = datetime.datetime.today().year - int(admission_year)
			if student.current_year == (diff + 1):
				'''
					Eg. If the script is run in July 2020
						Student's admission year is 2018
						Student's current_year = (2020 - 2018 + 1) = 3,
						then it is correct. Thus, continue.
				'''
				continue

			# Special Case
			# Programme: B.Tech./M.Tech. Dual Degree
			# The programme offers 6 years in total.
			# This programme has optional M.Tech. choice after B.Tech. completion
			# That is, 4 (B.Tech.) + 2 (M.Tech.[optional])
			# Thus, it is required to separately handle the graduation of the students
			# enrolled in this programme who've only pursued B.Tech.
			# Not able to think of any other way, a hard coded logic is being applied
			# Checking for specific stream codes
			# TODO: Add stream codes in the list if such anamoly is found
			# Also, students who are pursuing the optional course will be marked GRADUATED.
			# They'll need to be manually unmarked (admin panel).

			exceptional_streams = {'015': ['4'], '032': ['4'], '128': ['4']} # {'stream_codes': [possible_prog_termination_years]}
			
			try:
				if stream.code in exceptional_streams:
					if student.current_year in exceptional_streams[stream.code]:
						student.has_graduated = True
						student.save()
						graduated_pks.append(student.pk)
						continue
				
				if int(student.current_year) >= int(programme.years):
					""" i.e., as of 1st July XXXX, student has just completed the even semester of the final year """
					# Then graduate him/her
					student.has_graduated = True
					student.save()
					graduated_pks.append(student.pk)

				elif int(student.current_year) < int(programme.years):
					# Increase the student's current_year
					student.current_year = str(int(student.current_year) + 1)
					student.save()
					incremented_pks.append(student.pk)
			except Exception as e:
				studentLogger.error('GRADUATE - Student<%d> [%s]' % (student.pk, student.profile.username))
				self.stdout.write(self.style.ERROR('Error occurred while running. Continuing. Check student logs'))
#				mail_admins()

		studentLogger.info('Students Graduated: %s' % (graduated_pks))
		studentLogger.info('Students Incremented: %s' % (incremented_pks))
		accountLogger.info('SuperUser - %s - Incremented Academic Calendar for %s.\nGraduated: %s\nIncremented: %s' % (username, college_codes, graduated_pks, incremented_pks))
		self.stdout.write(self.style.SUCCESS('Successfully Run. Check logs.'))
