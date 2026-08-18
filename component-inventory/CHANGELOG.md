# Changelog

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
