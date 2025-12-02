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
from storage_state_persistence_utils import save_playwright_storage_state, get_playwright_storage_state, delete_playwright_storage_state

EASTERN_TZ = ZoneInfo('America/New_York')

BASE_URL           = 'https://static.practicefusion.com/apps/ehr/index.html'
LOGIN_URL          = 'https://static.practicefusion.com/apps/ehr/index.html#/login'
SECURITY_CHECK_URL = 'https://static.practicefusion.com/apps/ehr/index.html#/login/securitycheck'
MAIN_PAGE_URL      = 'https://static.practicefusion.com/apps/ehr/index.html#/PF/home/main'
SCHEDULE_URL       = 'https://static.practicefusion.com/apps/ehr/index.html#/PF/schedule/scheduler/agenda'


class SessionExpiredError(Exception):
    """Raised when the cached session is expired or invalid."""
    pass


async def validate_session(page: Page) -> bool:
    """
    Validate if the current session is still valid by attempting to access
    an authenticated page and checking for expected content.
    
    Returns True if session is valid, False if expired/invalid.
    """
    logger = ptmlog.get_logger()
    logger.info('validating cached session')
    
    try:
        # Try to navigate to the main page
        await page.goto(MAIN_PAGE_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)  # Give the SPA time to redirect if needed
        
        current_url = page.url
        logger.info('session validation navigation complete', current_url=current_url)
        
        # Check if we were redirected to login page (session expired)
        if '#/login' in current_url:
            logger.warning('session expired: redirected to login page', current_url=current_url)
            return False
        
        # Check if we're on an authenticated page
        if '#/PF/' in current_url:
            # Additional validation: check for authenticated UI elements
            try:
                # Look for elements that only appear when logged in (e.g., user menu, navigation)
                authenticated_element = await page.wait_for_selector(
                    'div[data-element="user-menu"], nav[data-element="main-nav"], .user-profile, .main-navigation',
                    timeout=5000
                )
                if authenticated_element:
                    logger.info('session validated successfully: authenticated UI elements found')
                    return True
            except PlaywrightTimeoutError:
                # If we can't find authenticated elements, session might be partially valid
                # but let's be conservative and consider it invalid
                logger.warning('session validation failed: no authenticated UI elements found')
                return False
        
        # If we're not on login or authenticated page, session is likely invalid
        logger.warning('session validation failed: unexpected page state', current_url=current_url)
        return False
        
    except PlaywrightTimeoutError:
        logger.warning('session validation failed: timeout during navigation')
        return False
    except Exception as e:
        logger.warning('session validation failed: unexpected error', error=str(e))
        return False


async def handle_mfa(page: Page):
    await page.locator('#sendCallButton').click()
    await page.wait_for_timeout(30_000)  # Wait for the MFA code to be sent
    mfa_code = await callharbor_utils.get_latest_mfa_code()
    await page.locator('#code').fill(mfa_code)
    await page.click('#sendCodeButton')


