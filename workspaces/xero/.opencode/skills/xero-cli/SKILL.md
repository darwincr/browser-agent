---
name: xero-cli
description: Use Xero through `xero-cli` whenever the user asks to manage Xero expenses, mileage claims, receipts, Payroll timesheets, pay periods, or to inspect the current Xero page through a real browser session.
license: MIT
compatibility: opencode
metadata:
  command: xero-cli
---

## Use This Skill For

Use this skill for Xero tasks, including listing and creating expenses and mileage claims, editing expense details, opening and inspecting Payroll timesheets, listing valid pay periods, viewing/editing/approving/reverting/deleting timesheets, checking authentication state, taking screenshots, and debugging the visible Xero page.

Do not skip this skill just because the user did not mention `xero-cli`. If the task explicitly asks for Xero expenses, receipts, mileage, timesheets, pay periods, or the Xero page, use this skill.

## Core Rule

Keep this skill minimal. Do not rely on memorized command examples beyond auth/session basics. Before running any task-specific Xero command, inspect the CLI's current help so the agent uses the installed CLI contract:

```bash
xero-cli --help
xero-cli <command> --help
xero-cli <command> <subcommand> --help
```

Prefer `--json` whenever available for structured output. Redirect stdout yourself if the user asks for a file.

`xero-cli` drives Xero through a persistent Camoufox browser profile with a background worker per session. Pick a session/profile with `--session <name>` (alias `--name`).

## Help Entry Points

Use these installed help entry points to discover current syntax on demand. The list mirrors the installed CLI surface (top-level verbs plus every grouped subcommand). Run the narrowest relevant `--help` before execution.

Top-level verbs:

```bash
xero-cli login --help
xero-cli screenshot --help
```

`session` group (local browser session state):

```bash
xero-cli session --help
xero-cli session clear --help
xero-cli session stop --help
```

`auth` group (authentication state and MFA):

```bash
xero-cli auth --help
xero-cli auth status --help
xero-cli auth mfa --help
```

`expenses` group (expense and mileage claims):

```bash
xero-cli expenses --help
xero-cli expenses list --help
xero-cli expenses create --help
xero-cli expenses mileage --help
xero-cli expenses edit-detail --help
```

`timesheets` group (Xero Payroll timesheets):

```bash
xero-cli timesheets --help
xero-cli timesheets open --help
xero-cli timesheets list --help
xero-cli timesheets periods --help
xero-cli timesheets create --help
xero-cli timesheets view --help
xero-cli timesheets edit --help
xero-cli timesheets revert-to-draft --help
xero-cli timesheets approve --help
xero-cli timesheets delete --help
```

`debug` group (visible page inspection without printing secrets):

```bash
xero-cli debug --help
xero-cli debug page --help
```

For any new or renamed subcommand not listed above, run `xero-cli <group> --help` first and use the installed CLI as the source of truth.

## Sign-In

Before listing expenses, editing expense details, opening timesheets, or any write action, verify authentication:

```bash
xero-cli auth status --json
```

If the session is not authenticated, start interactive login and wait for the user to complete it in the Camoufox window, including any MFA and the "Trust this device" step. Do not ask for or print credentials.

```bash
xero-cli login --interactive --manual-timeout 300
```

After login, run `xero-cli auth status --json` again. Proceed only when authentication is confirmed.

If Xero presents an MFA prompt during login and the user supplies a code, submit it with:

```bash
xero-cli auth mfa <code>
```

By default this selects "Trust/Remember this device" if Xero offers it; pass `--no-trust-device` to skip that.

If the browser worker needs to be closed without deleting login state, stop the session:

```bash
xero-cli session stop
```

Use `xero-cli session clear` only when the saved profile and login state should be deleted.

## Basic Operation Pattern

For each user request:

1. Confirm authentication with `xero-cli auth status --json`.
2. Run `xero-cli --help` if you do not know the current command group.
3. Run the narrowest relevant `--help`, such as `xero-cli expenses --help`, `xero-cli timesheets --help`, or a deeper subcommand help.
4. Execute the command using the flags shown by the current help output.
5. Use `--json` when available and summarize results for the user.

## Common Task Shapes

- List recent expenses or timesheets: `xero-cli expenses list --json` / `xero-cli timesheets list --json` (both accept `--limit`).
- Look up valid pay periods before creating a timesheet: `xero-cli timesheets periods --employee "<name>" --json` (`--employee` is required).
- Find a specific timesheet to view/edit/approve/revert/delete: use `--employee`, `--period`, and `--status` filters on `timesheets view/edit/revert-to-draft/approve/delete`.
- Open and fill an expense without submitting: `xero-cli expenses create ...` without `--submit`.
- Open and fill a timesheet without saving: `xero-cli timesheets create ...` without `--save`, or `timesheets edit ...` without `--save`.
- Inspect the current Xero page when a result is unclear: `xero-cli debug page --json` (optionally with `--url`, `--click-button`, `--limit`).
- Capture a still image: `xero-cli screenshot --output <path>`.

## Safety

Use the authenticated browser session already owned by the user. Do not ask for passwords, tokens, cookies, MFA codes, or other credentials.

Prefer read-only commands (`list`, `view`, `periods`, `auth status`) unless the user explicitly asks for a write action.

These actions change Xero state and must only run when the user's instruction is explicit and unambiguous:

- Submitting an expense or mileage claim for approval: the `--submit` flag on `expenses create` / `expenses mileage`. Without `--submit`, the form is only opened and filled.
- Approving a timesheet: `xero-cli timesheets approve --confirm`.
- Reverting a timesheet to draft: `xero-cli timesheets revert-to-draft --confirm`.
- Deleting a timesheet: `xero-cli timesheets delete --confirm`.

Without `--confirm`, the matching timesheet is identified and reported but not changed. Restate the exact action and target before running any of these with `--confirm`.

After a write action, retrieve the resulting state with a read command (for example `xero-cli expenses list --json` or `xero-cli timesheets list --json`) and report it.

## Filesystem Boundaries

Use the installed CLI help and this skill file as the contract. Do not inspect package source, site source code, `.env` files, browser profiles, or other files outside this workspace. If behavior is unclear, run the relevant `xero-cli --help` command and report the missing operation.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
