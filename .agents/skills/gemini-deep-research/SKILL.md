---
name: gemini-deep-research
description: Use the Browser Agent A2A service for deep research through a browser pre-authenticated to the Gemini web app. Use for Gemini web app research, multi-step investigation, synthesis, source gathering, report drafting, and generic browser research through the shared browser-agent-cli.
compatibility: "Requires Python 3.10+ and network access to the Browser Agent A2A endpoint. The shared CLI is standard-library only and reads the repository-root .env by default."
---

# Gemini Deep Research

Use this skill when the task should be researched through the Gemini web app or requires deep browser-based investigation. The Browser Agent has access to a web browser pre-authenticated to Gemini and can perform research over A2A using the shared CLI.

- Shared CLI: `./browser-agent-cli`
- Shared env file: `./.env`
- Output: compact minified JSON on stdout

## Common Uses

- Ask Gemini web app to perform deep research
- Gather, compare, and synthesize web sources
- Produce research briefs, summaries, and reports
- Investigate companies, markets, products, technologies, or topics
- Use a long-running browser task when research may take time
- Perform generic browser research with a remote authenticated browser

## CLI Utilities

This skill uses one portable utility:

- `./browser-agent-cli`: standard-library Python A2A client for Browser Agent

Available subcommands:

- `card`: fetch compact A2A agent card details
- `models`: list provider/model IDs configured on the A2A server
- `submit`: submit a message/task and wait up to 110 seconds by default (under the common 120s shell-tool timeout)
- `status`: fetch current state for a task ID
- `wait`: poll a task ID until completion, failure, cancellation, rejection, or timeout

## Sub-Agent Behavior

Treat `browser-agent-cli` like a sub-agent. A submitted task may keep running after the local CLI returns.

- If output contains `terminal:false`, `nextAction:"wait"`, or `recoverable:true`, do not submit the same request again.
- Run the returned `nextCommand` if present, or run `./browser-agent-cli wait TASK_ID` using the same `taskId`.
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

Check the agent card:

```bash
./browser-agent-cli card
```

Submit a deep research task:

```bash
./browser-agent-cli submit "Use the pre-authenticated Gemini web app for deep research on the current state of residential battery prices in Australia. Return sources and a concise synthesis."
```

Submit a long task and poll it:

```bash
./browser-agent-cli submit --no-wait "Use Gemini deep research to compare the top CRM platforms for a small MSP."
./browser-agent-cli wait TASK_ID
```

Attach a file:

```bash
./browser-agent-cli submit --file ./brief.pdf "Use this brief as context for Gemini deep research and return a report."
```

## Fallback

Use the `browser-harness` skill only if you need direct local Chrome/CDP mechanics such as screenshots, coordinate clicks, dialogs, downloads, uploads, iframe debugging, shadow DOM work, or raw CDP. Otherwise prefer this Browser Agent A2A helper.

Treat `./.env` as sensitive if it contains a bearer token. Do not print token values.
