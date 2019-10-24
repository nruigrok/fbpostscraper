# login and scroll routine are based on
# https://github.com/harismuneer/Ultimate-Facebook-Scraper

import amcatclient

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import logging

POST_ELEMENTS = "//div[@class='_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8']"

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
        self.driver.find_element_by_id('loginbutton').click()

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

    def get_posts(self):
        for i, e in enumerate(self.driver.find_elements_by_xpath(POST_ELEMENTS)):
            msg = e.find_element_by_css_selector(".userContent").text
            date = e.find_element_by_css_selector("abbr._5ptz").text
            try:
                reaction = e.find_element_by_css_selector("._81hb").text
            except NoSuchElementException:
                logging.debug(f"No reaction found: {e}")
                reaction = None
            try:
                opmerking = e.find_element_by_css_selector("._3hg-").text
            except NoSuchElementException:
                logging.debug(f"Geen opmerkingen bij: {e}")
                opmerking = None
            try:
                shares = e.find_element_by_css_selector("._3rwx").text
            except NoSuchElementException:
                logging.debug(f"Geen shares bij: {e}")
                shares = None
            try:
                link = e.find_element_by_css_selector("._52c6").text
            except NoSuchElementException:
                logging.debug(f"Geen link bij: {e}")
                link = None
            yield dict(message=msg, date=date, reaction=reaction, ncomments=opmerking, nshares=shares, link=link)

    def get_page_posts(self, page, max_scrolls=10):
        self.driver.get(f"https://facebook.com/{page}")
        self.scroll(max_scrolls=max_scrolls)
        return self.get_posts()
