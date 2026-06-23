#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" = "0" ]; then
  mkdir -p /workspace /data /home/opencode/.vnc
  chown -R opencode:opencode /workspace /data
  exec gosu opencode "$0" "$@"
fi

export HOME="${HOME:-/home/opencode}"
export DISPLAY="${DISPLAY:-:1}"
export OPENCODE_HOST="${OPENCODE_HOST:-127.0.0.1}"
export OPENCODE_PORT="${OPENCODE_PORT:-4096}"
export OPENCODE_BASE_URL="${OPENCODE_BASE_URL:-http://${OPENCODE_HOST}:${OPENCODE_PORT}}"
export A2A_HOST="${A2A_HOST:-0.0.0.0}"
export A2A_PORT="${A2A_PORT:-8000}"
export A2A_UPSTREAM_PORT="${A2A_UPSTREAM_PORT:-8001}"
export A2A_PUBLIC_URL="${A2A_PUBLIC_URL:-http://localhost:${A2A_PORT}}"
export OPENCODE_WORKSPACE_ROOT="${OPENCODE_WORKSPACE_ROOT:-/workspace}"
export A2A_TASK_STORE_DATABASE_URL="${A2A_TASK_STORE_DATABASE_URL:-sqlite+aiosqlite:////data/opencode-a2a.db}"
export A2A_FILE_PROXY_UPSTREAM="${A2A_FILE_PROXY_UPSTREAM:-http://127.0.0.1:${A2A_UPSTREAM_PORT}}"

mkdir -p /workspace /data "$HOME/.vnc"

# Seed /workspace from /workspace-seed if it is empty or missing key files.
# This handles bind-mounted empty directories (e.g. Coolify) while preserving
# existing local bind mounts that already contain the workspace content.
if [ -d /workspace-seed ] && [ ! -f /workspace/AGENTS.md ]; then
  cp -a /workspace-seed/. /workspace/
fi

# Always overwrite opencode.json from the seed so provider/model config tracks
# the image on every redeploy, even when /workspace already persists data.
if [ -f /workspace-seed/opencode.json ]; then
  cp /workspace-seed/opencode.json /workspace/opencode.json
fi

if [ $# -gt 0 ]; then
  exec "$@"
fi

if [ -n "${VNC_PASSWORD:-}" ]; then
  x11vnc -storepasswd "$VNC_PASSWORD" "$HOME/.vnc/passwd" >/dev/null 2>&1
  VNC_AUTH_ARGS=("-rfbauth" "$HOME/.vnc/passwd")
else
  VNC_AUTH_ARGS=("-nopw")
fi

cleanup() {
  jobs -pr | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

display_number="${DISPLAY#:}"
display_number="${display_number%%.*}"
lock_file="/tmp/.X${display_number}-lock"
socket_file="/tmp/.X11-unix/X${display_number}"

if [ -f "$lock_file" ]; then
  lock_pid="$(tr -d ' ' <"$lock_file" 2>/dev/null || true)"
  if [ -z "$lock_pid" ] || ! kill -0 "$lock_pid" 2>/dev/null; then
    rm -f "$lock_file" "$socket_file"
  fi
fi

Xvfb "$DISPLAY" -screen 0 "${VNC_GEOMETRY:-1440x900}x${VNC_DEPTH:-24}" -nolisten tcp 2>&1 | tee /tmp/xvfb.log &
sleep 1

startxfce4 2>&1 | tee /tmp/xfce.log &
x11vnc -display "$DISPLAY" -forever -shared "${VNC_AUTH_ARGS[@]}" -rfbport 5900 2>&1 | tee /tmp/x11vnc.log &
websockify --web=/usr/share/novnc/ "${NOVNC_PORT:-6080}" localhost:5900 2>&1 | tee /tmp/novnc.log &

opencode serve --hostname "$OPENCODE_HOST" --port "$OPENCODE_PORT" --log-level INFO 2>&1 | tee /tmp/opencode.log &

A2A_PORT="$A2A_UPSTREAM_PORT" A2A_HOST="127.0.0.1" opencode-a2a serve 2>&1 | tee /tmp/opencode-a2a.log &

exec a2a-file-proxy
