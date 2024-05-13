from datetime import datetime
import os
import time
from typing import LiteralString
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import json
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    filename="selenium_log.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

with open("config.json") as config_file:
    config = json.load(config_file)
    credentials = config["credentials"]
    username = credentials["username"]
    password = credentials["password"]
    login_url = credentials["login_url"]


def initialize_driver():

    print("Initializing Selenium driver...")
    # print("Initializing Selenium driver...")
    options = Options()
    selenium_options = config["selenium_options"]

    # # Set headless option based on config
    if selenium_options["headless"]:
        options.add_argument("--headless")

    # Set window size
    options.add_argument(f'--window-size={selenium_options["window_size"]}')
    # Additional necessary arguments for headless mode in Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )

    # Test with profile
    options.add_argument("user-data-dir=" + os.path.join(os.getcwd(), "ChromeProfile"))

    print("Driver initialized successfully.")

    return webdriver.Chrome(options=options)


def RequestCode():
    code = "code"
    print("Requesting code...")
    # Ask for code and get message id

    print(code)
    return code


def handle_mfa(driver):
    print("Handling MFA...")
    print("MFA handled successfully.")


def login(driver, username, password, url):
    try:

        print(f"Attempting login for user: {username}")
        # print(f"Attempting login for user: {username}")
        driver.get(url)

        # username_field = driver.find_element(By.ID, "inputUsername")
        # username_field.send_keys(username)

        password_field = driver.find_element(By.ID, "inputPswd")
        password_field.send_keys(password)
        login_button = driver.find_element(By.ID, "loginButton")
        login_button.click()

        # Handle MFA
        if config.get("mfa"):
            handle_mfa(driver)

    except Exception as e:
        print(f"An exception occurred during login: {e}")

        # print(f"An exception occurred during login: {e}")
        raise e

    # def GetRecods(driver, record):


def accept_alert(driver):
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except:
        print(" accept_alert ")
        pass


def get_appointments(driver):
    schedule_url: LiteralString = (
        f"https://static.practicefusion.com/apps/ehr/index.html?utm_source=exacttarget&utm_medium=email&utm_campaign=InitialSetupWelcomeAddedUser#/PF/schedule/scheduler/agenda"
    )
    driver.get(schedule_url)
    # Call this function before interacting with elements that might trigger alerts
    accept_alert(driver)
    time.sleep(5)

    if driver.current_url != schedule_url:
        print("Login has failed")
        return
    else:
        print("Login Successful")

    # Wait until the button is clickable
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@class='btn--default' and @data-element='btn-schedule-print']",
            )
        )
    )

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
        }
        appointments.append(appointment)

    # Convert the list of dictionaries to JSON
    return json.dumps(appointments, indent=4)


def main():
    # Load config file

    print("Initializing driver...")
    driver = initialize_driver()
    if driver:
        print(" driver Succesfully Initialized...")

    login(driver, username, password, login_url)
    time.sleep(2)
    # print("Starting to process accounts...")
    appointments = get_appointments(driver)

    print(f"Appointments: {appointments}")


if __name__ == "__main__":
    main()
