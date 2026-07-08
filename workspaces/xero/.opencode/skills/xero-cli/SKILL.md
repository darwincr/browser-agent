---
name: xero-cli
description: Operate and validate the xero-cli for browser-driven Xero workflows across expenses, mileage, timesheets, sales, purchases, payroll, auth, and live page debugging. Use when an agent needs to run any xero-cli command or discover the current command surface through --help while the CLI is still evolving.
---

# xero-cli

Use this skill when working with the `xero-cli` CLI. The CLI is installed system-wide and under active development, so do not rely on hardcoded command examples beyond help discovery. Always inspect the relevant `--help` output before choosing flags for an operation.

## Project Context

- CLI entry point: `xero-cli` (installed system-wide)
- Browser automation: Camoufox with Playwright sync API
- Persistent profile: `~/.xero-user-cli/profiles/<session>`
- Background browser worker: UNIX socket worker
- Environment config: `.env` resolved independent of the launch directory.
  Priority: `XERO_USER_CLI_ENV_FILE` (explicit path) → nearest `.env` walking up
  from the current working directory → `~/.xero-user-cli/.env`.
- Required environment variables (`XERO_USER`, `SECRET_XERO_PASSWORD`) are loaded
  from those `.env` locations. Empty/whitespace env vars are treated as unset so
  injected placeholders can be filled from `.env`; real non-empty env vars win.

## Operating Principles

- Prefer JSON output for agent workflows when the command supports it.
- Keep create/edit workflows non-destructive unless the user explicitly asks to submit/save/approve.
- Do not use submit/save/approve flags unless the user explicitly requested a real submission.
- Do not clear the browser profile unless the user explicitly asks, because it can remove trusted-device/session state.
- Stopping the worker (`xero-cli session stop`) is safe when needed to reload code; it does not delete the profile and is different from clearing the session.
- If source code changes are made while a worker is running, stop the worker so the next CLI invocation reloads the updated code.
- Do not clear the session as a first response to auth issues; preserving trusted-device state is valuable.
- Never print secrets, passwords, MFA codes, or `.env` contents.
- Run the relevant `--help` command before using a command area, because flags may change while this CLI is being developed.

## Help Discovery Map

Run these help commands to learn the current supported syntax for each functional area. The CLI is under active development, so always inspect the relevant `--help` output before choosing flags.

### Top-Level Capability Discovery

```bash
xero-cli --help
```

Use this first when unsure what command groups exist. Current groups: `session`, `login`, `screenshot`, `auth`, `expenses`, `timesheets`, `sales`, `purchases`, `payroll`, `accounting`, `debug`.

### Session Management

```bash
xero-cli session --help
xero-cli session clear --help
xero-cli session stop --help
```

`clear` deletes the local browser profile for a session; `stop` stops the background browser worker without deleting the profile.

### Authentication And MFA

```bash
xero-cli login --help
xero-cli auth --help
xero-cli auth status --help
xero-cli auth mfa --help
```

### Screenshots

```bash
xero-cli screenshot --help
```

### Expenses And Mileage

```bash
xero-cli expenses --help
xero-cli expenses list --help
xero-cli expenses create --help
xero-cli expenses view-detail --help
xero-cli expenses edit-detail --help
xero-cli expenses delete-detail --help
xero-cli expenses mileage --help
xero-cli expenses mileage create --help
xero-cli expenses mileage view-detail --help
xero-cli expenses mileage edit-detail --help
xero-cli expenses mileage delete-detail --help
```

### Timesheets

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

### Sales

```bash
xero-cli sales --help
xero-cli sales invoices --help
xero-cli sales invoices open --help
xero-cli sales invoices list --help
xero-cli sales invoices create --help
xero-cli sales payment-links --help
xero-cli sales payment-links open --help
xero-cli sales payment-links list --help
xero-cli sales payment-services --help
xero-cli sales payment-services open --help
xero-cli sales payment-services list --help
xero-cli sales quotes --help
xero-cli sales quotes open --help
xero-cli sales quotes list --help
xero-cli sales products --help
xero-cli sales products open --help
xero-cli sales products list --help
xero-cli sales customers --help
xero-cli sales customers open --help
xero-cli sales customers list --help
```

### Purchases

```bash
xero-cli purchases --help
xero-cli purchases bills --help
xero-cli purchases bills open --help
xero-cli purchases bills list --help
xero-cli purchases payments --help
xero-cli purchases payments open --help
xero-cli purchases payments list --help
xero-cli purchases purchase-orders --help
xero-cli purchases purchase-orders open --help
xero-cli purchases purchase-orders list --help
xero-cli purchases suppliers --help
xero-cli purchases suppliers open --help
xero-cli purchases suppliers list --help
```

### Payroll

```bash
xero-cli payroll --help
xero-cli payroll employees --help
xero-cli payroll employees open --help
xero-cli payroll employees list --help
xero-cli payroll leave --help
xero-cli payroll leave open --help
xero-cli payroll leave list --help
```

### Accounting

```bash
xero-cli accounting --help
xero-cli accounting accounts --help
xero-cli accounting accounts list --help
```

### Live Page Debugging

```bash
xero-cli debug --help
xero-cli debug page --help
```

The debug output is intended to expose visible page structure such as headings, buttons, labels, inputs, links, and body text. Do not add logging that exposes credentials, MFA codes, or other secrets.

## Authentication Command Reference

These are the validated stable auth flows. For evolving flags, still cross-check the relevant `--help` output above.

### Login (non-interactive primary flow)

```bash
xero-cli login --json
```

Expected behavior:

- Opens the neutral Xero homepage URL for the configured organisation
  (`$XERO_APP_BASE_URL/homepage`, defaulting to `https://go.xero.com/app/!M0777/homepage`)
- Fills username from `XERO_USER`
- Fills password from `SECRET_XERO_PASSWORD`
- Detects whether the user is authenticated
- Detects MFA and returns a structured `mfa_required` response
- Keeps the browser open in the background worker if MFA is required

### MFA continuation

```bash
xero-cli auth mfa CODE [--no-trust-device] [--timeout SECONDS] --json
```

Expected behavior:

- Reuses the existing worker browser session
- Inserts the MFA code into the current MFA page
- Selects the trust/remember device option if Xero offers it (unless `--no-trust-device`)
- Waits up to `--timeout` seconds (default 120) for Xero to finish
- Continues to the neutral homepage
- Returns authenticated JSON when successful

### Status inspection (read-only)

```bash
xero-cli auth status --json
```

### Manual fallback

```bash
xero-cli login --interactive --manual-timeout 300
```

Use only when the automated flow cannot handle a new Xero authentication/checkpoint variant.

### Authentication success criteria

Before feature work, verify:

```bash
xero-cli session clear
xero-cli login --json
```

If MFA is required:

```bash
xero-cli auth mfa CODE --json
```

Expected successful response:

```json
{
  "ok": true,
  "authenticated": true,
  "url": "https://go.xero.com/app/!yj48m/homepage",
  "state": "logged_in"
}
```