async def perform_credential_login(page: Page) -> None:
    """
    Perform a fresh login using credentials and handle MFA if required.
    This is called when session validation fails or force_fresh_login is True.
    """
    logger = ptmlog.get_logger()
    DEBUG_HTML: bool = os.getenv('DEBUG_HTML', 'FALSE') == 'TRUE'
    
    PRACTICEFUSION_USERNAME = os.environ['PRACTICEFUSION_USERNAME']
    PRACTICEFUSION_PASSWORD = os.environ['PRACTICEFUSION_PASSWORD']

    logger.info('performing credential login to practice fusion')
    await page.goto(LOGIN_URL, wait_until="domcontentloaded")
    
    # Save HTML at initial login page load
    if DEBUG_HTML:
        try:
            html_content = await page.content()
            with open('./screenshots/00_initial_login_page.html', 'w') as f:
                f.write(html_content)
            logger.info('saved initial login page HTML')
        except:
            logger.warning('failed to save initial login page HTML')

    # Fill out credentials and click login button
    await page.locator('#inputUsername').fill(PRACTICEFUSION_USERNAME)
    await page.locator('#inputPswd').fill(PRACTICEFUSION_PASSWORD)
    await page.locator('#loginButton').click()

    # Wait for the URL to change to the main page or the MFA page
    await page.wait_for_url(re.compile(r'(#\/login\/securitycheck|#\/PF\/home\/main)$'))
    
    # Save HTML after login attempt
    if DEBUG_HTML:
        try:
            html_content = await page.content()
            with open('./screenshots/00_after_login_click.html', 'w') as f:
                f.write(html_content)
            logger.info('saved HTML after login click')
        except:
            logger.warning('failed to save HTML after login click')
    
    if page.url.endswith('#/login/securitycheck'):
        logger.info('practice fusion mfa page detected, handling mfa')
        
        # Save HTML at MFA page
        if DEBUG_HTML:
            try:
                html_content = await page.content()
                with open('./screenshots/00_mfa_page.html', 'w') as f:
                    f.write(html_content)
                logger.info('saved MFA page HTML')
            except:
                logger.warning('failed to save MFA page HTML')
        
        await handle_mfa(page)
        
        # Save HTML after MFA
        if DEBUG_HTML:
            try:
                html_content = await page.content()
                with open('./screenshots/00_after_mfa.html', 'w') as f:
                    f.write(html_content)
                logger.info('saved HTML after MFA')
            except:
                logger.warning('failed to save HTML after MFA')

    # If we are still not on the main page, something has gone wrong
    try:
        await page.wait_for_url(MAIN_PAGE_URL)
    except PlaywrightTimeoutError:
        logger.exception('timed out waiting for main page after login', actual_url=page.url)
        # Save HTML on error
        if DEBUG_HTML:
            try:
                html_content = await page.content()
                with open('./screenshots/00_login_error.html', 'w') as f:
                    f.write(html_content)
                logger.info('saved HTML on login error')
            except:
                pass
        raise

    logger.info('credential login successful')


async def login(page: Page, skip_session_validation: bool = False) -> None:
    """
    Login to Practice Fusion, using cached session if valid.
    
    This function first validates the cached session. If the session is expired
    or invalid, it performs a fresh credential login with MFA.
    
    Args:
        page: Playwright page object
        skip_session_validation: If True, skip validation and go straight to credential login
    """
    logger = ptmlog.get_logger()
    DEBUG_HTML: bool = os.getenv('DEBUG_HTML', 'FALSE') == 'TRUE'
    logger.info('logging into practice fusion')

    if skip_session_validation:
        logger.info('skipping session validation, performing fresh credential login')
        await perform_credential_login(page)
        return

    # First, validate if the cached session is still valid
    session_valid = await validate_session(page)
    
    if session_valid:
        logger.info('cached session is valid, skipping credential login')
        # Navigate to main page to ensure we're in a good state
        await page.goto(MAIN_PAGE_URL, wait_until="domcontentloaded")
    else:
        logger.warning('cached session is invalid or expired, performing fresh credential login')
        await perform_credential_login(page)

    logger.info('successfully logged in to practice fusion')


