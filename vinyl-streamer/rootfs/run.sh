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
AUDIO_SAMPLERATE=$(bashio::config 'audio_samplerate')
AUDIO_CHANNELS=$(bashio::config 'audio_channels')
AUDIO_BITRATE=$(bashio::config 'audio_bitrate')
ICECAST_PASSWORD=$(bashio::config 'icecast_password')

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
bashio::log.info "Bitrate: ${AUDIO_BITRATE}kbps"

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

# Generate Icecast configuration
cat > /etc/icecast/icecast.xml << EOF
<icecast>
    <location>Home</location>
    <admin>admin@localhost</admin>
    <limits>
        <clients>10</clients>
        <sources>2</sources>
        <queue-size>524288</queue-size>
        <client-timeout>30</client-timeout>
        <header-timeout>15</header-timeout>
        <source-timeout>10</source-timeout>
        <burst-on-connect>1</burst-on-connect>
        <burst-size>65535</burst-size>
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
        <genre>Vinyl</genre>
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
bashio::log.info ""
bashio::log.info "TIP: Create a switch in HA to control streaming:"
bashio::log.info "  See DOCS for template switch configuration"

# Cleanup on exit
cleanup() {
    bashio::log.info "Shutting down..."
    kill $FFMPEG_PID 2>/dev/null || true
    kill $ICECAST_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start FFmpeg with auto-restart
while true; do
    bashio::log.info "Starting FFmpeg encoder..."
    
    ffmpeg -hide_banner -loglevel warning \
        -f "${INPUT_FORMAT}" \
        -i "${INPUT_DEVICE}" \
        -acodec libmp3lame \
        -ab "${AUDIO_BITRATE}k" \
        -ac "${AUDIO_CHANNELS}" \
        -ar "${AUDIO_SAMPLERATE}" \
        -content_type audio/mpeg \
        -f mp3 \
        "icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}" &
    
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
