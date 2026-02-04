#!/usr/bin/with-contenv bashio
# ==============================================================================
# Vinyl Streamer - Run Script
# Starts Icecast server and FFmpeg encoder
# Start/stop streaming by starting/stopping this add-on
# ==============================================================================

set -e

# Read configuration
STATION_NAME=$(bashio::config 'station_name')
STATION_DESC=$(bashio::config 'station_description')
MOUNT_POINT=$(bashio::config 'mount_point')
# Strip "(Default)" suffix from list values
AUDIO_SAMPLERATE=$(bashio::config 'audio_quality.samplerate' | sed 's/ (Default)//')
AUDIO_CHANNELS=$(bashio::config 'audio_quality.channels' | sed 's/ (Default)//')
AUDIO_BITRATE=$(bashio::config 'audio_quality.bitrate' | sed 's/ (Default)//')
ICECAST_PASSWORD=$(bashio::config 'icecast_password')

# Low latency mode
LOW_LATENCY=$(bashio::config 'low_latency')

# Audio processing settings (root level)
# volume_db is a string like "-6 dB" or "+4 dB", extract the number
VOLUME_DB_RAW=$(bashio::config 'volume_db' | sed 's/ dB.*//;s/+//')
VOLUME_DB="${VOLUME_DB_RAW}"
COMPRESSOR_ENABLED=$(bashio::config 'compressor_enabled')

# Audio format and Icecast settings
AUDIO_FORMAT=$(bashio::config 'audio_format' | sed 's/ (Default)//')
MAX_LISTENERS=$(bashio::config 'max_listeners')
GENRE=$(bashio::config 'genre')

# Noise reduction settings
HIGHPASS_ENABLED=$(bashio::config 'noise_reduction.highpass_enabled')
HIGHPASS_FREQ=$(bashio::config 'noise_reduction.highpass_freq')
LOWPASS_ENABLED=$(bashio::config 'noise_reduction.lowpass_enabled')
LOWPASS_FREQ=$(bashio::config 'noise_reduction.lowpass_freq')
DENOISE_ENABLED=$(bashio::config 'noise_reduction.denoise_enabled')
DENOISE_STRENGTH=$(bashio::config 'noise_reduction.denoise_strength')

# Get audio input from HA's built-in audio selector
if bashio::var.has_value "$(bashio::addon.audio_input)"; then
    AUDIO_DEVICE=$(bashio::addon.audio_input)
else
    AUDIO_DEVICE="default"
fi

bashio::log.info "Starting Vinyl Streamer..."
bashio::log.info "Station: ${STATION_NAME}"
bashio::log.info "Mount: ${MOUNT_POINT}"
bashio::log.info "Audio input: ${AUDIO_DEVICE}"
bashio::log.info "Format: ${AUDIO_FORMAT} @ ${AUDIO_BITRATE}kbps"

# Create status directory
mkdir -p /share/vinyl-streamer
START_TIME=$(date +%s)

# Create icecast user
addgroup -S icecast 2>/dev/null || true
adduser -S -G icecast -h /usr/share/icecast -s /sbin/nologin icecast 2>/dev/null || true

# Ensure directories exist
mkdir -p /var/log/icecast /etc/icecast
chown -R icecast:icecast /var/log/icecast /etc/icecast

# List available PulseAudio sources
bashio::log.info "Available PulseAudio sources:"
pactl list sources short 2>/dev/null | while read -r line; do
    bashio::log.info "  $line"
done || true

# Get HA IP address for hostname
HA_IP=$(bashio::network.ipv4_address | head -n1 | cut -d'/' -f1)
if [ -z "$HA_IP" ]; then
    HA_IP="localhost"
fi

# Set Icecast buffer sizes based on latency mode
if bashio::var.true "${LOW_LATENCY}"; then
    QUEUE_SIZE=131072
    BURST_SIZE=8192
    bashio::log.info "Low latency mode: enabled (may cause stuttering on slow networks)"
else
    QUEUE_SIZE=524288
    BURST_SIZE=65535
fi

