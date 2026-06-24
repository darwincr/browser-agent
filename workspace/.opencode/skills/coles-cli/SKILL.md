---
name: coles-cli
description: Use Coles through `coles` whenever the user asks to search Coles products, inspect Coles orders, list order items, manage the Coles trolley/cart, or place a Coles order through a real browser session.
license: MIT
compatibility: opencode
metadata:
  command: coles
---

## Use This Skill For

Use this skill for Coles shopping tasks, including searching products, adding products to the trolley, inspecting the trolley/cart, changing trolley item quantities, removing trolley items, listing current or past orders, inspecting order items, and placing orders.

Do not skip this skill just because the user did not mention `coles`. If the task explicitly asks for Coles products, orders, trolley, or checkout, use this skill.

## Core Rule

Keep this skill minimal. Do not rely on memorized command examples beyond auth/session basics. Before running any task-specific Coles command, inspect the CLI's current help so the agent uses the installed CLI contract:

```bash
coles --help
coles <command> --help
coles <command> <subcommand> --help
```

Prefer `--json` whenever available for structured output. Redirect stdout yourself if the user asks for a file.

`coles` uses a persistent Camoufox browser profile and a background worker per session. `cart` and `shoppingcart` are interchangeable aliases.

## Help Entry Points

Use these installed help entry points to discover current syntax on demand:

```bash
coles session --help
coles login --help
coles auth --help
coles orders --help
coles products --help
coles cart --help
coles shoppingcart --help
```

For command groups that expose subcommands, run the deeper subcommand help before execution.

## Sign-In

Before searching products, editing the trolley, listing orders, or checking out, verify authentication:

```bash
coles auth status --json
```

If the session is not authenticated, start interactive login and wait for the user to complete it in the Camoufox window. Do not ask for or print credentials.

```bash
coles login --interactive --wait --timeout 300
```

After login, run `coles auth status --json` again. Proceed only when authentication is confirmed.

If the browser worker needs to be closed without deleting login state, stop the session:

```bash
coles session stop
```

Use `coles session clear` only when the saved profile and login state should be deleted.

## Basic Operation Pattern

For each user request:

1. Confirm authentication with `coles auth status --json`.
2. Run `coles --help` if you do not know the current command group.
3. Run the narrowest relevant `--help`, such as `coles products --help`, `coles cart --help`, or `coles orders --help`, or a deeper subcommand help.
4. Execute the command using the flags shown by the current help output.
5. Use `--json` when available and summarize results for the user.

## Safety

Use the authenticated browser session already owned by the user. Do not ask for passwords, tokens, cookies, or other credentials.

Do not run checkout (`cart checkout`) unless the user explicitly authorizes placing a real Coles order. Checkout places a real order and may charge the user.

After checkout, retrieve the resulting order state with:

```bash
coles orders list --status current --json
```

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
