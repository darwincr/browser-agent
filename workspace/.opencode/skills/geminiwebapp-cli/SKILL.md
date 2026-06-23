---
name: geminiwebapp-cli
description: Use Gemini Web App through `geminiwebapp-cli` whenever the user asks to ask Gemini, use Gemini models, compare with Gemini, send prompts with files, run Deep Research, inspect Gemini chats, or generate Gemini media.
license: MIT
compatibility: opencode
metadata:
  command: geminiwebapp-cli
---

## Use This Skill For

Use this skill for Gemini Web App tasks, including asking Gemini questions, comparing this agent's answer with Gemini, sending prompts with attachments, analyzing files, running Deep Research, inspecting or continuing chats, and generating or saving Gemini images, videos, or music.

Do not skip this skill just because the user did not mention `geminiwebapp-cli`. If the task explicitly asks for Gemini or is better handled by Gemini Web App, use this skill.

## Core Rule

Keep this skill minimal. Do not rely on memorized command examples beyond auth/session basics. Before running any task-specific Gemini command, inspect the CLI's current help so the agent uses the installed CLI contract:

```bash
geminiwebapp-cli --help
geminiwebapp-cli <command> --help
geminiwebapp-cli <command> <subcommand> --help
```

Prefer `--json` whenever available for structured output. Redirect stdout yourself if the user asks for a file.

## Help Entry Points

Use these installed help entry points to discover current syntax on demand:

```bash
geminiwebapp-cli session --help
geminiwebapp-cli login --help
geminiwebapp-cli auth --help
geminiwebapp-cli chats --help
```

For command groups that expose subcommands, run the deeper subcommand help before execution.

## Sign-In

Before creating chats, uploading files, running Deep Research, reading chats, or generating media, verify authentication:

```bash
geminiwebapp-cli auth status --json
```

If the session is not authenticated, start interactive login and wait for the user to complete it. Do not ask for or print credentials.

```bash
geminiwebapp-cli login --interactive --wait --timeout 300
```

After login, run `geminiwebapp-cli auth status --json` again. Proceed only when authentication is confirmed.

If session cleanup or worker control is needed, inspect current session help first:

```bash
geminiwebapp-cli session --help
```

## Basic Operation Pattern

For each user request:

1. Confirm authentication with `geminiwebapp-cli auth status --json`.
2. Run `geminiwebapp-cli --help` if you do not know the current command group.
3. Run the narrowest relevant `--help`, such as `geminiwebapp-cli chats --help` or a deeper subcommand help.
4. Execute the command using the flags shown by the current help output.
5. Use `--json` when available and summarize results for the user.

## Safety

Use authenticated browser sessions already owned by the user. Do not ask for passwords, tokens, cookies, or other credentials.

For actions that create, publish, share, send, or otherwise modify external state, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
