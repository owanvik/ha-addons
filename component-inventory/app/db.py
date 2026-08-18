import csv
import io
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get('INVENTORY_DB', '/data/inventory.db')

PRODUCT_FIELDS = [
    'sku', 'name', 'category', 'subcategory', 'manufacturer', 'model',
    'unit', 'location', 'description', 'applications', 'tags',
    'specifications', 'notes', 'datasheet_url', 'product_url', 'purchase_sources'
]

BASE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    subcategory TEXT NOT NULL DEFAULT '',
    manufacturer TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    unit TEXT NOT NULL DEFAULT 'pcs',
    location TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    applications TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    specifications TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    datasheet_url TEXT NOT NULL DEFAULT '',
    product_url TEXT NOT NULL DEFAULT '',
    purchase_sources TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    delta INTEGER NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_items_sku_unique ON items(sku) WHERE sku <> '';
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
'''

MIGRATION_COLUMNS = {
    'sku': "TEXT NOT NULL DEFAULT ''",
    'subcategory': "TEXT NOT NULL DEFAULT ''",
    'manufacturer': "TEXT NOT NULL DEFAULT ''",
    'description': "TEXT NOT NULL DEFAULT ''",
    'applications': "TEXT NOT NULL DEFAULT '[]'",
    'specifications': "TEXT NOT NULL DEFAULT '{}'",
    'datasheet_url': "TEXT NOT NULL DEFAULT ''",
    'product_url': "TEXT NOT NULL DEFAULT ''",
    'purchase_sources': "TEXT NOT NULL DEFAULT '[]'",
}

SYNONYMS = {
    'distance': ['ultrasonic', 'range', 'hc-sr04'],
    'temperature': ['dht11', 'climate', 'humidity'],
    'humidity': ['dht11', 'climate', 'temperature'],
    'motion': ['pir', 'movement', 'hc-sr501'],
    'movement': ['pir', 'motion', 'hc-sr501'],
    'light': ['ldr', 'photoresistor', 'led', 'optical'],
    'sound': ['microphone', 'buzzer', 'speaker', 'audio'],
    'button': ['switch', 'tactile', 'button cap', 'keypad'],
    'display': ['lcd', '7-segment', 'matrix', '1602'],
    'wireless': ['bluetooth', 'rf', 'rfid', 'nfc', '433'],
    'motor': ['stepper', 'uln2003', 'driver'],
    'soil': ['moisture', 'fc-28'],
    'moisture': ['soil', 'fc-28'],
    'clock': ['rtc', 'ds1302'],
    'relay': ['switching', 'songle'],
    'infrared': ['ir', 'emitter', 'receiver', 'phototransistor'],
    'accelerometer': ['gy-61', 'motion', '3-axis'],
    'potentiometer': ['variable resistor', 'analog control'],
    'resistor': ['passive', 'through-hole', 'axial'],
}


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def _columns(con):
    return {row[1] for row in con.execute('PRAGMA table_info(items)').fetchall()}


def _json_text(value, default):
    if value is None or value == '':
        return json.dumps(default, ensure_ascii=False)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    text = str(value).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, type(default)):
            return json.dumps(parsed, ensure_ascii=False)
    except Exception:
        pass
    if isinstance(default, list):
        parts = [p.strip() for p in re.split(r'[;|]', text) if p.strip()]
        return json.dumps(parts, ensure_ascii=False)
    return json.dumps(default, ensure_ascii=False)


def _decode_item(row):
    item = dict(row)
    for field, default in [('applications', []), ('tags', []), ('specifications', {}), ('purchase_sources', [])]:
        try:
            item[field] = json.loads(item.get(field) or json.dumps(default))
        except Exception:
            item[field] = default
    return item


def _slug(value):
    s = re.sub(r'[^A-Za-z0-9]+', '-', str(value).upper()).strip('-')
    return s[:48]


def _ensure_skus(con):
    rows = con.execute("SELECT id, name, model, sku FROM items ORDER BY id").fetchall()
    used = {r['sku'] for r in rows if r['sku']}
    for row in rows:
        if row['sku']:
            continue
        base = _slug(row['model'] or row['name']) or f'ITEM-{row["id"]:04d}'
        sku = base
        n = 2
        while sku in used:
            sku = f'{base}-{n}'
            n += 1
        con.execute('UPDATE items SET sku=? WHERE id=?', (sku, row['id']))
        used.add(sku)


def initialize():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
        existing = _columns(con)
        core = {
            'category': "TEXT NOT NULL DEFAULT ''", 'model': "TEXT NOT NULL DEFAULT ''",
            'unit': "TEXT NOT NULL DEFAULT 'pcs'", 'location': "TEXT NOT NULL DEFAULT ''",
            'notes': "TEXT NOT NULL DEFAULT ''", 'tags': "TEXT NOT NULL DEFAULT '[]'"
        }
        for name, definition in {**core, **MIGRATION_COLUMNS}.items():
            if name not in existing:
                con.execute(f'ALTER TABLE items ADD COLUMN {name} {definition}')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            delta INTEGER NOT NULL,
            reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
        CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
        ''')
        # Convert legacy plain-text tags to JSON arrays if needed.
        for row in con.execute('SELECT id, tags FROM items').fetchall():
            tags = row['tags'] or ''
            try:
                parsed = json.loads(tags)
                if not isinstance(parsed, list):
                    raise ValueError
            except Exception:
                con.execute('UPDATE items SET tags=? WHERE id=?', (_json_text(tags, []), row['id']))
        _ensure_skus(con)
        try:
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_items_sku_unique ON items(sku) WHERE sku <> ''")
        except sqlite3.IntegrityError:
            _ensure_skus(con)
            con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_items_sku_unique ON items(sku) WHERE sku <> ''")
        con.commit()


