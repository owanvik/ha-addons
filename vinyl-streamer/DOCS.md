# Vinyl Streamer App

Stream audio from USB input (vinyl player, turntable, cassette deck, etc.) to your network via Icecast. Perfect for whole-home vinyl listening with Music Assistant!

## Requirements

You need a USB audio interface (sound card) to connect your vinyl player to Home Assistant.

### Supported USB Audio Devices

| Device | Notes |
|--------|-------|
| **Behringer U-Phono UFO202** | Built-in phono preamp, perfect for turntables |
| **Behringer UCA202/UCA222** | Line-level input, needs external preamp |
| **Burr-Brown USB Audio CODEC** | Generic TI chipset, widely compatible |
| **Creative Sound Blaster Play!** | Compact, works well |

Most USB audio devices with standard UAC (USB Audio Class) drivers work. Avoid devices requiring proprietary drivers.

**Tip:** If your turntable has a built-in preamp (phono/line switch), set it to "line" and use any USB interface. Otherwise, use one with built-in phono preamp like the UFO202.

## Features

- **Bundled Icecast + FFmpeg** - No separate setup needed
- **HA Audio Selector** - Pick audio input from dropdown
- **Auto-restart** - FFmpeg reconnects automatically if audio disconnects
- **Real IP Display** - Stream URL shown in log with actual IP address
- **Multiple Audio Formats** - MP3, AAC, or Opus encoding
- **Audio Processing** - Volume, compressor, stereo width controls
- **Recording** - Save streams to MP3 or FLAC files
- **HA Integration** - Status file for creating Home Assistant sensors

## Quick Start

1. **Install** the app
2. **Select audio input** in the "Audio" section at the bottom
3. **Start** the app
4. **Copy stream URL** from the log (e.g., `http://192.168.1.50:8000/vinyl`)
5. **Play** in Music Assistant, VLC, or any media player!

## Configuration

### Basic Settings

| Option | Description | Default |
|--------|-------------|---------|
| `station_name` | Name shown in stream metadata | Vinyl Radio |
| `station_description` | Description for the stream | Streaming from vinyl player |
| `mount_point` | URL path for the stream | /vinyl |
| `icecast_password` | Password for Icecast source | hackme |
| `low_latency` | Reduce stream delay (~2-3s instead of ~5-10s) | false |

### Audio Quality

| Option | Description | Default |
|--------|-------------|---------|
| `format` | Audio codec (mp3, aac, opus) | mp3 |
| `samplerate` | Sample rate in Hz | 44100 |
| `channels` | 1 (mono) or 2 (stereo) | 2 |
| `bitrate` | Bitrate in kbps (128-320) | 320 |

**Format comparison:**
- **MP3** - Most compatible, works everywhere
- **AAC** - Better quality at same bitrate, good for Apple devices
- **Opus** - Best quality, but less compatible with older players

### Audio Processing

| Option | Description | Default |
|--------|-------------|---------|
| `volume_db` | Volume adjustment (-10 to +10 dB) | 0 dB |
| `compressor_enabled` | Enable dynamic range compression | false |
| `compressor_threshold` | When compression starts (-40 to -5 dB) | -20 dB |
| `compressor_ratio` | Compression ratio (2:1 to 20:1) | 4:1 |

**When to use the compressor:**
- Records with inconsistent volume between tracks
- Very dynamic classical or jazz recordings
- Background listening where you want even volume

### Noise Reduction

| Option | Description | Default |
|--------|-------------|---------|
| `highpass_enabled` | Enable highpass filter (removes rumble) | false |
| `highpass_freq` | Highpass cutoff frequency in Hz (20-100) | 30 |
| `lowpass_enabled` | Enable lowpass filter (removes hiss) | false |
| `lowpass_freq` | Lowpass cutoff frequency in Hz (10000-20000) | 16000 |
| `denoise_enabled` | Enable FFT-based noise reduction | false |
| `denoise_strength` | Noise reduction strength (0.1-1.0) | 0.3 |

**Recommended settings for vinyl:**

- **Rumble issues:** Enable highpass at 30 Hz
- **Hiss/high-frequency noise:** Enable lowpass at 16000 Hz
- **General background noise:** Enable denoise at 0.3 strength

**Note:** Noise reduction adds some CPU overhead. Start with filters disabled and enable only if needed.

### Icecast Server

