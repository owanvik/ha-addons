# Vinyl Streamer Add-on

Stream audio from USB input (vinyl player, turntable, cassette deck, etc.) to your network via Icecast. Perfect for whole-home vinyl listening with Music Assistant!

## Features

- **Bundled Icecast + FFmpeg** - No separate setup needed
- **HA Audio Selector** - Pick audio input from dropdown
- **Auto-restart** - FFmpeg reconnects automatically if audio disconnects
- **Real IP Display** - Stream URL shown in log with actual IP address
- **High Quality** - 320kbps stereo MP3 by default

## Quick Start

1. **Install** the add-on
2. **Select audio input** in the "Lyd" (Audio) section at the bottom
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

## Audio Input Selection

Use the **"Lyd" (Audio)** section at the bottom of the add-on page:

1. Click the **Inngang** (Input) dropdown
2. Select your USB audio device (e.g., "USB Audio CODEC Analog Stereo")
3. Click **Lagre** (Save)
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
- Make sure correct input is selected in "Lyd" section

### FFmpeg keeps restarting

- Audio device may have disconnected
- Check add-on logs for specific error
- Try lowering bitrate to 256 or 192

### Stream stutters or lags

- Lower the bitrate to 192 or 256
- Check network/WiFi quality
- Ensure HA host isn't overloaded
