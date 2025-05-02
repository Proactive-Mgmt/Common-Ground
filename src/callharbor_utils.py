import re
import os

from playwright.sync_api import (
    sync_playwright,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
import pyotp

from shared import ptmlog
from storage_state_persistence_utils import save_playwright_storage_state, get_playwright_storage_state

LOGIN_URL    = 'https://control.callharbor.com/portal/login/index'
MFA_URL      = 'https://control.callharbor.com/portal/login/mfa/1'
MAIN_PAGE    = 'https://control.callharbor.com/portal/home'
MESSAGES_URL = 'https://control.callharbor.com/portal/messages'

def handle_mfa(page: Page) -> None:
    logger = ptmlog.get_logger()

    if page.url != MFA_URL:
        logger.error('not on mfa page, cannot handle mfa')
        raise Exception('not on mfa page, cannot handle mfa')
    
    CALLHARBOR_MFA_SECRET = os.environ['CALLHARBOR_MFA_SECRET']

    mfa_code = pyotp.TOTP(CALLHARBOR_MFA_SECRET).now()
    page.locator('input[name="data[Login][passcode]"]').fill(mfa_code)
    page.get_by_role('button', name='Submit').click()

    try:
        page.wait_for_url(MAIN_PAGE)
    except PlaywrightTimeoutError:
        logger.error('mfa failed, not on main page')
        raise Exception('mfa failed, not on main page')

def login(page: Page) -> None:
    logger = ptmlog.get_logger()
    logger.info('logging into callharbor')

    CALLHARBOR_USERNAME   = os.environ['CALLHARBOR_USERNAME']
    CALLHARBOR_PASSWORD   = os.environ['CALLHARBOR_PASSWORD']

    page.locator('input[name="data[Login][username]"]').fill(CALLHARBOR_USERNAME)
    page.locator('input[name="data[Login][password]"]').fill(CALLHARBOR_PASSWORD)
    page.get_by_role('button', name='Log In').click()

    if page.url.startswith(MFA_URL):
        logger.info('callharbor mfa page detected, handling mfa')
        handle_mfa(page)
    
    try:
        page.wait_for_url(MAIN_PAGE)
    except PlaywrightTimeoutError:
        logger.error('login failed, not on main page')
        raise Exception('login failed, not on main page')


def get_latest_mfa_code() -> str:
    logger = ptmlog.get_logger()
    logger.info('getting latest mfa code from call harbor')

    HEADLESS: bool = os.getenv('HEADLESS', 'TRUE') == 'TRUE'

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=HEADLESS)
        context = browser.new_context(storage_state=get_playwright_storage_state('callharbor'))
        page = context.new_page()
        try:
            page.goto(MESSAGES_URL)
            if page.url.startswith(LOGIN_URL):
                logger.info('not logged in, logging in')
                login(page)
                page.goto(MESSAGES_URL)
            all_recent_messages = page.locator(".conversation-recent-msg").all_text_contents()
        finally:
            save_playwright_storage_state('callharbor', context.storage_state())
        
        for message in all_recent_messages:
            match = re.search(r'^Your code is: (\d{5}). Thank you.$', message)
            if match:
                return match.group(1)
        
        # If we make it here, we didn't find a code
        logger.error('no mfa code found in call harbor messages')
        raise Exception('no mfa code found in call harbor messages')


if __name__ == '__main__':
    print(get_latest_mfa_code())
