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

Open **Settings** inside Component Inventory to see the MCP endpoint and bearer token, regenerate the token, and enable/disable inventory writes.

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

MCP search includes product name, SKU, model, applications, specifications, tags and purchase-source metadata. This allows coding agents to ask questions such as "find a 433 MHz transmitter", "what can I use to measure distance?" or "where can I buy the same HC-SR04 again?".

## Persistence and backup

The SQLite database and settings are stored under `/data` and are included in Home Assistant app backups.
