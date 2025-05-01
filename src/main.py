import os
from datetime import datetime

import practice_fusion_utils
import twilio_utils
import appointments_table_utils
from shared import ptmlog


def get_target_date():
    """
    Get target date from environment variable, default to current date.
    """
    target_date_str = os.getenv('TARGET_DATE')
    current_date = datetime.now().date()
    
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            logger = ptmlog.get_logger()
            logger.warning("invalid TARGET_DATE format, using current date", target_date_str=target_date_str)
            target_date = current_date
    else:
        target_date = current_date

    return target_date


@ptmlog.procedure('cg_hope_scale_survey_automation')
def main():
    logger = ptmlog.get_logger()

    target_date = get_target_date()
    logger.info('getting appointments from practice fusion', target_date=target_date)
    appointments = practice_fusion_utils.get_appointments(target_date)

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
    appointments_table_utils.save_appointments(filtered_appointments)

    logger.info('getting appointments that need surveys sent')
    appointments = appointments_table_utils.get_appointments()

    logger.info('sending surveys')
    processed_appointments = twilio_utils.process_messages(appointments)

    logger.info('updating appointments in azure table storage')
    appointments_table_utils.save_processed_appointments(processed_appointments)

    logger.debug('after saving appointments', processed_appointments=processed_appointments, appointments=appointments)


if __name__ == '__main__':
    main()