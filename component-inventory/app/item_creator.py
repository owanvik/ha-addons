import re
import sqlite3

import db

MAX_QUANTITY = 1000000
_URL = re.compile(r'^https?://\S+$', re.IGNORECASE)


def _text(data, key, limit, default=''):
    value = data.get(key)
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f'{key} must be text')
    value = str(value).strip()
    if len(value) > limit:
        raise ValueError(f'{key} is too long (max {limit} characters)')
    return value


def _url(data, key):
    value = _text(data, key, 500)
    # Links are shown as clickable links in the app, so only http(s) is allowed (no javascript: and similar)
    if value and not _URL.match(value):
        raise ValueError(f'{key} must start with http:// or https://')
    return value


def _quantity(data):
    value = data.get('quantity', 0)
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('quantity must be a whole number')
    if value < 0 or value > MAX_QUANTITY:
        raise ValueError(f'quantity must be between 0 and {MAX_QUANTITY}')
    return value


def _text_list(data, key, max_items, max_len):
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f'{key} must be a list of text values')
    if len(value) > max_items:
        raise ValueError(f'{key} has too many entries (max {max_items})')
    out = []
    for entry in value:
        text = _text({key: entry}, key, max_len)
        if text and text.lower() not in (x.lower() for x in out):
            out.append(text)
    return out


def _specifications(data):
    value = data.get('specifications')
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError('specifications must be an object of name/value pairs')
    if len(value) > 40:
        raise ValueError('specifications has too many entries (max 40)')
    out = {}
    for key, entry in value.items():
        name = _text({'specification name': key}, 'specification name', 60)
        if name:
            out[name] = _text({f'specification {name}': entry}, f'specification {name}', 200)
    return out


def _purchase_sources(data):
    value = data.get('purchase_sources')
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError('purchase_sources must be a list')
    if len(value) > 10:
        raise ValueError('purchase_sources has too many entries (max 10)')
    out = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError('each purchase source must be an object with vendor, url and part_number')
        source = {
            'vendor': _text(entry, 'vendor', 60),
            'url': _url(entry, 'url'),
            'part_number': _text(entry, 'part_number', 100),
        }
        if any(source.values()):
            out.append(source)
    return out


def _find_duplicate(name, sku):
    if sku:
        hit = db.get_item_by_sku(sku)
        if hit:
            return hit, f'SKU {sku}'
    lowered = name.lower()
    for item in db.list_items(limit=2000):
        if item['name'].lower() == lowered:
            return item, f'the name "{item["name"]}"'
    return None, ''


def _insert(fields):
    explicit = bool(fields['sku'])
    base = fields['sku'] or db._slug(fields['model'] or fields['name'])
    for attempt in range(1, 50):
        sku = base if attempt == 1 else f'{base}-{attempt}'
        try:
            return db.create_item({**fields, 'sku': sku})
        except sqlite3.IntegrityError:
            # SKUs are unique; a generated SKU gets a numeric suffix, an explicit one is refused
            if explicit or not base:
                raise ValueError(f'SKU {base} already exists')
    raise ValueError('Could not find a free SKU')


def create(data):
    """Validate and create a product. Raises ValueError with a readable message when the input is not acceptable."""
    if not isinstance(data, dict):
        raise ValueError('The product must be an object')
    name = _text(data, 'name', 200)
    if not name:
        raise ValueError('name is required')
    category = _text(data, 'category', 100)
    category = {c.lower(): c for c in db.categories()}.get(category.lower(), category)
    quantity = _quantity(data)
    fields = {
        'name': name,
        'sku': _text(data, 'sku', 64),
        'category': category,
        'subcategory': _text(data, 'subcategory', 100),
        'manufacturer': _text(data, 'manufacturer', 100),
        'model': _text(data, 'model', 100),
        'unit': _text(data, 'unit', 20) or 'pcs',
        'location': _text(data, 'location', 100),
        'description': _text(data, 'description', 2000),
        'notes': _text(data, 'notes', 2000),
        'datasheet_url': _url(data, 'datasheet_url'),
        'product_url': _url(data, 'product_url'),
        'applications': _text_list(data, 'applications', 30, 100),
        'tags': _text_list(data, 'tags', 30, 60),
        'specifications': _specifications(data),
        'purchase_sources': _purchase_sources(data),
        'quantity': 0,
    }
    existing, matched = _find_duplicate(name, fields['sku'])
    if existing:
        raise ValueError(
            f'An item with {matched} already exists (id {existing["id"]}, {existing["quantity"]} {existing["unit"]}). '
            'Use adjust_inventory_quantity to change its stock, or choose a different name or SKU.'
        )
    item = _insert(fields)
    if quantity:
        # Logged as a stock movement, like every other quantity change made through MCP
        item = db.adjust_quantity(item['id'], quantity, 'Created via MCP: initial stock')
    return item
