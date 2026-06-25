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

- `./workspace` to `/workspace` for project files
- `./data` to `/data` for the SQLite A2A task store
- `opencode-home` to `/home/opencode` for persisted OpenCode auth/config state

For Dockerfile-based deployments such as Coolify, the image also seeds `/workspace`
from the repository's `workspace/` directory at build time. Local Compose still
overlays that seeded copy with the `./workspace:/workspace` bind mount.

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

The image includes `ffmpeg` and two helper commands in the system path:

```bash
start-recording
stop-recording
```

`start-recording` captures the XFCE/Xvfb display and saves the MP4 file, log,
and PID metadata in the current directory.

Run `stop-recording` from the same directory used to start the recording.

Optional runtime settings:

- `SCREEN_RECORDING_FRAMERATE`: capture framerate, default `15`.
- `SCREEN_RECORDING_OUTPUT_DIR`: output directory, default current directory.
- `SCREEN_RECORDING_LOG_FILE`: log path, default `./screen-recording.log`.
- `SCREEN_RECORDING_PID_FILE`: PID path, default `./screen-recording.pid`.

You can also pass an explicit output path:

```bash
start-recording /workspace/demo.mp4
```

## Verify

After the container starts, check the public Agent Card:

```bash
curl http://localhost:18000/.well-known/agent-card.json
```

Authenticated requests require the bearer token configured in `A2A_STATIC_AUTH_CREDENTIALS`. The default Compose token is `change-me`; replace it before exposing this container beyond local development.

## Test A2A Requests

Use the included standard-library Python client:

```bash
python3 scripts/a2a_request.py "Explain what this repository does."
```

Streaming test:

```bash
python3 scripts/a2a_request.py --stream "Say hello and list three files you can see."
```

JSON-RPC test:

```bash
python3 scripts/a2a_request.py --json-rpc "Explain the current workspace."
```

If you change the Compose bearer token, pass it explicitly:

```bash
python3 scripts/a2a_request.py --token your-token "What can you do?"
```

Useful options:

- `--url http://localhost:18000`
- `--context-id test-conversation-1`
- `--session-id existing-opencode-session-id`
- `--model-provider provider-id --model model-id`
- `--directory /workspace/some-subdir`
- `--file ./path/to/input.pdf`

## A2A File Inputs And Artifacts

This image includes a lightweight A2A file proxy in front of `opencode-a2a`.
The proxy follows A2A file conventions while keeping the upstream OpenCode agent unchanged:

- Incoming `raw` or `url` file parts in `message.parts` are staged under `/workspace/a2a-tasks/<task-id>/inputs`.
- The agent receives an added instruction listing the staged input paths.
- Files the agent writes under `/workspace/a2a-tasks/<task-id>/outputs` are returned as A2A `artifacts` with URL parts.
- Artifact files are served from `/artifacts/<task-id>/outputs/<filename>` and require the same bearer token when `A2A_STATIC_AUTH_CREDENTIALS` is configured.

Attach a local file with the test client:

```bash
python3 scripts/a2a_request.py --file ./source.pdf "Summarize this file and write summary.md for the next agent."
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

Runtime knobs:

- `A2A_UPSTREAM_PORT`: internal `opencode-a2a` port, default `8001`.
- `A2A_FILE_TASK_ROOT`: task staging root, default `/workspace/a2a-tasks`.
- `A2A_FILE_MAX_INLINE_BYTES`: maximum inline `bytes` file size, default `10485760`.

## Provider Configuration

OpenCode provider credentials belong to the OpenCode runtime, not `opencode-a2a`.

You can configure them inside the desktop session or by injecting provider-specific environment variables into `docker-compose.yml`. Persisted OpenCode state is stored in the `opencode-home` volume.

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

`facebook-cli` currently exists as a private GitHub repository but has no default
branch, so the build skips it until the repo contains installable code.

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
- `/tmp/opencode.log`
- `/tmp/opencode-a2a.log`
