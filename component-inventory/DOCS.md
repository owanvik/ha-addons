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

### Install the Home Assistant integration

Claude and ChatGPT reach the inventory through a small custom Home Assistant integration (the companion integration). The app can install it for you:

1. In the app, open **Settings** and press **Install integration** under *Step 1*. This copies the integration into `custom_components/component_inventory` in Home Assistant's config folder.
2. Restart Home Assistant.
3. Open *Settings > Devices & services > Add integration*, search for **Component Inventory** and add it. Enter the address and token shown in the app (use `http://<HA-IP>:8098` if the suggested address cannot connect).

For this the app has read/write access to Home Assistant's config folder (`homeassistant_config`). The installer only writes inside `custom_components/component_inventory`, refuses to follow symbolic links, and keeps one backup of a replaced copy in `/data/companion_backup`. It never edits `configuration.yaml`, secrets or any other file. If you prefer, copy `companion-integration/custom_components/component_inventory` there yourself (for example over Samba).

After an app update, **Check setup** tells you if the installed integration differs from the bundled one. Press **Update integration** and restart Home Assistant.

### Remote access through Home Assistant / Nabu Casa (Claude, ChatGPT)

Claude and ChatGPT connect from the cloud and sign in with OAuth. They cannot use port `8098`, and Nabu Casa does not forward it. Instead, install the companion integration (see `companion-integration/COMPANION_INTEGRATION.md`) and use Home Assistant's own MCP endpoint:

`https://YOUR-ID.ui.nabu.casa/api/mcp/component_inventory`

The same guide, with copy buttons and downloadable config files, is in the app under **Settings > Connect Claude, ChatGPT and other clients**.

**ChatGPT** has no file to import, so it is added by URL in the app:

1. Open the plugins page (Settings > Plugins in the desktop app) and choose **Add > Add custom MCP server**. The menu name can differ between ChatGPT versions.
2. Name it `Component Inventory`, paste the URL under **Connection** and set **Authentication** to **OAuth**. If asked for an OAuth client ID, use `https://chatgpt.com`. Home Assistant does not use a client secret.
3. Confirm with **I understand and want to continue**, choose **Create as plugin**, then **Continue to Home Assistant** and log in.

Custom MCP servers need a ChatGPT plan with developer mode or custom MCP support. Check your plan if the option is missing.

**Claude** (claude.ai and Claude Desktop) has no file to import for custom connectors either:

1. Open **Customize > Connectors** (Claude Desktop: Settings > Connectors) and choose **Add custom connector**. On Team and Enterprise plans an Owner adds it under **Organization settings > Connectors** and members then click **Connect**.
2. Name it `Component Inventory` and paste the URL.
3. Set **Authentication** to **Sign in now** and **OAuth client** to **Use Claude's published identity**, then click **Add**.
4. Click **Connect**, log in to Home Assistant, and turn the connector on in a chat from the **+** menu > **Connectors**.

**Claude Code and Codex** can use the same URL with an OAuth login:

```bash
claude mcp add --transport http component-inventory https://YOUR-ID.ui.nabu.casa/api/mcp/component_inventory
claude mcp login component-inventory
codex mcp add component_inventory --url https://YOUR-ID.ui.nabu.casa/api/mcp/component_inventory
```

Settings can also download ready-made config files: `component-inventory.mcp.json` for Claude Code (save it as `.mcp.json` in your project folder) and `component-inventory-codex.toml` for Codex (append it to `~/.codex/config.toml`). The files never contain the API token. For direct LAN access they only refer to the environment variable `COMPONENT_INVENTORY_TOKEN`, which you set yourself; Settings has a button that copies the export command.

Sign in with a Home Assistant administrator account. Home Assistant's **External URL** (Settings > System > Network) must be the Nabu Casa address, otherwise OAuth fails.

Tools exposed this way: `search_inventory`, `get_inventory_item`, `get_inventory_item_by_sku`, `list_inventory`, `list_inventory_categories`, `adjust_inventory_quantity` and `create_inventory_item` (the last two only when writes are enabled in Settings).

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
- `create_inventory_item` (only when enabled in Settings)

All tools except the quantity adjustment are marked read-only. Clients can use that to tell search tools from the stock change, but each client decides for itself when to ask for confirmation.

### Check your setup and troubleshooting

In the app, open **Settings > Connect Claude, ChatGPT and other clients** and press **Check setup**. From the Home Assistant address the page is opened on, it checks that:

- the **Model Context Protocol Server** integration exists (the address `/api/mcp/component_inventory` is served),
- Home Assistant supports the sign-in method Claude and ChatGPT use (Client ID Metadata Documents),
- the address you will paste is a public https address, and
- you opened the page through Nabu Casa, and
- the Component Inventory integration has contacted the app. The app records when the integration last reached it (including when it was rejected for a wrong token), so the check can show how long ago that was.

The check sends no login and changes nothing in Home Assistant. The contact record is a small file, `/data/companion.json`, that is separate from your inventory and settings. After updating the app, the record starts empty. Reload the integration (*Settings > Devices & services > Component Inventory > menu > Reload*) to record a first contact.

You can also open the MCP address in a normal browser tab. **401 Unauthorized** means the address exists and wants a login. **404** means the MCP Server integration is missing.

Common problems:

- **"Couldn't connect" after you log in to Home Assistant:** the **Model Context Protocol Server** integration is usually missing. Add it under *Settings > Devices & services > Add integration*. Do not pick "Model Context Protocol" without "Server", which is the opposite direction.
- **Connected, but no inventory tools, or an "Unknown LLM API" error:** the Component Inventory integration is not set up. Press **Install integration** in Settings, restart Home Assistant and add it under Devices & services.
- **Component Inventory shows "Retrying setup":** the app address or token you entered is wrong, or the app is not running. Home Assistant retries by itself once the app answers.
- **403 or "forbidden":** sign in with a Home Assistant administrator account. Custom LLM APIs are admin-only.
- **Home Assistant asks you to give `https://chatgpt.com/oauth/.../client.json` access:** this is expected. ChatGPT identifies itself with that address, and Claude shows a similar one.
- **Sign-in loops or fails with an address or issuer error:** Home Assistant's External URL (*Settings > System > Network*) must be the same `.ui.nabu.casa` address the client uses. After repeated failed logins your IP can be banned, so check `ip_bans.yaml` in the Home Assistant config folder.
- **Quantity changes or new products are refused:** writes are off by default. Turn on "Allow inventory changes through MCP" in Settings if agents should adjust stock or create products.

### What agents can ask

MCP search includes product name, SKU, model, applications, specifications, tags and purchase-source metadata. This allows coding agents to ask questions such as "find a 433 MHz transmitter", "what can I use to measure distance?" or "where can I buy the same HC-SR04 again?".

## Persistence and backup

The SQLite database and settings are stored under `/data` and are included in Home Assistant app backups.

Updating the app keeps `/data`: existing products, stock movements and the API token are preserved, and startup only creates missing tables and columns, it never drops or rewrites inventory data. Uninstalling the app can remove its data, so take a backup or a JSON export first.
