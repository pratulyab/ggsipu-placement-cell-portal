from django.http import JsonResponse
from django.shortcuts import render
#from django.template import loader
from django.views.decorators.http import require_GET, require_http_methods

from account.utils import handle_user_type
from stats.forms import StatsForm
from stats.models import College, Company, YearRecord, Placement

# Create your views here.

@require_GET
def stats(request):
	if request.user.is_authenticated():
		return handle_user_type(request, redirect_request=True)
	print(request.GET)
	if request.is_ajax():
		if request.GET.get('years', '') == 'true':
			try:
				college = College.objects.prefetch_related('records').get(pk=request.GET.get('college', None))
				years = [c['year'] for c in college.records.values('year')]
				data = []
				for year in years:
					data.append({'html': year, 'value': year})
				return JsonResponse(status=200, data={'years': data})
			except:
				return JsonResponse(status=400, data={'errors': 'Invalid choice'})
		elif request.GET.get('stats', '') == 'true':
			college_pk = request.GET.get('college', None)
			year = request.GET.get('year', None)
			# Table
			headings = ['Company', 'Type', 'Total Offerings', 'Salary (LPA)']
			college = College.objects.prefetch_related('records').get(pk=college_pk)
			record = college.records.get(year=year)
			placements = record.placements.order_by('-salary').all()
			entries = []
			for each in placements:
				company = each.company.name
				type = dict(Placement.PLACEMENT_TYPE)[each.type]
				offered = each.total_offers if each.total_offers else 'Result Awaited'
				salary = each.salary_comment if each.salary_comment else each.salary
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
			return JsonResponse(status=400, data={'errors': 'Invalid choices'})
	else:
		context = {'stats_form': StatsForm()}
	return render(request, 'stats/stats.html', context)
