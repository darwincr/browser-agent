# syntax=docker/dockerfile:1
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
    A2A_HOST=0.0.0.0 \
    A2A_PORT=8000 \
    A2A_UPSTREAM_PORT=8001 \
    A2A_PUBLIC_URL=http://localhost:8000 \
    OPENCODE_BASE_URL=http://127.0.0.1:4096 \
    OPENCODE_TIMEOUT=1800 \
    OPENCODE_WORKSPACE_ROOT=/workspaces \
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
# No sudo is granted: the agent must not be able to escalate and tamper with the
# read-only global config or the locked per-workspace configs. Privilege drop at
# runtime is handled by gosu in the entrypoint, not sudo.
RUN useradd --create-home --shell /bin/bash --uid 1000 opencode \
    && mkdir -p /workspaces /data /opt/playwright-browsers \
    && chown opencode:opencode /workspaces /data /opt/playwright-browsers

RUN python -m pip install --no-cache-dir --upgrade pip "opencode-a2a==${OPENCODE_A2A_VERSION}" browser-harness \
    && npm install -g opencode-ai \
    && npm cache clean --force

# ---------------------------------------------------------------------------
# Browser runtimes (Layer A) -- keyed ONLY on the browser version args.
# Installed BEFORE the CLIs so touching any CLI never re-downloads Chromium or
# Camoufox (the slowest part of the build). The browsers are fetched for these
# exact versions and are baked into the image layer, so their install target
# must NOT be a BuildKit cache mount (that would leave them out of the final
# image). Only the pip wheel cache is mounted.
#
# camoufox is normally pulled in as a dependency of coles-cli/geminiwebapp-cli
# (both pin `camoufox>=0.4`), so it does not exist yet at this point. Install it
# explicitly here so `camoufox fetch` works; the pinned version satisfies their
# `>=0.4`, so their later installs keep it and the fetched Firefox stays matched.
# camoufox ignores cache-dir env vars and always fetches to $HOME/.cache/camoufox
# (i.e. /home/opencode/.cache/camoufox); entrypoint.sh chowns that tree to the
# opencode user at runtime, so no chmod is needed for it here.
# ---------------------------------------------------------------------------
ARG PLAYWRIGHT_VERSION=1.59.0
ARG CAMOUFOX_VERSION=0.4.11
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "playwright==${PLAYWRIGHT_VERSION}" "camoufox==${CAMOUFOX_VERSION}" \
    && python -m playwright install chromium \
    && python -m camoufox fetch \
    && chmod -R a+rX "$PLAYWRIGHT_BROWSERS_PATH"

# ---------------------------------------------------------------------------
# Required private CLIs -- one layer each, auto-pinned to the current `main`.
# Each `ADD .../commits/main` fetches that repo's latest commit; BuildKit hashes
# the response body, so a layer only busts when that repo's main actually moves.
# Result: bumping one CLI rebuilds only its own layer (not the others), updates
# are automatic (no manual SHA edits), and the cache stays correct. Repos are
# public (unauthenticated HTTPS), so no build secrets are required. Installs run
# as root into /usr/local so the CLIs survive the opencode-home volume mount.
# ---------------------------------------------------------------------------
# Helper that prints a visible banner when a CLI's main branch moves and keeps
# /etc/cli-build-summary up to date for the entrypoint to print on startup.
COPY --chmod=0755 docker/check-cli-update.sh /usr/local/bin/check-cli-update.sh

ADD https://api.github.com/repos/darwincr/geminiwebapp-cli/commits/main /tmp/geminiwebapp-cli.commit
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/cli-shas,id=cli-shas \
    check-cli-update.sh geminiwebapp-cli /tmp/geminiwebapp-cli.commit /root/.cache/cli-shas \
    && pip install "git+https://github.com/darwincr/geminiwebapp-cli.git@main"

