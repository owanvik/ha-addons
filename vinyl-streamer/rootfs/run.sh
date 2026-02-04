#!/usr/bin/with-contenv bashio
# ==============================================================================
# Vinyl Streamer - Run Script
# Starts Icecast server and FFmpeg encoder
# Start/stop streaming by starting/stopping this add-on
# ==============================================================================

set -e

# ==============================================================================
# Helper Functions
# ==============================================================================

# XML escape function for safe config values
xml_escape() {
    echo "$1" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&apos;/g'
}

# Update status file for HA integration
update_status() {
    local streaming="${1:-false}"
    local recording="${2:-false}"

    mkdir -p /share/vinyl-streamer
    cat > /share/vinyl-streamer/status.json << EOF
{
    "streaming": ${streaming},
    "recording": ${recording},
    "format": "${AUDIO_FORMAT}",
    "bitrate": ${AUDIO_BITRATE},
    "uptime_seconds": $(($(date +%s) - START_TIME)),
    "last_update": "$(date -Iseconds)"
}
EOF
}

START_TIME=$(date +%s)

# ==============================================================================
# Read Configuration
# ==============================================================================

# Basic settings
STATION_NAME=$(bashio::config 'station_name')
STATION_DESC=$(bashio::config 'station_description')
MOUNT_POINT=$(bashio::config 'mount_point')
ICECAST_PASSWORD=$(bashio::config 'icecast_password')
LOW_LATENCY=$(bashio::config 'low_latency')

# Audio quality - strip "(Default)" suffix
AUDIO_FORMAT=$(bashio::config 'audio_quality.format' | sed 's/ (Default)//')
AUDIO_SAMPLERATE=$(bashio::config 'audio_quality.samplerate' | sed 's/ (Default)//')
AUDIO_CHANNELS=$(bashio::config 'audio_quality.channels' | sed 's/ (Default)//')
AUDIO_BITRATE=$(bashio::config 'audio_quality.bitrate' | sed 's/ (Default)//')

# Audio processing
VOLUME_DB=$(bashio::config 'audio_processing.volume_db')
COMPRESSOR_ENABLED=$(bashio::config 'audio_processing.compressor_enabled')
COMPRESSOR_THRESHOLD=$(bashio::config 'audio_processing.compressor_threshold')
COMPRESSOR_RATIO=$(bashio::config 'audio_processing.compressor_ratio')
STEREO_WIDTH=$(bashio::config 'audio_processing.stereo_width' | sed 's/ (Default)//')

# Noise reduction
HIGHPASS_ENABLED=$(bashio::config 'noise_reduction.highpass_enabled')
HIGHPASS_FREQ=$(bashio::config 'noise_reduction.highpass_freq')
LOWPASS_ENABLED=$(bashio::config 'noise_reduction.lowpass_enabled')
LOWPASS_FREQ=$(bashio::config 'noise_reduction.lowpass_freq')
DENOISE_ENABLED=$(bashio::config 'noise_reduction.denoise_enabled')
DENOISE_STRENGTH=$(bashio::config 'noise_reduction.denoise_strength' | sed 's/ (Default)//')

# Icecast settings
MAX_LISTENERS=$(bashio::config 'icecast.max_listeners')
GENRE=$(bashio::config 'icecast.genre')

# Recording settings
RECORDING_ENABLED=$(bashio::config 'recording.enabled')
RECORDING_FORMAT=$(bashio::config 'recording.format' | sed 's/ (Default)//')
RECORDING_PATH=$(bashio::config 'recording.path')

# Get audio input from HA's built-in audio selector
if bashio::var.has_value "$(bashio::addon.audio_input)"; then
    AUDIO_DEVICE=$(bashio::addon.audio_input)
else
    AUDIO_DEVICE="default"
fi

# ==============================================================================
# Startup Logging
# ==============================================================================

bashio::log.info "=============================================="
bashio::log.info "Vinyl Streamer v1.9.0"
bashio::log.info "=============================================="
bashio::log.info "Station: ${STATION_NAME}"
bashio::log.info "Mount: ${MOUNT_POINT}"
bashio::log.info "Audio: ${AUDIO_FORMAT} @ ${AUDIO_BITRATE}kbps, ${AUDIO_SAMPLERATE}Hz, ${AUDIO_CHANNELS}ch"
bashio::log.info "Input device: ${AUDIO_DEVICE}"
bashio::log.info "Max listeners: ${MAX_LISTENERS}"
if bashio::var.true "${LOW_LATENCY}"; then
    bashio::log.info "Low latency mode: enabled"
fi
if bashio::var.true "${RECORDING_ENABLED}"; then
    bashio::log.info "Recording: enabled (${RECORDING_FORMAT} to ${RECORDING_PATH})"
fi

# ==============================================================================
# Setup Icecast
# ==============================================================================

# Create icecast user
addgroup -S icecast 2>/dev/null || true
adduser -S -G icecast -h /usr/share/icecast -s /sbin/nologin icecast 2>/dev/null || true

# Ensure directories exist
mkdir -p /var/log/icecast /etc/icecast
chown -R icecast:icecast /var/log/icecast /etc/icecast

