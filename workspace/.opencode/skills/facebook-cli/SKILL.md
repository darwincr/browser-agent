---
name: facebook-cli
description: Use Facebook through `facebook-cli` whenever the user asks to search inside Facebook, inspect Facebook content, send Facebook messages, manage Facebook interactions, or perform actions inside Facebook on the user's behalf.
license: MIT
compatibility: opencode
metadata:
  command: facebook-cli
---

## Use This Skill For

Use this skill when the user asks to do any of these in Facebook:

- Search inside Facebook.
- Inspect Facebook profiles, pages, groups, marketplace listings, posts, comments, messages, or notifications.
- Send Facebook messages or reply to conversations.
- Perform Facebook actions on behalf of the user, such as reacting, commenting, posting, joining, leaving, following, unfollowing, saving, sharing, or updating content.

Do not skip this skill just because the user does not mention the exact command name. If the task requires Facebook data or actions, use this skill.

The Docker image is configured to install `facebook-cli` from `darwincr/facebook-cli` when that repository has an installable default branch. Before using this skill, verify the command exists:

```bash
command -v facebook-cli
facebook-cli --help
```

If the command is unavailable, explain that `facebook-cli` is not installed in the current image and that the image must be rebuilt after the repository contains installable code.

## Required Preflight

Before searching Facebook, reading Facebook data, sending messages, or performing any Facebook action, always verify that Facebook is signed in.

First inspect available auth commands if needed:

```bash
facebook-cli --help
```

Then run the Facebook auth status command exposed by the CLI. Prefer this command when available:

```bash
facebook-cli auth status --json
```

If the auth status shows the user is not signed in, do not continue with the requested Facebook action. Start the CLI's interactive login flow and wait for the user to complete it. Prefer this command when available:

```bash
facebook-cli login --interactive --wait --timeout 300
```

After login completes, run the auth status command again. Only proceed when the status confirms an authenticated session.

If login cannot be completed, explain that Facebook is not signed in and the requested Facebook action cannot be performed yet. Do not ask for or print credentials.

## Action Safety

Read-only Facebook tasks, such as search and inspection, can proceed after auth is confirmed.

For write actions, such as sending messages, posting, commenting, reacting, joining, leaving, following, unfollowing, sharing, deleting, or changing settings, restate the exact action and target before executing unless the user has already provided explicit, unambiguous instructions in the current turn.

## Boundaries

Prefer read-only commands unless the user explicitly asks for a write action.

Do not ask for or print credentials. Use the user's authenticated browser session.

## File Outputs

If the user asks for files for another agent, write final files to the A2A outputs directory mentioned in the prompt. Do not only paste file contents into chat when a downstream agent needs a file artifact.
