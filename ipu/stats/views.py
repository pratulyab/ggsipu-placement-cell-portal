from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.views.decorators.http import require_GET, require_http_methods

from account.utils import handle_user_type
from stats.forms import StatsForm
from stats.models import College, Company, YearRecord, Placement

# Create your views here.

@require_GET
def stats(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	if request.is_ajax():
		if request.GET.get('years', '') == 'true':
			try:
				college = College.objects.prefetch_related('records').get(pk=request.GET.get('college', None))
				years = [c['academic_year'] for c in college.records.values('academic_year')]
				data = []
				for year in years:
					data.append({'html': year, 'value': year})
				return JsonResponse(status=200, data={'years': data})
			except:
				return JsonResponse(status=400, data={'errors': 'Please choose a valid college.'})
		elif request.GET.get('stats', '') == 'true':
			college_pk = request.GET.get('college', None)
			year = request.GET.get('year', None)
			if not year or not college_pk:
				message = 'Invalid ' + ('college chosen' if not college_pk else 'year chosen')
				return JsonResponse(status=400, data={'errors': message})
			# Table
			headings = ['Company', 'Type', 'Total Offerings', 'Salary (LPA)']
			college = College.objects.prefetch_related('records').get(pk=college_pk)
			record = college.records.get(academic_year=year)
			placements = record.placements.order_by('-salary').all()
			entries = []
			for each in placements:
				company = each.company.name
				type = dict(Placement.PLACEMENT_TYPE)[each.type]
				offered = each.total_offers or '---' #if each.total_offers else 'Result Awaited'
				salary = each.salary_comment if each.salary_comment else ('Training' if not each.salary and type.lower().startswith('i') else each.salary)
				entries.append([company, type, offered, salary])
			context = {'headings': headings, 'entries': entries}
			table = render(request, 'stats/table.html', context).content.decode('utf-8')
			# # #
			# Graph
			graph = []
			for each in placements:
				if each.salary_comment:
					continue
				point = {}
				point['salary'] = float(each.salary)
				point['offers'] = each.total_offers
				point['company'] = each.company.name
				graph.append(point)
			# # #
			return JsonResponse(status=200, data={'table': table, 'graph': graph})
		else:
			return JsonResponse(status=400, data={'errors': 'Please choose from the options.'})
	else:
		context = {'stats_form': StatsForm()}
	return render(request, 'stats/stats.html', context)

@require_GET
def past_recruiters(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	try:
		get_template('stats/past_recruiters_compiled.html')
		return render(request, 'stats/past_recruiters_compiled.html', {}) # optimization
	except:
		pass
	queryset = Company.objects.all().order_by('name')
	half = queryset.count()/2
	i,j = 0,0
	ones = queryset[:half]
	twos = queryset[half:]
	companies = []
	while i < len(ones) or j < len(twos):
		data = {}
		try:
			data['one'] = ones[i]
		except IndexError:
			pass
		try:
			data['two'] = twos[j]
		except IndexError:
			pass
		i = i+1
		j = j+1
		companies.append(data)
	r = render(request, 'stats/past_recruiters.html', {'companies': companies})
# compiling the data to a template because the data to be displayed is constant for long time
# so why hit the db
	content = r.content.decode('utf-8')
	f = open('templates/stats/past_recruiters_compiled.html', 'w')
	try:
		f.write(content)
	finally:
		f.close()
	return r
