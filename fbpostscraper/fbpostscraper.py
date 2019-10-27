# login and scroll routine are based on
# https://github.com/harismuneer/Ultimate-Facebook-Scraper
from urllib.parse import unquote
from amcatclient import AmcatAPI

import amcatclient

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
import logging
import re
from datetime import datetime


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
    return f"https://www.facebook.com/{url}"


def fburl(url):
    if url.startswith("https://l.facebook.com/l.php?u="):
        url = url[len("https://l.facebook.com/l.php?u="):]
        url = unquote(url)
        url = re.sub(r"\?fbclid=[\w-]+&h=[\w-]+$", "", url)
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


def get_driver():
    options = Options()
    #  Code to disable notifications pop up of Chrome Browser
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    # options.add_argument("headless")
    # install chrome web driver from http://chromedriver.chromium.org/downloads
    return webdriver.Chrome(executable_path="./chromedriver", options=options)


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
                driver.find_element_by_id('loginbutton').click()
                return True
            except NoSuchElementException:
                return False
        WebDriverWait(self.driver, 5, 0.5).until(click_login)

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

    def get_posts(self, page, max_scrolls=10, date_from=None):
        self.driver.get(f"https://facebook.com/{page}")
        scraped_ids = set()
        post_xpath = "//div[@class='_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8']"
        for i in range(max_scrolls):
            logging.info(f"... scroll {i}/{max_scrolls}, scraped {len(scraped_ids)} articles so far")
            self.scroll_once()
            for e in self.driver.find_elements_by_xpath(post_xpath):
                id = e.get_attribute("id")
                if id not in scraped_ids:
                    post = self.scrape_post(e)
                    if date_from and post['date'] < date_from:
                        logging.info(f"Last post is from {post['date']} < {date_from}, returning")
                        return
                    yield post
                scraped_ids.add(id)

    def scroll_once(self, timeout=8):
        old_height = self.driver.execute_script("return document.body.scrollHeight")

        def check_height(driver):
            new_height = driver.execute_script("return document.body.scrollHeight")
            return new_height != old_height

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(self.driver, timeout, 0.05).until(check_height)

    def scrape_post(self, e: WebElement) -> dict:
        try:
            msg = e.find_element_by_css_selector(".userContent").text
        except NoSuchElementException:
            logging.debug(f"No text by: {e}")
            msg = "-"
        try:
            headline = e.find_element_by_css_selector(".mbs._6m6._2cnj._5s6c").text
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
            reaction = e.find_element_by_css_selector("._81hb").text
            article["reactions"] = fbnumber(reaction)
        except NoSuchElementException:
            logging.debug(f"No reaction found: {e}")
        try:
            nremark = e.find_element_by_css_selector("._3hg-").text
            article["nremarks"] = fbnumber(nremark)
        except NoSuchElementException:
            logging.debug(f"No remarks by: {e}")
        try:
            share = e.find_element_by_css_selector("._3rwx").text
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



