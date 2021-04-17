"""The Janus WebRTC Streaming integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging
import voluptuous as vol

from homeassistant.components.websocket_api.const import ERR_NOT_FOUND
from homeassistant.components import websocket_api
from homeassistant.helpers.entity_component import DATA_INSTANCES
from homeassistant.components.websocket_api.decorators import (
    async_response,
    require_admin,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_registry import async_get_registry

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    PLATFORMS,
    WS_TYPE_JANUS_STREAM_CONFIGURATION,
    COMPONENT_DIR,
    CONF_STREAM_CONFIG,
)
from . import utils


@async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_TYPE_JANUS_STREAM_CONFIGURATION,
        vol.Required("entity_id"): cv.entity_id,
    }
)
async def websocket_handle_stream_configuration(hass, connection, msg):
    # We know the answer without having to fetch any information,
    # so we send it directly.
    registry = await async_get_registry(hass)
    entry = registry.entities.get(msg["entity_id"])
    if entry is None:
        connection.send_message(
            websocket_api.error_message(
                msg["id"], ERR_NOT_FOUND, "Entity not found in registry"
            )
        )
        return

    config = hass.data.get(DOMAIN, {}).get(CONF_STREAM_CONFIG)
    stream_config = config.get(entry.unique_id)

    if stream_config is None:
        connection.send_message(
            websocket_api.error_message(msg["id"], ERR_NOT_FOUND, "Entity not found")
        )
        return

    connection.send_message(websocket_api.result_message(msg["id"], stream_config))


async def register_static_file(hass, filename, add_resource=False):
    path = COMPONENT_DIR / "www/" / filename
    url_path = f"/janus-stream-resources/{filename}"
    hass.http.register_static_path(url_path, path)

    if add_resource and await utils.add_resource_module(hass, url_path):
        _LOGGER.debug(f"Lovelace card registered: {url_path}")


async def async_setup(hass, config):
    hass.data[DOMAIN] = {CONF_STREAM_CONFIG: {}}

    await register_static_file(hass, "janus-camera.js", add_resource=True)
    await register_static_file(hass, "adapter-and-janus.js")

    hass.components.websocket_api.async_register_command(
        websocket_handle_stream_configuration
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Janus WebRTC Streaming from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
