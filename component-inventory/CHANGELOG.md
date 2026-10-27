# Changelog

## 0.6.0
- New MCP tool **`create_inventory_item`** creates a product: name, quantity, category, subcategory, manufacturer, model, unit, location, description, applications, tags, specifications, purchase sources, datasheet and product links, notes and an optional SKU. It returns the created item with its id and SKU. It is available on the direct endpoint and through Home Assistant (after **Update integration** in Settings and a restart of Home Assistant; reconnect the connector in Claude or ChatGPT to see the new tool).
- It uses the same switch as quantity changes, so it only works when "Allow inventory changes through MCP" is on in Settings (the label now covers both).
- Input is validated: a name is required, quantity must be a whole number from 0, text fields have length limits, and links must start with http:// or https://. A SKU is generated when none is given and gets a numeric suffix if it already exists.
- Duplicates are refused with the id of the existing item: same SKU, or same name ignoring case. A category that matches an existing one ignoring case uses the existing spelling.
- Initial stock is recorded as a stock movement ("Created via MCP: initial stock"), like other quantity changes.
- New REST endpoint `POST /inventory-api/items` for the integration, behind the same switch.
- No changes to the database schema or `settings.json`: existing inventory, stock movements and the API token are kept when updating.

## 0.5.1
- The Home Assistant integration now ships its own icon and logo in `brand/` (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`), so it no longer shows a placeholder under Devices & services. Needs Home Assistant 2026.3 or later; older versions keep the placeholder.
- The images are sized as Home Assistant requires (icon 256 and 512 px square, logo 256 and 512 px high) and compressed to about 370 KB in total.
- After updating the app, Check setup reports the installed integration as outdated. Press **Update integration** in Settings and restart Home Assistant to get the icon.
- No changes to the database or `settings.json`.

## 0.5.0
- **Install integration** button in Settings copies the Home Assistant companion integration into `custom_components/component_inventory`. After a restart of Home Assistant it can be added under Devices & services. The integration is bundled in the app image.
- **New permission:** the app now has read/write access to Home Assistant's config folder (`homeassistant_config`). The installer writes only inside `custom_components/component_inventory`, refuses symbolic links, requires a folder that looks like Home Assistant's config, and keeps one backup of a replaced copy in `/data/companion_backup`. It never edits `configuration.yaml` or any other file.
- Because of the new permission, `0.5.0` is listed as a breaking version: automatic updates never install it, you update manually.
- **Check setup** gets a row for the installed integration files (installed, up to date, outdated or missing).
- No changes to the database or `settings.json`: existing inventory, stock movements and the API token are kept when updating.

## 0.4.3
- **Check setup** now shows whether the Home Assistant companion integration has contacted the app, how long ago, and whether it was rejected for a wrong token. The app records this in a new small file, `/data/companion.json`.
- The record starts empty after updating. Reload the integration in Home Assistant to record a first contact.
- No changes to the database or `settings.json`: existing inventory, stock movements and the API token are kept when updating.

## 0.4.2
- Add a **Check setup** button to Settings that verifies the Home Assistant MCP Server integration, OAuth support for Claude and ChatGPT, the public https address and Nabu Casa access. It sends no login, so it does not trigger failed-login warnings in Home Assistant.
- Add a troubleshooting section to Settings and DOCS.md, including the common "Couldn't connect" cause when the MCP Server integration is missing.
- Docs: stop promising that clients run read-only tools without asking; each client decides.
- No database or settings changes.

## 0.4.1
- Companion integration: retry setup with `ConfigEntryNotReady` when the app is not reachable yet, for example when Home Assistant starts before the app.
- Companion integration: support Home Assistant 2026.9+ (Probatio schemas) and 2026.10+ (`llm.ToolResult`, tool title, integration and annotations) while keeping older versions working.
- Mark the search/get/list tools as read-only and the quantity adjustment as a non-destructive write, both in the Home Assistant LLM API and on the direct MCP endpoint.
- Document Nabu Casa remote setup for Claude and ChatGPT and clarify that port 8098 is for local LAN clients only.
- Add a step-by-step connection guide for ChatGPT, Claude, Claude Code and Codex to Settings, with an editable public address and a warning when the address is local.
- Add downloadable Claude Code `.mcp.json` and Codex `config.toml` snippets. They never contain the API token; LAN variants only reference `COMPONENT_INVENTORY_TOKEN`.
- Copy buttons no longer fail silently when the browser blocks clipboard access.
- No database or settings changes: existing inventory, stock movements and the API token are kept when updating.

## 0.4.0
- Add authenticated `/inventory-api/*` endpoints for the Home Assistant companion integration.
- Add recommended Home Assistant/Nabu Casa MCP endpoint to Settings.
- Keep direct LAN MCP on port 8098 as a fallback.
- Clarify that external MCP authentication is handled by Home Assistant when using `/api/mcp/component_inventory`.
- Add companion integration package that registers Component Inventory as a Home Assistant LLM API.

## 0.3.0
- Product/ERP-oriented inventory model.
- CSV/JSON import and export.
- Product specifications, applications and purchase sources.
