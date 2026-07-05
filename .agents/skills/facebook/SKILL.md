---
name: facebook
description: Use the Browser Agent A2A service for Facebook tasks in a pre-authenticated browser. Use for Facebook page, group, marketplace, post, profile, event, social research, and generic Facebook browsing workflows through the shared browser-agent-cli.
compatibility: "Requires Python 3.10+ and network access to the Browser Agent A2A endpoint. The shared CLI is standard-library only and reads the repository-root .env by default."
---

# Facebook

Use this skill when the task involves Facebook in a browser that is already authenticated. The work is delegated to Browser Agent over A2A using the shared CLI.

- Shared CLI: `./browser-agent-cli`
- Shared env file: `./.env`
- Output: compact minified JSON on stdout
- By default, use the repository-root `.env` local Docker server. Only use `--env-file .env.coolify` when the user explicitly wants the production Coolify server.

## Common Uses

- Research Facebook pages, groups, posts, profiles, and events
- Inspect public or account-visible Facebook information
- Search Marketplace or community content when appropriate
- Summarize social activity, posts, comments, or event details
- Navigate Facebook using the remote pre-authenticated browser

## CLI Utilities

This skill uses one portable utility:

- `./browser-agent-cli`: standard-library Python A2A client for Browser Agent

Available subcommands:

- `card`: fetch compact A2A agent card details
- `models`: list provider/model IDs configured on the A2A server
- `submit`: submit a message/task and wait up to 110 seconds by default (under the common 120s shell-tool timeout)
- `status`: fetch current state for a task ID
- `wait`: poll a task ID until completion, failure, cancellation, rejection, or timeout
- `download`: download artifact files from a task ID, artifact URL, or `/artifacts/...` path using the same `.env` / auth settings

## Sub-Agent Behavior

Treat `browser-agent-cli` like a sub-agent. A submitted task may keep running after the local CLI returns.

- If output contains `terminal:false`, `nextAction:"wait"`, or `recoverable:true`, do not submit the same request again.
- Run the returned `nextCommand` if present, or run `./browser-agent-cli wait TASK_ID` using the same `taskId` and the same connection flags (`--env-file`, `--url`, `--token`) used for submit.
- Backend worker timeouts such as `BACKEND_REQUEST_TIMEOUT_STILL_POLL_EXISTING_TASK` mean poll the same task; they do not mean the user's request should be restarted.
- Default waits are kept below common coding-agent tool timeouts, so a long task can require multiple `wait` calls.
- Only start a new `submit` if the existing task reaches a true terminal failure and there is no `recoverable:true` guidance.

## Avoiding Duplicate Submissions

A `submit` creates the task on the backend the moment its HTTP POST succeeds — **before** any waiting. The CLI writes an acknowledgement to **stderr** the instant that happens, so it can never be lost to a later timeout:

```
{"event":"submitted","ok":true,"taskId":"816e842c-9657-44a7-8b79-346f11a91cdf","contextId":"f2256a20-..."}
```

Because the task exists from that point on, a second `submit` starts a **second** task. Do not let that happen.

- If a `submit` (or `wait`) is killed by the shell tool timeout or returns no stdout, the task was almost certainly still created. Read the captured stderr for the `{"event":"submitted",...}` line, recover the `taskId`, and run `./browser-agent-cli wait TASK_ID`. Do **not** `submit` again.
- Only resubmit when there is no `submitted` ack on stderr **and** no taskId in stdout — for example the POST itself failed with an HTTP/URL error. When you do resubmit, say so and explain why no prior task exists.
- For long tasks, prefer `submit --no-wait` to obtain the taskId immediately, then poll with `wait TASK_ID`.
- The default submit/wait windows are 110 seconds so the CLI returns before the common 120s shell-tool timeout; a long task simply needs several `wait` calls.

## Usage

Every `submit` must target the Facebook workspace with `--directory facebook`. The service has no default workspace and rejects a submit without a directory.

Check the agent card:

```bash
./browser-agent-cli card
```

Check the production Coolify agent card only when explicitly needed:

```bash
./browser-agent-cli --env-file .env.coolify card
```

Submit a Facebook task:

```bash
./browser-agent-cli submit --directory facebook "Use the pre-authenticated Facebook browser to inspect this page and summarize recent posts."
```

Submit a long task and poll it:

```bash
./browser-agent-cli submit --directory facebook --no-wait "Research these Facebook groups and summarize relevant recent discussions."
./browser-agent-cli wait TASK_ID
```

If submit used `--env-file .env.coolify`, wait/status calls must use the same env file, or use the CLI-returned `nextCommand`.

Attach a file:

```bash
./browser-agent-cli submit --directory facebook --file ./pages.txt "Use Facebook to research these pages and summarize findings."
```

Download returned artifacts without using `curl`:

```bash
./browser-agent-cli download TASK_ID --output-dir ./artifacts
./browser-agent-cli download /artifacts/msg-123/outputs/report.md --output-dir ./artifacts
```

If submit used `--env-file .env.coolify`, download calls must use the same env file unless the returned artifact URL is public and unauthenticated.

## Fallback

Use the `browser-harness` skill only if you need direct local Chrome/CDP mechanics such as screenshots, coordinate clicks, dialogs, downloads, uploads, iframe debugging, shadow DOM work, or raw CDP. Otherwise prefer this Browser Agent A2A helper.

Treat `./.env` as sensitive if it contains a bearer token. Do not print token values.
