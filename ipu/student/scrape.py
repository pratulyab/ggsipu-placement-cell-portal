import requests
from bs4 import BeautifulSoup
#from pprint import pprint

def cook_soup(url):
	try:
		headers = {
			'Accept-Language': 'en-US,en;q=0.8',
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
		}
		r = requests.get(url, headers=headers, timeout=5)
		soup = BeautifulSoup(r.text.encode('utf-8'), "html.parser")
		return soup
	except requests.exceptions.RequestException as e:
		print(e)
		return ''
	finally:
		r.close()

def codechef(username):
	result = {}
	base_url = "https://www.codechef.com"
	url = base_url + "/users/" + username
	result['url'] = url
	try:
		soup = cook_soup(url)
		if soup.__class__.__name__ == 'str':
			result['success'] = False
			return result
		# Profile
		profile = soup.select("#primary-content .profile")[0]
		tables = profile.find_all('table', {'cellspacing': 0, 'border': 0})
		result['pic'] = base_url + (tables[0].find('div', {'class': 'user-thumb-pic'}).find('img')['src'])
		result['name'] = tables[0].find('div', {'class': 'user-name-box'}).text.strip()
		trs = tables[1].find_all('tr')
		result['institution'] = ''
		for tr in trs:
			td = tr.find_all('td')
			if td[0].text.split(':')[0] == 'Institution':
				result['institution'] = td[1].text.strip()
		# Ranking
		table = soup.find('div', {'id': 'hp-sidebar-blurbRating'})
		rows = table.find_all('tr')
		rows = rows[1:]
		ranking = {}
		for row in rows:
			cols = row.find_all('td')
			rtype = cols[0].text.strip()
			rank = '/'.join([hx.text for hx in row.find_all('hx')])
			rating = cols[-1].text.strip().replace('\xa0(?)', '')
			ranking[rtype] = {'rank': rank, 'rating': rating}
		result['ranking'] = ranking
		result['success'] = True
	except:
		result['success'] = False
	finally:
#		pprint(result)
		return result

def codeforces(username):
	result = {}
	url = "http://www.codeforces.com/profile/" + username
	result['url'] = url
	try:
		soup = cook_soup(url)
		if type(soup) == 'str':
			result['success'] = False
			return result
		result['pic'] = soup.select('.roundbox .userbox .title-photo img')[0]['src']
		profile = soup.select('.roundbox .userbox .info')[0]
		main = profile.find('div', {'class': 'main-info'})
		result['rank'] = main.select('div.user-rank span')[0].text
		divs = main.find_all('div')[2:]
		info = []
		for div in divs:
			if div.has_attr('style'):
				a = div.find_all('a')
				info.append(' '.join([i.text for i in a]))
		result['info'] = info
		items = profile.find('ul').find_all('li')
		for li in items:
			text = li.text.strip().split(':')
			if len(text) != 2:
				continue
			result[text[0].strip()] = text[1].strip()
		result['success'] = True
	except:
		result['success'] = False
	finally:
#		pprint(result)
		return result

def spoj(username):
	result = {}
	url = "https://www.spoj.com/users/" + username
	result['url'] = url
	try:
		soup = cook_soup(url)
		if type(soup) == 'str':
			result['success'] = False
			return result
		profile = soup.find('div', {'id': 'user-profile-left'})
		try:
			result['name'] = profile.find('h3').text
		except AttributeError:
			result['name'] = ''
		info = []
		p = profile.find_all('p')
		for i in p:
			info.append(i.text.strip())
		result['info'] = info
		stats = soup.find('dl', {'class': 'dl-horizontal profile-info-data profile-info-data-stats'})
		dd = stats.find_all('dd')
		result['solved'] = dd[0].text.strip()
		result['submitted'] = dd[1].text.strip()
		result['success'] = True
	except:
		result['success'] = False
	finally:
#		pprint(result)
		return result

if __name__ == '__main__':
	codechef('yogeshkr0007')
	codeforces('dreamplay')
	codechef('brat_96')
	codeforces('vsp4')
	spoj('yogeshkr0007')
	codechef('alsdjfd')
	codeforces('qwertytthfgd')
	spoj('malghasdjfn')
