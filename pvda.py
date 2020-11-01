import datetime
import re
from datetime import datetime

import requests
from lxml import html

# Make sure to use Dutch date formats
import locale
locale.setlocale(locale.LC_TIME, "nl_NL.utf8")

URL_TEMPLATE = "https://www.pvda.nl/nieuws/page/{page}"
URL_ROOT = "https://www.pvda.nl/nieuws"

def get_css(tree, selection, text=True, error=True):
    res = tree.cssselect(selection)
    if len(res) != 1:
        if not error:
            return None
       # raise ValueError("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
        raise Warning("Selection {selection} yielded {n} results".format(n=len(res), **locals()))
    return res[0]
    
def scrape_pb(url, date, headline):
    print(url)
    page = requests.get(url)
    tree = html.fromstring(page.text)
    lead = tree.cssselect("div.siteorigin-widget-tinymce.textwidget")
    lead = lead[0].text_content()
    author = tree.cssselect("div.related-excerpt h2")
    if not author:
        author ="PvdA"
    else:
        author = author[0].text_content().strip()
    quotes = tree.cssselect("div.content blockquote")
    quote = []
    for q in quotes:
        q2 = q.text_content()
        quote.append(q2)
    quote = "\n\n".join(quote)
    content = tree.cssselect("div.content")
    body2=[]
    for cont in content:
        text = cont.text_content()
        body2.append(text)
    body2 = "\n\n".join(body2)
    return {"headline": headline,
            "lead": lead,
            "text": body2,
            "author": author,
            "date": date,
            "medium": "PvdA site",
            "quotes": quote,
            "url": url}

def get_links():
    for page in range(1, 823):
        url = URL_TEMPLATE.format(**locals())
        print(url)
        page = requests.get(url)
        open("/tmp/test.html","w").write(page.text)
        tree = html.fromstring(page.text)
        posts = tree.cssselect(".partial-post")
        for post in posts:
            # is hetzelfde als de title,= notatie
            #titles = post.cssselect("h2")
            #if len(titles) != 1:
            #    raise Exception("Boe")
            #title = titles[0]
            link, = post.cssselect("h2 > a")
            href = link.get("href")
            if not href.startswith("https://www.pvda.nl/nieuws/"):
                continue
            else:
                headline = link.text_content().strip()
                meta, = post.cssselect("span.meta")
                datestr = meta.text_content()
                m = re.match(r"(\d+ \w+ \d{4})", datestr.strip())
                if not m:
                    raise ValueError(f"Cannot prase date: {datestr}")
                datestr2 = m.group(1)
                date = datetime.strptime(datestr2, "%d %B %Y")
                yield date, headline, href

#a = scrape_pb("/actueel/nieuws/2019/03/04/reactie-minister-blok-op-het-terugroepen-van-de-nederlandse-ambassadeur-uit-iran")
#print(a)
#sys.exit()
from amcatclient import AmcatAPI
conn = AmcatAPI("https://amcat.nl")
for date, headline, href in get_links():
    a = scrape_pb(href, date, headline)
    conn.create_articles(2051, 80339, [a])
    
