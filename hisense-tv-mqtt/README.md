# Hisense TV MQTT Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Control your Hisense VIDAA Smart TV from Home Assistant via MQTT.

## Features

- **Power Control** - Turn TV on/off
- **Volume Control** - Slider, up/down, mute
- **Source Selection** - HDMI, TV, AV inputs
- **Navigation** - Up, Down, Left, Right, OK, Back, Home, Menu
- **Media Controls** - Play, Pause, Stop
- **Real-time Sync** - Remote changes reflected in HA
- **Auto-reconnect** - Reconnects when TV powers on

## Requirements

- Hisense Smart TV with VIDAA OS
- Home Assistant with MQTT broker (e.g., Mosquitto)

## Installation

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fowanvik%2Fha-addons)

1. Click the button above, or add repository: `https://github.com/owanvik/ha-addons`
2. Install **Hisense TV MQTT Bridge**
3. Configure TV IP and MQTT credentials
4. Start the app

## Configuration

| Option | Description |
|--------|-------------|
| `tv_ip` | Your TV's IP address |
| `tv_mac` | TV MAC address (for Wake-on-LAN) |
| `mqtt_host` | MQTT broker address (e.g., `core-mosquitto`) |
| `mqtt_port` | MQTT port (default: 1883) |
| `mqtt_username` | MQTT username |
| `mqtt_password` | MQTT password |
| `device_name` | Name shown in Home Assistant |

## Home Assistant Entities

After starting, these entities appear automatically via MQTT Discovery:

| Entity | Type | Description |
|--------|------|-------------|
| `media_player.hisense_tv` | Media Player | Main TV control |
| `select.hisense_tv_source` | Select | Input source |
| `number.hisense_tv_volume` | Number | Volume slider |
| `button.hisense_tv_*` | Buttons | Navigation and media |

## Troubleshooting

### TV not connecting
- Ensure TV is on the same network
- Verify TV IP is correct
- Check that TV supports VIDAA/RemoteNOW

### Entities not appearing
- Verify MQTT broker is running
- Check app logs for errors
- Ensure MQTT Discovery is enabled in HA

## License

MIT License