# Generate Icecast configuration
cat > /etc/icecast/icecast.xml << EOF
<icecast>
    <location>Home</location>
    <admin>admin@localhost</admin>
    <limits>
        <clients>${MAX_LISTENERS}</clients>
        <sources>2</sources>
        <queue-size>${QUEUE_SIZE}</queue-size>
        <client-timeout>30</client-timeout>
        <header-timeout>15</header-timeout>
        <source-timeout>10</source-timeout>
        <burst-on-connect>1</burst-on-connect>
        <burst-size>${BURST_SIZE}</burst-size>
    </limits>
    <authentication>
        <source-password>${ICECAST_PASSWORD}</source-password>
        <relay-password>${ICECAST_PASSWORD}</relay-password>
        <admin-user>admin</admin-user>
        <admin-password>${ICECAST_PASSWORD}</admin-password>
    </authentication>
    <hostname>${HA_IP}</hostname>
    <listen-socket>
        <port>8000</port>
    </listen-socket>
    <mount>
        <mount-name>${MOUNT_POINT}</mount-name>
        <stream-name>${STATION_NAME}</stream-name>
        <stream-description>${STATION_DESC}</stream-description>
        <genre>${GENRE}</genre>
        <public>0</public>
    </mount>
    <fileserve>1</fileserve>
    <paths>
        <basedir>/usr/share/icecast</basedir>
        <logdir>/var/log/icecast</logdir>
        <webroot>/usr/share/icecast/web</webroot>
        <adminroot>/usr/share/icecast/admin</adminroot>
    </paths>
    <logging>
        <accesslog>access.log</accesslog>
        <errorlog>error.log</errorlog>
        <loglevel>3</loglevel>
        <logsize>10000</logsize>
    </logging>
    <security>
        <chroot>0</chroot>
        <changeowner>
            <user>icecast</user>
            <group>icecast</group>
        </changeowner>
    </security>
</icecast>
EOF

# Start Icecast
bashio::log.info "Starting Icecast server..."
icecast -c /etc/icecast/icecast.xml &
ICECAST_PID=$!
sleep 3

if ! kill -0 $ICECAST_PID 2>/dev/null; then
    bashio::log.error "Icecast failed to start!"
    exit 1
fi
bashio::log.info "Icecast started on port 8000"

# Get HA IP address
HA_IP=$(bashio::network.ipv4_address | head -1 | cut -d'/' -f1)
if [ -z "${HA_IP}" ]; then
    HA_IP="[YOUR_HA_IP]"
fi

# Determine input format
if [ "${AUDIO_DEVICE}" = "default" ]; then
    INPUT_FORMAT="pulse"
    INPUT_DEVICE="default"
elif echo "${AUDIO_DEVICE}" | grep -q "^alsa_input\|^alsa_output"; then
    INPUT_FORMAT="pulse"
    INPUT_DEVICE="${AUDIO_DEVICE}"
else
    INPUT_FORMAT="alsa"
    INPUT_DEVICE="${AUDIO_DEVICE}"
fi

bashio::log.info "Using ${INPUT_FORMAT} input: ${INPUT_DEVICE}"
bashio::log.info "Stream URL: http://${HA_IP}:8000${MOUNT_POINT}"

# Build audio filter chain
AUDIO_FILTERS=""

if bashio::var.true "${HIGHPASS_ENABLED}"; then
    AUDIO_FILTERS="highpass=f=${HIGHPASS_FREQ}"
    bashio::log.info "Highpass filter: ${HIGHPASS_FREQ} Hz (removes rumble)"
fi

if bashio::var.true "${LOWPASS_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},lowpass=f=${LOWPASS_FREQ}"
    else
        AUDIO_FILTERS="lowpass=f=${LOWPASS_FREQ}"
    fi
    bashio::log.info "Lowpass filter: ${LOWPASS_FREQ} Hz (removes hiss)"
fi

if bashio::var.true "${DENOISE_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},afftdn=nf=-25:nr=${DENOISE_STRENGTH}:nt=w"
    else
        AUDIO_FILTERS="afftdn=nf=-25:nr=${DENOISE_STRENGTH}:nt=w"
    fi
    bashio::log.info "Noise reduction: strength ${DENOISE_STRENGTH}"
