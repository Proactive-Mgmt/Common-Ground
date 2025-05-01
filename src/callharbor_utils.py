import os
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import pyotp

from shared import ptmlog


def initialize_driver():
    HEADLESS = os.getenv('HEADLESS', 'TRUE')

    options = Options()

    options.add_argument(f'--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')

    # Set headless option based on config
    if HEADLESS != 'FALSE':
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    return driver


def get_latest_mfa_code() -> str:
    logger = ptmlog.get_logger()

    CALLHARBOR_USERNAME   = os.environ['CALLHARBOR_USERNAME']
    CALLHARBOR_PASSWORD   = os.environ['CALLHARBOR_PASSWORD']
    CALLHARBOR_MFA_SECRET = os.environ['CALLHARBOR_MFA_SECRET']

    driver = initialize_driver()

    driver.get('https://control.callharbor.com/portal/messages')
    driver.find_element(By.NAME, "data[Login][username]").send_keys(CALLHARBOR_USERNAME)
    driver.find_element(By.NAME, "data[Login][password]").send_keys(CALLHARBOR_PASSWORD)
    driver.find_element(By.XPATH, '//input[@class="btn btn-large color-primary" and @type="submit" and @value="Log In"]').click()
    
    WebDriverWait(driver, 10).until(EC.url_contains("https://control.callharbor.com/portal/login/mfa/1"))
    
    mfa_code = pyotp.TOTP(CALLHARBOR_MFA_SECRET).now()
    driver.find_element(By.NAME, "data[Login][passcode]").send_keys(mfa_code)
    time.sleep(2)
    driver.find_element(By.XPATH, '//input[@class="btn btn-large color-primary" and @type="submit" and @value="Submit"]').click()

    driver.get("https://control.callharbor.com/portal/messages")
    WebDriverWait(driver, 10).until(EC.url_contains("https://control.callharbor.com/portal/messages"))
    
    logger.info("getting most recent message")
    message_xpath = "//div[contains(@class, 'conversation-recent-msg')]"
    message_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, message_xpath)))
    message_text = message_element.text
    driver.close()

    # Extract code from message text
    match = re.search(r"Your code is: (\d+)", message_text)
    if not match:
        logger.exception('no mfa code found in call harbor message')
        raise Exception('no mfa code found in call harbor message')
    else:
        return match.group(1)
