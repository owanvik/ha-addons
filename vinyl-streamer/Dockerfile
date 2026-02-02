ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Icecast and audio tools
# Note: darkice is not in Alpine repos, using ffmpeg instead
RUN apk add --no-cache \
    icecast \
    ffmpeg \
    alsa-utils \
    alsa-lib \
    alsa-plugins-pulse \
    pulseaudio-utils \
    mosquitto-clients \
    lame \
    bash

# Create directories
RUN mkdir -p /etc/icecast /var/log/icecast /run

# Copy rootfs
COPY rootfs /

# Set permissions
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