fi

# Volume adjustment
if [ "${VOLUME_DB}" != "0" ]; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},volume=${VOLUME_DB}dB"
    else
        AUDIO_FILTERS="volume=${VOLUME_DB}dB"
    fi
    bashio::log.info "Volume adjustment: ${VOLUME_DB} dB"
fi

# Compressor
if bashio::var.true "${COMPRESSOR_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},acompressor=threshold=-20dB:ratio=4:attack=5:release=50"
    else
        AUDIO_FILTERS="acompressor=threshold=-20dB:ratio=4:attack=5:release=50"
    fi
    bashio::log.info "Audio compressor: enabled"
fi

if [ -z "${AUDIO_FILTERS}" ]; then
    bashio::log.info "Audio filters: none"
fi

bashio::log.info ""
bashio::log.info "TIP: Create a switch in HA to control streaming:"
bashio::log.info "  See DOCS for template switch configuration"

# Write status file for HA integration
write_status() {
    local streaming=$1
    local current_time=$(date +%s)
    local uptime=$((current_time - START_TIME))

    cat > /share/vinyl-streamer/status.json << EOF
{
  "streaming": ${streaming},
  "uptime_seconds": ${uptime},
  "format": "${AUDIO_FORMAT}",
  "bitrate": ${AUDIO_BITRATE},
  "samplerate": ${AUDIO_SAMPLERATE},
  "channels": ${AUDIO_CHANNELS},
  "station_name": "${STATION_NAME}",
  "mount_point": "${MOUNT_POINT}",
  "stream_url": "http://${HA_IP}:8000${MOUNT_POINT}"
}
EOF
}

# Cleanup on exit
cleanup() {
    bashio::log.info "Shutting down..."
    write_status false
    kill $FFMPEG_PID 2>/dev/null || true
    kill $ICECAST_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start FFmpeg with auto-restart
while true; do
    bashio::log.info "Starting FFmpeg encoder..."
    
    # Build FFmpeg command
    FFMPEG_CMD="ffmpeg -hide_banner -loglevel warning"

    # Add low latency flags if enabled
    if bashio::var.true "${LOW_LATENCY}"; then
        FFMPEG_CMD="${FFMPEG_CMD} -fflags nobuffer -flags low_delay"
    fi

    FFMPEG_CMD="${FFMPEG_CMD} -f ${INPUT_FORMAT} -i ${INPUT_DEVICE}"

    # Add audio filters if any
    if [ -n "${AUDIO_FILTERS}" ]; then
        FFMPEG_CMD="${FFMPEG_CMD} -af ${AUDIO_FILTERS}"
    fi

    # Set encoder based on audio format
    case "${AUDIO_FORMAT}" in
        "AAC")
            FFMPEG_CMD="${FFMPEG_CMD} -acodec aac -ab ${AUDIO_BITRATE}k -ac ${AUDIO_CHANNELS} -ar ${AUDIO_SAMPLERATE} -content_type audio/aac -f adts"
            ;;
        "Opus")
            FFMPEG_CMD="${FFMPEG_CMD} -acodec libopus -ab ${AUDIO_BITRATE}k -ac ${AUDIO_CHANNELS} -ar ${AUDIO_SAMPLERATE} -content_type audio/ogg -f opus"
            ;;
        *)
            # Default to MP3
            FFMPEG_CMD="${FFMPEG_CMD} -acodec libmp3lame -ab ${AUDIO_BITRATE}k -ac ${AUDIO_CHANNELS} -ar ${AUDIO_SAMPLERATE} -content_type audio/mpeg -f mp3"
            ;;
    esac

    # Write status before starting
    write_status true

    ${FFMPEG_CMD} "icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}" &
    
    FFMPEG_PID=$!
    
    # Wait for FFmpeg to exit
    wait $FFMPEG_PID || true
    
    # Check if we should restart
    if ! kill -0 $ICECAST_PID 2>/dev/null; then
        bashio::log.error "Icecast died, exiting"
        exit 1
    fi
    
    bashio::log.warning "FFmpeg exited, restarting in 5 seconds..."
    sleep 5
done
