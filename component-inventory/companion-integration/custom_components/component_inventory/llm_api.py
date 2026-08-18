from __future__ import annotations

from typing import Any, override

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .client import InventoryClient
from .const import LLM_API_ID


class InventoryTool(llm.Tool):
    def __init__(self, name: str, description: str, parameters: vol.Schema, client: InventoryClient, handler: str) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.client = client
        self.handler = handler

    @override
    async def async_call(self, hass: HomeAssistant, tool_input: llm.ToolInput, llm_context: llm.LLMContext) -> JsonObjectType:
        args = tool_input.tool_args
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
            ),
            InventoryTool(
                "get_inventory_item",
                "Get complete product details, specifications, applications, purchase links and stock for an inventory item ID.",
                vol.Schema({vol.Required("item_id"): int}),
                self.client,
                "get",
            ),
            InventoryTool(
                "get_inventory_item_by_sku",
                "Get complete product details by the stable inventory SKU.",
                vol.Schema({vol.Required("sku"): str}),
                self.client,
                "sku",
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
            ),
            InventoryTool(
                "list_inventory_categories",
                "List the product categories available in the electronics inventory.",
                vol.Schema({}),
                self.client,
                "categories",
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
