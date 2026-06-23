#!/usr/bin/env bash
set -euo pipefail

install_required() {
  local repo="$1"
  local package_url="git+https://github.com/darwincr/${repo}.git@main"

  printf 'Installing required private CLI repo: %s\n' "$repo"
  python -m pip install --no-cache-dir "$package_url"
}

install_optional() {
  local repo="$1"
  local package_url="git+https://github.com/darwincr/${repo}.git@main"

  if git ls-remote --exit-code "https://github.com/darwincr/${repo}.git" HEAD >/dev/null 2>&1; then
    printf 'Installing optional private CLI repo: %s\n' "$repo"
    python -m pip install --no-cache-dir "$package_url"
  else
    printf 'Skipping unavailable optional private CLI repo: %s\n' "$repo"
  fi
}

mkdir -p "$PLAYWRIGHT_BROWSERS_PATH" "$CAMOUFOX_CACHE_DIR"

install_required geminiwebapp-cli
install_required linkedin-cli
install_optional facebook-cli

python -m playwright install chromium
python -m camoufox fetch
chmod -R a+rX "$PLAYWRIGHT_BROWSERS_PATH" "$CAMOUFOX_CACHE_DIR"
