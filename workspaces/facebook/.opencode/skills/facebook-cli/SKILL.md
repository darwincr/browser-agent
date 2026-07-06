---
name: facebook-cli
description: "Operate Facebook through the facebook-cli command line tool. Drive a real browser profile to read profiles/search/posts/comments, create posts and comments, and read/send Messenger messages. USE FOR: reading the Facebook feed, search Facebook groups/pages/marketplace, list Messenger threads, send Facebook message, create Facebook post, comment on Facebook post, drive Facebook from CLI. DO NOT USE FOR: Instagram, WhatsApp, or other social media."
license: MIT
compatibility: opencode
metadata:
  command: facebook-cli
---

# facebook-cli Operator Skill

`facebook-cli` drives a real Playwright Chromium browser profile to operate Facebook. It never reads credentials. Login is done manually in the browser window. State is stored locally under `~/.facebook-cli/profiles/<session>`.

## Use This Skill For

Use this skill for Facebook tasks, including reading the feed; searching Facebook profiles, pages, groups, Marketplace, videos, and reels; inspecting profiles/pages and visible recent posts; reading post comments; creating posts and comments; listing Messenger threads; reading Messenger conversations; sending Facebook messages; and user-directed Facebook actions.

Do not skip this skill just because the user did not mention `facebook-cli`. If the task requires Facebook data or actions, use this skill.

## Core Conventions

- Use `facebook-cli <command> [flags]` from this workspace.
- Always append `--json` when available to get structured, parseable output. Without it the CLI prints a short human summary only.
- Target a specific profile with `--session <name>` or `--name <name>`, or set `$FACEBOOK_CLI_SESSION`. Default session is `default`.
- Options and defaults may change. Run the relevant `--help` before constructing any command you are unsure about.
- Errors in JSON include `ok: false` and `error.type`. When `error.type` is `interactive_authentication_required` or `checkpoint_challenge`, use the returned `next_command` when present.
- Commands reuse a per-session background Chromium worker. The first command starts the browser; later commands queue through one local socket so only one action touches the session at a time.
- Relevant env vars: `FACEBOOK_CLI_HOME`, `FACEBOOK_CLI_HEADLESS`, `FACEBOOK_CLI_LOG`, and `FACEBOOK_CLI_MESSENGER_PIN`.

## Browser State Checks

These commands are cheap, safe, read-only, and should be run frequently, especially before any action.

| Goal | Command | Notes |
|---|---|---|
| Check login state before acting | `facebook-cli auth status --json` | Returns `authenticated`, `state` (`logged_in`, `login_required`, or `checkpoint_required`), and when authenticated the visible `name` and `profile_url`. Always run this first when session state is unknown. |
| Verify session non-interactively | `facebook-cli login --json` | Confirms the current session; returns `interactive_authentication_required` if a login form is visible, without opening a window. |

If `auth status` is not authenticated, or any command returns `interactive_authentication_required` / `checkpoint_challenge`, run:

```bash
facebook-cli login --interactive --wait --timeout 300
```

Complete login/checkpoint manually in the opened browser. Then re-run `facebook-cli auth status --json` to confirm.

## Command Discovery

| When | Run |
|---|---|
| You are unfamiliar with the CLI, want the full command list, or need to confirm a command exists | `facebook-cli --help` |

For every task below, run the listed `--help` command first to get exact positional args, flags, choices, and defaults, then run the real command with `--json` when available.

### Authentication & Manual Login

| Run | To learn about |
|---|---|
| `facebook-cli login --help` | `login` with `--interactive`, `--wait`, `--timeout` |
| `facebook-cli auth --help` | The `auth` group and its subcommands |
| `facebook-cli auth status --help` | `auth status` read-only state check |
| `facebook-cli auth interactive --help` | `auth interactive` with `--wait`, `--timeout` |

### Session & Profile Lifecycle

| Run | To learn about |
|---|---|
| `facebook-cli session --help` | The `session` group |
| `facebook-cli session clear --help` | Delete the local browser profile for a session |

### Looking Up A Person Or Page

| Run | To learn about |
|---|---|
| `facebook-cli profile --help` | `profile <handle>` with `--limit` for visible posts |

### Searching Facebook

| Run | To learn about |
|---|---|
| `facebook-cli search --help` | Search by query with type choices such as `top`, `groups`, `pages`, `marketplace`, `videos`, and `reels`; scoped group/page search; Marketplace location; limits |

### Reading Feed, Timeline, And Group Posts

| Run | To learn about |
|---|---|
| `facebook-cli posts --help` | The `posts` group and all subcommands |
| `facebook-cli posts feed --help` | Home feed, with `--limit` |
| `facebook-cli posts profile --help` | Profile/page timeline |
| `facebook-cli posts group --help` | Group timeline |

### Reading Comments On A Post

| Run | To learn about |
|---|---|
| `facebook-cli posts comments --help` | Visible comments for a post URL/permalink/path |

### Writing Posts And Comments

These are write actions. Confirm target and text before running.

| Run | To learn about |
|---|---|
| `facebook-cli posts create --help` | Publish a text post to feed or a group |
| `facebook-cli posts comment --help` | Add a comment to a post |

### Messenger Conversations

| Run | To learn about |
|---|---|
| `facebook-cli messages --help` | The `messages` group and all subcommands |
| `facebook-cli messages threads --help` | List conversations |
| `facebook-cli messages read --help` | Read visible messages from a thread URL/path/id or current/default thread |
| `facebook-cli messages send --help` | Send a message to a thread URL/path/id or recipient search text |

## Operating Patterns

- Before any action, run `facebook-cli auth status --json`. If not authenticated, run the recovery flow before retrying.
- Read before write. When posting, commenting, or messaging, first read the target to confirm context, then perform the write.
- Always parse `--json`; short text output is for humans only and omits fields like URLs, ids, and unread flags.
- Do not run concurrent commands against the same `--session`; the worker serializes commands per session.
- Selectors are conservative on purpose. If a read returns fewer items than expected, the visible browser window in non-headless mode is the debugging surface.

## Raw Browser Tasks

For ad-hoc Facebook tasks such as "open this URL and report the title", first look for a `facebook-cli` verb that can inspect the requested object or URL. The authenticated Facebook session is only reachable through `facebook-cli` or a documented workspace helper; the generic Browser Harness browser is a different browser and may be logged out.

For the basic "open Facebook and report title/url" diagnostic, use the workspace helper:

```bash
python .opencode/open_fb.py
```

## Filesystem Boundaries

Use the installed CLI help, this skill file, and workspace helpers as the contract. Do not inspect package source, site source code, `.env` files, browser profiles, or other files outside this workspace. If behavior is unclear, run the relevant `facebook-cli --help` command and report the missing operation.

## Safety

Prefer read-only commands unless the user explicitly asks for a write action.

For write actions, such as sending messages, posting, commenting, reacting, joining, leaving, following, unfollowing, sharing, deleting, or changing settings, proceed only when the user's instruction is explicit and unambiguous. Otherwise, restate the exact action and target before executing.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
