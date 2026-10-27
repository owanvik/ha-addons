import json
import re

CLAUDE_CODE_SERVER = 'component-inventory'
CODEX_SERVER = 'component_inventory'
TOKEN_ENV = 'COMPONENT_INVENTORY_TOKEN'

_URL = re.compile(r'^https?://[^\s"\'\\\x00-\x1f]{1,300}$')


def valid_url(url):
    return bool(_URL.match(url or ''))


def claude_code_config(url, lan):
    """Project-scoped .mcp.json for Claude Code. The LAN variant only references the token variable."""
    server = {'type': 'http', 'url': url}
    if lan:
        server['headers'] = {'Authorization': 'Bearer ${' + TOKEN_ENV + '}'}
    return json.dumps({'mcpServers': {CLAUDE_CODE_SERVER: server}}, indent=2) + '\n'


def codex_config(url, lan):
    """Table to append to ~/.codex/config.toml. The LAN variant only references the token variable."""
    if lan:
        lines = [
            '# Component Inventory over the local network. Set %s in your shell first.' % TOKEN_ENV,
            '[mcp_servers.%s]' % CODEX_SERVER,
            'url = %s' % json.dumps(url),
            'bearer_token_env_var = %s' % json.dumps(TOKEN_ENV),
        ]
    else:
        lines = [
            '# Component Inventory through Home Assistant. Then run: codex mcp login %s' % CODEX_SERVER,
            '[mcp_servers.%s]' % CODEX_SERVER,
            'url = %s' % json.dumps(url),
        ]
    return '\n'.join(lines) + '\n'
