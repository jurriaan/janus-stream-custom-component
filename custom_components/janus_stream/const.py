"""Constants for the Janus WebRTC Streaming integration."""

import pathlib

DOMAIN = "janus_stream"

PLATFORMS = ["camera"]

WS_TYPE_JANUS_STREAM_CONFIGURATION = "janus/stream_configuration"

COMPONENT_DIR = pathlib.Path(__file__).parent.absolute()

LOVELACE_RESOURCE_TYPE_MODULE = "module"

CONF_RESOURCES = "resources"

CONF_STREAM_CONFIG = "stream_config"
