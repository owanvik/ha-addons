# Vinyl Streamer Add-on

Stream audio from USB input (like a vinyl player) to network via Icecast.

## Features

- **Bundled Icecast + Darkice** - No separate setup needed
- **Auto-restart** - Darkice reconnects automatically if audio device disconnects
- **Configurable** - Set station name, mount point, audio device, bitrate
- **Music Assistant compatible** - Add stream as radio station

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `station_name` | Name shown in stream metadata | Vinyl Radio |
| `station_description` | Description for the stream | Streaming from vinyl player |
| `mount_point` | URL path for the stream | /vinyl |
| `audio_device` | ALSA device name | hw:CARD=CODEC |
| `audio_samplerate` | Sample rate in Hz | 44100 |
| `audio_channels` | 1 (mono) or 2 (stereo) | 2 |
| `audio_bitrate` | MP3 bitrate in kbps | 320 |
| `icecast_password` | Password for Icecast source | hackme |

## Finding Your Audio Device

SSH into your Home Assistant and run:

```bash
arecord -l
```

Look for your USB audio interface. Example output:
```
card 1: CODEC [USB Audio CODEC], device 0: USB Audio [USB Audio]
```

The device name would be: `hw:CARD=CODEC` or `hw:1,0`

## Stream URL

After starting the add-on, your stream is available at:

```
http://YOUR_HA_IP:8000/vinyl
```

## Adding to Music Assistant

1. Go to Music Assistant → Settings → Providers
2. Add "Radio Browser" or "TuneIn" provider (if not already added)
3. Go to Radio → Add Radio Station
4. Enter your stream URL: `http://YOUR_HA_IP:8000/vinyl`
5. Give it a name like "Vinyl"

## Troubleshooting

### No audio / Darkice keeps restarting

1. Check if audio device is correct
2. Look at add-on logs for errors
3. Make sure USB device is connected before starting add-on

### Stream stutters

- Try increasing `bufferSecs` (edit run.sh)
- Lower the bitrate to 192 or 256
- Check CPU usage on HA host
