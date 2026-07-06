---
name: coles-cli
description: "Operate the coles-cli tool that drives Coles supermarket through a persistent browser session. USE FOR: grocery shopping using Coles shopping automation, list Coles cart/trolley, list Coles orders, search Coles products, add products to Coles shopping cart. DO NOT USE FOR: shopping through other grocery retailers."
license: MIT
compatibility: opencode
metadata:
  command: coles
---

# Coles CLI Skill

This skill guides an agent in operating the `coles` / `coles-cli` command. The CLI drives Coles online shopping through a persistent Camoufox browser profile and a background worker spawned per session.

## Use This Skill For

Use this skill for Coles shopping tasks, including searching products, adding products to the trolley, inspecting the trolley/cart, changing trolley item quantities, removing trolley items, listing current or past orders, inspecting order items, capturing Coles screenshots, and placing orders.

Do not skip this skill just because the user did not mention `coles`. If the task explicitly asks for Coles products, orders, trolley, or checkout, use this skill.

## Operating Rules

- Use `coles ...` from this workspace.
- Prefer `--json` for machine-readable output. Plain text output is a short human summary.
- Before running any command whose flags you are not certain of, run that command's `--help` first.
- The CLI keeps a persistent browser profile and a background worker per session name. The worker survives between commands so login state is reused.
- `coles session stop` closes the browser worker without deleting login/profile state.
- `coles session clear` deletes the local browser profile and login state for a session. Use only when login/profile state should be destroyed.
- Do not run checkout unless the user explicitly authorizes placing a real Coles order. Checkout places a real, potentially chargeable order.
- After a successful checkout, retrieve the resulting order with `coles orders list --status current --json`.
- The session/profile name defaults to `$COLES_CLI_SESSION` or `default`. Override per command with `--session <name>` or `--name <name>`.

## Checking Current Browser State

These read-only commands are safe to run anytime to observe the current browser/session state. No need to consult `--help` first.

| Goal | Command |
|---|---|
| Am I logged in? What account? | `coles auth status --json` |
| What is in the trolley/cart right now? | `coles cart list --json` (alias: `shoppingcart list`) |
| What are my current in-progress orders? | `coles orders list --status current --json` |
| Capture the current page to a file | `coles screenshot` (writes `screenshot.png`; override with `--output PATH`) |

`coles auth status` reports login state without opening a login flow. All four commands accept global `--session` / `--name` and `--json` flags. If `auth status` returns `login_required`, or any verb returns `interactive_authentication_required` with a `next_command`, sign in before doing anything else.

## Help Index

For every task that is not a read-only state check above, find the matching category below and run the listed `--help` command(s) to learn exact flags before executing.

### Orientation

| When | Run |
|---|---|
| You are unfamiliar with the CLI or need the full list of command groups | `coles --help` |

### Session & Browser Worker Lifecycle

| When | Run |
|---|---|
| Manage the local browser session | `coles session --help` |
| Stop the background worker but keep login/profile state | `coles session stop --help` |
| Delete the local browser profile and login state | `coles session clear --help` |

### Authentication / Sign-In

| When | Run |
|---|---|
| Log in or verify/ensure the Coles session | `coles login --help` |
| Auth command group overview | `coles auth --help` |
| Open Coles and wait while the user logs in manually | `coles auth interactive --help` |
| Read-only check | `coles auth status --json` |

### Product Discovery & Adding To The Trolley

| When | Run |
|---|---|
| Products command group overview | `coles products --help` |
| Search Coles products | `coles products search --help` |
| Add a search result to the trolley by index, optional quantity | `coles products add --help` |

### Trolley / Cart Management And Checkout

`shoppingcart` is a full alias of `cart`. Every `cart` subcommand exists identically under `shoppingcart`.

| When | Run |
|---|---|
| Cart command group overview | `coles cart --help` or `coles shoppingcart --help` |
| Remove a trolley item by list index | `coles cart remove --help` |
| Set a trolley item's final quantity by index | `coles cart set-quantity --help` |
| Complete checkout and place the order, authorized only | `coles cart checkout --help` |
| Read-only cart check | `coles cart list --json` |

### Orders: Listing And Line Items

| When | Run |
|---|---|
| Orders command group overview | `coles orders --help` |
| List current or past orders | `coles orders list --help` |
| Show visible line items of a specific order id | `coles orders items --help` |
| Read-only current orders check | `coles orders list --status current --json` |

### Diagnostics

| When | Run |
|---|---|
| Save a screenshot of the current page | `coles screenshot --help` |
| Read-only capture | `coles screenshot` |

## Common Arguments

All leaf commands accept these global flags:

- `--session <name>` / `--name <name>`: session/profile name, default `$COLES_CLI_SESSION` or `default`.
- `--json`: emit the full JSON payload instead of the short human-readable summary.
- `-h` / `--help`: show help.

## Workflow Patterns

- First-time sign-in: `auth status` -> if not logged in -> `login --interactive --wait --timeout 300` -> complete login in the Camoufox window -> re-run `auth status`.
- Standard shopping flow: `products search` -> `products add` -> `cart list` -> optionally `cart set-quantity` / `cart remove` -> `cart checkout` only if authorized -> `orders list --status current`.
- Free resources without losing login: `coles session stop`.
- Reset everything: `coles session clear`.

## Safety

Use the authenticated browser session already owned by the user. Do not ask for passwords, tokens, cookies, or other credentials.

Do not run checkout (`cart checkout`) unless the user explicitly authorizes placing a real Coles order. Checkout places a real order and may charge the user.

For any action that modifies the trolley or an order, proceed only when the user's instruction is explicit and unambiguous.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
