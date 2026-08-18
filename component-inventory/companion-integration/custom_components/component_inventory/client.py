from __future__ import annotations

from typing import Any
from urllib.parse import quote

from homeassistant.helpers.aiohttp_client import async_get_clientsession


class InventoryClient:
    def __init__(self, hass, base_url: str, token: str) -> None:
        self.hass = hass
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def _request(self, method: str, path: str, *, params=None, json=None) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        headers = {"Authorization": f"Bearer {self.token}"}
        async with session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            params=params,
            json=json,
            timeout=15,
        ) as response:
            data = await response.json(content_type=None)
            if response.status >= 400:
                raise RuntimeError(data.get("error") or f"Inventory API returned HTTP {response.status}")
            return data

    async def health(self):
        return await self._request("GET", "/inventory-api/health")

    async def search(self, query: str, category: str | None, in_stock_only: bool, limit: int):
        params = {"q": query, "in_stock_only": str(in_stock_only).lower(), "limit": limit}
        if category:
            params["category"] = category
        return await self._request("GET", "/inventory-api/search", params=params)

    async def list_items(self, category: str | None, in_stock_only: bool, limit: int):
        params = {"in_stock_only": str(in_stock_only).lower(), "limit": limit}
        if category:
            params["category"] = category
        return await self._request("GET", "/inventory-api/items", params=params)

    async def categories(self):
        return await self._request("GET", "/inventory-api/categories")

    async def get_item(self, item_id: int):
        return await self._request("GET", f"/inventory-api/items/{item_id}")

    async def get_by_sku(self, sku: str):
        return await self._request("GET", f"/inventory-api/items/sku/{quote(sku, safe='')}")

    async def adjust(self, item_id: int, delta: int, reason: str):
        return await self._request(
            "POST",
            f"/inventory-api/items/{item_id}/adjust",
            json={"delta": delta, "reason": reason},
        )