| Option | Description | Default |
|--------|-------------|---------|
| `max_listeners` | Maximum simultaneous listeners (1-100) | 10 |
| `genre` | Genre tag for stream metadata | Vinyl |

### Recording

| Option | Description | Default |
|--------|-------------|---------|
| `format` | Recording format (MP3 or FLAC) | MP3 |
| `path` | Directory to save recordings | /share/vinyl-recordings |

**Starting/stopping recordings:**
- **MQTT buttons:** Use the auto-created HA buttons (requires MQTT enabled)
- **MQTT command:** Publish to `vinyl_streamer/command`:
  - `start_recording` - Start recording
  - `stop_recording` - Stop recording
- **Automation:** See examples below

**Recording notes:**
- Files are named `vinyl_YYYYMMDD_HHMMSS.mp3` (or .flac)
- FLAC is lossless - larger files but perfect for archiving
- Recordings saved to `/share/` accessible from HA file browser
- Recording continues until stopped or app restarts

### Low Latency Mode

Enable `low_latency` to reduce stream delay from ~5-10 seconds down to ~2-3 seconds. This is useful when you want audio more in sync with the vinyl playback.

**Trade-offs:**
- May cause stuttering on slow or unstable networks
- Clients may take longer to buffer initially
- Not recommended for WiFi connections with poor signal

If you experience audio dropouts, disable this option.

## Home Assistant Integration

### MQTT Integration (Recommended)

The easiest way to integrate with Home Assistant. Enable MQTT in settings and sensors/controls are created automatically.

**Requirements:** Mosquitto broker app (or external MQTT broker)

**Auto-created entities:**
- `binary_sensor.vinyl_streamer_streaming` - Stream status
- `binary_sensor.vinyl_streamer_recording` - Recording status
- `sensor.vinyl_streamer_format` - Current audio format
- `sensor.vinyl_streamer_bitrate` - Current bitrate
- `sensor.vinyl_streamer_uptime` - Uptime in seconds
- `sensor.vinyl_streamer_url` - Stream URL
- `button.vinyl_streamer_start_recording` - Start recording
- `button.vinyl_streamer_stop_recording` - Stop recording

**Setup:**
1. Install Mosquitto broker app (if not already installed)
2. Enable "MQTT Discovery" in Vinyl Streamer settings
3. Restart the app
4. Entities appear automatically under "Vinyl Streamer" device

**Manual MQTT broker:** If using an external broker, fill in host/username/password. Leave empty to auto-detect Mosquitto.

### Status File

Location: `/share/vinyl-streamer/status.json`

```json
{
  "streaming": true,
  "recording": false,
  "recording_file": "",
  "uptime_seconds": 3600,
  "format": "MP3",
  "bitrate": 320,
  "samplerate": 44100,
  "channels": 2,
  "station_name": "Vinyl Radio",
  "mount_point": "/vinyl",
  "stream_url": "http://192.168.1.50:8000/vinyl"
}
```

### Creating a Sensor

Add this to your `configuration.yaml`:

```yaml
sensor:
  - platform: rest
    name: Vinyl Streamer Status
    resource: http://localhost:8123/local/vinyl-streamer/status.json
    value_template: "{{ value_json.streaming }}"
    json_attributes:
      - recording
      - format
      - bitrate
      - uptime_seconds
    scan_interval: 30
```

Or use a command line sensor:

```yaml
sensor:
  - platform: command_line
    name: Vinyl Streamer
    command: "cat /share/vinyl-streamer/status.json"
    value_template: "{{ value_json.streaming }}"
    json_attributes:
      - recording
      - format
      - bitrate
      - uptime_seconds
    scan_interval: 30
```

## Audio Input Selection

Use the **"Audio"** section at the bottom of the app page:

1. Click the **Input** dropdown
2. Select your USB audio device (e.g., "USB Audio CODEC Analog Stereo")
3. Click **Save**
4. Restart the app

## Adding to Music Assistant

This is the recommended way to stream vinyl throughout your home:

1. Open **Music Assistant**
2. Go to **Media → Radio**
3. Click the **+** button (Add Radio Station)
4. Enter the stream URL from the app log (e.g., `http://192.168.1.50:8000/vinyl`)
5. Name it "Vinyl" or "Platespiller"
6. Click **Save**

Now you can play vinyl on any room/speaker via Music Assistant!

## On-Demand Streaming (Save Resources)

To save resources, you can start/stop the app on demand instead of running it constantly.

