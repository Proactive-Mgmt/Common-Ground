import json
import logging
import storage as storage
from rpa import run_rpa
import message as message

def main():
    appointments = json.loads(run_rpa())

    logging.debug("Pre filter:\n%s", appointments)

    # Filter appointments
    filtered_appointments = [
        appointment
        for appointment in appointments
        if appointment["provider"] == "BHUC COMMON GROUND"
        and appointment["type"] == "CLINICIAN"
        and appointment["appointmentStatus"] == "Seen"
    ]

    logging.debug("Post Filter:\n%s", filtered_appointments)

    storage.save_appointments(filtered_appointments)

    appointments = storage.get_appointments()

    processed_appointments = message.process_messages(appointments)
    storage.save_processed_appointments(processed_appointments)

    logging.info('processed_appointments:\n%s', processed_appointments)
    logging.info('appointments:\n%s', appointments)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('azure').setLevel(logging.WARNING)

    main()