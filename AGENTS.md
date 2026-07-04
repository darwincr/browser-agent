# Browser Agent

Docker image that runs an A2A browser-automation service: `opencode-a2a` plus the
OpenCode runtime driving a real Chromium browser in an XFCE/Xvfb desktop viewable
over VNC/noVNC. Requests select an isolated workspace (`coles`, `linkedin`,
`facebook`, `gemini`, `browser-harness`), each with its own skill and read-only
config. `browser-agent-cli` is the A2A client for submitting tasks.

## Note

If the user asks to update `opencode.json`, they mean an `opencode.json` file
**inside this project** (e.g. `docker/opencode.json` or a workspace's
`opencode.json`) — not the OpenCode installation/config on this development
workstation.
