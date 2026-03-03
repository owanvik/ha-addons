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

| Option | Description | Default |
|--------|-------------|---------|
| `tv_ip` | Your TV's IP address | *Required* |
| `tv_port` | MQTT port on TV | `36669` |
| `mqtt_host` | MQTT broker address | `core-mosquitto` |
| `mqtt_port` | MQTT broker port | `1883` |
| `mqtt_username` | MQTT username | *Optional* |
| `mqtt_password` | MQTT password | *Optional* |
| `mqtt_timeout` | Connection timeout (seconds) | `30` |
| `device_id` | Unique device identifier | `hisense_tv` |
| `device_name` | Name shown in Home Assistant | `Hisense TV` |
| `volume_max` | Maximum volume level | `30` |
| `volume_step` | Volume step size | `1` |

## Home Assistant Entities

After starting, these entities appear automatically via MQTT Discovery:

| Entity | Type | Description |
|--------|------|-------------|
| `select.hisense_tv_source` | Select | Input source |
| `number.hisense_tv_volume` | Number | Volume slider |
| `button.hisense_tv_power` | Button | Power on/off |
| `button.hisense_tv_mute` | Button | Toggle mute |
| `button.hisense_tv_volume_up/down` | Button | Volume up/down |
| `button.hisense_tv_*` | Buttons | Navigation and media controls |

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