async def set_schedule_page_to_date(page: Page, target_date: date) -> None:
    """
    Set the schedule page to the specified date by going back the calculated number of days.
    Expects a playwright page that has already logged into Practice Fusion.
    """
    logger = ptmlog.get_logger()

    # Navigate directly to the schedule view; SPA may never reach reliable network idle
    logger.info('setting schedule page to default state')
    await page.goto(SCHEDULE_URL, wait_until="domcontentloaded")
    
    # Save HTML after navigating to schedule URL
    DEBUG_HTML: bool = os.getenv('DEBUG_HTML', 'FALSE') == 'TRUE'
    if DEBUG_HTML:
        try:
            html_content = await page.content()
            with open('./screenshots/02_schedule_url_loaded.html', 'w') as f:
                f.write(html_content)
            logger.info('saved HTML after schedule URL load')
        except:
            logger.warning('failed to save HTML after schedule URL load')

    # Ensure we actually landed on the schedule page; if not, try UI navigation fallback
    try:
        await page.wait_for_url(re.compile(r'.*#/PF/schedule/scheduler/agenda.*'), timeout=15000)
    except PlaywrightTimeoutError:
        logger.warning('schedule URL not loaded via direct route; attempting UI navigation to schedule')
        navigation_succeeded = False
        for attempt in range(3):
            try:
                nav_link = page.locator('a[href*="#/PF/schedule/scheduler"]').first
                if await nav_link.count() > 0:
                    await nav_link.click()
                else:
                    # Fallback: click a visible link with accessible name containing "Schedule"
                    await page.get_by_role('link', name=re.compile('schedule', re.IGNORECASE)).first.click()

                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_url(re.compile(r'.*#/PF/schedule/scheduler/agenda.*'), timeout=20000)
                navigation_succeeded = True
                break
            except PlaywrightTimeoutError:
                logger.warning(f'attempt {attempt + 1} to navigate to schedule via UI failed; retrying')
                await page.wait_for_timeout(3000)
            except Exception:
                logger.warning(f'unexpected error during schedule UI navigation attempt {attempt + 1}; retrying')
                await page.wait_for_timeout(3000)

        if not navigation_succeeded:
            logger.error('failed to navigate to schedule page via UI fallback')
            raise

    # Wait for the schedule page to fully load
    try:
        await page.wait_for_selector('#date-picker-button', timeout=15000)
        await page.wait_for_timeout(2000)  # Allow SPA to settle
    except PlaywrightTimeoutError:
        logger.warning('date picker button not found, continuing anyway')

    # Use the date picker to set the exact date
    logger.info(f'setting date to {target_date} using date picker')
    try:
        # Click the calendar button to open the date picker
        await page.click('#date-picker-button')
        await page.wait_for_timeout(1000)
        
        # Format the date as expected by the date picker input
        # The date picker might have an input field we can fill
        date_input = page.locator('input[type="text"]').first
        if await date_input.count() > 0 and await date_input.is_visible():
            # Clear and fill the date
            await date_input.fill(target_date.strftime('%m/%d/%Y'))
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(2000)
            logger.info('filled date in date picker input')
        else:
            # If no input field, try to navigate the calendar
            logger.info('no date input found, trying calendar navigation')
            
            # Click away to close the picker
            await page.click('body', position={'x': 10, 'y': 10})
            await page.wait_for_timeout(500)
            
            # Fall back to clicking back buttons
            current_date = datetime.now(EASTERN_TZ).date()
            days_difference = (current_date - target_date).days
            
            if days_difference > 0:
                logger.info(f'going back {days_difference} days from current date to reach {target_date}')
                await page.wait_for_selector('button.rotate-180', timeout=30000)
                
                for i in range(days_difference):
                    # Use JavaScript click to ensure the event fires
                    await page.evaluate('document.querySelector("button.rotate-180").click()')
                    await page.wait_for_timeout(1500)
                    logger.debug(f'clicked back button {i+1}/{days_difference}')
        
        # Wait for the schedule to update
        await page.wait_for_timeout(3000)
        
        # Verify the date changed by checking the visible date header
        try:
            date_header = page.locator('h3.h3.box-margin-Bn')
            if await date_header.count() > 0:
                date_text = await date_header.text_content()
                logger.info('current date header', date_text=date_text, target_date=str(target_date))
        except Exception as e:
            logger.debug('could not read date header', error=str(e))
        
        # Save HTML after date navigation
        if DEBUG_HTML:
            try:
                html_content = await page.content()
                with open(f'./screenshots/02_after_date_navigation_{target_date}.html', 'w') as f:
                    f.write(html_content)
                logger.info('saved HTML after date navigation', target_date=target_date)
            except:
                logger.warning('failed to save HTML after date navigation')
    except PlaywrightTimeoutError:
        logger.error("Timeout during date navigation")
        raise
    except Exception as e:
        logger.error("Error during date navigation", error=str(e))
        raise