ADD https://api.github.com/repos/darwincr/linkedin-cli/commits/main /tmp/linkedin-cli.commit
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/cli-shas,id=cli-shas \
    check-cli-update.sh linkedin-cli /tmp/linkedin-cli.commit /root/.cache/cli-shas \
    && pip install "git+https://github.com/darwincr/linkedin-cli.git@main"

ADD https://api.github.com/repos/darwincr/coles-cli/commits/main /tmp/coles-cli.commit
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/cli-shas,id=cli-shas \
    check-cli-update.sh coles-cli /tmp/coles-cli.commit /root/.cache/cli-shas \
    && pip install "git+https://github.com/darwincr/coles-cli.git@main"

ADD https://api.github.com/repos/darwincr/xero-cli/commits/main /tmp/xero-cli.commit
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/cli-shas,id=cli-shas \
    check-cli-update.sh xero-cli /tmp/xero-cli.commit /root/.cache/cli-shas \
    && pip install "git+https://github.com/darwincr/xero-cli.git@main" \
    && if ! command -v xero-cli >/dev/null 2>&1 && command -v xero-user-cli >/dev/null 2>&1; then \
        ln -s "$(command -v xero-user-cli)" /usr/local/bin/xero-cli; \
    fi

# ---------------------------------------------------------------------------
# facebook-cli -- same `ADD .../commits/main` pattern as the other CLIs for
# automatic, cache-correct updates. (Previously guarded with `git ls-remote`
# because the repo had no default branch; it now has `main`.)
# ---------------------------------------------------------------------------
ADD https://api.github.com/repos/darwincr/facebook-cli/commits/main /tmp/facebook-cli.commit
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/cli-shas,id=cli-shas \
    check-cli-update.sh facebook-cli /tmp/facebook-cli.commit /root/.cache/cli-shas \
    && pip install "git+https://github.com/darwincr/facebook-cli.git@main"

# ---------------------------------------------------------------------------
# Re-assert the Playwright pin (Layer F). The CLIs above can pull Playwright up
# to an incompatible version as a transitive dependency; force it back to the
# browser-matched pin. Chromium/Camoufox were already fetched for this version
# in Layer A, so this only swaps the Python package (no browser re-download).
# Firefox driver 1.60.0 crashes Camoufox on some Coles pages -- keep 1.59.0.
# ---------------------------------------------------------------------------
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --force-reinstall "playwright==${PLAYWRIGHT_VERSION}"

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/a2a_file_proxy.py /usr/local/bin/a2a-file-proxy
COPY docker/opencode-healthcheck /usr/local/bin/opencode-healthcheck
COPY docker/start-recording /usr/local/bin/start-recording
COPY docker/stop-recording /usr/local/bin/stop-recording
COPY docker/take-screenshot /usr/local/bin/take-screenshot
COPY docker/start-browser-harness-browser /usr/local/bin/start-browser-harness-browser
RUN chmod +x \
        /usr/local/bin/entrypoint.sh \
        /usr/local/bin/a2a-file-proxy \
        /usr/local/bin/opencode-healthcheck \
        /usr/local/bin/start-recording \
        /usr/local/bin/stop-recording \
        /usr/local/bin/take-screenshot \
        /usr/local/bin/start-browser-harness-browser

# Global OpenCode config, plugin shim, and vendored opencode-litellm source.
# Baked into the image because Coolify rebuilds the image on every push but
# never refreshes host-side bind-mount sources in its deployment directory.
# The entrypoint syncs these into the persistent opencode-home volume on boot.
COPY docker/opencode.json /opt/opencode-global/opencode.json
COPY docker/opencode-plugins/ /opt/opencode-global/plugins/
COPY docker/opencode-litellm/ /opt/opencode-global/opencode-litellm/

COPY --chown=opencode:opencode workspaces/ /workspaces-seed/

WORKDIR /workspaces

EXPOSE 8000 4096 5900 6080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["/usr/local/bin/opencode-healthcheck"]

ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
