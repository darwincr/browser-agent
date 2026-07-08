---
name: facebook-cli
description: "Operate Facebook through the facebook-cli command line tool. Drive a real browser profile to read profiles/search/posts/comments, create posts and comments, and read/send Messenger messages. USE FOR: reading the Facebook feed, search Facebook groups/pages/marketplace, list Messenger threads, send Facebook message, create Facebook post, comment on Facebook post, drive Facebook from CLI. DO NOT USE FOR: Instagram, WhatsApp, or other social media."
license: MIT
compatibility: opencode
metadata:
  command: facebook-cli
---

# facebook-cli Operator Skill

`facebook-cli` drives a real Playwright Chromium browser profile to operate
Facebook. It never reads credentials; login is done manually in the browser
window. State is stored locally under `~/.facebook-cli/profiles/<session>`.

## Use This Skill For

Use this skill for Facebook tasks, including reading the feed; searching
Facebook profiles, pages, groups, Marketplace, videos, and reels; inspecting
profiles/pages and visible recent posts; reading post comments; creating posts
and comments; listing Messenger threads; reading Messenger conversations;
sending Facebook messages; and user-directed Facebook actions.

Do not skip this skill just because the user did not mention `facebook-cli`.
If the task requires Facebook data or actions, use this skill.

## Invocation

Run the installed CLI directly from this workspace:

```bash
facebook-cli <noun> <verb> [args] [flags]
```

All examples below assume this form. Append `--json` to leaf commands whenever
you need parseable output.

## Core Conventions

- Run `facebook-cli auth status --json` before acting when session state is unknown.
- Target a profile with `--session <name>` or `$FACEBOOK_CLI_SESSION`; default is `default`.
- Use `facebook-cli <noun> --help` and `facebook-cli <noun> <verb> --help` when unsure.
- Errors in JSON include `ok: false` and `error.type`. When `error.type` is `interactive_authentication_required` or `checkpoint_challenge`, use the returned `next_command` when present.
- Commands reuse one background Chromium worker per session and serialize actions for that session.
- Relevant env vars: `FACEBOOK_CLI_HOME`, `FACEBOOK_CLI_HEADLESS`, `FACEBOOK_CLI_LOG`, and `FACEBOOK_CLI_MESSENGER_PIN`.

## Auth & Session

| Goal | Command |
|---|---|
| Check login state | `facebook-cli auth status --json` |
| Verify login non-interactively | `facebook-cli auth login --json` |
| Manual login/checkpoint recovery | `facebook-cli auth login --interactive --wait --timeout 300` |
| Clear local browser profile for a session | `facebook-cli session clear --session <name> --json` |

## Profiles & Pages

| Goal | Command |
|---|---|
| Read profile/page details and visible recent posts | `facebook-cli profile read <handle> --limit 5 --json` |
| Search pages/profiles | `facebook-cli profile search <query> --limit 10 --json` |

## Groups

| Goal | Command |
|---|---|
| Read group header details | `facebook-cli group read <id-or-url> --json` |
| Search groups | `facebook-cli group search <query> --limit 10 --json` |
| Read group timeline posts | `facebook-cli group posts <id-or-url> --limit 10 --json` |

## Posts

| Goal | Command |
|---|---|
| Read a single post permalink | `facebook-cli post read <post-url> --json` |
| Search posts globally | `facebook-cli post search <query> --limit 10 --json` |
| Search posts in a group | `facebook-cli post search <query> --group <group> --limit 10 --json` |
| Search posts on a page/profile | `facebook-cli post search <query> --page <page> --limit 10 --json` |
| Create a feed post | `facebook-cli post create --text "..." --json` |
| Create a group post | `facebook-cli post create --group <group> --text "..." --json` |
| Read post comments | `facebook-cli post comments <post-url> --limit 50 --json` |
| Comment on a post | `facebook-cli post comment <post-url> --text "..." --json` |

## Feed

| Goal | Command |
|---|---|
| Read home feed posts | `facebook-cli feed read --limit 10 --json` |

## Marketplace

| Goal | Command |
|---|---|
| Search Marketplace listings | `facebook-cli marketplace search <query> --location <slug> --json` |
| Read a Marketplace listing | `facebook-cli marketplace read <item> --json` |
| Read a listing's seller details | `facebook-cli marketplace seller <item-or-profile> --json` |
| Read a listing's seller chat | `facebook-cli marketplace messages <item> --limit 20 --json` |
| Inspect seller chat without sending | `facebook-cli marketplace message <item> --text "..." --dry-run --json` |
| Message a listing's seller | `facebook-cli marketplace message <item> --text "..." --json` |

## Video & Reels

| Goal | Command |
|---|---|
| Search videos | `facebook-cli video search <query> --json` |
| Search reels | `facebook-cli reel search <query> --json` |

## Messenger

| Goal | Command |
|---|---|
| List Messenger threads | `facebook-cli thread list --limit 10 --json` |
| Read a Messenger thread | `facebook-cli thread read <target> --limit 20 --json` |
| Send a Messenger message | `facebook-cli message send <target> --text "..." --json` |

If Messenger asks for a PIN, set `FACEBOOK_CLI_MESSENGER_PIN` in the shell or
in local `.env`. Prefer shell env for temporary overrides; it takes precedence
over `.env`.

For agent logic, treat `error.type == "messenger_pin_required"` as the only
signal that a PIN is currently required. On successful Messenger commands, use
`pin_status`: `not_required` means no PIN prompt was active for that command;
`unlocked_with_env_pin` means the CLI used `FACEBOOK_CLI_MESSENGER_PIN`.
`pin_unlocked` is a compatibility boolean and should not be interpreted as
"PIN required" when false.

## Operating Patterns

- Read before write: confirm context with `post read`, `post comments`, or `thread read` before posting, commenting, or messaging.
- Use `--json` for automation; text output is a human summary.
- Do not run concurrent commands against the same `--session`.
- If a read returns fewer items than expected, use the visible browser window in non-headless mode as the debugging surface.

## Raw Browser Tasks

For ad-hoc Facebook tasks such as "open this URL and report the title", first
look for a `facebook-cli` verb that can inspect the requested object or URL.
The authenticated Facebook session is only reachable through `facebook-cli` or
a documented workspace helper; the generic Browser Harness browser is a
different browser and may be logged out.

For the basic "open Facebook and report title/url" diagnostic, use the
workspace helper:

```bash
python .opencode/open_fb.py
```

## Filesystem Boundaries

Use the installed CLI help, this skill file, and workspace helpers as the
contract. Do not inspect package source, site source code, `.env` files,
browser profiles, or other files outside this workspace. If behavior is
unclear, run the relevant `facebook-cli --help` command and report the missing
operation.

## Safety

Prefer read-only commands unless the user explicitly asks for a write action.

For write actions, such as sending messages, posting, commenting, reacting,
joining, leaving, following, unfollowing, sharing, deleting, or changing
settings, proceed only when the user's instruction is explicit and
unambiguous. Otherwise, restate the exact action and target before executing.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the
requested output directory. Do not only paste file contents into chat when a
downstream agent needs a file artifact.
