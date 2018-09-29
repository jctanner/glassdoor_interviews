#!/opt/anaconda3/bin/python

import argparse
import json
import os
import requests
import time
from selenium import webdriver
from bs4 import BeautifulSoup


#data//firms.json
#data//firms_cache.sqlite
#data//jobs_cache.sqlite
#data//jobs.json


def get_firms(filter=None):

    firms = []


    with open('data/firms.json', 'r') as f:
        fdata = json.loads(f.read())
    with open('data/jobs.json', 'r') as f:
        jdata = json.loads(f.read())
    
    if filter is None or filter == 'management_consulting':
        for k,v in fdata.items():
            try:
                str(k)
                #print(v['title'])
            except:
                continue
            firms.append(v['title'])

    if filter is None or filter == 'all':
        for k,v in jdata.items():
            try:
                #print(k)
                #print(v['company'])
                str(k)
                str(v['company'])
            except:
                continue
            firms.append(v['company'])


    firms = sorted(set(firms))

    return firms


def scrape_overview(driver):
    pg_src = driver.page_source
    pg_soup = BeautifulSoup(pg_src, 'html.parser')

    try:
        driver.find_element_by_id('ToggleOnObtainer').click()
    except:
        try:
            driver.find_element_by_link_text("More").click()
        except:
            pass

    aref = pg_soup.find('a', {'class': 'interviews'})
    spans = aref.findAll('span')
    total_interviews = spans[0].text.strip()
    print('\ttotal interviews: ',total_interviews)

    stats = {
        'total': total_interviews
    }

    iviewstats = pg_soup.find('div', {'id': 'AllStats'})
    if not iviewstats:
        return stats

    statrows = iviewstats.findAll('div', {'class': 'row'})
    statrows += iviewstats.findAll('div', {'class': 'row toggleBody fullHeight'})
    for sr in statrows:
        try:
            label = sr.find('label').text.strip().lower()
            if label.lower() in ['positive', 'negative', 'neutral']:
                continue
            sr_span = sr.find('span', {'class': 'strong pros pct'})
            percent = sr_span.text.strip()
            stats[label] = int(percent)
            print('\t',label,' ',percent)
        except:
            continue
    
    return stats


def get_interviews(start=None):

    driver = webdriver.PhantomJS()
    driver.set_window_size(1280, 1024)
    driver.get('https://www.glassdoor.com/index.htm')

    # https://www.glassdoor.com/profile/login_input.htm?userOriginHook=HEADER_SIGNIN_LINK
    # <a href="/profile/login_input.htm?userOriginHook=HEADER_SIGNIN_LINK" target="_top" class="sign-in">Sign In</a>
    driver.find_element_by_link_text("Sign In").click()
    driver.save_screenshot('data/signin.png')
    driver.find_element_by_id('signInUsername').send_keys('moot.xk@gmail.com')
    driver.find_element_by_id('signInPassword').send_keys('850077tttT')
    driver.save_screenshot('data/login_box.png')
    driver.find_element_by_id('signInBtn').click()
    time.sleep(1)
    driver.save_screenshot('data/signedin.png')
    
    #driver.get('https://www.glassdoor.com/Reviews/index.htm')
    #driver.save_screenshot('data/company_search.png')

    firms = get_firms()
    total_firms = len(firms)
    for idf,firm in enumerate(firms):

        if start and firm != start:
            continue
        elif start and firm == start:
            start = None

        stats_file = 'data/interviews/{}.json'.format(firm)
        if os.path.isfile(stats_file):
            continue

        print(str(total_firms),'|',str(idf),firm)
        driver.get('https://www.glassdoor.com/Reviews/index.htm')
        driver.save_screenshot('data/company_search.png')

        driver.find_element_by_id('KeywordSearch').send_keys(firm)
        driver.find_element_by_id('LocationSearch').clear()
        driver.find_element_by_id('LocationSearch').send_keys('New York, NY (US)')
        driver.save_screenshot('data/company_search_box.png')
        driver.find_element_by_id('HeroSearchButton').click()

        thisurl = driver.current_url
        print(thisurl)
        driver.save_screenshot('data/company_search_result--{}.png'.format(firm))
        pg_src = driver.page_source
        pg_soup = BeautifulSoup(pg_src, 'html.parser')

        # could be a irrelevant results page, a short list results OR a direct company page
        if thisurl.startswith('https://www.glassdoor.com/Overview'):
            stats = scrape_overview(driver)
            with open(stats_file, 'w') as f:
                f.write(json.dumps(stats, indent=2, sort_keys=True))
            #import epdb; epdb.st()

        elif thisurl in ['https://www.glassdoor.com/' + firm.lower(), 'https://www.glassdoor.com/' + firm]:
            stats = scrape_overview(driver)
            with open(stats_file, 'w') as f:
                f.write(json.dumps(stats, indent=2, sort_keys=True)) 

        elif thisurl.startswith('https://www.glassdoor.com/Reviews'):
            # probably a search result list with first res being the firm?
            pg_src = driver.page_source
            pg_soup = BeautifulSoup(pg_src, 'html.parser')

            # https://www.glassdoor.com/Overview/Working-at-100Kin10-EI_IE1467539.11,19.htm
            refs = pg_soup.findAll('a')
            refs = [x for x in refs if firm.lower() in x.attrs.get('href', '').lower()]
            refs = [x for x in refs if x.attrs.get('href', '').startswith('/Overview/')]
            refs = [x for x in refs if 'logo' not in x.text.lower()]

            if refs:
                driver.get(refs[0].attrs['href'])
                stats = scrape_overview(driver)
                with open(stats_file, 'w') as f:
                    f.write(json.dumps(stats, indent=2, sort_keys=True))

            #import epdb; epdb.st()
            #continue
        elif thisurl.startswith('https://www.glassdoor.com/Job/jobs.htm?'):
            # no results so defaulted back to a job search
            continue
        else:
            print('ERROR: What kind of url is this?')
            import epdb; epdb.st()
        #import epdb; epdb.st()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str)
    args = parser.parse_args()
    get_interviews(start=args.start)