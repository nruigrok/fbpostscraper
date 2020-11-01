# login and scroll routine are based on
# https://github.com/harismuneer/Ultimate-Facebook-Scraper
from urllib.parse import unquote
from amcatclient import AmcatAPI

import amcatclient
import locale
import datetime

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
import logging
import re



def fbposturl(url):
    try:
        if "?__xts__" in url:
            url = url.split("?__xts__")[0]
    except NoSuchElementException:
        logging.debug(f"Cannot parse url {url}")
        try:
            if "?type=" in url:
                url = url.split("?__xts__")[0]
        except NoSuchElementException:
            logging.debug(f"Cannot parse url {url}")
    #return f"https://www.facebook.com/{url}"
    return url


def fburl(url):
    if url.startswith("https://l.facebook.com/l.php?u="):
        url = url[len("https://l.facebook.com/l.php?u="):]
        url = unquote(url)
        url = re.sub(r"\?fbclid=[\w-]+&h=[\w-]+$", "", url)
    else:
        url = "-"
    return url


def fbnumber(text):
    m = re.match(r"([0-9,\.]+) ?([a-zA-Z\.]+)?", text)
    if not m:
        raise ValueError(f"Cannot match FB number string {text}")
    num, spec = m.groups()
    num = float(num.replace(",", "."))
    if spec == 'd.':
        num = num*1000
    return int(num)


def get_browser_preferences():
    yield "dom.push.enabled", False

DRIVER = None
def get_driver():
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
 #   options.add_argument("dom.push.enabled", False)
    fp = webdriver.FirefoxProfile()
    for k, v in get_browser_preferences():
        fp.set_preference(k, v)
    driver = webdriver.Firefox(firefox_profile=fp)
    global DRIVER
    DRIVER = driver
    return driver


