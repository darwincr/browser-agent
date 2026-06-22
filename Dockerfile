FROM python:3.12-slim-bookworm

ARG OPENCODE_A2A_VERSION=1.1.1

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:1 \
    HOME=/home/opencode \
    NOVNC_PORT=6080 \
    VNC_GEOMETRY=1440x900 \
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
    OPENCODE_WORKSPACE_ROOT=/workspace \
    A2A_TASK_STORE_DATABASE_URL=sqlite+aiosqlite:////data/opencode-a2a.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        dbus-x11 \
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

RUN python -m pip install --no-cache-dir --upgrade pip uv \
    && uv tool install "opencode-a2a==${OPENCODE_A2A_VERSION}" \
    && ln -s /home/opencode/.local/bin/opencode-a2a /usr/local/bin/opencode-a2a \
    && npm install -g opencode-ai \
    && npm cache clean --force

COPY docker/install_private_clis.sh /usr/local/bin/install-private-clis
RUN chmod +x /usr/local/bin/install-private-clis
RUN install-private-clis

RUN useradd --create-home --shell /bin/bash --uid 1000 opencode \
    && usermod -aG sudo opencode \
    && printf 'opencode ALL=(ALL) NOPASSWD:ALL\n' >/etc/sudoers.d/opencode \
    && chmod 0440 /etc/sudoers.d/opencode \
    && mkdir -p /workspace /data /home/opencode/.vnc \
    && chown -R opencode:opencode /workspace /data /home/opencode

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/a2a_file_proxy.py /usr/local/bin/a2a-file-proxy
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/a2a-file-proxy

WORKDIR /workspace

EXPOSE 8000 4096 5900 6080

ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
