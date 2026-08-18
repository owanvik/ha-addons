import json
import secrets
from urllib.parse import parse_qs

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

import db
import settings


db.initialize()
settings.load_settings()

mcp = MCPServer('Component Inventory')


@mcp.tool()
def search_inventory(query: str, category: str | None = None, in_stock_only: bool = True, limit: int = 20) -> dict:
    """Search the electronics product catalog by name, SKU, model, purpose, applications, tags or specifications."""
    return {'query': query, 'items': db.search_items(query, category, in_stock_only, limit)}


@mcp.tool()
def get_inventory_item(item_id: int) -> dict:
    """Get a product and its stock data by numeric inventory ID."""
    item = db.get_item(item_id)
    return item or {'error': 'Item not found'}


@mcp.tool()
def get_inventory_item_by_sku(sku: str) -> dict:
    """Get a product by its stable internal SKU."""
    item = db.get_item_by_sku(sku)
    return item or {'error': 'Item not found'}


@mcp.tool()
def list_inventory(category: str | None = None, in_stock_only: bool = True, limit: int = 500) -> dict:
    """List inventory products, optionally filtered by exact category."""
    return {'items': db.list_items(category, in_stock_only, limit)}


@mcp.tool()
def list_categories() -> dict:
    """List product categories in the inventory."""
    return {'categories': db.categories()}


@mcp.tool()
def adjust_quantity(item_id: int, delta: int, reason: str = 'MCP') -> dict:
    """Adjust stock quantity. Disabled unless MCP writes are enabled in the app Settings panel."""
    if not settings.load_settings().get('allow_mcp_writes', False):
        return {'error': 'MCP writes are disabled. Enable them in Component Inventory > Settings.'}
    try:
        return db.adjust_quantity(item_id, delta, reason)
    except Exception as exc:
        return {'error': str(exc)}


mcp_app = mcp.streamable_http_app(
    streamable_http_path='/mcp',
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


async def _read_body(receive):
    chunks = []
    while True:
        message = await receive()
        if message['type'] != 'http.request':
            continue
        chunks.append(message.get('body', b''))
        if not message.get('more_body', False):
            return b''.join(chunks)


async def _json_response(send, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [
            (b'content-type', b'application/json; charset=utf-8'),
            (b'content-length', str(len(body)).encode()),
        ],
    })
    await send({'type': 'http.response.body', 'body': body})


class InventoryRestAPI:
    """Small authenticated REST surface used by the Home Assistant companion integration."""

    def __init__(self, fallback_app):
        self.fallback_app = fallback_app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.fallback_app(scope, receive, send)

        path = scope.get('path', '')
        if not path.startswith('/inventory-api/'):
            return await self.fallback_app(scope, receive, send)

        try:
            method = scope.get('method', 'GET').upper()
            query = parse_qs(scope.get('query_string', b'').decode())

            if path == '/inventory-api/health' and method == 'GET':
                return await _json_response(send, 200, {'ok': True, 'service': 'component-inventory'})

            if path == '/inventory-api/categories' and method == 'GET':
                return await _json_response(send, 200, {'categories': db.categories()})

            if path == '/inventory-api/search' and method == 'GET':
                q = query.get('q', [''])[0]
                category = query.get('category', [None])[0] or None
                in_stock_only = query.get('in_stock_only', ['true'])[0].lower() not in ('0', 'false', 'no')
                limit = min(max(int(query.get('limit', ['20'])[0]), 1), 500)
                return await _json_response(send, 200, {
                    'query': q,
                    'items': db.search_items(q, category, in_stock_only, limit),
                })

            if path == '/inventory-api/items' and method == 'GET':
                category = query.get('category', [None])[0] or None
                in_stock_only = query.get('in_stock_only', ['true'])[0].lower() not in ('0', 'false', 'no')
                limit = min(max(int(query.get('limit', ['500'])[0]), 1), 2000)
                return await _json_response(send, 200, {
                    'items': db.list_items(category, in_stock_only, limit),
                })

            if path.startswith('/inventory-api/items/sku/') and method == 'GET':
                sku = path.removeprefix('/inventory-api/items/sku/')
                item = db.get_item_by_sku(sku)
                return await _json_response(send, 200 if item else 404, item or {'error': 'Item not found'})

            if path.startswith('/inventory-api/items/'):
                suffix = path.removeprefix('/inventory-api/items/')
                if suffix.endswith('/adjust') and method == 'POST':
                    if not settings.load_settings().get('allow_mcp_writes', False):
                        return await _json_response(send, 403, {'error': 'Inventory writes are disabled'})
                    item_id = int(suffix[:-7].rstrip('/'))
                    data = json.loads((await _read_body(receive)).decode() or '{}')
                    result = db.adjust_quantity(item_id, int(data.get('delta', 0)), str(data.get('reason', 'Home Assistant MCP')))
                    return await _json_response(send, 200, result)
                if method == 'GET' and suffix.isdigit():
                    item = db.get_item(int(suffix))
                    return await _json_response(send, 200 if item else 404, item or {'error': 'Item not found'})

            return await _json_response(send, 404, {'error': 'Not found'})
        except Exception as exc:
            return await _json_response(send, 400, {'error': str(exc)})


class BearerAuth:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            headers = {k.decode().lower(): v.decode() for k, v in scope.get('headers', [])}
            supplied = headers.get('authorization', '')
            token = settings.load_settings()['api_token']
            if not supplied.startswith('Bearer ') or not secrets.compare_digest(supplied[7:], token):
                body = b'{"error":"unauthorized"}'
                await send({
                    'type': 'http.response.start',
                    'status': 401,
                    'headers': [(b'content-type', b'application/json'), (b'www-authenticate', b'Bearer')],
                })
                await send({'type': 'http.response.body', 'body': body})
                return
        await self.app(scope, receive, send)


app = BearerAuth(InventoryRestAPI(mcp_app))


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8098, log_level='info')