# Get HA IP address for hostname
HA_IP=$(bashio::network.ipv4_address | head -n1 | cut -d'/' -f1)
if [ -z "$HA_IP" ]; then
    HA_IP="localhost"
    bashio::log.warning "Could not detect IP address, using localhost"
fi

# Set Icecast buffer sizes based on latency mode
if bashio::var.true "${LOW_LATENCY}"; then
    QUEUE_SIZE=131072
    BURST_SIZE=8192
else
    QUEUE_SIZE=524288
    BURST_SIZE=65535
fi

# XML escape user-provided values
STATION_NAME_SAFE=$(xml_escape "${STATION_NAME}")
STATION_DESC_SAFE=$(xml_escape "${STATION_DESC}")
GENRE_SAFE=$(xml_escape "${GENRE}")

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
        <stream-name>${STATION_NAME_SAFE}</stream-name>
        <stream-description>${STATION_DESC_SAFE}</stream-description>
        <genre>${GENRE_SAFE}</genre>
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

# Secure the config file
chmod 600 /etc/icecast/icecast.xml

# Start Icecast
bashio::log.info "Starting Icecast server..."
icecast -c /etc/icecast/icecast.xml &
ICECAST_PID=$!

# Wait for Icecast to start and verify port is open
bashio::log.info "Waiting for Icecast to bind to port 8000..."
for i in $(seq 1 10); do
    if nc -z localhost 8000 2>/dev/null; then
        bashio::log.info "Icecast started successfully on port 8000"
        break
    fi
    if [ $i -eq 10 ]; then
        bashio::log.error "Icecast failed to bind to port 8000 after 10 seconds"
        exit 1
    fi
    sleep 1
done

if ! kill -0 $ICECAST_PID 2>/dev/null; then
    bashio::log.error "Icecast process died unexpectedly!"
    exit 1
fi

# ==============================================================================
# Setup FFmpeg
# ==============================================================================

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

# Volume adjustment
if [ "${VOLUME_DB}" != "0" ]; then
    AUDIO_FILTERS="volume=${VOLUME_DB}dB"
    bashio::log.info "Volume: ${VOLUME_DB} dB"
fi

# Stereo width (only if not mono and not 1.0)
if [ "${AUDIO_CHANNELS}" = "2" ] && [ "${STEREO_WIDTH}" != "1.0" ]; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},stereotools=mlev=${STEREO_WIDTH}"
    else
        AUDIO_FILTERS="stereotools=mlev=${STEREO_WIDTH}"
    fi
    bashio::log.info "Stereo width: ${STEREO_WIDTH}"
fi

# Compressor
if bashio::var.true "${COMPRESSOR_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},acompressor=threshold=${COMPRESSOR_THRESHOLD}dB:ratio=${COMPRESSOR_RATIO}:attack=20:release=250"
    else
        AUDIO_FILTERS="acompressor=threshold=${COMPRESSOR_THRESHOLD}dB:ratio=${COMPRESSOR_RATIO}:attack=20:release=250"
    fi
    bashio::log.info "Compressor: threshold ${COMPRESSOR_THRESHOLD}dB, ratio ${COMPRESSOR_RATIO}:1"
fi

# Highpass filter
if bashio::var.true "${HIGHPASS_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},highpass=f=${HIGHPASS_FREQ}"
    else
        AUDIO_FILTERS="highpass=f=${HIGHPASS_FREQ}"
    fi
    bashio::log.info "Highpass filter: ${HIGHPASS_FREQ} Hz"
fi

# Lowpass filter
if bashio::var.true "${LOWPASS_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},lowpass=f=${LOWPASS_FREQ}"
    else
        AUDIO_FILTERS="lowpass=f=${LOWPASS_FREQ}"
    fi
    bashio::log.info "Lowpass filter: ${LOWPASS_FREQ} Hz"
fi

# Denoise
if bashio::var.true "${DENOISE_ENABLED}"; then
    if [ -n "${AUDIO_FILTERS}" ]; then
        AUDIO_FILTERS="${AUDIO_FILTERS},afftdn=nf=-25:nr=${DENOISE_STRENGTH}:nt=w"
    else
        AUDIO_FILTERS="afftdn=nf=-25:nr=${DENOISE_STRENGTH}:nt=w"
    fi
    bashio::log.info "De-noise: strength ${DENOISE_STRENGTH}"
fi

if [ -z "${AUDIO_FILTERS}" ]; then
    bashio::log.info "Audio filters: none"
fi

# Setup recording directory if enabled
if bashio::var.true "${RECORDING_ENABLED}"; then
    mkdir -p "${RECORDING_PATH}"
    bashio::log.info "Recording directory: ${RECORDING_PATH}"
fi