async def get_schedule_page(page: Page, target_date: date) -> str:
    logger = ptmlog.get_logger()
    DEBUG_HTML: bool = os.getenv('DEBUG_HTML', 'FALSE') == 'TRUE'
    logger.info('getting schedule page content', target_date=target_date)

    # Set the schedule page to the target date
    await set_schedule_page_to_date(page, target_date)
    
    try:
        # Wait for a specific element that indicates the schedule is loaded
        await page.wait_for_selector('div[data-element="appointments-table"]', state='visible', timeout=45000)
        logger.info('appointments table loaded')
        
        # Save HTML after navigating to the date
        if DEBUG_HTML:
            logger.info('saving HTML after date navigation', target_date=target_date)
            html_content = await page.content()
            with open(f'./screenshots/02_after_date_navigation_{target_date}.html', 'w') as f:
                f.write(html_content)

        # Check the "All" checkbox to ensure all users' appointments are shown
        try:
            all_checkbox = page.locator('[data-element="chk-all-users"]')
            if await all_checkbox.count() > 0:
                # Check if it's already checked
                is_checked = await all_checkbox.locator('input').is_checked()
                if not is_checked:
                    await all_checkbox.click()
                    await page.wait_for_timeout(2000)
                    logger.info('checked All users checkbox')
                else:
                    logger.info('All users checkbox already checked')
        except Exception as e:
            logger.warning('could not check All users checkbox', error=str(e))

        # Open the print view with retries and explicit wait for visibility
        for attempt in range(3):
            try:
                print_button = page.get_by_text('Print')
                await print_button.wait_for(state='visible', timeout=10000)
                await print_button.click()
                logger.info('successfully clicked print button')
                
                # Wait for the print table to be populated with the current date's data
                await page.wait_for_timeout(3000)
                break
            except PlaywrightTimeoutError:
                logger.warning(f'attempt {attempt + 1} to click print button failed. Retrying...')
                await page.wait_for_timeout(5000)
        else:
            logger.error('failed to click print button after multiple attempts.')
            raise Exception('failed to click print button after multiple attempts')
            
        content = await page.content()
        logger.info('successfully retrieved schedule page content', target_date=target_date)

    except PlaywrightTimeoutError:
        logger.error(f"Timeout waiting for schedule page elements. Current URL: {page.url}, Title: {await page.title()}")
        raise

    return content


async def get_schedule_pages(target_dates: list[date]) -> list[str]:
    HEADLESS: bool = os.getenv('HEADLESS', 'TRUE') == 'TRUE'
    DEBUG_HTML: bool = os.getenv('DEBUG_HTML', 'FALSE') == 'TRUE'
    logger = ptmlog.get_logger()
    
    schedule_pages: list[str] = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        
        # Try with cached session first
        storage_state = get_playwright_storage_state('practicefusion')
        if storage_state:
            logger.info('found cached session state, attempting to use it')
        else:
            logger.info('no cached session state found, will perform fresh login')
        
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        
        try:
            await login(page)
            
            # Save HTML after login for debugging
            if DEBUG_HTML:
                logger.info('saving post-login HTML')
                html_content = await page.content()
                try:
                    with open('./screenshots/01_after_login.html', 'w') as f:
                        f.write(html_content)
                except:
                    logger.warning('failed to save HTML to local file')
            
            for i, target_date in enumerate(target_dates):
                schedule_page = await get_schedule_page(page, target_date)
                schedule_pages.append(schedule_page)
                
                # Save the schedule page HTML for debugging
                if DEBUG_HTML:
                    logger.info('saving schedule page HTML', target_date=target_date)
                    with open(f'./screenshots/03_schedule_page_{target_date}.html', 'w') as f:
                        f.write(schedule_page)
                        
        except SessionExpiredError:
            # Session expired during operation - clear cached state and retry with fresh login
            logger.warning('session expired during operation, clearing cached state and retrying')
            await context.close()
            delete_playwright_storage_state('practicefusion')
            
            # Create new context without cached state
            context = await browser.new_context()
            page = await context.new_page()
            
            # Perform fresh login (skip session validation since we know it's invalid)
            await login(page, skip_session_validation=True)
            
            # Retry getting schedule pages
            for i, target_date in enumerate(target_dates):
                schedule_page = await get_schedule_page(page, target_date)
                schedule_pages.append(schedule_page)
                
        except Exception:
            try:
                await page.screenshot(path='./screenshots/error_screenshot.png')
                # Always save HTML on error
                logger.error('saving error HTML')
                html_content = await page.content()
                with open('./screenshots/error_page.html', 'w') as f:
                    f.write(html_content)
            except:
                logger.warning('failed to save error screenshot/HTML')
            raise
        finally:
            # Always save the current session state for future runs
            try:
                save_playwright_storage_state('practicefusion', await context.storage_state())
                logger.info('saved session state for future runs')
            except:
                logger.warning('failed to save session state')
    
    return schedule_pages
    