<details>
<summary><strong>Automation Examples</strong> (click to expand)</summary>

### Start streaming when turntable powers on

If you have a smart plug monitoring your turntable:

```yaml
automation:
  - alias: "Start vinyl stream when turntable on"
    trigger:
      - platform: state
        entity_id: switch.turntable_plug
        to: "on"
    action:
      - service: hassio.app_start
        data:
          app: local_vinyl-streamer

  - alias: "Stop vinyl stream when turntable off"
    trigger:
      - platform: state
        entity_id: switch.turntable_plug
        to: "off"
        for:
          minutes: 5
    action:
      - service: hassio.app_stop
        data:
          app: local_vinyl-streamer
```

### Start/stop recording with a button

```yaml
automation:
  - alias: "Toggle vinyl recording"
    trigger:
      - platform: state
        entity_id: sensor.vinyl_button_action
        to: "double"
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: binary_sensor.vinyl_streamer_recording
                state: "on"
            sequence:
              - service: button.press
                target:
                  entity_id: button.vinyl_streamer_stop_recording
        default:
          - service: button.press
            target:
              entity_id: button.vinyl_streamer_start_recording
```

### Start/stop streaming with a physical button

Using a Zigbee/Z-Wave button:

```yaml
automation:
  - alias: "Toggle vinyl stream with button"
    trigger:
      - platform: state
        entity_id: sensor.vinyl_button_action
        to: "single"
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: switch.vinyl_streamer
                state: "on"
            sequence:
              - service: hassio.app_stop
                data:
                  app: local_vinyl-streamer
        default:
          - service: hassio.app_start
            data:
              app: local_vinyl-streamer
```

### Template Switch

Add this to your `configuration.yaml`:

```yaml
switch:
  - platform: template
    switches:
      vinyl_streamer:
        friendly_name: "Vinyl Streamer"
        icon_template: mdi:record-player
        value_template: >
          {{ is_state('binary_sensor.vinyl_streamer_running', 'on') }}
        turn_on:
          service: hassio.app_start
          data:
            app: local_vinyl-streamer
        turn_off:
          service: hassio.app_stop
          data:
            app: local_vinyl-streamer

binary_sensor:
  - platform: template
    sensors:
      vinyl_streamer_running:
        friendly_name: "Vinyl Streamer Running"
        value_template: >
          {{ is_state_attr('update.vinyl_streamer_update', 'installed_version', state_attr('update.vinyl_streamer_update', 'installed_version')) }}
```

**Note:** Replace `local_vinyl-streamer` with your app's slug. Find it in the app URL or run `ha apps` in SSH.

### Toggle Script

Create a script that toggles the app:

```yaml
script:
  toggle_vinyl_stream:
    sequence:
      - choose:
          - conditions:
              - condition: state
                entity_id: binary_sensor.vinyl_streamer_running
                state: 'on'
            sequence:
              - service: hassio.app_stop
                data:
                  app: local_vinyl-streamer
        default:
          - service: hassio.app_start
            data:
              app: local_vinyl-streamer
```

### Dashboard Button

Add a simple start/stop button to your dashboard:

```yaml
type: button
name: Start Vinyl
icon: mdi:record-player
tap_action:
  action: call-service
  service: hassio.app_start
  data:
    app: local_vinyl-streamer
hold_action:
  action: call-service
  service: hassio.app_stop
  data:
    app: local_vinyl-streamer
```

</details>

## Testing the Stream

You can test the stream in any of these ways:

- **Browser:** Open `http://[HA_IP]:8000/vinyl` directly
- **VLC:** Media → Open Network Stream → enter URL
- **Home Assistant:** Create a media_player with the stream URL

## Troubleshooting

### No audio devices found

- Make sure USB audio interface is connected
- Check if HA OS sees it: Run `ha audio info` in SSH terminal
- Try unplugging and reconnecting USB device

### Stream has no sound

- Verify audio is playing from the vinyl player
- Check volume/gain on the USB interface
- Make sure correct input is selected in "Audio" section

### FFmpeg keeps restarting

- Audio device may have disconnected
- Check app logs for specific error
- Try lowering bitrate to 256 or 192

### Stream stutters or lags

- Lower the bitrate to 192 or 256
- Check network/WiFi quality
- Ensure HA host isn't overloaded
- If using low latency mode, try disabling it

### Recording not working

- Check that the recording path exists and is writable
- Ensure there's enough disk space in /share
- Check app logs for errors
