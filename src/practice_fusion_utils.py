import asyncio
import re
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

import callharbor_utils
from models import PracticeFusionAppointment
from shared import ptmlog
from storage_state_persistence_utils import save_playwright_storage_state, get_playwright_storage_state

EASTERN_TZ = ZoneInfo('America/New_York')

BASE_URL      = 'https://static.practicefusion.com/apps/ehr/index.html'
LOGIN_URL     = 'https://static.practicefusion.com/apps/ehr/index.html#/login'
MAIN_PAGE_URL = 'https://static.practicefusion.com/apps/ehr/index.html#/PF/home/main'
LOGIN_URL     = 'https://static.practicefusion.com/apps/ehr/index.html#/login/securitycheck'
SCHEDULE_URL  = 'https://static.practicefusion.com/apps/ehr/index.html#/PF/schedule/scheduler/agenda'


async def handle_mfa(page: Page):
    await page.locator('#sendCallButton').click()
    await page.wait_for_timeout(30_000)  # Wait for the MFA code to be sent
    mfa_code = await callharbor_utils.get_latest_mfa_code()
    await page.locator('#code').fill(mfa_code)
    await page.click('#sendCodeButton')


async def login(page: Page) -> None:
    logger = ptmlog.get_logger()
    logger.info('logging into practice fusion')

    PRACTICEFUSION_USERNAME = os.environ['PRACTICEFUSION_USERNAME']
    PRACTICEFUSION_PASSWORD = os.environ['PRACTICEFUSION_PASSWORD']

    await page.goto(LOGIN_URL)

    # Fill out credentials and click login button
    await page.locator('#inputUsername').fill(PRACTICEFUSION_USERNAME)
    await page.locator('#inputPswd').fill(PRACTICEFUSION_PASSWORD)
    await page.locator('#loginButton').click()

    # Wait for the URL to change to the main page or the MFA page
    await page.wait_for_url(re.compile(r'(#\/login\/securitycheck|#\/PF\/home\/main)$'))
    if page.url.endswith('#/login/securitycheck'):
        logger.info('practice fusion mfa page detected, handling mfa')
        await handle_mfa(page)

    # If we are still not on the main page, something has gone wrong
    try:
        await page.wait_for_url(MAIN_PAGE_URL)
    except PlaywrightTimeoutError:
        logger.exception('timed out waiting for main page after login', actual_url=page.url)
        raise

    logger.info('successfully logged in to practice fusion')


async def set_schedule_page_to_date(page: Page, target_date: date) -> None:
    """
    Set the schedule page to the specified date by going back the calculated number of days.
    Expects a playwright page that has already logged into Practice Fusion.
    """
    logger = ptmlog.get_logger()

    # Reset the schedule page to the default state by navigating away and then back
    logger.info('setting schedule page to default state')
    await page.goto(BASE_URL)
    await page.goto(SCHEDULE_URL)

    # Calculate days to go back
    current_date = datetime.now(EASTERN_TZ).date()
    days_difference = (current_date - target_date).days

    # Click decrement button the calculated number of times
    if days_difference > 0:
        logger.info(f'going back {days_difference} days from current date to reach {target_date}')
        for _ in range(days_difference):
            await page.locator('.decrement-date').click()


async def get_schedule_page(page: Page, target_date: date) -> str:
    logger = ptmlog.get_logger()
    logger.info('getting schedule page content', target_date=target_date)

    # Set the schedule page to the target date
    await set_schedule_page_to_date(page, target_date)
    
    try:
        # Wait for a specific element that indicates the schedule is loaded
        await page.wait_for_selector('.agenda-container', timeout=30000)
        logger.info('schedule container loaded')

        # Open the print view with retries
        for attempt in range(3):
            try:
                await page.get_by_text('Print').click()
                logger.info('successfully clicked print button')
                break
            except PlaywrightTimeoutError:
                logger.warning(f'attempt {attempt + 1} to click print button failed. Retrying...')
                await page.wait_for_timeout(5000)
        else:
            logger.error('failed to click print button after multiple attempts.')
            raise
            
        content = await page.content()
        logger.info('successfully retrieved schedule page content', target_date=target_date)

    except PlaywrightTimeoutError:
        logger.error(f"Timeout waiting for schedule page elements. Current URL: {page.url}, Title: {await page.title()}")
        raise

    return content


async def get_schedule_pages(target_dates: list[date]) -> list[str]:
    HEADLESS: bool = os.getenv('HEADLESS', 'TRUE') == 'TRUE'
    
    schedule_pages: list[str] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(storage_state=get_playwright_storage_state('practicefusion'))
        page    = await context.new_page()
        try:
            await login(page)
            for target_date in target_dates:
                schedule_pages.append(await get_schedule_page(page, target_date))
        except:
            await page.screenshot(path='./screenshots/error_screenshot.png')
            raise
        finally:
            save_playwright_storage_state('practicefusion', await context.storage_state())
    
    return schedule_pages
    

def parse_schedule_page(schedule_page: str) -> list[PracticeFusionAppointment]:
    soup = BeautifulSoup(schedule_page, 'html.parser')

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


def parse_schedule_pages(schedule_pages: list[str]) -> list[PracticeFusionAppointment]:
    appointments: list[PracticeFusionAppointment] = []
    for page_content in schedule_pages:
        appointments.extend(parse_schedule_page(page_content))
    
    return appointments


async def get_appointments(target_dates: list[date]) -> list[PracticeFusionAppointment]:
    schedule_pages = await get_schedule_pages(target_dates)
    appointments = parse_schedule_pages(schedule_pages)
    
    return appointments


if __name__ == "__main__":
    target_date = datetime.now(EASTERN_TZ).date()
    asyncio.run(get_appointments([date(2025, 5, 1), date(2025, 5, 2)]))
