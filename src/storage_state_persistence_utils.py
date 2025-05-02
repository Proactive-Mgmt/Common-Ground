from pathlib import Path
import json

def get_playwright_storage_state(id: str):
    storage_state_path = Path(f'{id}.json')
    if storage_state_path.exists():
        return json.loads(storage_state_path.read_text())
    else:
        return None

def save_playwright_storage_state(id: str, storage_state) -> None:
    Path(f'{id}.json').write_text(json.dumps(storage_state))