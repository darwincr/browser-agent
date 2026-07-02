FROM python:3.12-slim-bookworm

ARG OPENCODE_A2A_VERSION=1.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    HOME=/home/opencode \
    NOVNC_PORT=6080 \
    VNC_GEOMETRY=1920x1080 \
    VNC_DEPTH=24 \
    OPENCODE_HOST=127.0.0.1 \
    OPENCODE_PORT=4096 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers \
    CAMOUFOX_CACHE_DIR=/opt/camoufox \
    A2A_HOST=0.0.0.0 \
    A2A_PORT=8000 \
    A2A_UPSTREAM_PORT=8001 \
    A2A_PUBLIC_URL=http://localhost:8000 \
    OPENCODE_BASE_URL=http://127.0.0.1:4096 \
    OPENCODE_TIMEOUT=1800 \
    OPENCODE_WORKSPACE_ROOT=/workspace \
    BH_HOME=/home/opencode/.browser-harness \
    BROWSER_HARNESS_HOME=/home/opencode/.browser-harness \
    BU_CDP_URL=http://127.0.0.1:9222 \
    BROWSER_HARNESS_SESSION=default \
    BROWSER_HARNESS_PROFILE_DIR=/home/opencode/.browser-harness/profiles/default \
    A2A_TASK_STORE_DATABASE_URL=sqlite+aiosqlite:////data/opencode-a2a.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        dbus-x11 \
        ffmpeg \
        git \
        gosu \
        libasound2 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdbus-glib-1-2 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnss3 \
        libpangocairo-1.0-0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        net-tools \
        nodejs \
        npm \
        procps \
        sudo \
        tini \
        x11vnc \
        xvfb \
        xfce4 \
        xfce4-terminal \
        novnc \
        websockify \
    && rm -rf /var/lib/apt/lists/*

# Create the opencode user BEFORE any installs that write to /home/opencode.
# Running subsequent installs as opencode avoids an 11-minute recursive chown
# of ~1 GB of camoufox/playwright cache files on the overlay filesystem.
RUN useradd --create-home --shell /bin/bash --uid 1000 opencode \
    && usermod -aG sudo opencode \
    && printf 'opencode ALL=(ALL) NOPASSWD:ALL\n' >/etc/sudoers.d/opencode \
    && chmod 0440 /etc/sudoers.d/opencode \
    && mkdir -p /workspace /data /opt/playwright-browsers /opt/camoufox \
    && chown opencode:opencode /workspace /data /opt/playwright-browsers /opt/camoufox

RUN python -m pip install --no-cache-dir --upgrade pip "opencode-a2a==${OPENCODE_A2A_VERSION}" browser-harness \
    && npm install -g opencode-ai \
    && npm cache clean --force

COPY docker/install_private_clis.sh /usr/local/bin/install-private-clis
RUN chmod +x /usr/local/bin/install-private-clis

# Install CLIs system-wide (/usr/local/bin) so they survive the opencode-home volume mount.
RUN install-private-clis

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/a2a_file_proxy.py /usr/local/bin/a2a-file-proxy
COPY docker/opencode-healthcheck /usr/local/bin/opencode-healthcheck
COPY docker/start-recording /usr/local/bin/start-recording
COPY docker/stop-recording /usr/local/bin/stop-recording
COPY docker/start-browser-harness-browser /usr/local/bin/start-browser-harness-browser
RUN chmod +x \
        /usr/local/bin/entrypoint.sh \
        /usr/local/bin/a2a-file-proxy \
        /usr/local/bin/opencode-healthcheck \
        /usr/local/bin/start-recording \
        /usr/local/bin/stop-recording \
        /usr/local/bin/start-browser-harness-browser

COPY --chown=opencode:opencode workspace/ /workspace-seed/

WORKDIR /workspace

EXPOSE 8000 4096 5900 6080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["/usr/local/bin/opencode-healthcheck"]

ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
