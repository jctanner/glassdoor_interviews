#!/opt/anaconda3/bin/python

import json
import os
import requests
import requests_cache
import shutil
import tempfile
from bs4 import BeautifulSoup
from pprint import pprint

requests_cache.install_cache('data/jobs_cache')

JOBS = {}
VISITED = []
UNVISITED = []


def add_job(job):
    global JOBS
    if job['jobid'] in JOBS:
        return None
    if os.path.isfile('data/jobs.json'):
        try:
            with open('data/jobs.json', 'r') as f:
                JOBS.update(json.loads(f.read()))
        except json.decoder.JSONDecodeError:
            os.remove('data/jobs.json')
    JOBS[job['jobid']] = job.copy()

    tfo,tfn = tempfile.mkstemp()
    #import epdb; epdb.st()
    with open(tfn, 'w') as f:
        f.write(json.dumps(JOBS, indent=2, sort_keys=True))
    shutil.move(tfn, 'data/jobs.json')


def get_indeed_listings(next_page=None):

    global VISITED
    global UNVISITED
    global JOBS

    if next_page is None:
        next_page = 'https://www.indeed.com/jobs?q=management+consultant&l=New+York%2C+NY&radius=100'

    while next_page:

        print(len(JOBS.keys()))

        rr = requests.get(next_page)
        soup = BeautifulSoup(rr.text, 'html.parser')

        # <link rel="next" href="/jobs?q=management+consultant&l=New+York%2C+NY&radius=100&start=10" /><style type="text/css">
        _next_page = next_page
        try:
            next_page = 'https://www.indeed.com' + soup.find('link', {'rel': 'next'}).attrs['href']
        except:
            break
        print(next_page)

        if next_page in VISITED:
            break

        rows = soup.select("div[class$=result]")
        for row in rows:
            title = None
            try:
                titles = row.select("a[class$=turnstileLink]")
                title = titles[0].attrs['title']
            except Exception as e:
                #print(e)
                import epdb; epdb.st()
            #print(title)
            if not title:
                continue

            jobid = row.attrs['data-jk']

            # <span class="company">
            company = row.find('span', {'class': 'company'})
            company_name = company.text.strip()
            #print('\t' + company_name)

            # <span class="location">
            location = row.find('span', {'class': 'location'})
            location_name = location.text.strip()
            #print('\t' + location_name)

            add_job({
                'jobid': jobid,
                'title': title,
                'company': company_name,
                'location': location_name
            })

        VISITED.append(_next_page)
        if _next_page in UNVISITED:
            UNVISITED.remove(_next_page)

        # other starting points?
        # <a rel=nofollow href="/jobs?q=management+consultant&l=New+York,+NY&radius=100&rbl=New+York,+NY&jlid=45f6c4ded55c00bf" title="New York, NY (3573)">New York, NY</a> (3573)</li>
        refs = soup.findAll('a', {'rel': 'nofollow'})
        refs = [x.attrs['href'] for x in refs]
        refs = [x for x in refs if x.startswith('/jobs?')]
        refs = ['https://www.indeed.com' + x for x in refs]
        refs = [x for x in refs if x not in VISITED]
        UNVISITED += refs
        print(len(JOBS.keys()))


    '''
    while UNVISITED:
        UNIVISTED = sorted(set(UNVISITED))
        for ref in UNVISITED:
            get_indeed_listings(next_page=ref)
            UNVISITED.remove(ref)
    '''

    return JOBS


if __name__ == "__main__":

    get_indeed_listings()

    while UNVISITED:
        UNIVISTED = sorted(set(UNVISITED))
        for ref in UNVISITED:
            get_indeed_listings(next_page=ref)
            UNVISITED.remove(ref)