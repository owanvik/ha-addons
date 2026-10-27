# Component Inventory

A lightweight electronics product catalog and inventory hosted as a Home Assistant app/add-on.

## Product catalog

Open **Component Inventory** from Home Assistant. Products use an ERP-style data model:

- SKU
- product name
- category and subcategory
- manufacturer and model
- stock quantity and unit
- location
- description
- typical applications
- flexible key/value specifications
- tags and notes
- product page and datasheet URLs
- multiple purchase sources

Purchase sources can point to AliExpress, DigiKey, Mouser, Amazon or any other supplier. Each source can include a vendor name, URL and supplier/listing part number.

## Import / Export

Open **Import / Export** in the app UI.

Supported imports:

- CSV
- JSON

Before importing, use **Preview import** to see whether each row will be created, updated, skipped, replaced or added to the existing quantity.

Existing products are matched by SKU first, then exact product name.

Duplicate modes:

- **Update existing product** - overwrite imported product fields and set the imported quantity.
- **Skip existing product** - only create products that do not already exist.
- **Add imported quantity to stock** - keep the existing product and add the imported quantity.
- **Replace existing product** - replace product data and quantity with the imported values.

Export is available as CSV and JSON. JSON is the best full-fidelity backup format. In CSV, the `applications`, `tags`, `specifications` and `purchase_sources` columns contain JSON values.

## Settings and MCP

Open **Settings** inside Component Inventory to see the MCP endpoints and bearer token, regenerate the token, and enable/disable inventory writes. Writes are off by default; keep them off if agents should only search and plan with available parts.

There are two ways to reach the inventory from an MCP client.

### Remote access through Home Assistant / Nabu Casa (Claude, ChatGPT)

Claude and ChatGPT connect from the cloud and sign in with OAuth. They cannot use port `8098`, and Nabu Casa does not forward it. Instead, install the companion integration (see `companion-integration/COMPANION_INTEGRATION.md`) and use Home Assistant's own MCP endpoint:

`https://YOUR-ID.ui.nabu.casa/api/mcp/component_inventory`

- **Claude:** add a custom connector with the URL, choose **Sign in now**, then **Use Claude's published identity**, and log in to Home Assistant.
- **ChatGPT:** add a custom MCP server with the URL, set authentication to **OAuth** (client ID `https://chatgpt.com`), and log in to Home Assistant.

Sign in with a Home Assistant administrator account. Home Assistant's **External URL** (Settings > System > Network) must be the Nabu Casa address, otherwise OAuth fails.

Tools exposed this way: `search_inventory`, `get_inventory_item`, `get_inventory_item_by_sku`, `list_inventory`, `list_inventory_categories` and `adjust_inventory_quantity` (only when writes are enabled in Settings).

### Direct LAN access (Claude Code, Codex, other local clients)

The app exposes Streamable HTTP MCP on TCP port `8098`:

`http://HOME_ASSISTANT_IP:8098/mcp`

Use the token shown in Settings:

`Authorization: Bearer YOUR_TOKEN`

Available tools:

- `search_inventory`
- `get_inventory_item`
- `get_inventory_item_by_sku`
- `list_inventory`
- `list_categories`
- `adjust_quantity` (only when enabled in Settings)

All tools except the quantity adjustment are marked read-only, so clients can run them without asking for confirmation.

### What agents can ask

MCP search includes product name, SKU, model, applications, specifications, tags and purchase-source metadata. This allows coding agents to ask questions such as "find a 433 MHz transmitter", "what can I use to measure distance?" or "where can I buy the same HC-SR04 again?".

## Persistence and backup

The SQLite database and settings are stored under `/data` and are included in Home Assistant app backups.

Updating the app keeps `/data`: existing products, stock movements and the API token are preserved, and startup only creates missing tables and columns, it never drops or rewrites inventory data. Uninstalling the app can remove its data, so take a backup or a JSON export first.
