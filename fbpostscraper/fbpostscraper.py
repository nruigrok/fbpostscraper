# login and scroll routine are based on
# https://github.com/harismuneer/Ultimate-Facebook-Scraper
from urllib.parse import unquote
from amcatclient import AmcatAPI

import amcatclient

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import logging
import re
from datetime import datetime

POST_ELEMENTS = "//div[@class='_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8']"

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

class FBPostScraper:
    def safe_find_element_by_id(self, elem_id):
        try:
            return self.driver.find_element_by_id(elem_id)
        except NoSuchElementException:
            return None

    def __init__(self, email, password):
        options = Options()
        #  Code to disable notifications pop up of Chrome Browser
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        # options.add_argument("headless")
        # install chrome web driver from http://chromedriver.chromium.org/downloads
        self.driver = webdriver.Chrome(executable_path="./chromedriver", options=options)
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

    def scroll(self, max_scrolls: int=10, timeout_per_scroll=8):
        for i in range(max_scrolls):
            logging.debug(f"... scroll {i}/{max_scrolls}")
            try:
                old_height = self.driver.execute_script("return document.body.scrollHeight")

                def check_height(driver):
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    return new_height != old_height

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                WebDriverWait(self.driver, timeout_per_scroll, 0.05).until(check_height)
            except TimeoutException:
                break

    @property
    def get_posts(self):
        for i, e in enumerate(self.driver.find_elements_by_xpath(POST_ELEMENTS)):
            msg = e.find_element_by_css_selector(".userContent").text
            date = e.find_element_by_css_selector("abbr._5ptz")
            date = date.get_attribute("title")
            date = datetime.strptime(date,"%d-%m-%Y %H:%M")
            try:
                reaction = e.find_element_by_css_selector("._81hb").text
                reactions = fbnumber(reaction)
            except NoSuchElementException:
                logging.debug(f"No reaction found: {e}")
                reactions = None
            try:
                nremark = e.find_element_by_css_selector("._3hg-").text
                nremarks = fbnumber(nremark)
            except NoSuchElementException:
                logging.debug(f"No remarks by: {e}")
                nremarks = None
            try:
                headline = e.find_element_by_css_selector(".mbs._6m6._2cnj._5s6c").text
            except NoSuchElementException:
                logging.debug(f"No headline by: {e}")
                headline = "-"
            try:
                share = e.find_element_by_css_selector("._3rwx").text
                shares = fbnumber(share)
            except NoSuchElementException:
                logging.debug(f"No shares by: {e}")
                shares = None
            try:
                link = e.find_element_by_css_selector("._52c6")
                link = link.get_attribute("href")
                link = fburl(link)
            except NoSuchElementException:
                logging.debug(f"No link by: {e}")
                link = None
            try:
                post_url = e.find_element_by_css_selector("._3hg-")
                post_url = post_url.get_attribute("href")
            except NoSuchElementException:
                logging.debug(f"No link by: {e}")
                post_url = None
            yield dict(headline=headline, message=msg, date=date, reactions=reactions, ncomments=nremarks, nshares=shares, link=link, post_url=post_url)

    def get_remarks(self):
            res = get_posts({key: dict[key] for key in dict.keys()
               & {'post_url'}})

    def get_page_posts(self, page, max_scrolls=10):
        self.driver.get(f"https://facebook.com/{page}")
        self.scroll(max_scrolls=max_scrolls)
        return self.get_posts


