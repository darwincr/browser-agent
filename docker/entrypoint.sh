#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" = "0" ]; then
  WORKSPACE_ROOT="${OPENCODE_WORKSPACE_ROOT:-/workspaces}"

  mkdir -p \
    "$WORKSPACE_ROOT" \
    /data \
    /home/opencode/.cache \
    /home/opencode/.config/opencode \
    /home/opencode/.browser-harness \
    /home/opencode/Desktop \
    /home/opencode/.local/share/opencode/log \
    /home/opencode/.local/state/screen-recording \
    /home/opencode/.local/state \
    /home/opencode/.vnc
  mkdir -p /tmp/.X11-unix /tmp/.ICE-unix
  chmod 1777 /tmp/.X11-unix /tmp/.ICE-unix
  chown opencode:opencode /home/opencode
  chown opencode:opencode /home/opencode/.config
  chown opencode:opencode /home/opencode/.config/opencode
  chown -R opencode:opencode \
    /data \
    /home/opencode/.cache \
    /home/opencode/.browser-harness \
    /home/opencode/Desktop \
    /home/opencode/.local \
    /home/opencode/.vnc

  refresh_workspaces="${OPENCODE_REFRESH_WORKSPACES_ON_START:-false}"

  # Optionally refresh source-controlled workspaces on every boot. Coolify
  # persists the /workspaces mount across deploys, but these agent workspaces are
  # disposable: the image seed is the source of truth. Keep only the shared A2A
  # task staging directory, which must remain writable for input/output artifacts.
  if [ "$refresh_workspaces" = "true" ] && [ -d /workspaces-seed ]; then
    for existing in "$WORKSPACE_ROOT"/*; do
      [ -e "$existing" ] || continue
      [ "$(basename "$existing")" = "a2a-tasks" ] && continue
      rm -rf -- "$existing"
    done
    cp -a /workspaces-seed/. "$WORKSPACE_ROOT"/
  elif [ -d /workspaces-seed ] && [ ! -e "$WORKSPACE_ROOT/.seeded" ]; then
    cp -a /workspaces-seed/. "$WORKSPACE_ROOT"/
    touch "$WORKSPACE_ROOT/.seeded"
  fi
  mkdir -p "$WORKSPACE_ROOT/a2a-tasks"
  chown -R opencode:opencode "$WORKSPACE_ROOT"

  # Give each workspace its own git worktree so OpenCode's upward search for
  # config, skills, and AGENTS.md stops at the workspace boundary. This is what
  # keeps one workspace's skill/config from leaking into another. A workspace is
  # any immediate subdirectory that ships an opencode.json.
  for dir in "$WORKSPACE_ROOT"/*/; do
    [ -f "${dir}opencode.json" ] || continue
    if [ ! -d "${dir}.git" ]; then
      gosu opencode git -C "$dir" init -q
    fi
  done

  if [ "$refresh_workspaces" = "true" ]; then
    # Lock the refreshed agent workspaces read-only and root-owned. The agent
    # runs as the sudo-less opencode user, so task output should go to /tmp or
    # the writable /workspaces/a2a-tasks artifact staging tree instead.
    for dir in "$WORKSPACE_ROOT"/*/; do
      [ -f "${dir}opencode.json" ] || continue
      chown -R root:root "$dir"
      chmod -R a-w "$dir"
    done
    chown root:root "$WORKSPACE_ROOT"
    chmod 0555 "$WORKSPACE_ROOT"
  else
    # Lock only control files for local bind-mounted development workspaces.
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -name opencode.json -type f -exec chown root:root {} +
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -name opencode.json -type f -exec chmod 0444 {} +
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -name AGENTS.md -type f -exec chown root:root {} +
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -name AGENTS.md -type f -exec chmod 0444 {} +
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -type d -name .opencode -exec chown -R root:root {} +
    find "$WORKSPACE_ROOT" -mindepth 2 -maxdepth 2 -type d -name .opencode -exec chmod -R a-w {} +
  fi
  chown -R opencode:opencode "$WORKSPACE_ROOT/a2a-tasks"
  chmod 0755 "$WORKSPACE_ROOT/a2a-tasks"

  exec gosu opencode "$0" "$@"
fi

export HOME="${HOME:-/home/opencode}"
export DISPLAY="${DISPLAY:-:1}"
export OPENCODE_HOST="${OPENCODE_HOST:-127.0.0.1}"
export OPENCODE_PORT="${OPENCODE_PORT:-4096}"
export OPENCODE_BASE_URL="${OPENCODE_BASE_URL:-http://${OPENCODE_HOST}:${OPENCODE_PORT}}"
export BH_HOME="${BH_HOME:-$HOME/.browser-harness}"
export BROWSER_HARNESS_HOME="${BROWSER_HARNESS_HOME:-$BH_HOME}"
export BU_CDP_URL="${BU_CDP_URL:-http://127.0.0.1:9222}"
export BROWSER_HARNESS_SESSION="${BROWSER_HARNESS_SESSION:-default}"
export BROWSER_HARNESS_PROFILE_DIR="${BROWSER_HARNESS_PROFILE_DIR:-$BH_HOME/profiles/$BROWSER_HARNESS_SESSION}"
export A2A_HOST="${A2A_HOST:-0.0.0.0}"
export A2A_PORT="${A2A_PORT:-8000}"
export A2A_UPSTREAM_PORT="${A2A_UPSTREAM_PORT:-8001}"
export A2A_PUBLIC_URL="${A2A_PUBLIC_URL:-http://localhost:${A2A_PORT}}"
export OPENCODE_WORKSPACE_ROOT="${OPENCODE_WORKSPACE_ROOT:-/workspaces}"
export A2A_TASK_STORE_DATABASE_URL="${A2A_TASK_STORE_DATABASE_URL:-sqlite+aiosqlite:////data/opencode-a2a.db}"
export A2A_FILE_PROXY_UPSTREAM="${A2A_FILE_PROXY_UPSTREAM:-http://127.0.0.1:${A2A_UPSTREAM_PORT}}"
export XDG_CONFIG_DIRS="${XDG_CONFIG_DIRS:-/etc/xdg}"
export XDG_DATA_DIRS="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

mkdir -p "$OPENCODE_WORKSPACE_ROOT" /data "$HOME/.vnc" "$HOME/Desktop" "$HOME/.local/state/screen-recording" "$BROWSER_HARNESS_PROFILE_DIR"

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

Xvfb "$DISPLAY" -screen 0 "${VNC_GEOMETRY:-1920x1080}x${VNC_DEPTH:-24}" -nolisten tcp 2>&1 | tee /tmp/xvfb.log &
sleep 1

dbus-run-session -- bash -lc '
  xfsettingsd &
  xfwm4 --replace &
  xfdesktop &
  xfce4-panel &
  wait
' 2>&1 | tee /tmp/xfce.log &
x11vnc -display "$DISPLAY" -forever -shared "${VNC_AUTH_ARGS[@]}" -rfbport 5900 2>&1 | tee /tmp/x11vnc.log &
websockify --web=/usr/share/novnc/ "${NOVNC_PORT:-6080}" localhost:5900 2>&1 | tee /tmp/novnc.log &

start-browser-harness-browser 2>&1 | tee /tmp/browser-harness-browser.log &

opencode serve --hostname "$OPENCODE_HOST" --port "$OPENCODE_PORT" --log-level INFO 2>&1 | tee /tmp/opencode.log &

A2A_PORT="$A2A_UPSTREAM_PORT" A2A_HOST="127.0.0.1" opencode-a2a serve 2>&1 | tee /tmp/opencode-a2a.log &

exec a2a-file-proxy
