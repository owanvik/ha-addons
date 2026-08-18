from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .client import InventoryClient
from .const import CONF_ADDON_URL, CONF_API_TOKEN, DEFAULT_ADDON_URL, DOMAIN


class ComponentInventoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                client = InventoryClient(self.hass, user_input[CONF_ADDON_URL], user_input[CONF_API_TOKEN])
                await client.health()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("component_inventory")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Component Inventory", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_ADDON_URL, default=DEFAULT_ADDON_URL): str,
            vol.Required(CONF_API_TOKEN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
