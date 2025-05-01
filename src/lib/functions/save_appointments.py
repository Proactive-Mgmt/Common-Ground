from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient, TableEntity
import hashlib
import uuid
import os

from shared import ptmlog

def save_appointments(appointments):
    logger = ptmlog.get_logger()

    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        # Generate row_key by hashing compound key (dob+lastname+phonenumber)
        hash_input = appointment['patientDOB'] + appointment['patientName'].split()[1] + appointment['patientPhone'] + appointment['appointmentTime']
        md5_hash = hashlib.md5(hash_input.encode()).hexdigest()
        row_key = str(uuid.UUID(md5_hash))

        appointment['RowKey'] = row_key
        appointment['PartitionKey'] = row_key[-1]
        appointment['sentOn'] = ''
        appointment['message_sid'] = ''
        entity = TableEntity(**appointment)
        try:
            logger.info('creating entity', entity=entity)
            table_client.create_entity(entity)
        except ResourceExistsError:
            logger.warning('entity already exists', entity=entity)