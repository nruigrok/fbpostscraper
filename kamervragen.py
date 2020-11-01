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
from datetime import date

URL_TEMPLATE = "https://www.openkamer.org/kamervragen/?page={page}"
URL_ROOT = "https://www.openkamer.org"

def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
        raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]
    
def scrape_pb(url):
    url = url
    print(url)
    page = requests.get(url)
    tree = html.fromstring(page.text)
    headline = get_css(tree, ".panel-heading h4")
    headline = headline.text_content()
    print(headline)
    indiener = get_css(tree, ".table.table-condensed th")
    indiener = indiener.text_content()
    print(indiener)
    lead = get_css(tree, "div.intro")
    lead = lead.text_content()
    date = get_css(tree, "p.article-meta")
    date = date.text_content()
    m = re.search((r'\d{2}-\d{2}-\d{4}'),(date))
    if m:
        date2 = datetime.datetime.strptime(m.group(), '%d-%m-%Y').date()
    content = tree.cssselect("div > div.contentBox")
    content += tree.cssselect("div.intro ~ p")
    body2=[]
    body2.append(lead)
    for cont in content:
        text = cont.text_content()
        body2.append(text)
    body2 = "\n\n".join(body2)
    date3 =date2
    return {"headline": headline,
            "text": body2,
            "date": date3,
            "medium": "Persberichten",
            "url": url}

def get_links():
    for page in range(1, 2):
        url = URL_TEMPLATE.format(**locals())
        print(url)
        page = requests.get(url)
        tree = html.fromstring(page.text)
        links = list(tree.cssselect('h5.kamervraag-panel-title-col a'))
        for a in links:
            l = a.get("href")
            link=URL_ROOT+l
            print(link)
            #if not link.startswith("/actueel/"):
             #   raise ValueError("Not a persbericht? {link}".format(**locals()))
            yield link


#a = scrape_pb("/actueel/nieuws/2019/03/04/reactie-minister-blok-op-het-terugroepen-van-de-nederlandse-ambassadeur-uit-iran")
#print(a)
#sys.exit()
from amcatclient import AmcatAPI
conn = AmcatAPI("http://localhost:8000")
for link in get_links():
    a = scrape_pb(link)
    conn.create_articles(2, 42, [a])
    
