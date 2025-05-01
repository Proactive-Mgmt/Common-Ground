import os
from datetime import datetime, UTC

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
    pf_appointments = practice_fusion_utils.get_appointments(target_date)

    # Filter appointments
    logger.debug('pre-filter', appointments=pf_appointments)
    filtered_appointments = [
        appointment
        for appointment in pf_appointments
        if appointment.provider == 'BHUC COMMON GROUND'
        and appointment.type == 'CLINICIAN'
        and appointment.appointment_status == 'Seen'
    ]
    logger.debug('post-filter', appointments=filtered_appointments)

    logger.info('saving filtered appointments to azure table storage')
    appointments_table_utils.save_appointments(filtered_appointments)

    logger.info('getting appointments that need surveys sent')
    table_appointments = appointments_table_utils.get_appointments()

    logger.info('sending surveys')
    for table_appointment in table_appointments:
        message_sid = twilio_utils.send_survey(
            id            = table_appointment.row_key,
            patient_name  = table_appointment.patient_name,
            patient_phone = table_appointment.patient_phone,
        )
        appointments_table_utils.update_appointment(
            row_key       = table_appointment.row_key,
            partition_key = table_appointment.partition_key,
            sent_on       = datetime.now(UTC),
            message_sid   = message_sid,
        )

    logger.debug('after saving appointments', processed_appointments=processed_appointments, table_appointments=table_appointments)


if __name__ == '__main__':
    main()