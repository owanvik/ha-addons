import hashlib
import json
import os
import shutil
import socket
import time
from pathlib import Path

DOMAIN = 'component_inventory'
SOURCE = Path(os.environ.get('COMPANION_SOURCE', '/opt/companion/component_inventory'))
CONFIG_DIR = Path(os.environ.get('HA_CONFIG_DIR', '/homeassistant'))
BACKUP_DIR = Path(os.environ.get('COMPANION_BACKUP', '/data/companion_backup'))


class InstallError(Exception):
    pass


def _files(root):
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob('*')
        if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix != '.pyc'
    )


def _digest(root):
    h = hashlib.sha256()
    for rel in _files(root):
        h.update(rel.encode('utf-8') + b'\0' + (root / rel).read_bytes() + b'\0')
    return h.hexdigest()


def _version(root):
    try:
        return json.loads((root / 'manifest.json').read_text(encoding='utf-8')).get('version')
    except (OSError, json.JSONDecodeError):
        return None


def _config_writable():
    looks_like_ha = (CONFIG_DIR / 'configuration.yaml').is_file() or (CONFIG_DIR / '.storage').is_dir()
    return CONFIG_DIR.is_dir() and looks_like_ha and os.access(CONFIG_DIR, os.W_OK)


def status():
    """State of the Home Assistant integration files: unavailable, not_mapped, not_installed, outdated or current."""
    target = CONFIG_DIR / 'custom_components' / DOMAIN
    out = {
        'bundled_version': _version(SOURCE),
        'installed_version': _version(target) if target.is_dir() else None,
        'suggested_url': 'http://%s:8098' % socket.gethostname(),
    }
    if not (SOURCE / 'manifest.json').is_file():
        out['state'] = 'unavailable'
    elif not _config_writable():
        out['state'] = 'not_mapped'
    elif not target.is_dir():
        out['state'] = 'not_installed'
    else:
        out['state'] = 'current' if _digest(SOURCE) == _digest(target) else 'outdated'
    return out


def _backup(target):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for old in BACKUP_DIR.glob(DOMAIN + '-*'):
        shutil.rmtree(old, ignore_errors=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    shutil.copytree(target, BACKUP_DIR / ('%s-%s' % (DOMAIN, stamp)), ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def install():
    """Copy the bundled integration to <config>/custom_components/component_inventory and nothing else."""
    st = status()
    if st['state'] == 'unavailable':
        raise InstallError('This build of the app does not include the integration files.')
    if st['state'] == 'not_mapped':
        raise InstallError("The app cannot write to Home Assistant's config folder. Update the app to the latest version, which asks for that permission.")
    custom = CONFIG_DIR / 'custom_components'
    target = custom / DOMAIN
    if custom.is_symlink() or target.is_symlink():
        raise InstallError('custom_components is a symbolic link here. Copy the integration manually instead.')
    custom.mkdir(exist_ok=True)
    new, old = custom / ('.%s.new' % DOMAIN), custom / ('.%s.old' % DOMAIN)
    for leftover in (new, old):
        if leftover.exists():
            shutil.rmtree(leftover)
    shutil.copytree(SOURCE, new, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    try:
        if target.exists():
            if st['state'] == 'outdated':
                _backup(target)
            target.rename(old)
        new.rename(target)
    except OSError:
        if old.exists() and not target.exists():
            old.rename(target)
        shutil.rmtree(new, ignore_errors=True)
        raise
    shutil.rmtree(old, ignore_errors=True)
    return status()
