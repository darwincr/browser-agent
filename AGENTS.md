# Browser Agent

Docker image that runs an A2A browser-automation service: `opencode-a2a` plus the
OpenCode runtime driving a real Chromium browser in an XFCE/Xvfb desktop viewable
over VNC/noVNC. Requests select an isolated workspace (`coles`, `linkedin`,
`facebook`, `gemini`, `xero`, `browser-harness`), each with its own skill and
read-only config. `browser-agent-cli` is the A2A client for submitting tasks.

See `README.md` for build, run, ports, environment variables, screen recording,
A2A file/artifact handling, and operational details. This file governs **agent
behavior** only.

---

## Two separate OpenCode runtimes — do not confuse them

There are two distinct OpenCode installations involved in this project. Files
that look the same (`opencode.json`, `AGENTS.md`, `skills/`) exist in both, but
they belong to different runtimes and must never be conflated.

### 1. You — the development agent (this workstation)

You are an OpenCode agent running on the user's local development workstation.
You are editing **this repository**. Your own runtime state lives at:

| Purpose | Path |
| --- | --- |
| This behavior file | `AGENTS.md` (this file, project root) |
| Your own global config | `~/.config/opencode/opencode.json` |
| Your own dev-agent skills (for A2A testing) | `.agents/skills/<name>/SKILL.md` |

Your own global config at `~/.config/opencode/opencode.json` is your
**private runtime config**. Never edit it in response to a user request in this
project — the user is never referring to it from inside this repo.

### 2. The deployed browser-agent (runs inside the Docker container)

A **separate** OpenCode runtime that executes inside the container and serves
A2A requests. Its source-controlled state lives inside this repo:

| Purpose | Path |
| --- | --- |
| Global config for the in-container runtime | `docker/opencode.json` |
| Per-workspace config | `workspaces/<name>/opencode.json` |
| Per-workspace behavior file | `workspaces/<name>/AGENTS.md` |
| Per-workspace skills (used by the deployed agent) | `workspaces/<name>/.opencode/skills/<skill>/SKILL.md` |
| Shared A2A task staging (read-write at runtime) | `workspaces/a2a-tasks/` |

---

## Operating modes — pick the right one per request

The user asks you to do one of two fundamentally different things. Identify
which, and behave accordingly.

### Mode A — Coding agent (changes to this repository)

The user wants you to modify the source of `browser-agent` itself: the
Dockerfile, `docker-compose.yml`, `docker/opencode.json`, a workspace's
`opencode.json` or `AGENTS.md`, a workspace skill, the `browser-agent-cli`
script, Python sources, tests, etc.

In this mode you are an ordinary coding agent: explore the code, edit files in
place, run `uv run ruff check` / `uv run pytest` when relevant, and follow the
repo's existing conventions. Do not invoke the A2A CLI unless the change
explicitly needs to.

### Mode B — A2A testing through the deployed browser-agent

The user wants to verify how the deployed agent behaves when it receives a
request through A2A. They will typically phrase this as "do X in coles",
"research Y on LinkedIn", "ask gemini to Z", "check the facebook workspace",
etc. — referencing a website or workspace rather than a source file.

In this mode, **do not** open workspace files or edit anything. Instead, load
the matching dev-agent skill and use `browser-agent-cli` to submit the task to
the deployed container over A2A. The available dev-agent skills are:

- `.agents/skills/browser-harness` → load the `browser-harness` skill
- `.agents/skills/coles` → load the `coles` skill
- `.agents/skills/facebook` → load the `facebook` skill
- `.agents/skills/gemini` → load the `gemini` skill
- `.agents/skills/linkedin` → load the `linkedin` skill

Each of those skills is a thin wrapper that drives the shared
`./browser-agent-cli` against the workspace of the same name. If the user asks
about the `xero` workspace (which has no dev-agent skill), call
`browser-agent-cli` directly with `--directory xero`.

If you are unsure which mode applies, ask once before acting.

---

## Disambiguation rules

These rules override any default assumption. When the user uses any of the
phrases below without further qualification, this is what they mean:

| User says | They mean (path) | They do NOT mean |
| --- | --- | --- |
| "the global opencode.json" / "global opencode config" / "update opencode.json" | `docker/opencode.json` | `~/.config/opencode/opencode.json` |
| "the facebook opencode.json" / "the coles config", etc. | `workspaces/<name>/opencode.json` | your own global config |
| "the facebook skill" / "update the coles skill", etc. | `workspaces/<name>/.opencode/skills/<skill>/SKILL.md` (the deployed agent's skill) | `.agents/skills/<name>/SKILL.md` (your dev-agent skill) |
| "the workspace AGENTS.md" / "the facebook agent rules" | `workspaces/<name>/AGENTS.md` | this file |
| "the CLI" / "browser-agent-cli" | `./browser-agent-cli` (the script in this repo) | any system-installed tool |
| "do X in coles" / "test gemini", etc. | Mode B: submit via the matching dev-agent skill | edit `workspaces/<name>/` |
| "make a code change" / "update the repo" / "fix the Dockerfile", etc. | Mode A: edit files in place | submit A2A tasks |

### Skill-name collisions — read the path, not the name

Both runtimes have skills that look related but serve different purposes:

- `workspaces/facebook/.opencode/skills/facebook-cli/SKILL.md` — used **by the
  deployed agent** to drive Facebook inside the container.
- `.agents/skills/facebook/SKILL.md` — used **by you** to submit an A2A task
  that exercises the Facebook workspace.

Same naming pattern applies to `coles`, `gemini`, `linkedin`, and
`browser-harness`. When the user says "update the facebook skill", they mean the
**deployed** skill under `workspaces/`, not your dev-agent skill.

### Config precedence

If the user asks for a change that could be either global or per-workpace (for
example an `external_directory` permission, a model, or an agent definition),
default to the **smallest scope that satisfies the request**: prefer
`workspaces/<name>/opencode.json` over `docker/opencode.json`, and confirm with
the user if the change clearly belongs at the global level.

---

## Conventions when editing

- Match the existing formatting of the file you are editing. JSON files use two
  spaces; markdown files use the section style already present.
- Never commit secrets, bearer tokens, or `.env` values. `.env`, `.env.coolify`,
  and `.env.local` are git-ignored for a reason — do not paste their contents
  into commits, logs, or chat.
- Never run `git push` or `git commit` unless the user explicitly asks.
- When editing a workspace skill (`workspaces/<name>/.opencode/skills/...`),
  keep the YAML front matter `name` and `description` fields in sync with what
  that skill actually does.
- After non-trivial code changes, run lint/typecheck/tests if a command exists.
  For Python, that is typically `uv run ruff check` and `uv run pytest`.
