#!/usr/bin/with-contenv bashio
# ==============================================================================
# Vinyl Streamer - Run Script
# Starts Icecast server and Darkice encoder
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
cat > /etc/icecast2/icecast.xml << EOF
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
        <logdir>/var/log/icecast2</logdir>
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

# Generate Darkice configuration
cat > /etc/darkice/darkice.cfg << EOF
# Darkice configuration for Vinyl Streamer
# Auto-generated - do not edit manually

[general]
duration        = 0
bufferSecs      = 5
reconnect       = yes

[input]
device          = ${AUDIO_DEVICE}
sampleRate      = ${AUDIO_SAMPLERATE}
bitsPerSample   = 16
channel         = ${AUDIO_CHANNELS}

[icecast2-0]
bitrateMode     = cbr
format          = mp3
bitrate         = ${AUDIO_BITRATE}
server          = localhost
port            = 8000
password        = ${ICECAST_PASSWORD}
mountPoint      = ${MOUNT_POINT}
name            = ${STATION_NAME}
description     = ${STATION_DESC}
genre           = Vinyl
public          = no
EOF

# Start Icecast in background
bashio::log.info "Starting Icecast server..."
icecast -c /etc/icecast2/icecast.xml &
ICECAST_PID=$!

# Wait for Icecast to be ready
sleep 3

# Check if Icecast is running
if ! kill -0 $ICECAST_PID 2>/dev/null; then
    bashio::log.error "Icecast failed to start!"
    cat /var/log/icecast2/error.log || true
    exit 1
fi
bashio::log.info "Icecast started on port 8000"

# Function to start Darkice with retry logic
start_darkice() {
    while true; do
        bashio::log.info "Starting Darkice encoder..."
        
        # Check if audio device exists
        if ! arecord -L | grep -q "${AUDIO_DEVICE%%,*}"; then
            bashio::log.warning "Audio device ${AUDIO_DEVICE} not found. Waiting..."
            sleep 10
            continue
        fi
        
        darkice -c /etc/darkice/darkice.cfg
        
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            bashio::log.warning "Darkice exited with code ${EXIT_CODE}. Restarting in 5 seconds..."
            sleep 5
        fi
    done
}

# Start Darkice with auto-restart
start_darkice &
DARKICE_PID=$!

bashio::log.info "Vinyl Streamer is running!"
bashio::log.info "Stream URL: http://[YOUR_HA_IP]:8000${MOUNT_POINT}"

# Wait for any process to exit
wait -n $ICECAST_PID $DARKICE_PID

# Exit with error if any process died unexpectedly
bashio::log.error "One of the services died unexpectedly"
exit 1