def _insert_item(con, data):
    ts = now()
    values = {
        'sku': str(data.get('sku', '')).strip(),
        'name': str(data.get('name', '')).strip(),
        'category': str(data.get('category', '')).strip(),
        'subcategory': str(data.get('subcategory', '')).strip(),
        'manufacturer': str(data.get('manufacturer', '')).strip(),
        'model': str(data.get('model', '')).strip(),
        'quantity': max(0, int(data.get('quantity', 0) or 0)),
        'unit': str(data.get('unit', 'pcs') or 'pcs').strip(),
        'location': str(data.get('location', '')).strip(),
        'description': str(data.get('description', '')).strip(),
        'applications': _json_text(data.get('applications'), []),
        'tags': _json_text(data.get('tags'), []),
        'specifications': _json_text(data.get('specifications'), {}),
        'notes': str(data.get('notes', '')).strip(),
        'datasheet_url': str(data.get('datasheet_url', '')).strip(),
        'product_url': str(data.get('product_url', '')).strip(),
        'purchase_sources': _json_text(data.get('purchase_sources'), []),
        'created_at': ts,
        'updated_at': ts,
    }
    if not values['name']:
        raise ValueError('name is required')
    if not values['sku']:
        values['sku'] = _slug(values['model'] or values['name'])
    cols = list(values.keys())
    cur = con.execute(
        f"INSERT INTO items({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
        [values[c] for c in cols]
    )
    return cur.lastrowid


def list_items(category=None, in_stock_only=False, limit=500):
    sql = 'SELECT * FROM items WHERE 1=1'
    args = []
    if category:
        sql += ' AND lower(category)=lower(?)'
        args.append(category)
    if in_stock_only:
        sql += ' AND quantity > 0'
    sql += ' ORDER BY category, subcategory, name LIMIT ?'
    args.append(min(max(int(limit), 1), 2000))
    with connect() as con:
        return [_decode_item(r) for r in con.execute(sql, args).fetchall()]


def get_item(item_id):
    with connect() as con:
        row = con.execute('SELECT * FROM items WHERE id=?', (int(item_id),)).fetchone()
        return _decode_item(row) if row else None


def get_item_by_sku(sku):
    with connect() as con:
        row = con.execute('SELECT * FROM items WHERE lower(sku)=lower(?)', (str(sku),)).fetchone()
        return _decode_item(row) if row else None


