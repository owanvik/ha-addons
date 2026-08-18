from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm

from .client import InventoryClient
from .const import CONF_ADDON_URL, CONF_API_TOKEN, DOMAIN
from .llm_api import ComponentInventoryAPI


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = InventoryClient(hass, entry.data[CONF_ADDON_URL], entry.data[CONF_API_TOKEN])
    await client.health()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    unregister = llm.async_register_api(hass, ComponentInventoryAPI(hass, client))
    entry.async_on_unload(unregister)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