def parse_schedule_page(schedule_page: str) -> list[PracticeFusionAppointment]:
    logger = ptmlog.get_logger()
    soup = BeautifulSoup(schedule_page, 'html.parser')

    # Get the date from the page - try both print view header and main view header
    h3_elements = soup.find_all('h3')
    header_date_string = None
    for h3 in h3_elements:
        text = h3.text.strip()
        if text.startswith('Schedule Standard view - '):
            header_date_string = text.split('Schedule Standard view - ')[1].strip()
            break
    
    # Also try to get date from the main schedule header
    if header_date_string is None:
        date_header = soup.find('h3', class_='h3 box-margin-Bn')
        if date_header:
            # Format: "Thu, Nov 20, 2025"
            header_date_string = date_header.text.strip()
            # Convert to format expected: "Thursday, November, 20, 2025"
            try:
                parsed_date = datetime.strptime(header_date_string, '%a, %b %d, %Y').date()
                schedule_date = parsed_date
                logger.debug('parsed date from main header', date=str(schedule_date))
            except ValueError:
                pass
    
    if header_date_string is None:
        raise ValueError('Could not find the date in the header')
    elif 'schedule_date' not in locals():
        try:
            schedule_date = datetime.strptime(header_date_string, '%A, %B, %d, %Y').date()
        except ValueError:
            # Try alternate format
            schedule_date = datetime.strptime(header_date_string, '%a, %b %d, %Y').date()

    # First try to get appointments from the print table
    table = soup.find('table', {'data-element': 'table-agenda-print'})
    appointments: list[PracticeFusionAppointment] = []
    
    if table:
        rows = table.find_all('tr')
        for row in rows[1:]:
            # get column values using data-element attributes from print view
            status_td   = row.find('td', {'data-element': 'td-intake-status'})
            patient_td  = row.find('td', {'data-element': 'td-patient-name'})
            time_td     = row.find('td', {'data-element': 'td-start-at'})
            provider_td = row.find('td', {'data-element': 'td-provider-name'})
            type_td     = row.find('td', {'data-element': 'td-appointment-type'})

            # Defensive: skip rows that are missing any required cell
            if not all([status_td, patient_td, time_td, provider_td, type_td]):
                continue

            status_column_text   = status_td.text
            patient_column_text  = patient_td.text
            time_column_text     = time_td.text
            provider_column_text = provider_td.text
            type_column_text     = type_td.text

            # Parse simple values from the columns
            appointment_status   = status_column_text.strip()
            appointment_provider = provider_column_text.strip()
            appointment_type     = type_column_text.strip()

            # Parse the patient column
            patient_column_split = re.split(r'\s*\n\s*', patient_column_text.strip())
            patient_name_raw  = patient_column_split[0]
            patient_dob_raw   = patient_column_split[1]
            patient_phone_raw = patient_column_split[2] if len(patient_column_split) > 2 else ""

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
    
    # If print table has no appointments, try parsing from main appointments table
    if len(appointments) == 0:
        logger.info('no appointments in print table, trying main appointments table')
        main_table = soup.find('div', {'data-element': 'appointments-table'})
        if main_table:
            # Find all table rows in the main table - they have data-element="data-table-row-N"
            rows = main_table.find_all('tr', {'data-element': re.compile(r'^data-table-row-')})
            logger.debug(f'found {len(rows)} appointment rows in main table')
            
            for idx, row in enumerate(rows):
                try:
                    # Get status - look for the status span with "Seen", "Cancelled", etc.
                    status_span = row.find('span', class_='text-color-default')
                    if status_span:
                        appointment_status = status_span.text.strip()
                    else:
                        # Try to find status from the intake status select dropdown
                        status_div = row.find('div', {'data-element': re.compile(r'^intake-status-select-')})
                        if status_div:
                            status_text_div = status_div.find('div', {'title': True})
                            appointment_status = status_text_div.get('title', '') if status_text_div else ''
                        else:
                            appointment_status = ''
                    
                    # Get patient info from cell-patient-N
                    patient_cell = row.find('td', {'data-element': re.compile(r'^cell-patient-')})
                    if patient_cell:
                        # Patient name is typically in an anchor tag or just text
                        patient_link = patient_cell.find('a')
                        if patient_link:
                            patient_name = patient_link.text.strip()
                        else:
                            # Get text content, first non-empty line is the name
                            patient_text = patient_cell.get_text(separator='\n').strip()
                            patient_lines = [l.strip() for l in patient_text.split('\n') if l.strip()]
                            patient_name = patient_lines[0] if patient_lines else ''
                        
                        # DOB is in a span with data-element="cell-dob"
                        dob_span = patient_cell.find('span', {'data-element': 'cell-dob'})
                        if dob_span:
                            patient_dob = datetime.strptime(dob_span.text.strip(), '%m/%d/%Y').date()
                        else:
                            patient_dob = None
                        
                        # Phone is in a span with data-element="cell-phone" 
                        phone_span = patient_cell.find('span', {'data-element': 'cell-phone'})
                        if phone_span:
                            patient_phone = re.sub(r'\D', '', phone_span.text.strip())
                        else:
                            # Try to find phone in text
                            patient_phone = ''
                            for line in patient_cell.get_text(separator='\n').split('\n'):
                                line = line.strip()
                                if re.match(r'M\.\s*\(?\d', line):
                                    patient_phone = re.sub(r'\D', '', line)
                                    break
                    else:
                        logger.debug(f'no patient cell found for row {idx}')
                        continue
                    
                    # Get time from cell-time-N
                    time_cell = row.find('td', {'data-element': re.compile(r'^cell-time-')})
                    if time_cell:
                        time_text = time_cell.text.strip().split('\n')[0].strip()
                        # Handle formats like "11:30 AM" or "11:30AM"
                        time_text = re.sub(r'(\d)(AM|PM)', r'\1 \2', time_text, flags=re.IGNORECASE)
                        appointment_time = datetime.strptime(time_text, '%I:%M %p').time()
                        appointment_time = datetime.combine(schedule_date, appointment_time)
                    else:
                        logger.debug(f'no time cell found for row {idx}')
                        continue
                    
                    # Get provider - it's in a td without specific data-element, but contains provider name
                    # Look for td cells and find one that contains provider text
                    all_tds = row.find_all('td')
                    appointment_provider = ''
                    for td in all_tds:
                        td_text = td.text.strip()
                        if 'BHUC' in td_text or 'COMMON GROUND' in td_text:
                            appointment_provider = td_text
                            break
                    
                    # Get type - similar approach
                    appointment_type = ''
                    for td in all_tds:
                        td_text = td.text.strip()
                        if td_text in ['CLINICIAN', 'NP FOLLOW UP', 'FOLLOW UP REQ', 'MED REFILL']:
                            appointment_type = td_text
                            break
                    
                    if patient_name and appointment_time:
                        appointments.append(PracticeFusionAppointment(
                            patient_name       = patient_name,
                            appointment_status = appointment_status,
                            patient_dob        = patient_dob or date(1900, 1, 1),  # Default if not found
                            patient_phone      = patient_phone,
                            provider           = appointment_provider,
                            type               = appointment_type,
                            appointment_time   = appointment_time,
                        ))
                        logger.debug('parsed appointment from main table', patient_name=patient_name, status=appointment_status)
                except Exception as e:
                    logger.warning('failed to parse appointment row', error=str(e))
                    continue
    
    return appointments


