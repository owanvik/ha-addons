# Component Inventory - Home Assistant MCP companion integration

Home Assistant 2026.7+ can expose every registered LLM API over its built-in MCP Server at `/api/mcp/<API ID>`. The companion integration registers the inventory as the LLM API `component_inventory`.

## Why this exists

The app/add-on owns SQLite, the product UI, imports, images, stock and purchase sources. The small Home Assistant integration only exposes inventory tools to Home Assistant. This lets remote MCP clients use the normal Home Assistant HTTPS endpoint, including Nabu Casa, without opening the add-on's port to the internet.

## Install

1. Install/update the `Component Inventory` app to v0.4.1 and start it.
2. Copy `companion-integration/custom_components/component_inventory` into `/config/custom_components/component_inventory` on Home Assistant.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration > Component Inventory**.
5. Enter a local URL that Home Assistant Core can reach, typically `http://<HOME_ASSISTANT_LAN_IP>:8098`, and paste the token from **Component Inventory > Settings**.
6. Add Home Assistant's built-in **Model Context Protocol Server** integration if it is not already configured.

## Remote MCP endpoint

Use:

`https://<your-home-assistant-external-url>/api/mcp/component_inventory`

With Nabu Casa this means your normal `https://....ui.nabu.casa` URL. Do **not** append port 8098.

Authentication is handled by Home Assistant, which uses OAuth 2.0 with PKCE and Client ID Metadata Documents (not Dynamic Client Registration). Custom LLM API endpoints require an administrator account.

- **Claude:** add a custom connector with the URL, choose **Sign in now**, then **Use Claude's published identity**, and log in to Home Assistant.
- **ChatGPT:** add a custom MCP server with the URL, set authentication to **OAuth** (client ID `https://chatgpt.com`), and log in to Home Assistant.
- **Other clients:** clients that can send headers may be able to use a Home Assistant long-lived access token as a bearer token. This is standard Home Assistant API authentication, but it is not covered by Home Assistant's MCP Server documentation, so test it first.

For OAuth, Home Assistant's **External URL** (Settings > System > Network) must match the hostname the client uses, normally the `.ui.nabu.casa` address.

## Compatibility

The integration detects the Home Assistant 2026.9 (Probatio) and 2026.10 (`llm.ToolResult`, tool annotations) changes at runtime, so the same files are meant to work before and after them. The search, get and list tools are declared read-only; the quantity adjustment is declared as a non-destructive write and only works when writes are enabled in the app Settings.

If Home Assistant starts before the app, the integration shows "Retrying setup" and connects once the app is reachable.

## Local/direct fallback

The app still exposes its own MCP endpoint on LAN port 8098:

`http://<HOME_ASSISTANT_LAN_IP>:8098/mcp`

This direct endpoint uses the local app API token and does not need the companion integration.
