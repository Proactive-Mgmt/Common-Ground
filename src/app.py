import logging
from lib import (
    get_practicefusion_appointments,
    process_messages,
    get_appointments,
    save_appointments,
    save_processed_appointments,
)

def main():
    appointments = get_practicefusion_appointments()

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

    save_appointments(filtered_appointments)

    appointments = get_appointments()

    processed_appointments = process_messages(appointments)
    save_processed_appointments(processed_appointments)

    logging.info('processed_appointments:\n%s', processed_appointments)
    logging.info('appointments:\n%s', appointments)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('azure').setLevel(logging.WARNING)

    main()