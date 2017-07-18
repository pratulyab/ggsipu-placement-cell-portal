from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from decimal import Decimal

# Create your models here.

class Company(models.Model):
	name = models.CharField(max_length=200, unique=True)
	alias = models.CharField(max_length=20, blank=True)
	website = models.URLField(blank=True)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = "Companies"

class College(models.Model):
	name = models.CharField(max_length=200)
	code = models.CharField(max_length=3, unique=True)
	alias = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return "[%s]" % (self.alias if self.alias else self.code)

class YearRecord(models.Model):
	college = models.ForeignKey(College, related_name="records")
	year = models.CharField(max_length=4)
	jobs_placement_percentage = models.DecimalField('Percentage Placed for Jobs',\
			max_digits=5, decimal_places=2, default=0,\
			validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))])
	internships_placement_percentage = models.DecimalField('Percentage of Internships',\
			max_digits=5, decimal_places=2, default=0,\
			validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))]
		)
	students_participated_jobs = models.PositiveSmallIntegerField(default=0)
	students_participated_internships = models.PositiveSmallIntegerField(default=0)
	companies = models.ManyToManyField(Company, through='Placement', related_name="records", blank=True)

# sum([p['total_offers'] for p in College.objects.get(code='CCC').records.get(year='XXXX').placements.filter(type='J').values('total_offers')])
	students_selected_jobs = models.PositiveSmallIntegerField(default=0)
#sum([p['total_offers'] for p in College.objects.get(code='CCC').records.get(year='XXXX').placements.filter(type='I').values('total_offers')])
	students_selected_internships = models.PositiveSmallIntegerField(default=0)

	def __str__(self):
		return "%s [%s]" % (self.college.__str__(), self.year)

	class Meta:
		unique_together = ['college', 'year']

class Placement(models.Model):
	PLACEMENT_TYPE = (
		('J', 'Job'),
		('I', 'Internship'),
	)
	record = models.ForeignKey(YearRecord, related_name="placements")
	company = models.ForeignKey(Company, related_name="placements")
	type = models.CharField(max_length=1, choices=PLACEMENT_TYPE, default=PLACEMENT_TYPE[0][0])
	salary = models.DecimalField('Salary (Lakhs P.A.)', max_digits=4, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
# If salary=0 or ND, then place salary_comment. Eg. 5-7 (range of salary)
	salary_comment = models.CharField(max_length=20, blank=True)
# Highly sensitive field. If discrepancy in data regarding salary, then mention the salary column here.
# In templates, check if salary_comment, then display that; else salary
	total_offers = models.PositiveSmallIntegerField(default=0)
