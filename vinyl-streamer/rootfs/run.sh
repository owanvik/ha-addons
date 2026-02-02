#!/usr/bin/with-contenv bashio
# ==============================================================================
# Vinyl Streamer - Run Script
# Starts Icecast server and FFmpeg encoder
# ==============================================================================

set -e

# Read configuration from add-on options
STATION_NAME=$(bashio::config 'station_name')
STATION_DESC=$(bashio::config 'station_description')
MOUNT_POINT=$(bashio::config 'mount_point')
AUDIO_DEVICE=$(bashio::config 'audio_device')
AUDIO_SAMPLERATE=$(bashio::config 'audio_samplerate')
AUDIO_CHANNELS=$(bashio::config 'audio_channels')
AUDIO_BITRATE=$(bashio::config 'audio_bitrate')
ICECAST_PASSWORD=$(bashio::config 'icecast_password')

bashio::log.info "Starting Vinyl Streamer..."
bashio::log.info "Station: ${STATION_NAME}"
bashio::log.info "Mount: ${MOUNT_POINT}"
bashio::log.info "Audio device: ${AUDIO_DEVICE}"
bashio::log.info "Bitrate: ${AUDIO_BITRATE}kbps"

# List available audio devices for debugging
bashio::log.info "Available audio devices:"
arecord -l || bashio::log.warning "Could not list audio devices"

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
    </security>
</icecast>
EOF

# Start Icecast in background
bashio::log.info "Starting Icecast server..."
icecast -c /etc/icecast/icecast.xml &
ICECAST_PID=$!

# Wait for Icecast to be ready
sleep 3

# Check if Icecast is running
if ! kill -0 $ICECAST_PID 2>/dev/null; then
    bashio::log.error "Icecast failed to start!"
    cat /var/log/icecast/error.log || true
    exit 1
fi
bashio::log.info "Icecast started on port 8000"

# Function to start FFmpeg encoder with retry logic
start_ffmpeg_encoder() {
    while true; do
        bashio::log.info "Starting FFmpeg encoder..."
        
        # Skip device check if using "default"
        if [ "${AUDIO_DEVICE}" != "default" ]; then
            if ! arecord -L 2>/dev/null | grep -q "${AUDIO_DEVICE%%,*}"; then
                bashio::log.warning "Audio device ${AUDIO_DEVICE} not found. Waiting..."
                bashio::log.info "Available devices:"
                arecord -L 2>/dev/null | head -20 || true
                sleep 10
                continue
            fi
        fi
        
        # FFmpeg command matching user's working config
        # -f alsa: ALSA audio input
        # -i: Input device (can be "default" or specific like "hw:CARD=CODEC")
        # -acodec libmp3lame: MP3 encoding
        # -ab: Audio bitrate
        # -ac: Audio channels
        # -ar: Audio sample rate
        # -sample_fmt s32p: Sample format for better quality
        # -content_type audio/mpeg: Required for Icecast
        # -f mp3: Output format
        ffmpeg -hide_banner -loglevel warning \
            -f alsa \
            -i "${AUDIO_DEVICE}" \
            -acodec libmp3lame \
            -ab "${AUDIO_BITRATE}k" \
            -ac "${AUDIO_CHANNELS}" \
            -ar "${AUDIO_SAMPLERATE}" \
            -sample_fmt s32p \
            -content_type audio/mpeg \
            -f mp3 \
            "icecast://source:${ICECAST_PASSWORD}@localhost:8000${MOUNT_POINT}"
        
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            bashio::log.warning "FFmpeg exited with code ${EXIT_CODE}. Restarting in 5 seconds..."
            sleep 5
        fi
    done
}

# Start FFmpeg encoder with auto-restart
start_ffmpeg_encoder &
FFMPEG_PID=$!

bashio::log.info "Vinyl Streamer is running!"
bashio::log.info "Stream URL: http://[YOUR_HA_IP]:8000${MOUNT_POINT}"

# Trap signals for clean shutdown
cleanup() {
    bashio::log.info "Shutting down..."
    kill $FFMPEG_PID 2>/dev/null || true
    kill $ICECAST_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for any process to exit
wait -n $ICECAST_PID $FFMPEG_PID

# Exit with error if any process died unexpectedly
bashio::log.error "One of the services died unexpectedly"
exit 1
