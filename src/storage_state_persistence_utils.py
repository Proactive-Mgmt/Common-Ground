from pathlib import Path
import json
from azure.storage.blob import BlobClient
from azure.core.exceptions import ResourceNotFoundError
import os

STORAGE_ACCOUNT_CONNECTION_STRING = os.environ['STORAGE_ACCOUNT_CONNECTION_STRING']


def get_playwright_storage_state(id: str):
    os.environ['STORAGE_ACCOUNT_CONNECTION_STRING'] = STORAGE_ACCOUNT_CONNECTION_STRING
    client = BlobClient.from_connection_string(
        conn_str       = STORAGE_ACCOUNT_CONNECTION_STRING,
        container_name = 'playwright-storage-state',
        blob_name      = id,
    )
    try:
        return json.load(client.download_blob())
    except ResourceNotFoundError:
        return None
    

def save_playwright_storage_state(id: str, storage_state) -> None:
    os.environ['STORAGE_ACCOUNT_CONNECTION_STRING'] = STORAGE_ACCOUNT_CONNECTION_STRING
    client = BlobClient.from_connection_string(
        conn_str       = STORAGE_ACCOUNT_CONNECTION_STRING,
        container_name = 'playwright-storage-state',
        blob_name      = id,
    )
    client.upload_blob(
        data = json.dumps(storage_state),
        overwrite = True,
    )

def get_playwright_storage_state_local(id: str):
    storage_state_path = Path(f'{id}.json')
    if storage_state_path.exists():
        return json.loads(storage_state_path.read_text())
    else:
        return None

def save_playwright_storage_state_local(id: str, storage_state) -> None:
    Path(f'{id}.json').write_text(json.dumps(storage_state))