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

Use these installed help entry points to discover current syntax on demand:

```bash
facebook-cli session --help
facebook-cli login --help
facebook-cli auth --help
facebook-cli profile --help
facebook-cli search --help
facebook-cli posts --help
facebook-cli messages --help
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

## Safety

Prefer read-only commands unless the user explicitly asks for a write action.

For write actions, such as sending messages, posting, commenting, reacting, joining, leaving, following, unfollowing, sharing, deleting, or changing settings, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
