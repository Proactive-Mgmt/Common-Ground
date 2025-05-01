from practice_fusion import get_practicefusion_appointments
from twilio import process_messages
from appointments_table import get_appointments, save_appointments, save_processed_appointments
from shared import ptmlog

@ptmlog.procedure('cg_hope_scale_survey_automation')
def main():
    logger = ptmlog.get_logger()

    logger.info('getting appointments from practice fusion')
    appointments = get_practicefusion_appointments()

    # Filter appointments
    logger.debug('pre-filter', appointments=appointments)
    filtered_appointments = [
        appointment
        for appointment in appointments
        if appointment['provider'] == 'BHUC COMMON GROUND'
        and appointment['type'] == 'CLINICIAN'
        and appointment['appointmentStatus'] == 'Seen'
    ]
    logger.debug('post-filter', appointments=filtered_appointments)

    logger.info('saving filtered appointments to azure table storage')
    save_appointments(filtered_appointments)

    logger.info('getting appointments that need surveys sent')
    appointments = get_appointments()

    logger.info('sending surveys')
    processed_appointments = process_messages(appointments)

    logger.info('updating appointments in azure table storage')
    save_processed_appointments(processed_appointments)

    logger.debug('after saving appointments', processed_appointments=processed_appointments, appointments=appointments)


if __name__ == '__main__':
    main()