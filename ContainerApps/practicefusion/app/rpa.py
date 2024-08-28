from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import LiteralString
import json
import logging
import pyotp
import re
import time
import os

# GLOBAL CONFIG
with open("config.json") as config_file:
    config = json.load(config_file)


def initialize_driver():
    logging.info('initialize_driver')

    options = Options()
    selenium_options = config['selenium_options']

    options.add_argument(f'--window-size={selenium_options["window_size"]}')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')

    # Set headless option based on config
    if selenium_options['headless']:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)
    logging.info('Driver initialized successfully.')

    return driver

def scrape_ch_mfa(driver):
    driver.execute_script("window.open('https://control.callharbor.com/portal/messages', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.find_element(By.NAME, "data[Login][username]").send_keys("sms@proactivemgmt")
    driver.find_element(By.NAME, "data[Login][password]").send_keys("kB8zaXGbDD4-xdk0")
    driver.find_element(By.XPATH, '//input[@class="btn btn-large color-primary" and @type="submit" and @value="Log In"]').click()
    
    WebDriverWait(driver, 10).until(EC.url_contains("https://control.callharbor.com/portal/login/mfa/1"))
    
    mfa_code = pyotp.TOTP("JINDQR33AJDPJXED").now()
    driver.find_element(By.NAME, "data[Login][passcode]").send_keys(mfa_code)
    driver.find_element(By.XPATH, '//input[@class="btn btn-large color-primary" and @type="submit" and @value="Submit"]').click()
    
    driver.get("https://control.callharbor.com/portal/messages")
    WebDriverWait(driver, 10).until(EC.url_contains("https://control.callharbor.com/portal/messages"))
    
    message_xpath = '/html/body/div[2]/div[5]/div[2]/div[2]/div[1]/table/tbody/tr[1]/td[4]/div'
    message_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, message_xpath)))
    
    message_text = message_element.text
    match = re.search(r"Your code is: (\d+)", message_text)
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    return match.group(1) if match else None


def handle_mfa(driver):
    logging.info('handle_mfa')
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'sendCallButton'))
    )

    send_call_button = driver.find_element(By.ID, 'sendCallButton')
    send_call_button.click()
    time.sleep(5)
    code = scrape_ch_mfa(driver)
    if not code:
        raise Exception('MFA code not retrieved.')

    code_field = driver.find_element(By.ID, 'code')
    code_field.send_keys(code)

    send_code_button = driver.find_element(By.ID, 'sendCodeButton')
    send_code_button.click()

    # Wait for the MFA process to complete and navigate to the next page
    WebDriverWait(driver, 20).until(EC.url_changes)


def login(driver):
    PRACTICEFUSION_USERNAME = os.getenv('PRACTICEFUSION_USERNAME')
    PRACTICEFUSION_PASSWORD = os.getenv('PRACTICEFUSION_PASSWORD')

    logging.info('Attempting login for user: %s', PRACTICEFUSION_USERNAME)
    driver.get('https://static.practicefusion.com/apps/ehr/index.html#/login')

    username_field = driver.find_element(By.ID, 'inputUsername')
    username_field.clear()
    username_field.send_keys(PRACTICEFUSION_USERNAME)

    password_field = driver.find_element(By.ID, 'inputPswd')
    password_field.send_keys(PRACTICEFUSION_PASSWORD)
    login_button = driver.find_element(By.ID, 'loginButton')
    login_button.click()

    # Handle MFA
    if config.get('mfa'):
        handle_mfa(driver)


def accept_alert(driver):
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        logging.info('accept_alert')


def get_appointments(driver):
    schedule_url: LiteralString = (
        "https://static.practicefusion.com/apps/ehr/index.html?utm_source=exacttarget&utm_medium=email&utm_campaign=InitialSetupWelcomeAddedUser#/PF/schedule/scheduler/agenda"
    )
    driver.get(schedule_url)
    # Call this function before interacting with elements that might trigger alerts
    accept_alert(driver)
    time.sleep(10)
    logging.info(f"driver.current_url: {driver.current_url}")

    if config.get("get_yestdays_records"):
        decrementbutton = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@class='btn-sm decrement-date']")
            )
        )
        if decrementbutton:
            decrementbutton.click()
            logging.info("decrementbutton clicked ")
        else:
            logging.info("decrementbutton not found ")

        time.sleep(10)

    # Wait until the button is clickable
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@class='btn--default' and @data-element='btn-schedule-print']",
            )
        )
    )
    logging.info("schedulebutton clicked ")
    button.click()

    time.sleep(3)
    # Find the HTML element representing the table
    table = driver.find_element(
        By.CSS_SELECTOR, 'table[data-element="table-agenda-print"]'
    )

    # Get all the rows in the table
    rows = table.find_elements(By.TAG_NAME, "tr")

    # Iterate through the rows (skipping the header row) and extract the data
    all_row_data = []
    for row in rows[1:]:
        cols = row.find_elements(By.TAG_NAME, "td")
        row_data = []
        for col in cols:
            cell_text = col.get_attribute("textContent").strip()
            contact_details = col.find_elements(By.CSS_SELECTOR, "div.contact-details")
            if contact_details:
                details = [
                    detail.text.strip()
                    for detail in contact_details[0].find_elements(By.TAG_NAME, "div")
                ]
                cell_text += f" ({', '.join(details)})"
            row_data.append(cell_text)
        all_row_data.append(row_data)

    appointments = []
    for row in all_row_data:
        phone_number = row[1].split("\n")[8].split("(, , )")[0].strip()
        patientPhone = "".join(filter(str.isdigit, phone_number))
        time_object = datetime.strptime(row[2], "%I:%M %p").time()
        # # Create a dummy date (e.g., today's date)
        dummy_date = datetime.today().date()
        # # Combine the time object with the dummy date
        appointmentTime = datetime.combine(dummy_date, time_object)
        patientDOBraw = row[1].split("\n")[3].strip()
        # Convert the input date string to a datetime object
        date_object: datetime = datetime.strptime(patientDOBraw, "%m/%d/%Y")
        patientDOB = date_object.strftime("%Y-%m-%d")

        appointment = {
            "patientName": row[1].split("\n")[0].strip(),
            "patientDOB": patientDOB,
            "patientPhone": patientPhone,
            "appointmentTime": appointmentTime.strftime("%Y-%m-%dT%H:%M"),
            "appointmentStatus": row[0],
            "provider": row[3],
            "type": row[4],
        }
        appointments.append(appointment)

    return appointments


def run_rpa():
    driver = initialize_driver()
    login(driver)
    time.sleep(2)
    appointments = get_appointments(driver)

    return appointments

if __name__ == "__main__":
    run_rpa()