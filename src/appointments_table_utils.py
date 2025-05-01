from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient, TableEntity
import hashlib
import uuid
import os

from models import PracticeFusionAppointment
from shared import ptmlog

def save_appointments(appointments: list[PracticeFusionAppointment]):
    logger = ptmlog.get_logger()

    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        # Generate row_key by hashing compound key (dob+lastname+phonenumber)
        hash_input = appointment.patient_dob.strftime(r'%Y-%m-%d') + appointment.patient_name.split()[1] + appointment.patient_phone + appointment.appointment_time.strftime(r'%Y-%m-%dT%H:%M')
        md5_hash = hashlib.md5(hash_input.encode()).hexdigest()
        row_key = str(uuid.UUID(md5_hash))

        table_entity = TableEntity(
            RowKey            = row_key,
            PartitionKey      = row_key[-1],
            sentOn            = '',
            message_sid       = '',
            patientName       = appointment.patient_name,
            patientDOB        = appointment.patient_dob.strftime(r'%Y-%m-%d'),
            patientPhone      = appointment.patient_phone,
            appointmentTime   = appointment.appointment_time.strftime(r'%Y-%m-%dT%H:%M'),
            appointmentStatus = appointment.appointment_status,
            provider          = appointment.provider,
            type              = appointment.type,
        )
        try:
            logger.info('creating table_entity', table_entity=table_entity)
            table_client.create_entity(table_entity)
        except ResourceExistsError:
            logger.warning('table_entity already exists', table_entity=table_entity)

def get_appointments():
    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    my_filter = "appointmentStatus eq 'Seen' and provider eq 'BHUC COMMON GROUND' and type eq 'CLINICIAN' and sentOn eq ''"
    entities = table_client.query_entities(my_filter)

    return list(entities)

def save_processed_appointments(appointments):
    logger = ptmlog.get_logger()

    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        entity = TableEntity(**appointment)
        logger.info('updating entity', entity=entity)
        table_client.update_entity(entity)
