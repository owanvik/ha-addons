# Home Assistant Add-ons

Custom add-ons for Home Assistant.

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fowanvik%2Fha-addons)

## Installation

Click the button above, or manually:

1. Go to **Settings → Add-ons → Add-on Store**
2. Click the menu (⋮) → **Repositories**
3. Add: `https://github.com/owanvik/ha-addons`
4. Refresh and install the add-on you want

## Available Add-ons

### 🎵 [Vinyl Streamer](vinyl-streamer/)

Stream audio from USB input (vinyl player, turntable, etc.) to your network via Icecast. Perfect for streaming vinyl to any room via Music Assistant, AirPlay, or any media player.

**Features:**
- Bundled Icecast + FFmpeg (no external setup)
- Uses HA's built-in audio selector
- Auto-restart on failure
- Shows stream URL with actual IP in log
- 320kbps MP3 streaming

**Quick Start:**
1. Install add-on
2. Select audio input in "Lyd" section (e.g., USB Audio CODEC)
3. Start add-on
4. Stream URL shown in log: `http://[HA_IP]:8000/vinyl`

**Music Assistant Integration:**
1. Go to **Music Assistant → Media → Radio**
2. Click **Add Radio Station** (+)
3. Enter stream URL from add-on log
4. Name it "Vinyl" and save
5. Play on any speaker/room!

---

### 📺 [Hisense TV MQTT Bridge](hisense-tv-mqtt/)

Control Hisense VIDAA Smart TVs via MQTT and Home Assistant.

**Features:**
- Power on/off, volume, mute
- Source/input selection
- Channel control
- Media player entity in HA
- Auto-discovery via MQTT

**Requirements:**
- Hisense TV with VIDAA OS
- MQTT broker (e.g., Mosquitto)