class FBPostScraper:
    def safe_find_element_by_id(self, elem_id):
        try:
            return self.driver.find_element_by_id(elem_id)
        except NoSuchElementException:
            return None

    def __init__(self, email, password):
        self.driver = get_driver()
        self.login(email, password)

    def login(self, email, password):
        fb_path = "https://facebook.com"
        self.driver.get(fb_path)
        self.driver.maximize_window()
        # filling the form
        self.driver.find_element_by_name('email').send_keys(email)
        self.driver.find_element_by_name('pass').send_keys(password)

        # clicking on login button
        def click_login(driver):
            try:
                driver.find_element_by_id('u_0_d').click()
                return True
            except NoSuchElementException:
                return False
        WebDriverWait(self.driver, 5, 1).until(click_login)

        # if your account uses multi factor authentication
        mfa_code_input = self.safe_find_element_by_id('approvals_code')

        if mfa_code_input is None:
            return

        mfa_code_input.send_keys(input("Enter MFA code: "))
        self.driver.find_element_by_id('checkpointSubmitButton').click()
        # there are so many screens asking you to verify things. Just skip them all

        while self.safe_find_element_by_id('checkpointSubmitButton') is not None:
            dont_save_browser_radio = self.safe_find_element_by_id('u_0_3')
            if dont_save_browser_radio is not None:
                dont_save_browser_radio.click()

            self.driver.find_element_by_id('checkpointSubmitButton').click()

    def get_posts(self, page, max_scrolls=100000, date_from=None, date_to=None):
        self.driver.get(f"https://facebook.com/{page}")
        scraped_urls = set()
        post_xpath = "//div[@class='du4w35lb k4urcfbm l9j0dhe7 sjgh65i0']"
        posts_counter = 1
        def has_more_posts(driver):
            nonlocal posts_counter
            nposts = len(self.driver.find_elements_by_xpath(post_xpath))
            logging.info(f"Found {nposts} posts, had {posts_counter} posts")
            result = nposts > posts_counter
            posts_counter = nposts
            return result
        WebDriverWait(self.driver, 5, 1).until(has_more_posts)
        for i in range(max_scrolls):
            logging.info(f"... scroll {i}/{max_scrolls}, scraped {len(scraped_urls)} articles so far")
            self.scroll_once()
            WebDriverWait(self.driver, 5, 1).until(has_more_posts)
            for e in self.driver.find_elements_by_xpath(post_xpath):
                try:
                    id = e.find_element_by_xpath(".//a[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 a8c37x1j p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 p8dawk7l']")
                    url = id.get_attribute("href")
                except NoSuchElementException:
                    # maybe it's a video link
                    try:
                        video = e.find_element_by_css_selector("video.k4urcfbm.datstx6m.a8c37x1j")
                        url = video.get_attribute("src")
                    except NoSuchElementException:
                        # maybe it is a different video link
                        try:
                            video = e.find_element_by_css_selector("div.i09qtzwb.rq0escxv.n7fi1qx3.pmk7jnqg.j9ispegn.kr520xx4.bp9cbjyn.j83agx80.taijpn5t")
                            url = video.get_attribute("src")
                        except NoSuchElementException:
                            # maybe it is just a photo
                            try:
                                img = e.find_element_by_xpath(".//img[@class='i09qtzwb n7fi1qx3 datstx6m pmk7jnqg j9ispegn kr520xx4 k4urcfbm bixrwtb6']")
                                url = img.get_attribute("src")
                            except NoSuchElementException:
                                # maybe it is just another photo
                                try:
                                    img = e.find_element_by_xpath(
                                        ".//img[@class='k4urcfbm bixrwtb6 datstx6m q9uorilb']")
                                    url = img.get_attribute("src")
                                except NoSuchElementException:
                                    try:
                                        id = e.find_element_by_xpath(
                                            ".//a[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl gmql0nx0 gpro0wi8 datstx6m pmk7jnqg j9ispegn kr520xx4 k4urcfbm tkr6xdv7']")
                                        url = id.get_attribute("href")
                                    except NoSuchElementException:
                                        continue
               # print(f"gevonden{url} in scraped ids? {url in scraped_urls}")
                if url not in scraped_urls:
                    post = self.scrape_post(e, url)
                    if date_from and post['date'] < date_from:
                        logging.info(f"Last post is from {post['date']} < {date_from}, returning")
                        return
                    if date_to and post['date'] > date_to:
                        continue
                    yield post
                scraped_urls.add(url)

    def scroll_once(self, timeout=8):
        old_height = self.driver.execute_script("return document.body.scrollHeight")

        def check_height(driver):
            new_height = driver.execute_script("return document.body.scrollHeight")
            return new_height != old_height

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#        WebDriverWait(self.drwwq222iver, timeout, 0.5).until(check_height)

    def scrape_post(self, e: WebElement, url: str) -> dict:
        date = e.find_element_by_css_selector("span.tojvnm2t.a6sixzi8.abs2jz4q.a8s20v7p.t1p8iaqh.k5wvi7nf.q3lfd5jv.pk4s997a.bipmatt0.cebpdrjk.qowsmv63.owwhemhu.dp1hu0rb.dhp61c6y.iyyx5f41").text
        print(0, date)
        if not date:
    #except NoSuchElementException:
            date = e.find_element_by_css_selector("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.gmql0nx0.gpro0wi8.b1v8xokw").text
            print(1,date)
        locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
        if re.search(r'\du', date):
            date = datetime.datetime.today()
            print(2,date)
        elif re.search(r'\dm',date):
            date = datetime.datetime.today()
            print(3,date)
        elif 'Gisteren' in date:
            datum = datetime.datetime.today()
            date = datum - datetime.timedelta(days=1)
            print(4,date)
        elif re.search(r'om', date):
            m = re.match(r"(\d+ \w+) om (\d\d:\d\d)", date)
            date, time = m.groups()
            date = f"{date} 2020 {time}"
            date = datetime.datetime.strptime(date, "%d %B %Y %H:%M")
            print(5, date)
        else:
            m = re.match(r"(\d+ \w+)", date)
            date = m[1]
            date = f"{date} 2020"
            print(9,date)
            date = datetime.datetime.strptime(date, "%d %B %Y")
          #  date = datetime.datetime.strptime(date, "%d %B")
            print(6, date)
        try:
            headline = e.find_element_by_css_selector("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.oo9gr5id.gpro0wi8.lrazzd5p").text
        except NoSuchElementException:
            logging.debug(f"No headline by: {e}")
            headline = "-"
        print(headline)
        try:
            url = e.find_element_by_css_selector(".fsm > ._5pcq")
            url = fbposturl(url.get_attribute("href"))
        except NoSuchElementException:
            logging.debug(f"No url by: {e}")
            url = "-"
        print(url)
        try:
            date = e.find_element_by_css_selector("abbr._5ptz")
            date = date.get_attribute("title")
            date = datetime.strptime(date, "%d-%m-%Y %H:%M")
        except NoSuchElementException:
            logging.debug(f"No headline by: {e}")
            date = "01-01-1990 00:00"
            date = datetime.strptime(date, "%d-%m-%Y %H:%M")
        print(date)
        article = dict(title=headline, date=date, text=msg, url=url)
        try:
            msg = e.find_element_by_css_selector("div.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.c1et5uql.ii04i59q").text
        except NoSuchElementException:
            logging.debug(f"No message by: {e}")
            msg = "-"
        if msg.strip() == "":
            logging.debug(f"No message by: {e}")
            msg = "-"
        #url = e.find_element_by_css_selector("a.oajrlxb2.g5ia77u1.qu0x051f.esr5mh6w.e9989ue4.r7d6kgcz.rq0escxv.nhd2j8a9.nc684nl6.p7hjln8o.kvgmc6g5.cxmmr5t8.oygrvhab.hcukyx3x.jb3vyjys.rz4wbd8a.qt6c0cv9.a8nywdso.i1ao9s8h.esuyzwwr.f1sip0of.lzcic4wl.oo9gr5id.gpro0wi8.lrazzd5p")
        #url = fbposturl(url.get_attribute("href"))
        article = dict(title=headline, date=date, text=msg, url=url, medium="dtvnieuws")
      #  print(f"artikel is {headline},{date}")
        try:
            lijst = [x.text for x in e.find_elements_by_xpath(".//div[@class='oajrlxb2 g5ia77u1 qu0x051f esr5mh6w e9989ue4 r7d6kgcz rq0escxv nhd2j8a9 nc684nl6 p7hjln8o kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x jb3vyjys rz4wbd8a qt6c0cv9 a8nywdso i1ao9s8h esuyzwwr f1sip0of lzcic4wl l9j0dhe7 abiwlrkh gpro0wi8 dwo3fsh8 ow4ym5g4 auili1gw du4w35lb gmql0nx0']")]
            for i in lijst:
                if 'opmerkingen' in i:
                    remarks = i
                    article['nremarks'] = fbnumber(remarks)
                else:
                    article['nremarks'] = 0
                if 'gedeeld' in i:
                    share = i
                    article['nshares'] = fbnumber(share)
                else:
                    article['nshares'] = 0
        except NoSuchElementException:
            logging.debug(f"No remarks by: {e}")
        try:
            share = e.find_element_by_xpath("//div[@class='bp9cbjyn m9osqain j83agx80 jq4qci2q bkfpd7mw a3bd9o3v kvgmc6g5 wkznzc2l oygrvhab dhix69tm jktsbyx5 rz4wbd8a osnr6wyh a8nywdso s1tcr66n']").text
            article["shares"] = fbnumber(share)
        except NoSuchElementException:
            logging.debug(f"No shares by: {e}")
        try:
            link = e.find_element_by_css_selector("._52c6")
            link = link.get_attribute("href")
            article["article_url"]= fburl(link)
        except NoSuchElementException:
            logging.debug(f"No link by: {e}")
        return article



