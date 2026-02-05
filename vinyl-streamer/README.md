# Vinyl Streamer

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fowanvik%2Fha-addons)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Stream audio from USB input (vinyl player, turntable, cassette deck) to your network via Icecast. Perfect for whole-home vinyl listening with Music Assistant!

## Features

- **Bundled Icecast + FFmpeg** - No separate setup needed
- **HA Audio Selector** - Pick audio input from dropdown
- **High Quality** - 320kbps stereo MP3 by default
- **Auto-restart** - FFmpeg reconnects automatically if audio disconnects
- **Real IP Display** - Stream URL shown in log with actual IP address

## Requirements

- USB audio interface (sound card) connected to Home Assistant
- Vinyl player, turntable, or other audio source

### Supported USB Audio Devices

| Device | Notes |
|--------|-------|
| Behringer U-Phono UFO202 | Built-in phono preamp |
| Behringer UCA202/UCA222 | Line-level input |
| Burr-Brown USB Audio CODEC | Generic TI chipset |
| Creative Sound Blaster Play! | Compact |

## Installation

1. Click the button above, or add repository: `https://github.com/owanvik/ha-addons`
2. Install **Vinyl Streamer**
3. Select your audio input in the "Audio" section
4. Start the app
5. Copy the stream URL from the log

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `station_name` | Name shown in stream metadata | Vinyl Radio |
| `station_description` | Description for the stream | Streaming from vinyl player |
| `mount_point` | URL path for the stream | /vinyl |
| `audio_samplerate` | Sample rate in Hz | 44100 |
| `audio_channels` | 1 (mono) or 2 (stereo) | 2 |
| `audio_bitrate` | MP3 bitrate in kbps | 320 |
| `icecast_password` | Password for Icecast source | hackme |

## Usage

1. Connect your turntable/audio source to USB audio interface
2. Start the app
3. Find the stream URL in the log (e.g., `http://192.168.1.50:8000/vinyl`)
4. Add to Music Assistant, VLC, or any media player

## Music Assistant Integration

1. Open **Music Assistant**
2. Go to **Media → Radio**
3. Click **+** (Add Radio Station)
4. Enter the stream URL
5. Name it "Vinyl" and save

Now you can play vinyl on any speaker via Music Assistant!

## On-Demand Streaming

Save resources by starting/stopping the app on demand. See [DOCS.md](DOCS.md) for automation examples.

## Support

- [Documentation](DOCS.md)
- [Changelog](CHANGELOG.md)
- [Issues](https://github.com/owanvik/ha-addons/issues)
