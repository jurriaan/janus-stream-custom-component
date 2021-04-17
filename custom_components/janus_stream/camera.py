from homeassistant.components.camera import SUPPORT_ON_OFF, Camera
import asyncio
import aiohttp
from uuid import uuid4
import logging
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from homeassistant.exceptions import PlatformNotReady

LOGGER = logging.getLogger(__name__)
from .const import DOMAIN


class JanusCamera(Camera):
    def __init__(self, stream, config):
        """Initialize demo camera component."""
        super().__init__()
        self._name = stream["description"]
        self._stream_id = stream["id"]
        self._unique_id = f"janus-{config['name']}-{self.stream_id}"
        self.server = config["server"]
        self.is_streaming = stream["enabled"]

    async def async_camera_image(self):
        """Return a faked still image response."""
        return None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        LOGGER.info(f"{self.entity_id} initialized")

    @property
    def stream_id(self):
        return self._stream_id

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique camera id."""
        return self._unique_id

    @property
    def is_on(self):
        """Whether camera is on (streaming)."""
        return self.is_streaming

    @property
    def extra_state_attributes(self):
        return {"server": self.server, "stream_id": self.stream_id}


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    LOGGER.info("Setting up Janus camera")

    streams = await fetch_streams(hass, config)
    cameras = [JanusCamera(stream, config) for stream in streams]
    for camera in cameras:
        hass.data[DOMAIN]["stream_config"][camera.unique_id] = {
            "stream_id": camera.stream_id,
            "apisecret": config.get("apisecret"),
            "ice_servers": config.get("ice_servers"),
            "server": camera.server,
        }

    async_add_devices(cameras, True)


def create_request_body(request, config):
    request["transaction"] = str(uuid4())

    if config["apisecret"]:
        request["apisecret"] = config["apisecret"]

    return request


async def send_request(session, url, request):
    async with session.post(url, json=request) as response:
        return await response.json()


async def create_session(session, config):
    create_request = create_request_body(
        {
            "janus": "create",
        },
        config,
    )

    url = config["server"]
    response = await send_request(session, url, create_request)

    return f"{url}/{response['data']['id']}"


async def attach_streaming_plugin(session, config, url):
    request = create_request_body(
        {"janus": "attach", "plugin": "janus.plugin.streaming"}, config
    )

    response = await send_request(session, url, request)

    return f"{url}/{response['data']['id']}"


async def list_streams(session, config, url):
    request = create_request_body(
        {"janus": "message", "body": {"request": "list"}}, config
    )

    response = await send_request(session, url, request)
    return response["plugindata"]["data"]["list"]


async def detach_plugin(session, config, url):
    request = create_request_body(
        {
            "janus": "detach",
        },
        config,
    )

    response = await send_request(session, url, request)
    return True


async def destroy_session(session, config, url):
    request = create_request_body(
        {
            "janus": "destroy",
        },
        config,
    )

    response = await send_request(session, url, request)
    return True


async def fetch_streams(hass, config):
    async with aiohttp.ClientSession() as session:
        session_url = await create_session(session, config)
        plugin_url = await attach_streaming_plugin(session, config, session_url)
        streams = await list_streams(session, config, plugin_url)
        await detach_plugin(session, config, plugin_url)
        await destroy_session(session, config, session_url)
        return streams