# Determine codec settings based on format
case "${AUDIO_FORMAT}" in
    "mp3")
        CODEC_ARGS="-acodec libmp3lame -ab ${AUDIO_BITRATE}k"
        CONTENT_TYPE="audio/mpeg"
        OUTPUT_EXT="mp3"
        ;;
    "aac")
        CODEC_ARGS="-acodec aac -b:a ${AUDIO_BITRATE}k"
        CONTENT_TYPE="audio/aac"
        OUTPUT_EXT="aac"
        ;;
    "opus")
        CODEC_ARGS="-acodec libopus -b:a ${AUDIO_BITRATE}k"
        CONTENT_TYPE="audio/ogg"
        OUTPUT_EXT="opus"
        ;;
    *)
        CODEC_ARGS="-acodec libmp3lame -ab ${AUDIO_BITRATE}k"
        CONTENT_TYPE="audio/mpeg"
        OUTPUT_EXT="mp3"
        ;;
esac

bashio::log.info ""
bashio::log.info "Starting stream..."

# ==============================================================================
# Cleanup Handler
# ==============================================================================

cleanup() {
    bashio::log.info "Shutting down..."
    update_status false false

    # Try graceful shutdown first
    kill $FFMPEG_PID 2>/dev/null || true
    sleep 2

    # Force kill if still running
    kill -9 $FFMPEG_PID 2>/dev/null || true
    kill $ICECAST_PID 2>/dev/null || true

    exit 0
}
trap cleanup SIGTERM SIGINT

# ==============================================================================
# FFmpeg Loop with Exponential Backoff
# ==============================================================================

RESTART_COUNT=0
RESTART_DELAY=5
MAX_RESTART_DELAY=60
LAST_STABLE_TIME=$START_TIME

while true; do
    bashio::log.info "Starting FFmpeg encoder..."

    # Build FFmpeg command
    FFMPEG_CMD="ffmpeg -hide_banner -loglevel warning -nostats"

    # Add low latency flags if enabled
    if bashio::var.true "${LOW_LATENCY}"; then
        FFMPEG_CMD="${FFMPEG_CMD} -fflags nobuffer -flags low_delay"
    fi

    FFMPEG_CMD="${FFMPEG_CMD} -f ${INPUT_FORMAT} -i ${INPUT_DEVICE}"

    # Add audio filters if any
    if [ -n "${AUDIO_FILTERS}" ]; then
        FFMPEG_CMD="${FFMPEG_CMD} -af ${AUDIO_FILTERS}"
    fi

    FFMPEG_CMD="${FFMPEG_CMD} ${CODEC_ARGS} -ac ${AUDIO_CHANNELS} -ar ${AUDIO_SAMPLERATE}"

    # Output - either direct to Icecast or tee for recording
    if bashio::var.true "${RECORDING_ENABLED}"; then
        RECORDING_FILE="${RECORDING_PATH}/vinyl_$(date +%Y%m%d_%H%M%S).${OUTPUT_EXT}"
        bashio::log.info "Recording to: ${RECORDING_FILE}"

        # Use tee muxer to output to both Icecast and file
        if [ "${AUDIO_FORMAT}" = "mp3" ]; then
            FFMPEG_CMD="${FFMPEG_CMD} -f tee -map 0:a \"[f=mp3]${RECORDING_FILE}|[f=mp3:content_type=${CONTENT_TYPE}]icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}\""
        elif [ "${AUDIO_FORMAT}" = "flac" ]; then
            # Recording as FLAC, streaming as MP3
            FFMPEG_CMD="${FFMPEG_CMD} -f tee -map 0:a \"[f=flac]${RECORDING_FILE}|[f=mp3:content_type=audio/mpeg]icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}\""
        else
            FFMPEG_CMD="${FFMPEG_CMD} -content_type ${CONTENT_TYPE} -f ${OUTPUT_EXT} icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}"
        fi
        update_status true true
    else
        FFMPEG_CMD="${FFMPEG_CMD} -content_type ${CONTENT_TYPE} -f mp3 icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}"
        update_status true false
    fi

    # Run FFmpeg
    eval ${FFMPEG_CMD} &
    FFMPEG_PID=$!

    # Wait for FFmpeg to exit
    wait $FFMPEG_PID || true

    # Check if Icecast is still running
    if ! kill -0 $ICECAST_PID 2>/dev/null; then
        bashio::log.error "Icecast died, exiting"
        update_status false false
        exit 1
    fi

    # Calculate uptime since last restart
    CURRENT_TIME=$(date +%s)
    UPTIME_SINCE_START=$((CURRENT_TIME - LAST_STABLE_TIME))

    # Reset backoff if stable for 5 minutes
    if [ $UPTIME_SINCE_START -gt 300 ]; then
        RESTART_COUNT=0
        RESTART_DELAY=5
    fi

    # Increment restart counter
    RESTART_COUNT=$((RESTART_COUNT + 1))

    # Calculate delay with exponential backoff
    if [ $RESTART_COUNT -gt 1 ]; then
        RESTART_DELAY=$((RESTART_DELAY * 2))
        if [ $RESTART_DELAY -gt $MAX_RESTART_DELAY ]; then
            RESTART_DELAY=$MAX_RESTART_DELAY
        fi
    fi

    bashio::log.warning "FFmpeg exited (restart #${RESTART_COUNT}), restarting in ${RESTART_DELAY} seconds..."
    update_status false false
    sleep $RESTART_DELAY

    LAST_STABLE_TIME=$(date +%s)
done
