ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Icecast and audio tools
RUN apk add --no-cache \
    icecast \
    ffmpeg \
    alsa-utils \
    alsa-lib \
    alsa-plugins-pulse \
    pulseaudio-utils \
    lame \
    mailcap \
    bash \
    netcat-openbsd

# Create directories
RUN mkdir -p /etc/icecast /var/log/icecast /run

# Copy rootfs
COPY rootfs /

# Set permissions
RUN chmod a+x /run.sh

# Health check - verify Icecast is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD nc -z localhost 8000 || exit 1

CMD [ "/run.sh" ]
