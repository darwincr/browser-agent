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

Runtime configuration lives in `.env`. The defaults publish:

- A2A service on host port `18000`
- OpenCode web UI/upstream service on host port `14096`
- VNC on host port `5900`
- noVNC on host port `6080`

If a host port is already taken, edit the corresponding value in `.env`, for example:

```dotenv
OPENCODE_HOST_PORT=15096
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

Test project-local OpenCode skill discovery:

```bash
python3 scripts/a2a_request.py "Load the test-skill skill and tell me the confirmation sentence."
```

The skill lives at:

```text
workspace/.opencode/skills/test-skill/SKILL.md
```

Inside the container this appears at:

```text
/workspace/.opencode/skills/test-skill/SKILL.md
```

Useful options:

- `--url http://localhost:18000`
- `--context-id test-conversation-1`
- `--session-id existing-opencode-session-id`
- `--model-provider provider-id --model model-id`
- `--directory /workspace/some-subdir`

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
