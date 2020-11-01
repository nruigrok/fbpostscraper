from lxml import html, etree
from amcatclient import AmcatAPI
import requests
from itertools import count
from datetime import datetime
import html2text
import re
import datetime
import html2text
import sys
import locale
from datetime import date

URL_TEMPLATE = "https://www.om.nl/actueel/nieuwsberichten/?pager_page={page}"
URL_ROOT = "https://www.om.nl"

def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]
    
def scrape_pb(url, date):
    url = url
    page = requests.get(url)
    tree = html.fromstring(page.text)
    #headline = get_css(tree, "h1.grid-title"
    headline = tree.cssselect('h1.grid-title')
    headline = headline[0].text_content()
    locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
    date =  date
    lead = tree.cssselect('meta[property="dcterms:description"]')[0].get('content')
    if not lead:
        lead ="-"
    text = tree.cssselect('div.iprox-rich-content.iprox-content')
    if not text:
        text = tree.cssselect('div.iprox-rich-content.iprox-content p')
    body2 = []
    body2.append(lead)
    for t in text:
        t2 = t.text_content()
        body2.append(t2)
    body2 = "\n\n".join(body2).strip()
    return {"headline": headline,
            "lead" : lead,
            "text": body2,
            "date": date.isoformat(),
            "medium": "Persberichten OM",
            "url": url}


def get_links():
    for page in range(435, 734):
        url = URL_TEMPLATE.format(**locals())
        print(url)
        page = requests.get(url)
        open("/tmp/test.html","w").write(page.text)
        tree = html.fromstring(page.text)
        for article in tree.cssselect("#results .grid-element"):
            a, = article.cssselect('a.siteLink')
            link = a.get("href")
            if not link.startswith("https://www.om.nl/actueel/nieuwsberichten"):
                continue
            locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
            date, = article.cssselect("div.iprox-content.iprox-date.date")
            date = date.text_content().split("-")[0].strip()
            #date = date.text_content().strip()
            date2 = datetime.datetime.strptime(date, "%d %B %Y")
            yield link, date2

from amcatclient import AmcatAPI
conn = AmcatAPI("https://amcat.nl")
for link, date in get_links():
    a = scrape_pb(link, date)
    conn.create_articles(2088, 80277, [a])
    
