---
name: linkedin-cli
description: "Operate the linkedin-cli tool that drives LinkedIn through a real authenticated browser session. USE FOR: any task involving LinkedIn, searching people/jobs/posts, reading or messaging profiles, managing connection requests, reading and replying to notifications, creating/editing/scheduling/deleting personal or company page posts, replying to company page inbox threads, saving/applying to jobs. DO NOT USE FOR: anything not related to LinkedIn."
license: MIT
compatibility: opencode
metadata:
  command: linkedin-cli
---

# linkedin-cli Operator Skill

`linkedin-cli` drives LinkedIn through a real, logged-in Chromium session. Every command emits one JSON object on stdout with `--json`; logs and errors go to stderr. There is no API key and no SaaS. It acts as the session owner's own LinkedIn account.

## Use This Skill For

Use this skill for LinkedIn tasks, including searching people, jobs, and posts; reading profiles; checking connection status; sending connection requests; reading and sending direct messages with optional attachments; listing inbox threads; inspecting jobs; saving, unsaving, and applying to jobs; reading, creating, editing, deleting, scheduling, and engaging with posts; reading and acting on notifications; and administering company pages, page posts, scheduled page posts, and page inbox threads.

Do not skip this skill just because the user did not mention `linkedin-cli`. If the task requires LinkedIn data or actions, use this skill.

## Core Conventions

- Use `linkedin-cli <verb> [args...] --json` from this workspace.
- Use `--session <name>` or `$LINKEDIN_CLI_SESSION` to select the authenticated browser session. The updated CLI commonly uses session `work`; use the current workspace/session convention unless the user specifies otherwise.
- Always use `--json` when consuming output programmatically. Without it you get a short human summary.
- Commands against the same session are serialized by a local lock. Do not run parallel live-browser commands against the same session.
- stdout carries only the result; logs and `error: ...` lines are on stderr. Stable error types include `checkpoint_challenge`, `authentication`, `profile_inaccessible`, `skip_profile`, and `connection_limit`.
- Thread IDs, activity IDs, job IDs, comment IDs, and notification indexes returned by one command are the handles you pass into the next. There is no implicit session state between commands.

## Functional Command Map

Every verb supports `<verb> --help` for exact arguments, choices, and result shape. Do not guess arguments. When a task matches a category below, run the listed `--help` command first, then run the verb with `--json`.

### Authentication & Session

| Intent | Verb | Mode |
|---|---|---|
| Confirm who the session is logged in as | `linkedin-cli whoami --help` | read |
| Login or clear a checkpoint | `linkedin-cli login --help` | write |
| Launch and bind a persistent browser for legacy/debug workflows | `linkedin-cli session open --help` | read |
| Stop the worker or legacy launcher | `linkedin-cli session close --help` | read |

### People: Discover, Inspect, Reach Out

| Intent | Verb | Mode |
|---|---|---|
| Find members by keyword and facets such as network degree, geo, company, school, industry, language, verified, or open-to-volunteer | `linkedin-cli search --help` | read |
| Read a member's full profile | `linkedin-cli profile --help` | read |
| Check connection state with a member | `linkedin-cli status --help` | read |
| Send a connection request | `linkedin-cli connect --help` | write |
| Send a direct message with optional attachments | `linkedin-cli message --help` | write |
| List recent personal messaging conversations | `linkedin-cli inbox --help` | read |
| Read the message thread with a member or by inbox thread id | `linkedin-cli thread --help` | read |

Typical loop: `search` -> `profile` / `status` -> `message` / `thread`, or `inbox` -> `thread`.

### Jobs: Search, Track, Apply

| Intent | Verb | Mode |
|---|---|---|
| Search jobs by keyword, location, date, type, remote, easy-apply | `linkedin-cli jobs search --help` | read |
| List saved / in-progress / applied / archived job cards | `linkedin-cli jobs saved --help` | read |
| Show full structured details for one job | `linkedin-cli jobs show --help` | read |
| Save a job | `linkedin-cli jobs save --help` | write |
| Unsave one or more jobs | `linkedin-cli jobs unsave --help` | write |
| Start or submit an Easy Apply application | `linkedin-cli jobs apply --help` | write |

### Personal Posts: Read

| Intent | Verb | Mode |
|---|---|---|
| List recent posts by a member | `linkedin-cli posts profile --help` | read |
| Search posts by keyword, sort, date, content type, author facets | `linkedin-cli posts search --help` | read |
| Show one post's content and aggregate engagement | `linkedin-cli posts show --help` | read |
| Show engagement and visible comments for a post | `linkedin-cli posts engagement --help` | read |
| List visible comments on a post | `linkedin-cli posts comments --help` | read |

### Personal Posts: Write, Edit, Delete

