import logging
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.helpers.typing import HomeAssistantType

from homeassistant.components.lovelace.const import (
    CONF_RESOURCE_TYPE_WS,
    DOMAIN as LOVELACE_DOMAIN,
    CONF_URL,
)

from .const import LOVELACE_RESOURCE_TYPE_MODULE, CONF_RESOURCES

_LOGGER = logging.getLogger(__name__)


async def add_resource_module(hass: HomeAssistantType, url: str) -> bool:
    resources: ResourceStorageCollection = hass.data[LOVELACE_DOMAIN][CONF_RESOURCES]

    await resources.async_get_info()

    for resource in resources.async_items():
        if resource[CONF_URL] == url:
            # Item is already in the list
            return False

    try:
        await resources.async_create_item(
            {CONF_URL: url, CONF_RESOURCE_TYPE_WS: LOVELACE_RESOURCE_TYPE_MODULE}
        )

        return True
    except:
        _LOGGER.warn(f"Cannot add {url} as lovelace resource, please do so manually")

    return False
