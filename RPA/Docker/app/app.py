import json
import logging
import storage as storage
from rpa import return_appointments


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


def main():

    print("Initializing orchestrator")

    # print("Starting to process accounts...")
    appointments = return_appointments()
    storage.save_appointments(appointments)

    # save_appointments(appointments)

    print(f"Appointments: {appointments}")


if __name__ == "__main__":
    main()
