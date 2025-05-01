from azure.data.tables import TableClient, TableEntity
import os
from shared import ptmlog

def save_processed_appointments(appointments):
    logger = ptmlog.get_logger()

    STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        entity = TableEntity(**appointment)
        logger.info('updating entity', entity=entity)
        table_client.update_entity(entity)