| Intent | Verb | Mode |
|---|---|---|
| Create a post with optional images, documents, or poll | `linkedin-cli posts create --help` | write |
| Edit the text of an already-published post | `linkedin-cli posts edit --help` | write |
| Delete a post by id, URN, or URL | `linkedin-cli posts delete --help` | write |

### Personal Posts: Scheduling

Scheduled posts are addressed by a 1-based index from `posts scheduled`.

| Intent | Verb | Mode |
|---|---|---|
| Save LinkedIn's draft prompt | `linkedin-cli posts draft --help` | write |
| Schedule a text post for a specific local datetime | `linkedin-cli posts schedule --help` | write |
| Update scheduled time and/or text by index | `linkedin-cli posts update-schedule --help` | write |
| List scheduled posts | `linkedin-cli posts scheduled --help` | read |
| Cancel a scheduled post by index | `linkedin-cli posts cancel --help` | write |

### Personal Posts & Comments: Engagement

| Intent | Verb | Mode |
|---|---|---|
| React to a post | `linkedin-cli posts react --help` | write |
| Reply to a visible comment on a post | `linkedin-cli posts comment-reply --help` | write |
| React to a visible comment on a post | `linkedin-cli posts comment-react --help` | write |

### Notifications

Replies and reactions target a 1-based index from the `notifications` list.

| Intent | Verb | Mode |
|---|---|---|
| List visible notifications with activity/comment ids | `linkedin-cli notifications --help` | read |
| Reply to the comment referenced by a notification | `linkedin-cli notifications reply --help` | write |
| React to the post/comment referenced by a notification | `linkedin-cli notifications react --help` | write |

### Company Pages: Discovery & Content Read

`<company-id>` is the numeric id from a company admin URL. Discover it with `page list` first.

| Intent | Verb | Mode |
|---|---|---|
| List company pages this session can administer | `linkedin-cli page list --help` | read |
| List published company page posts | `linkedin-cli page posts --help` | read |
| Show one company page post by activity id or URL | `linkedin-cli page post --help` | read |
| List scheduled company page posts | `linkedin-cli page post-scheduled --help` | read |

### Company Pages: Content Management

Scheduled posts are addressed by a 1-based index from `page post-scheduled`.

| Intent | Verb | Mode |
|---|---|---|
| Create a text post as the page with optional media/poll | `linkedin-cli page post-create --help` | write |
| Edit the text of a published page post | `linkedin-cli page post-edit --help` | write |
| Schedule a page text post | `linkedin-cli page post-schedule --help` | write |
| Update scheduled page post time and/or text by index | `linkedin-cli page post-update-schedule --help` | write |
| Cancel a scheduled page post by index | `linkedin-cli page post-cancel --help` | write |
| Delete a page post by activity id or URL | `linkedin-cli page post-delete --help` | write |

### Company Pages: Inbox

| Intent | Verb | Mode |
|---|---|---|
| List visible page inbox threads | `linkedin-cli page inbox --help` | read |
| Read messages in a page inbox thread | `linkedin-cli page thread --help` | read |
| Reply to a page inbox thread with optional attachments | `linkedin-cli page reply --help` | write |

## Raw Browser Tasks

For ad-hoc LinkedIn tasks such as "open this URL and report the title", first look for a `linkedin-cli` verb that can inspect the requested object or URL. The authenticated LinkedIn session is only reachable through `linkedin-cli`; the generic Browser Harness browser is a different browser and may be logged out.

If no `linkedin-cli` verb exists for the raw browser action, say that the CLI does not expose that authenticated browser operation instead of switching silently to Browser Harness and reporting unauthenticated state.

## Filesystem Boundaries

Use the installed CLI help and this skill file as the contract. Do not inspect package source, site source code, `.env` files, browser profiles, or other files outside this workspace. If behavior is unclear, run the relevant `linkedin-cli --help` command and report the missing operation.

## Safety

Read-only verbs are safe to run for inspection: `whoami`, `search`, `profile`, `status`, `inbox`, `thread`, `notifications`, `jobs search`, `jobs saved`, `jobs show`, `posts profile`, `posts search`, `posts show`, `posts engagement`, `posts comments`, `posts scheduled`, `page list`, `page posts`, `page post`, `page post-scheduled`, `page inbox`, and `page thread`.

Write verbs change LinkedIn state. Before running any write verb, confirm the specific action with the user, especially `posts delete`, `page post-delete`, `posts cancel`, `page post-cancel`, `connect`, `message`, `page reply`, and `jobs apply --submit`.

Do not ask for passwords, tokens, cookies, or other credentials.

## File Outputs

If the user asks for files for another agent, write final files to the requested output directory. Do not only paste file contents into chat when a downstream agent needs a file artifact.
