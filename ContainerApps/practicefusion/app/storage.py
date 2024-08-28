from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient, TableEntity
import hashlib
import uuid
import logging
import os

def save_appointments(appointments):
    logging.info('save_appointments')

    STORAGE_ACCOUNT_CONNECTION_STRING = os.getenv('STORAGE_ACCOUNT_CONNECTION_STRING')
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        #  compound key (dob+lastname+phonenumber)+
        row_key = generate_deterministic_uuid(
            appointment['patientDOB']
            + appointment['patientName'].split()[1]
            + appointment['patientPhone']
        )

        logging.info(f'row_key: {row_key}')
        logging.info(f'row_key: {row_key[-1]}')

        appointment['RowKey'] = row_key
        appointment['PartitionKey'] = row_key[-1]
        appointment['sentOn'] = ''
        appointment['message_sid'] = ''
        entity = TableEntity(**appointment)
        try:
            logging.info('Creating entity:\n%s', entity)
            table_client.create_entity(entity)
        except ResourceExistsError:
            logging.warning('Entity already exists:\n%s', entity)


def generate_deterministic_uuid(input_string):
    # Create an MD5 hash of the input string
    md5_hash = hashlib.md5(input_string.encode()).hexdigest()

    # Convert the MD5 hash to a UUID
    deterministic_uuid = uuid.UUID(md5_hash)

    return str(deterministic_uuid)


def get_appointments() -> None:
    logging.info('get_appointments')

    STORAGE_ACCOUNT_CONNECTION_STRING = os.getenv('STORAGE_ACCOUNT_CONNECTION_STRING')
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    my_filter = "appointmentStatus eq 'Seen' and provider eq 'BHUC COMMON GROUND' and type eq 'CLINICIAN' and sentOn eq ''"
    entities = table_client.query_entities(my_filter)

    return list(entities)


def save_processed_appointments(appointments):
    logging.info('save_processed_appointments')

    STORAGE_ACCOUNT_CONNECTION_STRING = os.getenv('STORAGE_ACCOUNT_CONNECTION_STRING')
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        entity = TableEntity(**appointment)
        logging.info('Updating entity:\n%s', entity)
        table_client.update_entity(entity)