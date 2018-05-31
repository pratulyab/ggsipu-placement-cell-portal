from celery.decorators import task
from celery.utils.log import get_task_logger

from django.conf import settings
from stats.models import Company as SCompany, College as SCollege, YearRecord as SYear, Placement as SPlacement
from recruitment.models import Association, PlacementSession
from dummy_company.models import DummySession

logger = get_task_logger(__name__)

def get_academic_year(date): # drive_date
	year = date.year
	# COLLEGE ACADEMIC CAL: Jul - Jun
	start = 7 # Incase sessions created during holidays (Jul)
	end = 6 # Ends in June
	cal = None

	if date.month >= start: # Jul - Dec (Odd Sem)
		cal = str(year) + '-' + str(year + 1)[2:]
	elif date.month <= end: # Jan - Jun (Even Sem)
		cal = str(year - 1) + '-' + str(year)[2:]
	return cal

@task(name="dump_stats_record_task")
def dump_stats_record_task(pk, is_dummy):
	""" Used to dump a session or dummysession into stats as soon as it ends. """
	
	try:
		if is_dummy:
			dsession = DummySession.objects.get(pk=pk)
			
			if not dsession.ended:
				return
			
			company = dsession.dummy_company
			college = company.college
			drive_date = dsession.created_on
			type = dsession.type
			salary = dsession.salary
			offers = dsession.students.count()

		else:
			session = PlacementSession.objects.get(pk=pk)
			
			if not session.ended:
				return
			
			association = session.association
			company = association.company
			college = association.college
			drive_date = session.created_on
			type = association.type
			salary = association.salary
			offers = session.students.count()
	 
		stats_college = SCollege.objects.get_or_create(code=college.code, defaults={'name': college.name.title()})[0]
		stats_company = SCompany.objects.get_or_create(name=company.name.title(), defaults={'website': company.website})[0]
		year_record = SYear.objects.get_or_create(academic_year = get_academic_year(drive_date), college=stats_college)[0]
		placement, created = SPlacement.objects.get_or_create(record=year_record, company=stats_company, type=type, salary=salary)
		if created:
			placement.total_offers = offers
		else:
			placement.total_offers += offers
		placement.save()
	
	except Exception as e:
		logger.error(str(e))
