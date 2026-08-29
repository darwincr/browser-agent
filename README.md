# Custom opencode-a2a XFCE Image

This workspace builds a custom Docker image containing:

- `opencode-a2a`
- OpenCode CLI/runtime (`opencode-ai`)
- XFCE desktop running under Xvfb
- VNC on port `5900`
- noVNC browser access on port `6080`

The image is structured so you can add more software later by extending the package list in `Dockerfile`.

## Build

```bash
docker compose build
```

Or without Compose:

```bash
docker build -t custom-opencode-a2a-xfce:latest .
```

## Run

```bash
docker compose up
```

Endpoints:

- A2A service: `http://localhost:18000`
- OpenCode web UI/upstream service: `http://localhost:14096`
- noVNC desktop: `http://localhost:6080/vnc.html`
- VNC desktop: `localhost:5900`

OpenCode still listens on port `4096` inside the container; Compose publishes it on the host port configured by `OPENCODE_HOST_PORT` in `.env`.

The Compose file mounts:

- `./workspaces` to `/workspaces` for the per-workspace project files
- `./data` to `/data` for the SQLite A2A task store
- `opencode-home` to `/home/opencode` for persisted OpenCode auth/config state

The global OpenCode config (`docker/opencode.json`), the plugin shim
(`docker/opencode-plugins/`), and the vendored `opencode-litellm` source
(`docker/opencode-litellm/`) are baked into the image under
`/opt/opencode-global/` and synced into the `opencode-home` volume by the
entrypoint on every boot. They are deliberately **not** bind-mounted: Coolify
rebuilds the image on every push but never refreshes host-side bind-mount
sources in its deployment directory, so bind mounts would serve stale files.

For Dockerfile-based deployments such as Coolify, the image also seeds `/workspaces`
from the repository's `workspaces/` directory at build time. Set
`OPENCODE_REFRESH_WORKSPACES_ON_START=true` for image-based deployments with a
persisted `/workspaces` mount. On every container start, the entrypoint then
refreshes the source-controlled agent workspaces from that seed so repo changes
are picked up after each redeploy. Files created inside agent workspaces are
disposable and are removed during this refresh. The shared `/workspaces/a2a-tasks`
staging tree is preserved and remains writable for A2A inputs and output
artifacts. Local Compose keeps this disabled by default because it overlays the
seeded copy with the `./workspaces:/workspaces` bind mount.

## Workspaces

Each subdirectory of `/workspaces` is an isolated OpenCode workspace with its own
`AGENTS.md`, read-only `opencode.json`, and `.opencode/skills/`:

| Directory | Dedicated skill | Also includes |
| --- | --- | --- |
| `coles` | `coles-cli` | `screen-recording` |
| `linkedin` | `linkedin-cli` | `screen-recording` |
| `facebook` | `facebook-cli` | `screen-recording` |
| `gemini` | `geminiwebapp-cli` | `screen-recording` |
| `xero` | `xero-cli` | `screen-recording` |
| `browser-harness` | `browser-harness` | `screen-recording` |

A request selects its workspace with `metadata.opencode.directory` (the
`--directory` flag on `browser-agent-cli`). `opencode-a2a` resolves that value
under `OPENCODE_WORKSPACE_ROOT` (`/workspaces`) and runs the OpenCode session in
that directory, so only that workspace's skill, rules, and config load. There is
**no default workspace**: a submit without a directory is rejected.

Isolation and lock-down are enforced at startup by the entrypoint:

- Each workspace is given its own git worktree so OpenCode's upward search for
  config, skills, and `AGENTS.md` stops at the workspace boundary.
- Each source-controlled agent workspace is made root-owned and read-only. The
  agent runs as a sudo-less user, so it can read workspace instructions, config,
  and skills but cannot persist changes there.
- Scratch files should be written to `/tmp`. Files intended for the user or
  another A2A agent should be written under `/workspaces/a2a-tasks/**`.
- Security-critical settings (providers, permissions, the `external_directory`
  allow-list) live in the read-only global `docker/opencode.json`.

Runtime configuration lives in `.env`. The defaults publish:

- A2A service on host port `18000`
- OpenCode web UI/upstream service on host port `14096`
- VNC on host port `5900`
- noVNC on host port `6080`
- VNC/noVNC desktop resolution `1920x1080` at 24-bit depth

If a host port is already taken, edit the corresponding value in `.env`, for example:

