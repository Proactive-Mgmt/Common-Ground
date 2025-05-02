import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from azure.core.exceptions import ResourceExistsError

import practice_fusion_utils
import twilio_utils
import appointments_table_utils
from shared import ptmlog

EASTERN_TZ = ZoneInfo('America/New_York')

def get_target_date():
    """
    Get target date from environment variable, default to current date.
    """
    target_date_str = os.getenv('TARGET_DATE')
    current_date = datetime.now(EASTERN_TZ).date()
    
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
async def main():
    logger = ptmlog.get_logger()

    target_date = get_target_date()
    logger.info('getting appointments from practice fusion', target_date=target_date)
    pf_appointments = await practice_fusion_utils.get_appointments(target_dates=[target_date])

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

    for appointment in filtered_appointments:
        try:
            logger.info('creating appointment in azure table', appointment=appointment)
            appointments_table_utils.create_new_appointment(
                patient_name       = appointment.patient_name,
                patient_dob        = appointment.patient_dob,
                patient_phone      = appointment.patient_phone,
                appointment_time   = appointment.appointment_time,
                appointment_status = appointment.appointment_status,
                provider           = appointment.provider,
                type               = appointment.type,
            )
        except ResourceExistsError:
            logger.exception('appointment already exists in azure table', appointment=appointment)
            continue  # This should not end the process

    logger.info('getting appointments that need surveys sent')
    table_appointments = appointments_table_utils.get_appointments()

    for table_appointment in table_appointments:
        logger.info('sending survery', patient_name=table_appointment.patient_name)
        try:
            message_sid = twilio_utils.send_survey(
                id            = table_appointment.row_key,
                patient_name  = table_appointment.patient_name,
                patient_phone = table_appointment.patient_phone,
            )
        except:
            logger.exception('error sending survey', patient_name=table_appointment.patient_name)
            continue  # This should not end the process

        logger.info('updating table appointment', patient_name=table_appointment.patient_name)
        try:
            appointments_table_utils.update_appointment(
                row_key       = table_appointment.row_key,
                partition_key = table_appointment.partition_key,
                sent_on       = datetime.now(timezone.utc),
                message_sid   = message_sid,
            )
        except:
            logger.exception('error updating table appointment', patient_name=table_appointment.patient_name)
            continue  # This should not end the process


if __name__ == '__main__':
    main()