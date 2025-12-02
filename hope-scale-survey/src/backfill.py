"""
Backfill script to sync appointments for a range of dates.

Usage:
    python src/backfill.py --start 2025-11-25 --end 2025-12-02

This script will:
1. Retrieve appointments from Practice Fusion for each date in the range
2. Store them in Azure Table Storage (skipping duplicates)
3. Send surveys to patients who haven't received one yet
"""
import os
import sys
import argparse
import asyncio
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

from azure.core.exceptions import ResourceExistsError

import practice_fusion_utils
import twilio_utils
import appointments_table_utils
from shared import ptmlog

EASTERN_TZ = ZoneInfo('America/New_York')


def generate_date_range(start_date: date, end_date: date) -> list[date]:
    """Generate a list of dates from start_date to end_date (inclusive)."""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


@ptmlog.procedure('cg_hope_scale_backfill_sync')
def backfill_sync_appointments(target_dates: list[date]):
    """
    Retrieve appointments from Practice Fusion for multiple dates and store them in Azure Table Storage.
    """
    logger = ptmlog.get_logger()
    
    logger.info('starting backfill sync', 
        start_date=str(target_dates[0]), 
        end_date=str(target_dates[-1]),
        total_dates=len(target_dates)
    )
    
    # Get appointments for all dates in one browser session
    logger.info('getting appointments from practice fusion for date range')
    pf_appointments = asyncio.run(practice_fusion_utils.get_appointments(target_dates=target_dates))
    
    logger.info('retrieved appointments from practice fusion', total_appointments=len(pf_appointments))
    
    # Log detailed appointment data for diagnosis
    for i, appointment in enumerate(pf_appointments):
        if appointment:
            logger.debug(f'appointment_{i}_details', 
                patient_name=appointment.patient_name,
                provider=appointment.provider,
                type=appointment.type,
                appointment_status=appointment.appointment_status,
                appointment_time=str(appointment.appointment_time)
            )
    
    # Filter appointments
    filtered_appointments = [
        appointment
        for appointment in pf_appointments
        if appointment.type == 'CLINICIAN'
        and appointment.appointment_status == 'Seen'
    ]
    
    logger.info('filter_results', 
        total_retrieved=len(pf_appointments),
        after_filtering=len(filtered_appointments)
    )
    
    # Track statistics
    created_count = 0
    duplicate_count = 0
    error_count = 0
    
    for appointment in filtered_appointments:
        try:
            logger.info('creating appointment in azure table', 
                patient_name=appointment.patient_name,
                appointment_time=str(appointment.appointment_time)
            )
            appointments_table_utils.create_new_appointment(
                patient_name       = appointment.patient_name,
                patient_dob        = appointment.patient_dob,
                patient_phone      = appointment.patient_phone,
                appointment_time   = appointment.appointment_time,
                appointment_status = appointment.appointment_status,
                provider           = appointment.provider,
                type               = appointment.type,
            )
            created_count += 1
        except ResourceExistsError:
            logger.info('appointment already exists in azure table', patient_name=appointment.patient_name)
            duplicate_count += 1
            continue
        except Exception as e:
            logger.exception('error creating appointment', patient_name=appointment.patient_name, error=str(e))
            error_count += 1
            continue
    
    logger.info('backfill sync complete',
        created=created_count,
        duplicates=duplicate_count,
        errors=error_count
    )
    
    return {
        'total_retrieved': len(pf_appointments),
        'after_filtering': len(filtered_appointments),
        'created': created_count,
        'duplicates': duplicate_count,
        'errors': error_count
    }


@ptmlog.procedure('cg_hope_scale_backfill_send_surveys')
def backfill_send_surveys():
    """
    Send surveys to all patients who haven't received one yet.
    """
    logger = ptmlog.get_logger()
    
    logger.info('getting appointments that need surveys sent')
    table_appointments = appointments_table_utils.get_appointments()
    
    logger.info('found appointments needing surveys', count=len(list(table_appointments)))
    
    # Re-query since we consumed the iterator
    table_appointments = appointments_table_utils.get_appointments()
    
    sent_count = 0
    error_count = 0
    
    for table_appointment in table_appointments:
        logger.info('sending survey', patient_name=table_appointment.patient_name)
        try:
            message_sid = twilio_utils.send_survey(
                id            = table_appointment.row_key,
                patient_name  = table_appointment.patient_name,
                patient_phone = table_appointment.patient_phone,
            )
            sent_count += 1
        except Exception as e:
            logger.exception('error sending survey', patient_name=table_appointment.patient_name, error=str(e))
            error_count += 1
            continue

        logger.info('updating table appointment', patient_name=table_appointment.patient_name)
        try:
            appointments_table_utils.update_appointment(
                row_key       = table_appointment.row_key,
                partition_key = table_appointment.partition_key,
                sent_on       = datetime.now(timezone.utc),
                message_sid   = message_sid,
            )
        except Exception as e:
            logger.exception('error updating table appointment', patient_name=table_appointment.patient_name, error=str(e))
            error_count += 1
            continue
    
    logger.info('backfill send surveys complete',
        sent=sent_count,
        errors=error_count
    )
    
    return {
        'sent': sent_count,
        'errors': error_count
    }


def main():
    parser = argparse.ArgumentParser(description='Backfill appointments for a date range')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--skip-surveys', action='store_true', help='Skip sending surveys after sync')
    parser.add_argument('--dry-run', action='store_true', help='Only show what would be done, do not sync')
    
    args = parser.parse_args()
    
    logger = ptmlog.get_logger()
    
    try:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error('invalid date format', error=str(e))
        print(f"Error: Invalid date format. Use YYYY-MM-DD. {e}")
        sys.exit(1)
    
    if start_date > end_date:
        logger.error('start date must be before or equal to end date')
        print("Error: Start date must be before or equal to end date.")
        sys.exit(1)
    
    target_dates = generate_date_range(start_date, end_date)
    
    logger.info('backfill starting',
        start_date=str(start_date),
        end_date=str(end_date),
        total_dates=len(target_dates),
        dry_run=args.dry_run,
        skip_surveys=args.skip_surveys
    )
    
    print(f"Backfill: {start_date} to {end_date} ({len(target_dates)} days)")
    print(f"Dates: {', '.join(str(d) for d in target_dates)}")
    
    if args.dry_run:
        print("\n[DRY RUN] Would sync appointments for the above dates.")
        print("[DRY RUN] No changes will be made.")
        return
    
    # Sync appointments
    try:
        sync_result = backfill_sync_appointments(target_dates)
        print(f"\nSync Results:")
        print(f"  Total retrieved: {sync_result['total_retrieved']}")
        print(f"  After filtering: {sync_result['after_filtering']}")
        print(f"  Created: {sync_result['created']}")
        print(f"  Duplicates: {sync_result['duplicates']}")
        print(f"  Errors: {sync_result['errors']}")
    except Exception as e:
        logger.exception('error during backfill sync')
        print(f"\nError during sync: {e}")
        sys.exit(1)
    
    # Send surveys
    if not args.skip_surveys:
        try:
            survey_result = backfill_send_surveys()
            print(f"\nSurvey Results:")
            print(f"  Sent: {survey_result['sent']}")
            print(f"  Errors: {survey_result['errors']}")
        except Exception as e:
            logger.exception('error during backfill send surveys')
            print(f"\nError during survey send: {e}")
            sys.exit(1)
    else:
        print("\n[SKIPPED] Survey sending skipped as requested.")
    
    print("\nBackfill complete!")


if __name__ == '__main__':
    main()

