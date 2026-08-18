import json
import os
import secrets
from pathlib import Path

SETTINGS_PATH = Path(os.environ.get('INVENTORY_SETTINGS', '/data/settings.json'))

DEFAULTS = {
    'api_token': '',
    'allow_mcp_writes': False,
}


def _ensure_parent():
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _new_token():
    return secrets.token_urlsafe(36)


def load_settings():
    _ensure_parent()
    data = {}
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            data = {}
    merged = {**DEFAULTS, **data}
    if not merged.get('api_token'):
        merged['api_token'] = _new_token()
        save_settings(merged)
    return merged


def save_settings(data):
    _ensure_parent()
    clean = {
        'api_token': str(data.get('api_token') or _new_token()),
        'allow_mcp_writes': bool(data.get('allow_mcp_writes', False)),
    }
    tmp = SETTINGS_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(clean, indent=2), encoding='utf-8')
    os.chmod(tmp, 0o600)
    tmp.replace(SETTINGS_PATH)
    return clean


def update_settings(changes):
    current = load_settings()
    if 'allow_mcp_writes' in changes:
        current['allow_mcp_writes'] = bool(changes['allow_mcp_writes'])
    return save_settings(current)


def rotate_token():
    current = load_settings()
    current['api_token'] = _new_token()
    return save_settings(current)
