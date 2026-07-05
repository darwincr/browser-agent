---
name: facebook-cli
description: Use Facebook through `facebook-cli` whenever the user asks to search Facebook profiles, pages, groups, marketplace, posts, comments, messages, notifications, or perform Facebook actions on the user's behalf.
license: MIT
compatibility: opencode
metadata:
  command: facebook-cli
---

## Use This Skill For

Use this skill for Facebook tasks, including search, profiles, pages, posts, messages,  groups, marketplace search, inspect profiles/pages and user-directed Facebook actions.

Do not skip this skill just because the user did not mention `facebook-cli`. If the task requires Facebook data or actions, use this skill.

## Core Rule

Keep this skill minimal. Do not rely on memorized command examples beyond auth/session basics. Before running any task-specific Facebook command, inspect the CLI's current help so the agent uses the installed CLI contract:

```bash
facebook-cli --help
facebook-cli <command> --help
facebook-cli <command> <subcommand> --help
```

Prefer `--json` whenever available for structured output. Redirect stdout yourself if the user asks for a file.

## Help Entry Points

Use these installed help entry points to discover current syntax on demand. Run the narrowest one that matches the task. The CLI surface is:

```bash
# Top level
facebook-cli --help

# Session state
facebook-cli session --help
facebook-cli session clear --help

# Login / authentication
facebook-cli login --help
facebook-cli auth --help
facebook-cli auth status --help
facebook-cli auth interactive --help

# Profile / page inspection
facebook-cli profile --help

# Search
facebook-cli search --help

# Posts (read and write)
facebook-cli posts --help
facebook-cli posts feed --help
facebook-cli posts profile --help
facebook-cli posts group --help
facebook-cli posts create --help
facebook-cli posts comments --help
facebook-cli posts comment --help

# Messenger messages (read and send)
facebook-cli messages --help
facebook-cli messages threads --help
facebook-cli messages read --help
facebook-cli messages send --help
```

For command groups that expose subcommands, run the deeper subcommand help before execution.

## Sign-In

Before any Facebook read or write action, verify authentication:

```bash
facebook-cli auth status --json
```

If the session is not authenticated, start interactive login and wait for the user to complete it. Do not ask for or print credentials.

```bash
facebook-cli login --interactive --wait --timeout 300
```

After login, run `facebook-cli auth status --json` again. Proceed only when authentication is confirmed.

`facebook-cli` uses an authenticated worker browser session. That worker browser is separate from any generic Browser Harness desktop browser on CDP `:9222`. `facebook-cli auth status --json` only proves the `facebook-cli` worker session is authenticated; it does not prove the generic Browser Harness browser is signed in to Facebook.

If session cleanup is needed, inspect current session help first:

```bash
facebook-cli session --help
```

## Basic Operation Pattern

For each user request:

1. Confirm authentication with `facebook-cli auth status --json`.
2. Run `facebook-cli --help` if you do not know the current command group.
3. Run the narrowest relevant `--help`, such as `facebook-cli search --help`, `facebook-cli posts --help`, `facebook-cli messages --help`, or a deeper subcommand help.
4. Execute the command using the flags shown by the current help output.
5. Use `--json` when available and summarize results for the user.

## Raw Browser Tasks

For ad-hoc Facebook tasks such as "open this URL and report the title", first look for a `facebook-cli` verb that can inspect the requested object or URL. The authenticated Facebook session is only reachable through `facebook-cli` or a documented workspace helper; the generic Browser Harness browser is a different browser and may be logged out.

For the basic "open Facebook and report title/url" diagnostic, use the workspace helper instead of package-source introspection:

```bash
python .opencode/open_fb.py
```

For other raw authenticated browser diagnostics, use the same public API shape as that helper:

```python
from facebook_cli import worker
from facebook_cli.session import FacebookSession

worker.stop_worker("default")
with FacebookSession("default") as s:
    s.page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    print({"title": s.page.title(), "url": s.page.url})
```

Stop the worker first when directly opening the persistent profile; otherwise the profile can be locked by the background worker. Use `FacebookSession` as a context manager because `__init__` does not populate `s.page`.

## Filesystem Boundaries

Use the installed CLI help, this skill file, and workspace helpers as the contract. Do not inspect package source, site source code, `.env` files, browser profiles, or other files outside this workspace. If behavior is unclear, run the relevant `facebook-cli --help` command and report the missing operation.

## Safety

Prefer read-only commands unless the user explicitly asks for a write action.

For write actions, such as sending messages, posting, commenting, reacting, joining, leaving, following, unfollowing, sharing, deleting, or changing settings, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
