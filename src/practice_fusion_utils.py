from datetime import datetime, date
import time
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

from shared import ptmlog
from models import PracticeFusionAppointment
import callharbor_utils


SCHEDULE_PAGE_URL = 'https://static.practicefusion.com/apps/ehr/index.html?utm_source=exacttarget&utm_medium=email&utm_campaign=InitialSetupWelcomeAddedUser#/PF/schedule/scheduler/agenda'
LOGIN_PAGE_URL = 'https://static.practicefusion.com/apps/ehr/index.html#/login'


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


def login(driver: webdriver.Chrome):
    logger = ptmlog.get_logger()

    PRACTICEFUSION_USERNAME = os.environ['PRACTICEFUSION_USERNAME']
    PRACTICEFUSION_PASSWORD = os.environ['PRACTICEFUSION_PASSWORD']

    logger.info('logging into practice fusion', username=PRACTICEFUSION_USERNAME)

    driver.get(LOGIN_PAGE_URL)

    # USERNAME
    username_field = driver.find_element(By.ID, 'inputUsername')
    username_field.clear()
    username_field.send_keys(PRACTICEFUSION_USERNAME)

    # PASSWORD
    driver.find_element(By.ID, 'inputPswd').send_keys(PRACTICEFUSION_PASSWORD)

    # SUBMIT
    driver.find_element(By.ID, 'loginButton').click()

    # MFA
    logger.info('handling mfa')
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'sendCallButton'))) # Wait for the MFA page to load
    driver.find_element(By.ID, 'sendCallButton').click()    # Click the "Send Call" button

    time.sleep(5)
    mfa_code = callharbor_utils.get_latest_mfa_code()       # Get the latest MFA code from CallHarbor

    driver.find_element(By.ID, 'code').send_keys(mfa_code)  # Enter the MFA code
    driver.find_element(By.ID, 'sendCodeButton').click()    # Click submit

    # Wait for the MFA process to complete and navigate to the next page
    WebDriverWait(driver, 20).until(EC.url_changes)  # type: ignore
    time.sleep(2)


def go_back_one_day(driver: webdriver.Chrome):
    logger = ptmlog.get_logger()

    try:
        decrement_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@class='btn-sm decrement-date']")
            )
        )
        decrement_button.click()
        time.sleep(1)  # Small delay between clicks
    except:
        logger.exception('error clicking decrement button')
        raise


def set_schedule_page_to_date(driver: webdriver.Chrome, target_date: date):
    """
    Set the schedule page to the specified date by going back the calculated number of days.
    Expects a driver that has already logged into Practice Fusion.
    """
    logger = ptmlog.get_logger()

    # Reset the schedule page to the default state by navigating away and then back
    logger.info('resetting schedule page to default state')
    driver.get('https://google.com/')
    time.sleep(2)
    driver.get(SCHEDULE_PAGE_URL)

    # Calculate days to go back
    current_date = datetime.now().date()
    days_difference = (current_date - target_date).days

    # Click decrement button the calculated number of times
    if days_difference > 0:
        logger.info(f'going back {days_difference} days from current date to reach {target_date}')
        
        # Wait for page to be fully loaded
        time.sleep(5)
        
        for _ in range(days_difference):
            go_back_one_day(driver)


def get_schedule_page_content(driver: webdriver.Chrome, target_date: date) -> str:
    logger = ptmlog.get_logger()

    set_schedule_page_to_date(driver, target_date)

    # Call this function before interacting with elements that might trigger alerts
    try:
        logger.info('accepting alert')
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        logger.info('no alert to accept')

    time.sleep(10)

    # Wait until the schedule button is clickable
    logger.info('clicking schedule button')
    schedule_button_xpath = "//button[@class='btn--default' and @data-element='btn-schedule-print']"
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, schedule_button_xpath))).click()

    time.sleep(3)
    return driver.page_source


def parse_schedule_page_content(page_content: str) -> list[PracticeFusionAppointment]:
    soup = BeautifulSoup(page_content, 'html.parser')

    # Get the date from the page
    h3_elements = soup.find_all('h3')
    header_date_string = None
    for h3 in h3_elements:
        if h3.text.startswith('Schedule Standard view - '):
            header_date_string = h3.text.split('Schedule Standard view - ')[1].strip()
            break
    if header_date_string is None:
        raise ValueError('Could not find the date in the header')
    else:
        schedule_date = datetime.strptime(header_date_string, '%A, %B %d, %Y').date()

    # Get all the rows in the table
    table = soup.find('table', {'data-element': 'table-agenda-print'})
    rows = table.find_all('tr')  # type: ignore

    # Iterate through the rows (skipping the header row) and extract the data
    appointments: list[PracticeFusionAppointment] = []
    for row in rows[1:]:
        # get column values
        status_column_text   = row.find('td', {'class': 'status-column'}).text   # type: ignore
        patient_column_text  = row.find('td', {'class': 'patient-column'}).text  # type: ignore
        time_column_text     = row.find('td', {'class': 'time-column'}).text     # type: ignore
        provider_column_text = row.find('td', {'class': 'provider-column'}).text # type: ignore
        type_column_text     = row.find('td', {'class': 'type-column'}).text     # type: ignore

        # Parse simple values from the columns
        appointment_status   = status_column_text.strip()
        appointment_provider = provider_column_text.strip()
        appointment_type     = type_column_text.strip()

        # Parse the patient column
        patient_column_split = re.split(r'\s*\n\s*', patient_column_text.strip())
        patient_name_raw  = patient_column_split[0]
        patient_dob_raw   = patient_column_split[1]
        patient_phone_raw = patient_column_split[3]

        patient_name  = patient_name_raw.strip()
        patient_dob   = datetime.strptime(patient_dob_raw.strip(), '%m/%d/%Y').date()
        patient_phone = re.sub(r'\D', '', patient_phone_raw.strip())

        # Parse the time column
        appointment_time = datetime.strptime(time_column_text.strip(), '%I:%M %p').time()
        appointment_time = datetime.combine(schedule_date, appointment_time)

        appointments.append(PracticeFusionAppointment(
            patient_name       = patient_name,
            appointment_status = appointment_status,
            patient_dob        = patient_dob,
            patient_phone      = patient_phone,
            provider           = appointment_provider,
            type               = appointment_type,
            appointment_time   = appointment_time,
        ))

    return appointments


def get_appointments(target_dates: list[date]) -> list[PracticeFusionAppointment]:
    driver = initialize_driver()
    login(driver)

    # Get the schedule page content for each target date
    schedule_pages: list[str] = []
    for target_date in target_dates:
        schedule_pages.append(get_schedule_page_content(driver, target_date))
    driver.quit()

    # Parse the schedule page content for each target date
    appointments: list[PracticeFusionAppointment] = []
    for schedule_page_content in schedule_pages:
        appointments.extend(parse_schedule_page_content(schedule_page_content))
    
    return appointments


if __name__ == "__main__":
    target_date = datetime.now().date()
    get_appointments([target_date])
