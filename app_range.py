import logging
import os
from datetime import datetime, timedelta
from lib import (
    get_practicefusion_appointments,
    process_messages,
    get_appointments,
    save_appointments,
    save_processed_appointments,
)

def process_date(target_date):
    # Set the TARGET_DATE environment variable
    os.environ['TARGET_DATE'] = target_date.strftime('%Y-%m-%d')
    logging.info(f'Processing date: {target_date.strftime("%Y-%m-%d")}')

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
    if filtered_appointments:
        save_appointments(filtered_appointments)
        appointments = get_appointments()
        processed_appointments = process_messages(appointments)
        save_processed_appointments(processed_appointments)
        logging.info('processed_appointments:\n%s', processed_appointments)
    else:
        logging.info('No appointments found for date %s', target_date.strftime('%Y-%m-%d'))

def main():
    # Get date range from environment variables
    start_date_str = os.getenv('START_DATE')
    end_date_str = os.getenv('END_DATE')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        logging.error('Invalid date format. Please use YYYY-MM-DD format for START_DATE and END_DATE')
        return

    if start_date > end_date:
        logging.error('START_DATE must be before or equal to END_DATE')
        return

    # Process each date in the range
    current_date = start_date
    while current_date <= end_date:
        process_date(current_date)
        current_date += timedelta(days=1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('azure').setLevel(logging.WARNING)

    main()