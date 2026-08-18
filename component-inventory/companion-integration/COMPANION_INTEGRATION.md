# Component Inventory - Home Assistant MCP companion integration

Home Assistant 2026.7+ can expose every registered LLM API over its built-in MCP Server at `/api/mcp/<API ID>`. The companion integration registers the inventory as the LLM API `component_inventory`.

## Why this exists

The app/add-on owns SQLite, the product UI, imports, images, stock and purchase sources. The small Home Assistant integration only exposes inventory tools to Home Assistant. This lets remote MCP clients use the normal Home Assistant HTTPS endpoint, including Nabu Casa, without opening the add-on's port to the internet.

## Install

1. Install/update the `Component Inventory` app to v0.4.0 and start it.
2. Copy `companion-integration/custom_components/component_inventory` into `/config/custom_components/component_inventory` on Home Assistant.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration > Component Inventory**.
5. Enter a local URL that Home Assistant Core can reach, typically `http://<HOME_ASSISTANT_LAN_IP>:8098`, and paste the token from **Component Inventory > Settings**.
6. Add Home Assistant's built-in **Model Context Protocol Server** integration if it is not already configured.

## Remote MCP endpoint

Use:

`https://<your-home-assistant-external-url>/api/mcp/component_inventory`

With Nabu Casa this means your normal `https://....ui.nabu.casa` URL. Do **not** append port 8098.

Authentication is handled by Home Assistant. Clients that support OAuth can authenticate against Home Assistant; clients that support bearer tokens can use a Home Assistant long-lived access token. Custom LLM API endpoints require admin authorization.

## Local/direct fallback

The app still exposes its own MCP endpoint on LAN port 8098:

`http://<HOME_ASSISTANT_LAN_IP>:8098/mcp`

This direct endpoint uses the local app API token and does not need the companion integration.
