#!/usr/bin/with-contenv bashio
# ==============================================================================
# Vinyl Streamer - Run Script
# Starts Icecast server and FFmpeg encoder with MQTT control
# ==============================================================================

set -e

# Read configuration from add-on options
STATION_NAME=$(bashio::config 'station_name')
STATION_DESC=$(bashio::config 'station_description')
MOUNT_POINT=$(bashio::config 'mount_point')
AUDIO_SAMPLERATE=$(bashio::config 'audio_samplerate')
AUDIO_CHANNELS=$(bashio::config 'audio_channels')
AUDIO_BITRATE=$(bashio::config 'audio_bitrate')
ICECAST_PASSWORD=$(bashio::config 'icecast_password')
AUTO_START=$(bashio::config 'auto_start')
MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USER=$(bashio::config 'mqtt_username')
MQTT_PASS=$(bashio::config 'mqtt_password')

# Get audio input from HA's built-in audio selector
if bashio::var.has_value "$(bashio::addon.audio_input)"; then
    AUDIO_DEVICE=$(bashio::addon.audio_input)
else
    AUDIO_DEVICE="default"
fi

# MQTT topics
TOPIC_BASE="vinyl_streamer"
TOPIC_COMMAND="${TOPIC_BASE}/stream/set"
TOPIC_STATE="${TOPIC_BASE}/stream/state"
TOPIC_AVAILABILITY="${TOPIC_BASE}/availability"

# State tracking
FFMPEG_PID=""
STREAMING=false

bashio::log.info "Starting Vinyl Streamer..."
bashio::log.info "Station: ${STATION_NAME}"
bashio::log.info "Mount: ${MOUNT_POINT}"
bashio::log.info "Audio input: ${AUDIO_DEVICE}"
bashio::log.info "Bitrate: ${AUDIO_BITRATE}kbps"
bashio::log.info "Auto-start: ${AUTO_START}"

# Create icecast user and group for running as non-root
addgroup -S icecast 2>/dev/null || true
adduser -S -G icecast -h /usr/share/icecast -s /sbin/nologin icecast 2>/dev/null || true

# Ensure directories exist
mkdir -p /var/log/icecast /etc/icecast
chown -R icecast:icecast /var/log/icecast /etc/icecast

# List available PulseAudio sources
bashio::log.info "Available PulseAudio sources:"
pactl list sources short 2>/dev/null | while read -r line; do
    bashio::log.info "  $line"
done || bashio::log.warning "Could not list PulseAudio sources"

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
    <hostname>localhost</hostname>
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

# MQTT authentication options
MQTT_AUTH=""
if [ -n "${MQTT_USER}" ]; then
    MQTT_AUTH="-u ${MQTT_USER}"
    if [ -n "${MQTT_PASS}" ]; then
        MQTT_AUTH="${MQTT_AUTH} -P ${MQTT_PASS}"
    fi
fi

# Function to publish MQTT message
mqtt_publish() {
    mosquitto_pub -h "${MQTT_HOST}" -p "${MQTT_PORT}" ${MQTT_AUTH} -t "$1" -m "$2" -r
}

# Function to start FFmpeg streaming
start_streaming() {
    if [ "$STREAMING" = true ] && [ -n "$FFMPEG_PID" ] && kill -0 $FFMPEG_PID 2>/dev/null; then
        bashio::log.info "Already streaming"
        return
    fi
    
    bashio::log.info "Starting stream..."
    
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
    STREAMING=true
    mqtt_publish "${TOPIC_STATE}" "ON"
    bashio::log.info "Stream started! URL: http://${HA_IP}:8000${MOUNT_POINT}"
}

# Function to stop FFmpeg streaming
stop_streaming() {
    if [ "$STREAMING" = false ]; then
        bashio::log.info "Not streaming"
        return
    fi
    
    bashio::log.info "Stopping stream..."
    if [ -n "$FFMPEG_PID" ]; then
        kill $FFMPEG_PID 2>/dev/null || true
        wait $FFMPEG_PID 2>/dev/null || true
    fi
    FFMPEG_PID=""
    STREAMING=false
    mqtt_publish "${TOPIC_STATE}" "OFF"
    bashio::log.info "Stream stopped"
}

# Publish MQTT discovery config for switch entity
publish_discovery() {
    local discovery_topic="homeassistant/switch/${TOPIC_BASE}/config"
    local discovery_payload=$(cat << DISCOVERY
{
  "name": "Vinyl Streamer",
  "unique_id": "vinyl_streamer_switch",
  "command_topic": "${TOPIC_COMMAND}",
  "state_topic": "${TOPIC_STATE}",
  "availability_topic": "${TOPIC_AVAILABILITY}",
  "payload_on": "ON",
  "payload_off": "OFF",
  "icon": "mdi:record-player",
  "device": {
    "identifiers": ["vinyl_streamer"],
    "name": "Vinyl Streamer",
    "model": "Icecast + FFmpeg",
    "manufacturer": "owanvik"
  }
}
DISCOVERY
)
    mqtt_publish "${discovery_topic}" "${discovery_payload}"
    mqtt_publish "${TOPIC_AVAILABILITY}" "online"
    bashio::log.info "MQTT discovery published - switch.vinyl_streamer available in HA"
}

# Cleanup on exit
cleanup() {
    bashio::log.info "Shutting down..."
    mqtt_publish "${TOPIC_AVAILABILITY}" "offline"
    stop_streaming
    kill $ICECAST_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Publish MQTT discovery
publish_discovery

# Initial state
mqtt_publish "${TOPIC_STATE}" "OFF"

# Auto-start if configured
if [ "${AUTO_START}" = "true" ]; then
    bashio::log.info "Auto-start enabled, starting stream..."
    start_streaming
else
    bashio::log.info "Waiting for command to start streaming..."
    bashio::log.info "Turn on switch.vinyl_streamer in Home Assistant to start"
fi

bashio::log.info "Stream URL (when active): http://${HA_IP}:8000${MOUNT_POINT}"

# Listen for MQTT commands
bashio::log.info "Listening for MQTT commands on ${TOPIC_COMMAND}..."
mosquitto_sub -h "${MQTT_HOST}" -p "${MQTT_PORT}" ${MQTT_AUTH} -t "${TOPIC_COMMAND}" | while read -r command; do
    bashio::log.info "Received command: ${command}"
    case "${command}" in
        "ON"|"on"|"1"|"true")
            start_streaming
            ;;
        "OFF"|"off"|"0"|"false")
            stop_streaming
            ;;
        *)
            bashio::log.warning "Unknown command: ${command}"
            ;;
    esac
done &
MQTT_SUB_PID=$!

# Monitor FFmpeg and restart if needed (only if streaming)
while true; do
    if [ "$STREAMING" = true ]; then
        if [ -n "$FFMPEG_PID" ] && ! kill -0 $FFMPEG_PID 2>/dev/null; then
            bashio::log.warning "FFmpeg died, restarting..."
            sleep 2
            start_streaming
        fi
    fi
    
    # Check if Icecast is still running
    if ! kill -0 $ICECAST_PID 2>/dev/null; then
        bashio::log.error "Icecast died unexpectedly"
        cleanup
    fi
    
    sleep 5
done