```dotenv
OPENCODE_HOST_PORT=15096
```

To change the noVNC desktop size, edit `VNC_GEOMETRY` in `.env`, for example:

```dotenv
VNC_GEOMETRY=1280x720
```

## Screen Recording

The image includes `ffmpeg` and visual capture helper commands in the system path:

```bash
take-screenshot
start-recording
stop-recording
```

`take-screenshot` captures the current XFCE/Xvfb display and saves a PNG file in
the current directory.

`start-recording` captures the XFCE/Xvfb display and saves the MP4 file, log,
and PID metadata in the current directory.

Run `stop-recording` from the same directory used to start the recording.

Optional runtime settings:

- `SCREENSHOT_OUTPUT_DIR`: screenshot output directory, default current directory.
- `SCREEN_RECORDING_FRAMERATE`: capture framerate, default `15`.
- `SCREEN_RECORDING_OUTPUT_DIR`: output directory, default current directory.
- `SCREEN_RECORDING_LOG_FILE`: log path, default `./screen-recording.log`.
- `SCREEN_RECORDING_PID_FILE`: PID path, default `./screen-recording.pid`.

You can also pass an explicit output path:

```bash
take-screenshot ./page-state.png
start-recording ./demo.mp4
```

## Verify

After the container starts, check the public Agent Card:

```bash
curl http://localhost:18000/.well-known/agent-card.json
```

The Agent Card describes the browser/desktop automation, workspace command, and file-artifact capabilities. Set `A2A_BROWSER_VIEW_URL` to the public noVNC URL that observers can open to watch the browser session.

Authenticated requests require the bearer token configured in `A2A_STATIC_AUTH_CREDENTIALS`. The default Compose token is `change-me`; replace it before exposing this container beyond local development.

## Browser Agent CLI

`browser-agent-cli` is a single portable executable script (standard library
only). It reads `A2A_PUBLIC_URL` and `A2A_STATIC_AUTH_CREDENTIALS` from a `.env`
file in the current directory or alongside the script by default. Run it as
`./browser-agent-cli` from the project, or copy/symlink it onto your `PATH`
(e.g. `/usr/local/bin`) to call `browser-agent-cli` from anywhere.

```bash
./browser-agent-cli --help
```

Fetch the deployed Coolify agent card using `.env.coolify`:

```bash
./browser-agent-cli --env-file .env.coolify card
```

Submit a task to the Coolify deployment. Every `submit` must select a workspace with
`--directory` (there is no default workspace), and the task message must be provided
on stdin. The command waits up to 110 seconds by default (under the common 120s
shell-tool timeout) and returns compact JSON for agent consumption:

```bash
./browser-agent-cli --env-file .env.coolify submit --directory browser-harness < /tmp/task.txt
```

If the task is still running, use the returned `taskId` as input to `wait`:

```bash
./browser-agent-cli --env-file .env.coolify wait task-id-from-submit
```

Check state without waiting:

```bash
./browser-agent-cli --env-file .env.coolify status task-id-from-submit
```

List provider/model IDs configured on the A2A server:

```bash
./browser-agent-cli --env-file .env.coolify models
./browser-agent-cli --env-file .env.coolify models --provider dr-openai
```

Useful options:

- `--url https://browser-agent.example.com`
- `--token your-token`
- `submit --wait-seconds 300 < /tmp/task.txt`
- `submit --no-wait < /tmp/task.txt`
- `submit --context-id test-conversation-1 < /tmp/task.txt`
- `submit --session-id existing-opencode-session-id < /tmp/task.txt`
- `submit --model-provider provider-id --model model-id < /tmp/task.txt`
- `models --provider provider-id`
- `submit --directory coles < /tmp/task.txt` (required for submit)
- `submit --file ./path/to/input.pdf < /tmp/task.txt`
- `download task-id-from-submit --output-dir ./artifacts`
- `download http://localhost:18000/artifacts/msg-123/outputs/screenshot.png --output-dir ./artifacts`
- `wait --poll-timeout 600 task-id-from-submit`

The CLI writes compact JSON to stdout. Successful outputs keep only values that
are useful as future inputs, such as `taskId`, `contextId`, `state`, `terminal`,
`text`, and artifact file URLs.

## Test A2A Requests

Run the script (reads `.env` for `A2A_PUBLIC_URL` and the bearer token):

