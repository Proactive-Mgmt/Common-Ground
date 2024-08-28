import json
import logging
import storage as storage
from rpa import run_rpa
import message as message


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

with open("config.json") as config_file:
    config = json.load(config_file)
    credentials = config["credentials"]
    username = credentials["username"]
    password = credentials["password"]
    login_url = credentials["login_url"]


def main():

    logging.info("Initializing orchestrator")

    # logging.info("Starting to process accounts...")

    appointments = json.loads(run_rpa())

    # Filter Python objects with list comprehensions
    logging.info("Pre filter", appointments)
    # Filter appointments
    filtered_appointments = [
        appointment
        for appointment in appointments
        if appointment["provider"] == "BHUC COMMON GROUND"
        and appointment["type"] == "CLINICIAN"
        and appointment["appointmentStatus"] == "Seen"
    ]

    logging.info("Post Filter", filtered_appointments)

    storage.save_appointments(filtered_appointments)

    appointments = storage.get_appointments()

    processed_appointments = message.process_messages(appointments)
    logging.info("processed_appointments ", processed_appointments)
    storage.save_processed_appointments(processed_appointments)
    # save_appointments(appointments)

    logging.info(f"Appointments: {appointments}")


if __name__ == "__main__":
    main()