def categories():
    with connect() as con:
        return [r[0] for r in con.execute("SELECT DISTINCT category FROM items WHERE category<>'' ORDER BY category").fetchall()]


def _tokens(query):
    base = [t for t in re.findall(r'[\w+.-]+', (query or '').lower()) if len(t) > 1]
    expanded = []
    for token in base:
        expanded.append(token)
        expanded.extend(SYNONYMS.get(token, []))
    return list(dict.fromkeys(expanded))


def _search_blob(item):
    specs = ' '.join(f'{k} {v}' for k, v in item.get('specifications', {}).items())
    sources = ' '.join(f"{s.get('vendor','')} {s.get('part_number','')} {s.get('url','')}" for s in item.get('purchase_sources', []))
    fields = [item.get(k, '') for k in ['sku','name','category','subcategory','manufacturer','model','description','notes','location']]
    fields += item.get('applications', []) + item.get('tags', []) + [specs, sources]
    return ' '.join(str(v) for v in fields).lower()


def search_items(query, category=None, in_stock_only=True, limit=20):
    tokens = _tokens(query)
    candidates = list_items(category=category, in_stock_only=in_stock_only, limit=2000)
    if not tokens:
        return candidates[:limit]
    scored = []
    for item in candidates:
        hay = _search_blob(item)
        score = 0
        for token in tokens:
            pattern = r'(?<![a-z0-9])' + re.escape(token) + r'(?![a-z0-9])'
            if re.search(pattern, hay):
                direct = ' '.join([item['name'], item['model'], item['sku']]).lower()
                apps = ' '.join(item.get('applications', [])).lower()
                if re.search(pattern, direct):
                    score += 4
                elif re.search(pattern, apps):
                    score += 2
                else:
                    score += 1
        min_score = 2 if len(tokens) > 1 else 1
        if score >= min_score:
            if item['quantity'] > 0:
                score += 1
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1]['name'].lower()))
    return [item for _, item in scored[:min(max(int(limit), 1), 100)]]


def adjust_quantity(item_id, delta, reason=''):
    delta = int(delta)
    with connect() as con:
        row = con.execute('SELECT quantity FROM items WHERE id=?', (int(item_id),)).fetchone()
        if not row:
            raise KeyError('Item not found')
        new_qty = row[0] + delta
        if new_qty < 0:
            raise ValueError('Quantity cannot become negative')
        ts = now()
        con.execute('UPDATE items SET quantity=?, updated_at=? WHERE id=?', (new_qty, ts, int(item_id)))
        con.execute('INSERT INTO movements(item_id,delta,reason,created_at) VALUES(?,?,?,?)', (int(item_id), delta, reason, ts))
        con.commit()
    return get_item(item_id)


def update_item(item_id, fields):
    clean = {}
    for key in PRODUCT_FIELDS:
        if key not in fields:
            continue
        value = fields[key]
        if key in ('applications', 'tags'):
            clean[key] = _json_text(value, [])
        elif key == 'specifications':
            clean[key] = _json_text(value, {})
        elif key == 'purchase_sources':
            clean[key] = _json_text(value, [])
        else:
            clean[key] = str(value or '').strip()
    if 'quantity' in fields:
        clean['quantity'] = max(0, int(fields['quantity']))
    if not clean:
        return get_item(item_id)
    clean['updated_at'] = now()
    sets = ', '.join(f'{k}=?' for k in clean)
    vals = list(clean.values()) + [int(item_id)]
    with connect() as con:
        con.execute(f'UPDATE items SET {sets} WHERE id=?', vals)
        con.commit()
    return get_item(item_id)


def create_item(data):
    with connect() as con:
        item_id = _insert_item(con, data)
        con.commit()
    return get_item(item_id)


