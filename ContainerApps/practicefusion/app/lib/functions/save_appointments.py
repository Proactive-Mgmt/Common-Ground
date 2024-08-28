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
        # Generate row_key by hashing compound key (dob+lastname+phonenumber)
        hash_input = appointment['patientDOB'] + appointment['patientName'].split()[1] + appointment['patientPhone']
        md5_hash = hashlib.md5(hash_input.encode()).hexdigest()
        row_key = str(uuid.UUID(md5_hash))

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