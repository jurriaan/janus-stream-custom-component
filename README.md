# Janus WebRTC streaming

Very basic Home Assistant custom component for viewing Janus-Gateway
WebRTC streams.

## Installation

### Using HACS

Go to `HACS > Integrations > ellipsis > Custom repositories`

Enter the following data:

```yaml
URL: jurriaan/janus-stream-custom-component
Category: Integration
```

### Manual install

Copy the `janus_stream` directory to the `custom_components` directory
in your configuration.

## Configuration

Add the `janus_stream` platform entry to the camera domain like this:

```yaml
camera:
- platform: janus_stream
  name: 'Janus stream server'
  server: 'https://janus-host/janus'
  apisecret: !secret here
```

## Lovelace card

Add a custom card with the following card configuration:

```yaml
type: 'custom:janus-camera'
entity: camera.frontdoor
```
