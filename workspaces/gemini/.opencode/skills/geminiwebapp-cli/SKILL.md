---
name: geminiwebapp-cli
description: "Operate geminiwebapp-cli to drive Gemini (https://gemini.google.com) through a real browser: sending prompts, file attachments, media generation (images/videos/music), Deep Research. USE FOR: performing Deep Research using Google services, image and video generation, and editing or analyzing images, videos, PDFs, audio, and other files."
license: MIT
compatibility: opencode
metadata:
  command: geminiwebapp-cli
---

# geminiwebapp-cli Skill

Operate `geminiwebapp-cli`, a CLI that drives https://gemini.google.com through a real Camoufox browser with a persistent local profile. No API key is used; login is done manually once and reused. The browser UI is not a stable API, so expect occasional locator maintenance.

## Use This Skill For

Use this skill for Gemini Web App tasks, including asking Gemini questions, comparing this agent's answer with Gemini, sending prompts with attachments, analyzing files/images/PDFs/screenshots/audio/video, running Deep Research, inspecting chats, continuing chats, creating chats, generating or saving Gemini images, videos, or music, and using Gemini models/tools via the web app.

Do not skip this skill just because the user did not mention `geminiwebapp-cli`. If the task explicitly asks for Gemini or is better handled by Gemini Web App, use this skill.

## Core Conventions

- Always invoke `geminiwebapp-cli ...` from this workspace.
- Always pass `--json` for structured, parseable agent output. Errors emit `ok: false` and `error.type`.
- Use `--session <name>` or `$GEMINIWEBAPP_CLI_SESSION` to target a profile. Default is `default`.
- `<chat>` accepts a full Gemini URL, `/app/...` path, Gemini chat id, or a 1-based index from `chats list`.
- A per-session background Camoufox worker is reused across commands. The first command starts it and it exits when idle. Run `session stop` to close it without losing login.
- `.env` in the cwd is auto-loaded; existing env vars take precedence.

## Functional Help Index

For every action below, run the listed `<command> --help` to get current flags, choices, and defaults before composing the command. This skill intentionally does not duplicate flag lists. Fetch help on demand per task.

### Top-Level & Subcommand Discovery

| When | Run |
|---|---|
| See all top-level commands | `geminiwebapp-cli --help` |
| See chats subcommands | `geminiwebapp-cli chats --help` |
| See auth subcommands | `geminiwebapp-cli auth --help` |
| See session subcommands | `geminiwebapp-cli session --help` |

### Authentication

| When | Run |
|---|---|
| Log in or verify the current session | `geminiwebapp-cli login --help` |
| Open Gemini for manual login | `geminiwebapp-cli auth interactive --help` |
| Read-only login-state check | `geminiwebapp-cli auth status --help` |

### Session Lifecycle

| When | Run |
|---|---|
| Stop the background worker, keep the saved profile | `geminiwebapp-cli session stop --help` |
| Delete the local browser profile, also logging out | `geminiwebapp-cli session clear --help` |

### Send A Prompt

| When | Run |
|---|---|
| Start a new chat and send a prompt | `geminiwebapp-cli chats new --help` |
| Send a follow-up to an existing chat | `geminiwebapp-cli chats send --help` |
| Alias of `chats send` | `geminiwebapp-cli chats continue --help` |

### Media Generation & Download

| When | Run |
|---|---|
| Save generated images from a chat | `geminiwebapp-cli chats images --help` |
| Save generated videos from a chat | `geminiwebapp-cli chats videos --help` |
| Save generated music from a chat | `geminiwebapp-cli chats music --help` |

### Discovery

| When | Run |
|---|---|
| List sidebar chats | `geminiwebapp-cli chats list --help` |
| List visible `+` menu tool options | `geminiwebapp-cli chats tools --help` |

### Reading Chats & Diagnostics

| When | Run |
|---|---|
| Read the messages in a chat | `geminiwebapp-cli chats read --help` |
| Show a chat's type/status, auto-detecting Deep Research | `geminiwebapp-cli chats status --help` |
| Show a Deep Research chat's status | `geminiwebapp-cli chats research --help` |
| Save a screenshot of the current page | `geminiwebapp-cli screenshot --help` |

## Deep Research

For Deep Research, prefer a token-efficient two-step workflow:

1. Start the request using the current `chats new --help` syntax, with Deep Research selected and JSON output enabled.
2. Run the returned `wait_command` to retrieve the completed report and sources in one result.

When the report is completed, use `research.report.text` and `research.sources` directly to answer the user. Do not report only a preview or ask the user to run another command.

## Environment Variables

- `GEMINIWEBAPP_CLI_SESSION`: default session name.
- `GEMINIWEBAPP_CLI_HOME`: state root, default `~/.geminiwebapp-cli`.
- `GEMINIWEBAPP_CLI_HEADLESS`: `1`/`true`/`yes` for headless mode.
- `GEMINIWEBAPP_CLI_LOG`: Python logging level.

## Safety

Use authenticated browser sessions already owned by the user. Do not ask for passwords, tokens, cookies, or other credentials.

For actions that create, publish, share, send, or otherwise modify external state, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
