#!/opt/anaconda3/bin/python

import json
import requests
import requests_cache
from bs4 import BeautifulSoup
from pprint import pprint

requests_cache.install_cache('data/firms_cache')


def get_forbes():
    url = 'https://www.forbes.com/best-management-consulting-firms/list/6/#tab:overall'
    rr = requests.get(url)
    soup = BeautifulSoup(rr.text, 'html.parser')
    import epdb; epdb.st()


def get_wikipedia():

    firms = {}

    url = 'https://en.wikipedia.org/wiki/List_of_management_consulting_firms'
    rr = requests.get(url)
    soup = BeautifulSoup(rr.text, 'html.parser')
    lis = soup.findAll('li')
    arefs = []
    for li in lis:
        _arefs = li.findAll('a')
        _arefs = [x for x in _arefs if x.attrs.get('href', '').startswith('/wiki')]
        _arefs = [x for x in _arefs if ':' not in x.attrs.get('href', '').lower()]
        _arefs = [x for x in _arefs if 'main_page' not in x.attrs.get('href', '').lower()]
        _arefs = [x for x in _arefs if '_by_' not in x.attrs.get('href', '').lower()]
        _arefs = [x for x in _arefs if x.attrs.get('title')]
        _arefs = [x for x in _arefs if 'list' not in x.attrs.get('title', '').lower()]
        _arefs = [x for x in _arefs if 'list' not in x.attrs.get('href', '').lower()]
        _arefs = [x for x in _arefs if 'category:' not in str(x.attrs.get('class', '')).lower()]
        arefs += _arefs
    pprint([x.attrs['href'] for x in arefs])
    for aref in arefs:
        name = aref.attrs['title']
        url = 'https://en.wikipedia.org' + aref.attrs['href']
        title = aref.text
        firms[name] = {
            'wiki_url': url,
            'name': name,
            'title': title
        }
    pprint(firms)

    keys = sorted(firms.keys())
    for key in keys:
        print('# {}'.format(key))
        rr = requests.get(firms[key]['wiki_url'])
        soup = BeautifulSoup(rr.text, 'html.parser')

        #<tr>
        #<th scope="row" style="padding-right:0.5em;">Industry</th>
        #<td class="category" style="line-height:1.35em;"><a href="/wiki/Management_consulting" title="Management consulting">Management consulting</a></td>
        #</tr>
        for tr in soup.findAll('tr'):
            th = tr.find('th')
            if not th:
                continue
            if 'style' not in th.attrs:
                continue
            if th.attrs['style'] != "padding-right:0.5em;":
                continue
            td = tr.find('td')
            if not td:
                continue
            thiskey = th.text.lower().replace('\n', '').strip()
            thiskey = thiskey.replace('\xa0', '')
            thisval = td.text.lower().replace('\n', ' ').strip()
            if (thiskey == 'website' or 'website' in thiskey):
                thisval = td.find('a').attrs['href']
                if thisval.startswith('www.'):
                    thisval = 'http://' + thisval
                if not thisval.startswith('http') and thisval.endswith('.com'):
                    thisval = 'http://' + thisval
                if not thisval.startswith('http') and '.com' in thisval:
                    thisval = 'http://' + thisval
                if not thisval.startswith('http'):
                    import epdb; epdb.st()

            firms[key][thiskey] = thisval
            #import epdb; epdb.st()

    pprint(firms)
    #import epdb; epdb.st()
    return firms

if __name__ == "__main__":
    #get_forbes()
    firms = get_wikipedia()
    with open('data/firms.json', 'w') as f:
        f.write(json.dumps(firms, indent=2, sort_keys=True))
