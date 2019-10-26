"""
Selenium-based Facebook Post scraper.

Make sure chrome and chromedriver are installed, see https://github.com/nruigrok/fbpostscraper.
Output is a csv file written to standard out.
"""
from amcatclient import AmcatAPI

from fbpostscraper import FBPostScraper
import argparse
import sys
import csv
import logging
from datetime import datetime


parser = argparse.ArgumentParser(description=__doc__, prog="python -m fbpostscraper")
parser.add_argument("page", help="Name of the FB page to scrape")
parser.add_argument("--username", "-u", help="Username to login to FB. Can also supply from fbcredentials_example.py file")
parser.add_argument("--password", "-P", help="Password to login to FB. Can also supply from fbcredentials_example.py file")
parser.add_argument("--verbose", "-v", help="Verbose mode: also print debug messages",  action="store_true")
parser.add_argument("--quiet", "-q", help="Quiet mode: only print warning and error messages",  action="store_true")
parser.add_argument("--max-scrolls", "-m", type=int, default=10, help="Maximum number of pages to scroll down")
parser.add_argument("--amcathost", "-a", help="Location of your AmCAT")
parser.add_argument("--project", "-p", help="Projectid in AmCAT")
parser.add_argument("--set", "-s", help="Setid in AmCAT")
parser.add_argument("--date", "-d", help="Date from which to scrape")


args = parser.parse_args()

loglevel = (logging.DEBUG if args.verbose else (logging.WARNING if args.quiet else logging.INFO))
logging.basicConfig(format='[%(asctime)s %(levelname)8s] %(message)s', level=loglevel)

username = args.username
password = args.password
if not username or not password:
    logging.debug("Username or password not given, importing fbcredentials")
    try:
        import fbcredentials
    except ImportError:
        print("Error: Username and password need to be supplied as arguments "
              "or in a fbcredentials_example.py file on the PYTHONPATH", file=sys.stderr)
        raise
if username is None:
    if fbcredentials.username is None:
        raise ValueError("Username not given in fbcredentials")
    username = fbcredentials.username
if password is None:
    if fbcredentials.password is None:
        raise ValueError("Password not given in fbcredentials")
    password = fbcredentials.password

date = datetime.strptime(args.date, "%d-%m-%Y")

logging.info(f"Logging in to facebook as {username}")
scraper = FBPostScraper(username, password)
try:
    posts = list(scraper.get_posts(args.page, max_scrolls=args.max_scrolls, date_from=date))
finally:
    pass#scraper.driver.close()

if args.amcathost:
    conn = AmcatAPI("http://localhost:8000")
    conn.create_articles(project=args.project, articleset=args.set, json_data=posts)
else:
    w = csv.writer(sys.stdout)
    for i, post in enumerate(posts):
        if i == 0:
            keys = list(post.keys())
            w.writerow(post.keys())
        w.writerow([post[k] for k in keys])






