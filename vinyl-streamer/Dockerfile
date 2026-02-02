ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Icecast and Darkice
RUN apk add --no-cache \
    icecast \
    darkice \
    alsa-utils \
    alsa-lib \
    lame \
    bash \
    jq

# Create directories
RUN mkdir -p /etc/icecast2 /etc/darkice /var/log/icecast2 /run

# Copy config templates
COPY rootfs /

# Set permissions
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
