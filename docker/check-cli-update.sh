#!/usr/bin/env bash
# Prints a prominent banner when a GitHub-sourced CLI's main branch has moved
# since the last build, and records the image's CLI SHAs for entrypoint.sh to
# compare at runtime. The last-seen SHA is persisted in a BuildKit cache mount
# so it survives across builds on the same builder.
#
# Usage:  check-cli-update.sh <cli-name> <commit-json-file> <sha-cache-dir>
set -euo pipefail

CLI_NAME="$1"
COMMIT_FILE="$2"
SHA_CACHE_DIR="${3:-/tmp/cli-shas}"
SUMMARY_FILE="/etc/cli-build-summary"
SHA_FILE="$SHA_CACHE_DIR/${CLI_NAME}.sha"

# Extract the 40-char commit SHA from the GitHub API JSON response.
NEW_SHA="$(grep -m1 '"sha"' "$COMMIT_FILE" 2>/dev/null | grep -oE '[0-9a-f]{40}' || true)"

if [ -z "$NEW_SHA" ]; then
    echo ">>> [cli] ${CLI_NAME}: could not parse commit SHA, installing anyway"
    exit 0
fi

SHORT_NEW="${NEW_SHA:0:12}"
OLD_SHA="$(cat "$SHA_FILE" 2>/dev/null || true)"
SHORT_OLD="${OLD_SHA:0:12}"

# Persist the current SHA for the next build's comparison and bake the image's
# current CLI SHAs for runtime comparison against the previous deployment.
mkdir -p "$SHA_CACHE_DIR"
printf '%s\n' "$NEW_SHA" > "$SHA_FILE"
printf '%s %s\n' "$CLI_NAME" "$NEW_SHA" >> "$SUMMARY_FILE" 2>/dev/null || true

if [ -z "$OLD_SHA" ]; then
    exit 0
elif [ "$NEW_SHA" != "$OLD_SHA" ]; then
    cat <<EOF

================================================================
  [CLI UPDATE] ${CLI_NAME}
    was:  ${SHORT_OLD}
    now:  ${SHORT_NEW}
================================================================

EOF
else
    exit 0
fi
