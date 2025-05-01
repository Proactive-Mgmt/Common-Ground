from azure.data.tables import TableClient, TableEntity
import logging
import os

def save_processed_appointments(appointments):
    logging.info('save_processed_appointments')

    STORAGE_ACCOUNT_CONNECTION_STRING = os.getenv('STORAGE_ACCOUNT_CONNECTION_STRING')
    table_client = TableClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING, 'appointments')

    for appointment in appointments:
        entity = TableEntity(**appointment)
        logging.info('Updating entity:\n%s', entity)
        table_client.update_entity(entity)