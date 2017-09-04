from student.models import Student
import openpyxl as excel, time
from datetime import date
from hashids import Hashids

def get_excel_structure(main_heading, secondary_heading, students_queryset):
	workbook = excel.Workbook()
	worksheet = workbook.active
	worksheet.title = "Placement Session"
	worksheet['A1'].font = excel.styles.Font(name='Times New Roman', size=20, bold=True)
	worksheet.merge_cells("A1:I2");worksheet.merge_cells("A3:I3")
	worksheet['A1'] = main_heading # Job/Internship @ College
	worksheet['A3'] = secondary_heading # Programme - Streams
	worksheet.freeze_panes = 'A5'
	
	# S.No. | Enrollment No. | First Name | Last Name | Gender | Email | Stream | Year | Tenth | Twelfth | Graduation | Post Grad | Doctorate
	worksheet['A4'] = 'S.No.'; worksheet['B4'] = 'Enrollment No.'; worksheet['C4'] = 'First Name'; worksheet['D4'] = 'Last Name';
	worksheet['E4'] = 'Gender'; worksheet['F4'] = 'Email'; worksheet['G4'] = 'Stream'; worksheet['H4'] = 'Year';
	worksheet['I4'] = '10th'; worksheet['J4'] = '12th'; worksheet['K4'] = 'Graduation'; worksheet['L4'] = 'Post Graduation'; worksheet['M4'] = 'Doctorate'
	
	bold = excel.styles.Font(bold=True)
	for i in range(1,9):
		worksheet.cell(row=4, column=i).font = bold
	
	GENDER = dict(Student.GENDER_CHOICES)
	for i, student in enumerate(students_queryset, 1):
		qualifications = getattr(student, 'qualifications', None)
		row = worksheet.max_row+1
		worksheet.cell(row=row, column=1).value = i
		worksheet.cell(row=row, column=2).value = student.profile.username
		worksheet.cell(row=row, column=3).value = student.firstname.title()
		worksheet.cell(row=row, column=4).value = student.lastname.title()
		worksheet.cell(row=row, column=5).value = GENDER[student.gender].__str__()
		worksheet.cell(row=row, column=6).value = student.profile.email
		worksheet.cell(row=row, column=7).value = student.stream.name.title()
		worksheet.cell(row=row, column=8).value = student.current_year
		worksheet.cell(row=row, column=9).value = get_qual_value(qualifications, 'tenth')
		worksheet.cell(row=row, column=10).value = get_qual_value(qualifications, 'twelfth')
		worksheet.cell(row=row, column=11).value = get_qual_value(qualifications, 'graduation')
		worksheet.cell(row=row, column=12).value = get_qual_value(qualifications, 'post_graduation')
		worksheet.cell(row=row, column=13).value = get_qual_value(qualifications, 'doctorate')
	
	to_letter = excel.cell.get_column_letter
	for col in [1,5,8]:
		worksheet.column_dimensions[to_letter(col)].width = 5
	for col in [2,3,4,9,10,11,12,13]:
		worksheet.column_dimensions[to_letter(col)].width = 12
	for col in [6,7]:
		worksheet.column_dimensions[to_letter(col)].width = 20
	return workbook

def get_master_excel_structure(college, students_queryset): # All students' data
	students_queryset = students_queryset.order_by('stream__code') # Grouping stream-wise
	workbook = excel.Workbook()
	worksheet = workbook.active
	worksheet.title = "Master"
	worksheet['A1'].font = excel.styles.Font(name='Times New Roman', size=20, bold=True)
	worksheet.merge_cells("A1:I2");worksheet.merge_cells("A3:I3")
	worksheet['A1'] = college.name.title() # College Name
	worksheet['A3'] = date.today().strftime("Students' data as of %d %b, %Y") # Date
	worksheet.freeze_panes = 'A5'
	
	# S.No. | Enrollment No. | First Name | Last Name | Gender | Email | Stream | Year | Tenth | Twelfth | Graduation | Post Grad | Doctorate | Verified
	# | Back(s) | Phone Number | DoB
	worksheet['A4'] = 'S.No.'; worksheet['B4'] = 'Enrollment No.'; worksheet['C4'] = 'First Name'; worksheet['D4'] = 'Last Name';
	worksheet['E4'] = 'Gender'; worksheet['F4'] = 'Email'; worksheet['G4'] = 'Stream'; worksheet['H4'] = 'Year';
	worksheet['I4'] = '10th'; worksheet['J4'] = '12th'; worksheet['K4'] = 'Graduation'; worksheet['L4'] = 'Post Graduation'; worksheet['M4'] = 'Doctorate'
	worksheet['N4'] = 'Verified'; worksheet['O4'] = 'Back(s)'; worksheet['P4'] = 'Min. Salary Expected';
	worksheet['Q4'] = 'Phone Number'; worksheet['R4'] = 'Date of Birth';
	
	bold = excel.styles.Font(bold=True)
	for i in range(1,9):
		worksheet.cell(row=4, column=i).font = bold
	
	GENDER = dict(Student.GENDER_CHOICES)
	for i, student in enumerate(students_queryset, 1):
		qualifications = getattr(student, 'qualifications', None)
		row = worksheet.max_row+1
		worksheet.cell(row=row, column=1).value = i
		worksheet.cell(row=row, column=2).value = student.profile.username
		worksheet.cell(row=row, column=3).value = student.firstname.title()
		worksheet.cell(row=row, column=4).value = student.lastname.title()
		worksheet.cell(row=row, column=5).value = GENDER[student.gender].__str__()
		worksheet.cell(row=row, column=6).value = student.profile.email
		worksheet.cell(row=row, column=7).value = student.stream.name.title()
		worksheet.cell(row=row, column=8).value = student.current_year
		worksheet.cell(row=row, column=9).value = get_qual_value(qualifications, 'tenth')
		worksheet.cell(row=row, column=10).value = get_qual_value(qualifications, 'twelfth')
		worksheet.cell(row=row, column=11).value = get_qual_value(qualifications, 'graduation')
		worksheet.cell(row=row, column=12).value = get_qual_value(qualifications, 'post_graduation')
		worksheet.cell(row=row, column=13).value = get_qual_value(qualifications, 'doctorate')
		worksheet.cell(row=row, column=14).value = "Yes" if (student.is_verified and student.verified_by) else "No"
		worksheet.cell(row=row, column=15).value = "Yes" if student.is_sub_back else "No"
		worksheet.cell(row=row, column=16).value = ("%d LPA" % student.salary_expected) if student.salary_expected else "--"
		worksheet.cell(row=row, column=17).value = student.phone_number
		worksheet.cell(row=row, column=18).value = student.dob.__str__()
	
	to_letter = excel.cell.get_column_letter
	for col in [1,5,8,14,15]:
		worksheet.column_dimensions[to_letter(col)].width = 7
	for col in [2,3,4,9,10,11,12,13,17,18]:
		worksheet.column_dimensions[to_letter(col)].width = 12
	for col in [6,7,16]:
		worksheet.column_dimensions[to_letter(col)].width = 20
	return workbook


def get_qual_value(qualifications, attr):
	value = getattr(qualifications, attr, None)
	if not value or float(value) == 33:
		return '-'
	else:
		return str(value) + '%'
