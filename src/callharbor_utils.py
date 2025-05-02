import re
import os
import asyncio

from playwright.async_api import (
    async_playwright,
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

async def handle_mfa(page: Page) -> None:
    logger = ptmlog.get_logger()

    if page.url != MFA_URL:
        logger.error('not on mfa page, cannot handle mfa')
        raise Exception('not on mfa page, cannot handle mfa')
    
    CALLHARBOR_MFA_SECRET = os.environ['CALLHARBOR_MFA_SECRET']

    mfa_code = pyotp.TOTP(CALLHARBOR_MFA_SECRET).now()
    await page.locator('input[name="data[Login][passcode]"]').fill(mfa_code)
    await page.get_by_role('button', name='Submit').click()

    try:
        await page.wait_for_url(MAIN_PAGE)
    except PlaywrightTimeoutError:
        await page.screenshot(path='./screenshots/mfa_failed.png')
        logger.error('mfa failed, not on main page', actual_url=page.url)
        raise Exception('mfa failed, not on main page')

async def login(page: Page) -> None:
    logger = ptmlog.get_logger()
    logger.info('logging into callharbor')

    CALLHARBOR_USERNAME   = os.environ['CALLHARBOR_USERNAME']
    CALLHARBOR_PASSWORD   = os.environ['CALLHARBOR_PASSWORD']

    await page.locator('input[name="data[Login][username]"]').fill(CALLHARBOR_USERNAME)
    await page.locator('input[name="data[Login][password]"]').fill(CALLHARBOR_PASSWORD)
    await page.get_by_role('button', name='Log In').click()

    if page.url.startswith(MFA_URL):
        logger.info('callharbor mfa page detected, handling mfa')
        await handle_mfa(page)
    
    try:
        await page.wait_for_url(MAIN_PAGE)
    except PlaywrightTimeoutError:
        await page.screenshot(path='./screenshots/login_failed.png')
        logger.error('login failed, not on main page', actual_url=page.url)
        raise Exception('login failed, not on main page')


async def get_latest_mfa_code() -> str:
    """
    Get the latest mfa code from call harbor messages.
    """

    logger = ptmlog.get_logger()
    logger.info('getting latest mfa code from call harbor')

    HEADLESS: bool = os.getenv('HEADLESS', 'TRUE') == 'TRUE'

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(storage_state=get_playwright_storage_state('callharbor'))
        page    = await context.new_page()
        try:
            await page.goto(MESSAGES_URL)
            if page.url.startswith(LOGIN_URL):
                logger.info('not logged in, logging in')
                await login(page)
                logger.info('navigating to the messages page')
                await page.goto(MESSAGES_URL)
            all_recent_messages = await page.locator(".conversation-recent-msg").all_text_contents()
        finally:
            save_playwright_storage_state('callharbor', await context.storage_state())
        
        for message in all_recent_messages:
            match = re.search(r'^Your code is: (\d{5,}). Thank you.$', message)
            if match:
                return match.group(1)
        
        # If we make it here, we didn't find a code
        await page.screenshot(path='./screenshots/no_mfa_code_found_in_call_harbor_messages.png')
        logger.error('no mfa code found in call harbor messages', all_recent_messages=all_recent_messages)
        raise Exception('no mfa code found in call harbor messages')


if __name__ == '__main__':
    print(asyncio.run(get_latest_mfa_code()))
