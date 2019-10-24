# login and scroll routine are based on
# https://github.com/harismuneer/Ultimate-Facebook-Scraper


from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import logging

def safe_find_element_by_id(driver, elem_id):
    try:
        return driver.find_element_by_id(elem_id)
    except NoSuchElementException:
        return None


def get_driver():
    options = Options()

    #  Code to disable notifications pop up of Chrome Browser
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    # options.add_argument("headless")
    # install chrome web driver from http://chromedriver.chromium.org/downloads
    return webdriver.Chrome(executable_path="./chromedriver", options=options)


def login(driver, email, password):
    fb_path = "https://facebook.com"
    driver.get(fb_path)
    driver.maximize_window()

    # filling the form
    driver.find_element_by_name('email').send_keys(email)
    driver.find_element_by_name('pass').send_keys(password)

    # clicking on login button
    driver.find_element_by_id('loginbutton').click()

    # if your account uses multi factor authentication
    mfa_code_input = safe_find_element_by_id(driver, 'approvals_code')

    if mfa_code_input is None:
        return

    mfa_code_input.send_keys(input("Enter MFA code: "))
    driver.find_element_by_id('checkpointSubmitButton').click()

    # there are so many screens asking you to verify things. Just skip them all
    while safe_find_element_by_id(driver, 'checkpointSubmitButton') is not None:
        dont_save_browser_radio = safe_find_element_by_id(driver, 'u_0_3')
        if dont_save_browser_radio is not None:
            dont_save_browser_radio.click()

        driver.find_element_by_id('checkpointSubmitButton').click()


def scroll(driver, max_scrolls: int=100, timeout_per_scroll=8):
    for i in range(max_scrolls):
        logging.debug(f"... scroll {i}/{max_scrolls}")
        try:
            old_height = driver.execute_script("return document.body.scrollHeight")

            def check_height(driver):
                new_height = driver.execute_script("return document.body.scrollHeight")
                return new_height != old_height

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, timeout_per_scroll, 0.05).until(check_height)
        except TimeoutException:
            break


POST_ELEMENTS = "//div[@class='_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8']"


def get_posts(driver):
    for i, e in enumerate(driver.find_elements_by_xpath(POST_ELEMENTS)):
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