```bash
./browser-agent-cli submit --directory browser-harness < /tmp/task.txt
```

If you change the Compose bearer token, pass it explicitly:

```bash
./browser-agent-cli submit --directory browser-harness --token your-token < /tmp/task.txt
```

Useful options:

- `--url http://localhost:18000`
- `--context-id test-conversation-1`
- `--session-id existing-opencode-session-id`
- `--model-provider provider-id --model model-id`
- `--directory coles` (required for submit; selects the workspace)
- `--file ./path/to/input.pdf`

## A2A File Inputs And Artifacts

This image includes a lightweight A2A file proxy in front of `opencode-a2a`.
The proxy follows A2A file conventions while keeping the upstream OpenCode agent unchanged:

- Incoming `raw` or `url` file parts in `message.parts` are staged under `/workspaces/a2a-tasks/<task-id>/inputs`.
- The agent receives an added instruction listing the staged input paths.
- Files the agent writes under `/workspaces/a2a-tasks/<task-id>/outputs` are returned as A2A `artifacts` with URL parts.
- Artifact files are served from `/artifacts/<task-id>/outputs/<filename>` and require the same bearer token when `A2A_STATIC_AUTH_CREDENTIALS` is configured.

The `/workspaces/a2a-tasks` staging root sits outside the per-workspace directories, so the global config and each workspace config allow it via the `external_directory` permission while all other paths outside a workspace stay blocked by default. The global config also denies the `question` tool so non-interactive requests fail instead of opening a permission prompt.

Attach a local file with the test client:

```bash
./browser-agent-cli submit --directory browser-harness --file ./source.pdf < /tmp/task.txt
```

The client sends the file as an inline A2A `raw` part:

```json
{
  "filename": "source.pdf",
  "mediaType": "application/pdf",
  "raw": "base64-encoded-content"
}
```

For larger agent-to-agent workflows, prefer URI-based file parts:

```json
{
  "filename": "source.pdf",
  "mediaType": "application/pdf",
  "url": "https://files.example.com/tasks/task-123/source.pdf"
}
```

When the agent writes output files to the provided `outputs` directory, the proxy adds artifacts like:

```json
{
  "artifactId": "summary.md",
  "name": "summary.md",
  "parts": [
    {
      "filename": "summary.md",
      "mediaType": "text/markdown",
      "url": "http://localhost:18000/artifacts/msg-123/outputs/summary.md"
    }
  ]
}
```

Download artifacts with the same `.env` / `--url` / `--token` settings as the rest of the CLI:

```bash
./browser-agent-cli download task-id-from-submit --output-dir ./artifacts
./browser-agent-cli download http://localhost:18000/artifacts/msg-123/outputs/summary.md --output-dir ./artifacts
./browser-agent-cli download /artifacts/msg-123/outputs/summary.md --output-dir ./artifacts
```

Runtime knobs:

- `A2A_UPSTREAM_PORT`: internal `opencode-a2a` port, default `8001`.
- `A2A_BROWSER_VIEW_URL`: public noVNC URL advertised in the Agent Card, for example `http://localhost:6080/vnc.html`.
- `A2A_FILE_TASK_ROOT`: task staging root, default `/workspaces/a2a-tasks`.
- `A2A_FILE_MAX_INLINE_BYTES`: maximum inline `bytes` file size, default `10485760`.
- `OPENCODE_TIMEOUT`: max seconds `opencode-a2a` waits for OpenCode to finish a non-streaming request, default `1800` in this image.

## Provider Configuration

OpenCode provider credentials belong to the OpenCode runtime, not `opencode-a2a`.

You can configure them inside the desktop session or by injecting provider-specific environment variables into `docker-compose.yml`. Persisted OpenCode state is stored in the `opencode-home` volume.

### LiteLLM dynamic model discovery

