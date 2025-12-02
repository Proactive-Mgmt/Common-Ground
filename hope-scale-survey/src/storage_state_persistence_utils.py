from pathlib import Path
import json
from azure.storage.blob import BlobClient
from azure.core.exceptions import ResourceNotFoundError
import os

from shared import ptmlog

STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']


def get_playwright_storage_state(id: str):
    logger = ptmlog.get_logger()
    client = BlobClient.from_connection_string(
        conn_str       = STORAGE_ACCOUNT_CONNECTION_STRING,
        container_name = 'playwright-storage-state',
        blob_name      = id,
    )
    try:
        storage_state = json.load(client.download_blob())
        logger.debug('loaded playwright storage state from blob', id=id)
        return storage_state
    except ResourceNotFoundError:
        logger.debug('no playwright storage state found in blob', id=id)
        return None
    

def save_playwright_storage_state(id: str, storage_state) -> None:
    logger = ptmlog.get_logger()
    client = BlobClient.from_connection_string(
        conn_str       = STORAGE_ACCOUNT_CONNECTION_STRING,
        container_name = 'playwright-storage-state',
        blob_name      = id,
    )
    client.upload_blob(
        data = json.dumps(storage_state),
        overwrite = True,
    )
    logger.debug('saved playwright storage state to blob', id=id)


def delete_playwright_storage_state(id: str) -> None:
    """
    Delete the cached playwright storage state from blob storage.
    Called when session is detected as expired/invalid to force fresh login.
    """
    logger = ptmlog.get_logger()
    client = BlobClient.from_connection_string(
        conn_str       = STORAGE_ACCOUNT_CONNECTION_STRING,
        container_name = 'playwright-storage-state',
        blob_name      = id,
    )
    try:
        client.delete_blob()
        logger.info('deleted playwright storage state from blob', id=id)
    except ResourceNotFoundError:
        logger.debug('no playwright storage state to delete', id=id)

def get_playwright_storage_state_local(id: str):
    storage_state_path = Path(f'{id}.json')
    if storage_state_path.exists():
        return json.loads(storage_state_path.read_text())
    else:
        return None

def save_playwright_storage_state_local(id: str, storage_state) -> None:
    Path(f'{id}.json').write_text(json.dumps(storage_state))