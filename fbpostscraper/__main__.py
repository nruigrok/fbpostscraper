"""
Selenium-based Facebook Post scraper.

Make sure chrome and chromedriver are installed, see https://github.com/nruigrok/fbpostscraper.
Output is a csv file written to standard out.
"""

from fbpostscraper import FBPostScraper
import argparse
import sys
import csv
import logging

parser = argparse.ArgumentParser(description=__doc__, prog="python -m fbpostscraper")
parser.add_argument("page", help="Name of the FB page to scrape")
parser.add_argument("--username", "-u", help="Username to login to FB. Can also supply from fbcredentials_example.py file")
parser.add_argument("--password", "-p", help="Password to login to FB. Can also supply from fbcredentials_example.py file")
parser.add_argument("--verbose", "-v", help="Verbose mode: also print debug messages",  action="store_true")
parser.add_argument("--quiet", "-q", help="Quiet mode: only print warning and error messages",  action="store_true")
parser.add_argument("--max-scrolls", "-m", type=int, default=10, help="Maximum number of pages to scroll down")

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

logging.info(f"Logging in to facebook as {username}")
scraper = FBPostScraper(username, password)
try:
    w = csv.writer(sys.stdout)
    for i, post in enumerate(scraper.get_page_posts(args.page, max_scrolls=args.max_scrolls)):
        if i == 0:
            keys = list(post.keys())
            w.writerow(post.keys())
        w.writerow([post[k] for k in keys])
finally:
    scraper.driver.close()
