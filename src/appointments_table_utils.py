from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient, TableEntity
from datetime import datetime, date
import hashlib
import uuid
import os

from models import PracticeFusionAppointment, TableAppointment
from shared import ptmlog

def calculate_row_key(patient_dob: date, patient_name: str, patient_phone: str, appointment_time: datetime) -> str:
    """
    Calculate the row key for the appointment entity based on the patient's details and appointment time.
    """
    hash_input = patient_dob.strftime(r'%Y-%m-%d') + patient_name.split()[1] + patient_phone + appointment_time.strftime(r'%Y-%m-%dT%H:%M')
    md5_hash = hashlib.md5(hash_input.encode()).hexdigest()
    row_key = str(uuid.UUID(md5_hash))
    return row_key

def create_new_appointment(
    patient_name      : str,
    patient_dob       : date,
    patient_phone     : str,
    appointment_time  : datetime,
    appointment_status: str,
    provider          : str,
    type              : str,
) -> None: 
    """
    Create a new appointment entity in the Azure Table Storage.
    Raises azure.core.exceptions.ResourceExistsError if the entity already exists.
    """
    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    row_key = calculate_row_key(patient_dob, patient_name, patient_phone, appointment_time)

    table_client.create_entity(TableEntity(
        RowKey            = row_key,
        PartitionKey      = row_key[-1],
        sentOn            = '',
        message_sid       = '',
        patientName       = patient_name,
        patientDOB        = patient_dob.strftime(r'%Y-%m-%d'),
        patientPhone      = patient_phone,
        appointmentTime   = appointment_time.strftime(r'%Y-%m-%dT%H:%M'),
        appointmentStatus = appointment_status,
        provider          = provider,
        type              = type,
    ))

def save_appointments(appointments: list[PracticeFusionAppointment]):
    logger = ptmlog.get_logger()

    for appointment in appointments:
        try:
            logger.info('creating table_entity', appointment=appointment)
            create_new_appointment(
                patient_name      = appointment.patient_name,
                patient_dob       = appointment.patient_dob,
                patient_phone     = appointment.patient_phone,
                appointment_time  = appointment.appointment_time,
                appointment_status= appointment.appointment_status,
                provider          = appointment.provider,
                type              = appointment.type,
            )
        except ResourceExistsError:
            logger.warning('table_entity already exists', appointment=appointment)

def get_appointments() -> list[TableAppointment]:
    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    my_filter = "appointmentStatus eq 'Seen' and provider eq 'BHUC COMMON GROUND' and type eq 'CLINICIAN' and sentOn eq ''"
    entities = table_client.query_entities(my_filter)

    table_appointments = []
    for entity in entities:
        table_appointments.append(TableAppointment(
            row_key       = entity['RowKey'],
            partition_key = entity['PartitionKey'],
            patient_name  = entity['patientName'],
            patient_phone = entity['patientPhone'],
        ))

    return table_appointments

def update_appointment(row_key: str, partition_key: str, sent_on: datetime, message_sid: str):
    logger = ptmlog.get_logger()

    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    logger.info('updating entity', row_key=row_key, partition_key=partition_key, sent_on=sent_on, message_sid=message_sid)
    table_client.update_entity(TableEntity(
        PartitionKey = partition_key,
        RowKey       = row_key,
        sentOn       = sent_on,
        message_sid  = message_sid,
    ))
