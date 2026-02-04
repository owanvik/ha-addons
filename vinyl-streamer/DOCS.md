# Vinyl Streamer Add-on

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
- **High Quality** - 320kbps stereo MP3 by default

## Quick Start

1. **Install** the add-on
2. **Select audio input** in the "Audio" section at the bottom
3. **Start** the add-on
4. **Copy stream URL** from the log (e.g., `http://192.168.1.50:8000/vinyl`)
5. **Play** in Music Assistant, VLC, or any media player!

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
| `low_latency` | Reduce stream delay (~2-3s instead of ~5-10s) | false |

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

### Low Latency Mode

Enable `low_latency` to reduce stream delay from ~5-10 seconds down to ~2-3 seconds. This is useful when you want audio more in sync with the vinyl playback.

**Trade-offs:**
- May cause stuttering on slow or unstable networks
- Clients may take longer to buffer initially
- Not recommended for WiFi connections with poor signal

If you experience audio dropouts, disable this option.

## Audio Input Selection

Use the **"Audio"** section at the bottom of the add-on page:

1. Click the **Input** dropdown
2. Select your USB audio device (e.g., "USB Audio CODEC Analog Stereo")
3. Click **Save**
4. Restart the add-on

## Adding to Music Assistant

This is the recommended way to stream vinyl throughout your home:

1. Open **Music Assistant**
2. Go to **Media → Radio**
3. Click the **+** button (Add Radio Station)
4. Enter the stream URL from the add-on log (e.g., `http://192.168.1.50:8000/vinyl`)
5. Name it "Vinyl" or "Platespiller"
6. Click **Save**

Now you can play vinyl on any room/speaker via Music Assistant!

## On-Demand Streaming (Save Resources)

To save resources, you can start/stop the add-on on demand instead of running it constantly.

### Automation Examples

#### Start streaming when turntable powers on

If you have a smart plug monitoring your turntable:

```yaml
automation:
  - alias: "Start vinyl stream when turntable on"
    trigger:
      - platform: state
        entity_id: switch.turntable_plug
        to: "on"
    action:
      - service: hassio.addon_start
        data:
          addon: local_vinyl-streamer

  - alias: "Stop vinyl stream when turntable off"
    trigger:
      - platform: state
        entity_id: switch.turntable_plug
        to: "off"
        for:
          minutes: 5
    action:
      - service: hassio.addon_stop
        data:
          addon: local_vinyl-streamer
```

#### Start/stop with a physical button

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
              - service: hassio.addon_stop
                data:
                  addon: local_vinyl-streamer
        default:
          - service: hassio.addon_start
            data:
              addon: local_vinyl-streamer
```

### Option 1: Template Switch

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
          service: hassio.addon_start
          data:
            addon: local_vinyl-streamer
        turn_off:
          service: hassio.addon_stop
          data:
            addon: local_vinyl-streamer

binary_sensor:
  - platform: template
    sensors:
      vinyl_streamer_running:
        friendly_name: "Vinyl Streamer Running"
        value_template: >
          {{ is_state_attr('update.vinyl_streamer_update', 'installed_version', state_attr('update.vinyl_streamer_update', 'installed_version')) }}
```

**Note:** Replace `local_vinyl-streamer` with your add-on's slug. Find it in the add-on URL or run `ha addons` in SSH.

### Option 2: Automation Button

Create a button that toggles the add-on:

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
              - service: hassio.addon_stop
                data:
                  addon: local_vinyl-streamer
        default:
          - service: hassio.addon_start
            data:
              addon: local_vinyl-streamer
```

### Option 3: Dashboard Button

Add a simple start/stop button to your dashboard:

```yaml
type: button
name: Start Vinyl
icon: mdi:record-player
tap_action:
  action: call-service
  service: hassio.addon_start
  data:
    addon: local_vinyl-streamer
hold_action:
  action: call-service
  service: hassio.addon_stop
  data:
    addon: local_vinyl-streamer
```

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
- Check add-on logs for specific error
- Try lowering bitrate to 256 or 192

### Stream stutters or lags

- Lower the bitrate to 192 or 256
- Check network/WiFi quality
- Ensure HA host isn't overloaded