def parse_schedule_page_legacy(schedule_page: str) -> list[PracticeFusionAppointment]:
    """Legacy parser that only uses the print table - kept for reference."""
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
        schedule_date = datetime.strptime(header_date_string, '%A, %B, %d, %Y').date()

    # Get all the rows in the table
    table = soup.find('table', {'data-element': 'table-agenda-print'})
    rows = table.find_all('tr')  # type: ignore

    # Iterate through the rows (skipping the header row) and extract the data
    appointments: list[PracticeFusionAppointment] = []
    for row in rows[1:]:
        # get column values using data-element attributes from print view
        status_td   = row.find('td', {'data-element': 'td-intake-status'})
        patient_td  = row.find('td', {'data-element': 'td-patient-name'})
        time_td     = row.find('td', {'data-element': 'td-start-at'})
        provider_td = row.find('td', {'data-element': 'td-provider-name'})
        type_td     = row.find('td', {'data-element': 'td-appointment-type'})

        # Defensive: skip rows that are missing any required cell
        if not all([status_td, patient_td, time_td, provider_td, type_td]):
            continue

        status_column_text   = status_td.text
        patient_column_text  = patient_td.text
        time_column_text     = time_td.text
        provider_column_text = provider_td.text
        type_column_text     = type_td.text

        # Parse simple values from the columns
        appointment_status   = status_column_text.strip()
        appointment_provider = provider_column_text.strip()
        appointment_type     = type_column_text.strip()

        # Parse the patient column
        patient_column_split = re.split(r'\s*\n\s*', patient_column_text.strip())
        patient_name_raw  = patient_column_split[0]
        patient_dob_raw   = patient_column_split[1]
        patient_phone_raw = patient_column_split[2] if len(patient_column_split) > 2 else ""

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
