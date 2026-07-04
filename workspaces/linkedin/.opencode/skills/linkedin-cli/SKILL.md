---
name: linkedin-cli
description: Use LinkedIn through `linkedin-cli` whenever the user asks to search LinkedIn, inspect profiles, pages, posts, jobs, messages, notifications, or perform LinkedIn actions on the user's behalf.
license: MIT
compatibility: opencode
metadata:
  command: linkedin-cli
---

## Use This Skill For

Use this skill for LinkedIn tasks, including search, profile or page inspection, posts, jobs, messages, connection state, connection requests, notifications, and company page administration.

Do not skip this skill just because the user did not mention `linkedin-cli`. If the task requires LinkedIn data or actions, use this skill.

## Core Rule

Keep this skill minimal. Do not rely on memorized command examples beyond auth/session basics. Before running any task-specific LinkedIn command, inspect the CLI's current help so the agent uses the installed CLI contract:

```bash
linkedin-cli --help
linkedin-cli <command> --help
linkedin-cli <command> <subcommand> --help
```

Prefer `--json` whenever available for structured output. Redirect stdout yourself if the user asks for a file.

## Help Entry Points

Use these installed help entry points to discover current syntax on demand:

```bash
linkedin-cli session --help
linkedin-cli login --help
linkedin-cli whoami --help
linkedin-cli profile --help
linkedin-cli status --help
linkedin-cli connect --help
linkedin-cli inbox --help
linkedin-cli thread --help
linkedin-cli message --help
linkedin-cli search --help
linkedin-cli jobs --help
linkedin-cli posts --help
linkedin-cli notifications --help
linkedin-cli page --help
```

For command groups that expose subcommands, run the deeper subcommand help before execution.

## Session And Sign-In

`linkedin-cli` uses its own authenticated worker browser session. One long-running `session open` process owns that browser; other `linkedin-cli` commands connect to it. Pick a session name with `--session <name>` or `LINKEDIN_CLI_SESSION`.

This worker browser is separate from any generic Browser Harness desktop browser on CDP `:9222`. `linkedin-cli whoami --json` only proves the `linkedin-cli` worker session is authenticated. It does not prove the generic Browser Harness browser is signed in to LinkedIn.

Use `linkedin-cli` commands for account-visible LinkedIn data. Do not use Browser Harness for LinkedIn unless the user explicitly asks for generic unauthenticated browser mechanics, or the task is only about the visible desktop browser itself.

Start a session when one is not already running:

```bash
export LINKEDIN_CLI_SESSION=work
linkedin-cli session open --session work
```

Keep the session process running while doing LinkedIn work. When finished and appropriate, close it:

```bash
linkedin-cli session close
```

Before any LinkedIn read or write action, verify authentication:

```bash
linkedin-cli whoami --json
```

If the session is not authenticated, start login and let the user complete any browser checkpoint. Do not ask for or print credentials.

```bash
linkedin-cli login
```

After login, run `linkedin-cli whoami --json` again. Proceed only when authentication is confirmed.

## Basic Operation Pattern

For each user request:

1. Confirm the session is open and authenticated with `whoami`.
2. Run `linkedin-cli --help` if you do not know the current command group.
3. Run the narrowest relevant `--help`, such as `linkedin-cli jobs --help`, `linkedin-cli posts --help`, `linkedin-cli page --help`, or a deeper subcommand help.
4. Execute the command using the flags shown by the current help output.
5. Use `--json` when available and summarize results for the user.

## Raw Browser Tasks

For ad-hoc LinkedIn tasks such as "open this URL and report the title", first look for a `linkedin-cli` verb that can inspect the requested object or URL. The authenticated LinkedIn session is only reachable through `linkedin-cli`; the generic Browser Harness browser is a different browser and may be logged out.

If no `linkedin-cli` verb exists for the raw browser action, say that the CLI does not expose that authenticated browser operation instead of switching silently to Browser Harness and reporting unauthenticated state.

## Filesystem Boundaries

Use the installed CLI help and this skill file as the contract. Do not inspect package source, site source code, `.env` files, browser profiles, or other files outside this workspace. If behavior is unclear, run the relevant `linkedin-cli --help` command and report the missing operation.

## Safety

Prefer read-only commands unless the user explicitly asks for a write action.

For write actions, such as sending messages, connecting, posting, commenting, reacting, deleting, applying to jobs, saving jobs, or replying from a company page, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
