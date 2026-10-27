import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

PATH = Path(os.environ.get('INVENTORY_COMPANION', '/data/companion.json'))
THROTTLE_SECONDS = 60

_written = {}


def _load():
    try:
        data = json.loads(PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def record(path, ok):
    """Remember when the Home Assistant companion integration last reached the app. Never raises."""
    keys = ['last_ok' if ok else 'last_rejected']
    if ok and path == '/inventory-api/health':
        keys.append('last_health')
    now = time.monotonic()
    due = [k for k in keys if k == 'last_health' or now - _written.get(k, -THROTTLE_SECONDS) >= THROTTLE_SECONDS]
    if not due:
        return
    try:
        data = _load()
        stamp = datetime.now(timezone.utc).isoformat()
        for key in due:
            data[key] = stamp
            _written[key] = now
        PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = PATH.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        tmp.replace(PATH)
    except OSError:
        pass


def status():
    """Seconds since the last accepted request, the last setup call and the last rejected request (None if never)."""
    data = _load()
    now = datetime.now(timezone.utc)
    out = {}
    for name, key in (('ok', 'last_ok'), ('health', 'last_health'), ('rejected', 'last_rejected')):
        try:
            out[name] = max(0, int((now - datetime.fromisoformat(data[key])).total_seconds()))
        except (KeyError, ValueError, TypeError):
            out[name] = None
    return out