def _normalize_import_item(raw):
    item = {k: raw.get(k, '') for k in PRODUCT_FIELDS}
    item['quantity'] = max(0, int(raw.get('quantity', 0) or 0))
    item['unit'] = raw.get('unit') or 'pcs'
    for key in ('applications', 'tags'):
        value = raw.get(key, [])
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                value = parsed if isinstance(parsed, list) else [value]
            except Exception:
                value = [x.strip() for x in re.split(r'[;|]', value) if x.strip()]
        item[key] = value
    for key, default in [('specifications', {}), ('purchase_sources', [])]:
        value = raw.get(key, default)
        if isinstance(value, str):
            try:
                value = json.loads(value) if value.strip() else default
            except Exception:
                value = default
        item[key] = value
    item['sku'] = str(item.get('sku', '')).strip()
    item['name'] = str(item.get('name', '')).strip()
    if not item['name']:
        raise ValueError('Missing product name')
    return item


def parse_import(content, fmt):
    fmt = fmt.lower()
    if fmt == 'json':
        data = json.loads(content)
        rows = data.get('items', data) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError('JSON must be an array or an object containing an items array')
    elif fmt == 'csv':
        rows = list(csv.DictReader(io.StringIO(content)))
    else:
        raise ValueError('Unsupported import format')
    return [_normalize_import_item(row) for row in rows]


def _find_existing(con, item):
    if item.get('sku'):
        row = con.execute('SELECT * FROM items WHERE lower(sku)=lower(?)', (item['sku'],)).fetchone()
        if row:
            return row
    return con.execute('SELECT * FROM items WHERE lower(name)=lower(?)', (item['name'],)).fetchone()


def preview_import(items, mode='update_existing'):
    result = []
    with connect() as con:
        for item in items:
            existing = _find_existing(con, item)
            if not existing:
                action = 'create'
            elif mode == 'skip_existing':
                action = 'skip'
            elif mode == 'add_quantity':
                action = 'add_quantity'
            elif mode == 'replace':
                action = 'replace'
            else:
                action = 'update'
            result.append({
                'sku': item.get('sku', ''), 'name': item['name'], 'quantity': item['quantity'],
                'action': action, 'existing_quantity': existing['quantity'] if existing else None
            })
    return result


def import_items(items, mode='update_existing'):
    counts = {'created': 0, 'updated': 0, 'skipped': 0, 'quantity_added': 0, 'replaced': 0}
    with connect() as con:
        for item in items:
            existing = _find_existing(con, item)
            if not existing:
                _insert_item(con, item)
                counts['created'] += 1
                continue
            item_id = existing['id']
            if mode == 'skip_existing':
                counts['skipped'] += 1
                continue
            if mode == 'add_quantity':
                new_qty = existing['quantity'] + item['quantity']
                con.execute('UPDATE items SET quantity=?, updated_at=? WHERE id=?', (new_qty, now(), item_id))
                con.execute('INSERT INTO movements(item_id,delta,reason,created_at) VALUES(?,?,?,?)', (item_id, item['quantity'], 'Import: add quantity', now()))
                counts['quantity_added'] += 1
                continue
            values = {}
            for key in PRODUCT_FIELDS:
                if key in item:
                    if key in ('applications', 'tags'):
                        values[key] = _json_text(item[key], [])
                    elif key == 'specifications':
                        values[key] = _json_text(item[key], {})
                    elif key == 'purchase_sources':
                        values[key] = _json_text(item[key], [])
                    else:
                        values[key] = str(item[key] or '').strip()
            values['quantity'] = item['quantity']
            values['updated_at'] = now()
            sets = ', '.join(f'{k}=?' for k in values)
            con.execute(f'UPDATE items SET {sets} WHERE id=?', list(values.values()) + [item_id])
            counts['replaced' if mode == 'replace' else 'updated'] += 1
        con.commit()
    return counts


def export_json():
    return json.dumps({'version': 1, 'items': list_items(limit=2000)}, ensure_ascii=False, indent=2)


def export_csv():
    output = io.StringIO()
    columns = ['sku','name','category','subcategory','manufacturer','model','quantity','unit','location','description','applications','tags','specifications','notes','datasheet_url','product_url','purchase_sources']
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for item in list_items(limit=2000):
        row = {k: item.get(k, '') for k in columns}
        for key in ('applications','tags','specifications','purchase_sources'):
            row[key] = json.dumps(row[key], ensure_ascii=False, separators=(',', ':'))
        writer.writerow(row)
    return output.getvalue()
