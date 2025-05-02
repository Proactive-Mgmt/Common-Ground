from pathlib import Path
import json

def get_playwright_storage_state():
    storage_state_path = Path('storage_state.json')
    if storage_state_path.exists():
        return json.loads(storage_state_path.read_text())
    else:
        return None

def save_playwright_storage_state(storage_state) -> None:
    Path('storage_state.json').write_text(json.dumps(storage_state))