The in-container runtime loads the [opencode-litellm](https://github.com/darwincr/opencode-litellm) plugin (a local fork of `yuseferi/opencode-litellm`, vendored in `docker/opencode-litellm/`). The image bakes it under `/opt/opencode-global/` and the entrypoint syncs it to `~/.config/opencode/opencode-litellm` (plus the shim from `docker/opencode-plugins/` into `~/.config/opencode/plugins/`, which OpenCode auto-loads) on every boot. The plugin needs no `"plugin"` array entry.

Providers in `docker/opencode.json` opt in with `"litellm": true` and discover their models from `https://litellm.dranzone.net` at startup (`dr-anthropic`, `dr-google`, `dr-openai`). Options mirror the workstation setup:

- `modelFilter` / `excludeModels` — glob include/deny lists applied to **discovered** models only
- `modelDefaults` — gap-filling defaults (limits, cost, variants) for matching model ids
- `litellmMcp` / `litellmMcpEnabled` — opt-in MCP-server discovery from the same proxy (currently off)

The provider `models` maps are intentionally empty: the model lineup (including
all pinned agent models) comes from LiteLLM discovery. If discovery fails
(proxy unreachable, bad `LITELLM_API_KEY`), OpenCode starts with no dr-* models
and the plugin logs a warning to `/tmp/opencode.log`.

The fork has no runtime npm dependencies (type-only imports), so the vendored source runs without `node_modules`. To update it, re-vendor from `~/.config/opencode/opencode-litellm` on the workstation (copy `src/`, `package.json`, `LICENSE`, `README.md`, `tsconfig.json`).

## Adding More Software

Add Debian packages to this block in `Dockerfile`:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ...
```

For language tools, add install commands after the existing Python/Node installation block.

## Private CLI Tools For Skills

The image installs Python CLI tools from public GitHub repositories during the
Docker build:

- `geminiwebapp-cli` from `darwincr/geminiwebapp-cli`
- `linkedin-cli` from `darwincr/linkedin-cli`
- `coles-cli` from `darwincr/coles-cli`
- `facebook-cli` from `darwincr/facebook-cli` when that repository has a default branch

`geminiwebapp-cli`, `linkedin-cli`, and `coles-cli` are required build dependencies. If SSH
forwarding is not working, the build fails rather than silently creating an image
without the tools required by skills.

The build uses unauthenticated HTTPS Git URLs, so no GitHub credentials or SSH
keys are needed in the Docker build.

Skills can call these commands directly when the image is running:

```bash
geminiwebapp-cli --help
linkedin-cli --help
coles --help
facebook-cli --help
browser-harness --help
```

`geminiwebapp-cli` uses persistent browser sessions. Its
state is stored under the container user's home directory by default, which is
persisted by the `opencode-home` volume.

`linkedin-cli` uses Playwright Chromium with a bind + connect session model.
Open a session once (`linkedin-cli session open`) and drive it from any shell.
Its browser profile is stored under the container user's home directory, which is
persisted by the `opencode-home` volume.

`coles-cli` (command `coles`) uses a persistent Camoufox browser profile with a
background worker per session. It does not handle Coles credentials; login is
completed manually in the opened browser and reused from the saved profile. Its
profile is stored under the container user's home directory, which is persisted by
the `opencode-home` volume.

`facebook-cli` uses a persistent Playwright Chromium profile with a background
worker per session. Login is completed manually in the opened browser and reused
from the saved profile. Its profile is stored under the container user's home
directory, which is persisted by the `opencode-home` volume.

Set `FACEBOOK_CLI_MESSENGER_PIN` in `.env` when the Facebook Messenger session
requires PIN unlock. `docker-compose.yml` passes it through to the container for
`facebook-cli`.

`browser-harness` uses a generic persistent Chromium profile at
`~/.browser-harness/profiles/default`. The container starts this browser
automatically in the visible noVNC desktop and exposes CDP only inside the
container at `http://127.0.0.1:9222`. The launcher reuses Playwright's installed
Chromium executable instead of installing a second Debian Chromium package.

## Overriding Startup

The default entrypoint starts XFCE, VNC, noVNC, `opencode serve`, and `opencode-a2a serve`.

To open a shell instead:

```bash
docker compose run --rm opencode-a2a-xfce bash
```

Runtime logs are written inside the container at:

- `/tmp/xfce.log`
- `/tmp/x11vnc.log`
- `/tmp/novnc.log`
- `/tmp/browser-harness-browser.log`
- `/tmp/opencode.log`
- `/tmp/opencode-a2a.log`

## Health Check

The image includes a Docker `HEALTHCHECK` for Coolify and other container
orchestrators. It probes the OpenCode API at `/global/health` on
`127.0.0.1:${OPENCODE_PORT:-4096}` and expects `healthy: true`.

If `OPENCODE_SERVER_PASSWORD` is set, the health check uses OpenCode basic auth
with `OPENCODE_SERVER_USERNAME` or the default username `opencode`.
