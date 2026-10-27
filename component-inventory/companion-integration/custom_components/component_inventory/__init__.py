from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import llm

from .client import InventoryClient
from .const import CONF_ADDON_URL, CONF_API_TOKEN, DOMAIN
from .llm_api import ComponentInventoryAPI


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = InventoryClient(hass, entry.data[CONF_ADDON_URL], entry.data[CONF_API_TOKEN])
    try:
        await client.health()
    except (aiohttp.ClientError, TimeoutError, RuntimeError, ValueError) as err:
        # The app may still be starting when Home Assistant boots; let Home Assistant retry
        raise ConfigEntryNotReady(f"Component Inventory app is not reachable at {client.base_url}: {err}") from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    unregister = llm.async_register_api(hass, ComponentInventoryAPI(hass, client))
    entry.async_on_unload(unregister)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
