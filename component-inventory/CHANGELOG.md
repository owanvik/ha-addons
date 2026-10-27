# Changelog

## 0.4.1
- Companion integration: retry setup with `ConfigEntryNotReady` when the app is not reachable yet, for example when Home Assistant starts before the app.
- Companion integration: support Home Assistant 2026.9+ (Probatio schemas) and 2026.10+ (`llm.ToolResult`, tool title, integration and annotations) while keeping older versions working.
- Mark the search/get/list tools as read-only and the quantity adjustment as a non-destructive write, both in the Home Assistant LLM API and on the direct MCP endpoint.
- Document Nabu Casa remote setup for Claude and ChatGPT and clarify that port 8098 is for local LAN clients only.
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
