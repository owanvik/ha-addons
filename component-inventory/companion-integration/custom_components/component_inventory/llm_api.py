from __future__ import annotations

from typing import Any, override

try:
    import probatio as vol  # Home Assistant 2026.9+ validates schemas with Probatio
except ImportError:
    import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .client import InventoryClient
from .const import DOMAIN, LLM_API_ID


class InventoryTool(llm.Tool):
    def __init__(
        self,
        name: str,
        description: str,
        parameters: vol.Schema,
        client: InventoryClient,
        handler: str,
        *,
        title: str,
        read_only: bool,
    ) -> None:
        self.name = name
        self.title = title
        self.description = description
        self.parameters = parameters
        self.integration = DOMAIN
        self.client = client
        self.handler = handler
        if hasattr(llm, "ToolAnnotations"):  # Home Assistant 2026.10+
            # The default annotations describe the least safe case (writes, destructive, open world)
            self.annotations = llm.ToolAnnotations(
                read_only=read_only, destructive=False, idempotent=read_only, open_world=False
            )

    @override
    async def async_call(self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext) -> Any:
        data = await self._call(tool_input.tool_args)
        if hasattr(llm, "ToolResult"):  # Home Assistant 2026.10+
            return llm.ToolResult(data=data)
        return data

    async def _call(self, args: dict[str, Any]) -> JsonObjectType:
        if self.handler == "search":
            return await self.client.search(
                args["query"], args.get("category"), args.get("in_stock_only", True), args.get("limit", 20)
            )
        if self.handler == "list":
            return await self.client.list_items(args.get("category"), args.get("in_stock_only", True), args.get("limit", 500))
        if self.handler == "categories":
            return await self.client.categories()
        if self.handler == "get":
            return await self.client.get_item(args["item_id"])
        if self.handler == "sku":
            return await self.client.get_by_sku(args["sku"])
        if self.handler == "adjust":
            return await self.client.adjust(args["item_id"], args["delta"], args.get("reason", "Home Assistant MCP"))
        if self.handler == "create":
            return await self.client.create_item({k: v for k, v in args.items() if v is not None})
        return {"error": "Unknown tool handler"}


class ComponentInventoryAPI(llm.API):
    def __init__(self, hass: HomeAssistant, client: InventoryClient) -> None:
        super().__init__(hass=hass, id=LLM_API_ID, name="Component Inventory")
        self.client = client

    @override
    async def async_get_api_instance(self, llm_context: llm.LLMContext) -> llm.APIInstance:
        tools: list[llm.Tool] = [
            InventoryTool(
                "search_inventory",
                "Search the electronics inventory by product name, SKU, model, specification, tag, application or intended use. Use this before recommending parts for a project.",
                vol.Schema({
                    vol.Required("query"): str,
                    vol.Optional("category"): str,
                    vol.Optional("in_stock_only", default=True): bool,
                    vol.Optional("limit", default=20): vol.All(int, vol.Range(min=1, max=100)),
                }),
                self.client,
                "search",
                title="Search inventory",
                read_only=True,
            ),
            InventoryTool(
                "get_inventory_item",
                "Get complete product details, specifications, applications, purchase links and stock for an inventory item ID.",
                vol.Schema({vol.Required("item_id"): int}),
                self.client,
                "get",
                title="Get inventory item",
                read_only=True,
            ),
            InventoryTool(
                "get_inventory_item_by_sku",
                "Get complete product details by the stable inventory SKU.",
                vol.Schema({vol.Required("sku"): str}),
                self.client,
                "sku",
                title="Get inventory item by SKU",
                read_only=True,
            ),
            InventoryTool(
                "list_inventory",
                "List inventory products, optionally filtered by category and stock status.",
                vol.Schema({
                    vol.Optional("category"): str,
                    vol.Optional("in_stock_only", default=True): bool,
                    vol.Optional("limit", default=500): vol.All(int, vol.Range(min=1, max=1000)),
                }),
                self.client,
                "list",
                title="List inventory",
                read_only=True,
            ),
            InventoryTool(
                "list_inventory_categories",
                "List the product categories available in the electronics inventory.",
                vol.Schema({}),
                self.client,
                "categories",
                title="List inventory categories",
                read_only=True,
            ),
            InventoryTool(
                "adjust_inventory_quantity",
                "Adjust the physical stock quantity for a product. This only works when inventory writes are enabled in the Component Inventory app.",
                vol.Schema({
                    vol.Required("item_id"): int,
                    vol.Required("delta"): int,
                    vol.Optional("reason", default="Home Assistant MCP"): str,
                }),
                self.client,
                "adjust",
                title="Adjust inventory quantity",
                read_only=False,
            ),
            InventoryTool(
                "create_inventory_item",
                "Create a new product in the electronics inventory. Search first to avoid duplicates, and use an existing category from list_inventory_categories when one fits so the spelling stays consistent. Give specification values as text, for example \"5 V\". Returns the created item with its id and SKU. This only works when inventory changes are enabled in the Component Inventory app.",
                vol.Schema({
                    vol.Required("name"): str,
                    vol.Optional("quantity", default=0): vol.All(int, vol.Range(min=0, max=1000000)),
                    vol.Optional("category"): str,
                    vol.Optional("subcategory"): str,
                    vol.Optional("manufacturer"): str,
                    vol.Optional("model"): str,
                    vol.Optional("unit"): str,
                    vol.Optional("location"): str,
                    vol.Optional("description"): str,
                    vol.Optional("applications"): [str],
                    vol.Optional("tags"): [str],
                    vol.Optional("specifications"): {str: str},
                    vol.Optional("purchase_sources"): [{
                        vol.Optional("vendor"): str,
                        vol.Optional("url"): str,
                        vol.Optional("part_number"): str,
                    }],
                    vol.Optional("datasheet_url"): str,
                    vol.Optional("product_url"): str,
                    vol.Optional("notes"): str,
                    vol.Optional("sku"): str,
                }),
                self.client,
                "create",
                title="Create inventory item",
                read_only=False,
            ),
        ]
        return llm.APIInstance(
            api=self,
            api_prompt=(
                "This API represents the user's physical electronics component inventory. "
                "Search the inventory before suggesting purchases or selecting parts for hardware projects. "
                "Prefer parts that are in stock and use product specifications and applications when evaluating suitability."
            ),
            llm_context=llm_context,
            tools=tools,
        )
