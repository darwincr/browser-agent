---
name: screen-recording
description: Use `take-screenshot`, `start-recording`, and `stop-recording` to capture the browser or XFCE desktop when the user asks to inspect, record, observe, review, debug, or preserve what the browser is doing visually.
license: MIT
compatibility: opencode
metadata:
  screenshot_command: take-screenshot
  start_command: start-recording
  stop_command: stop-recording
---

## Use This Skill For

Use this skill when the user asks to capture or inspect what is happening in the browser, desktop, VNC/noVNC session, Playwright browser, or any browser-based tool visually.

Prefer a screenshot for quick visual inspection. Use recording only when motion, a flow, or a longer-running process needs to be preserved.

Use it proactively when a task is easier to verify visually rather than relying only on logs or CLI output, especially for browser automation, login flows, visual regressions, page loading problems, modal dialogs, navigation failures, or unexpected UI behavior.

## Commands

Every command requires an output folder as its first argument.

Take a screenshot:

```bash
take-screenshot /workspaces/a2a-tasks/<task-id>/outputs
```

Start a recording:

```bash
start-recording /workspaces/a2a-tasks/<task-id>/outputs
```

Stop the recording, passing the same folder:

```bash
stop-recording /workspaces/a2a-tasks/<task-id>/outputs
```

## Output Folder

The screenshot PNG (for `take-screenshot`) and the recording MP4, log, and PID metadata (for `start-recording`) are all written inside the output folder you provide. Filenames are generated automatically with a timestamp.

When handling an A2A task, use the **task outputs directory** from the *"A2A file handling context"* of the request — it looks like `/workspaces/a2a-tasks/<task-id>/outputs`. Files written there are returned to the caller as A2A artifacts.

If you omit the folder, the command exits with an error reminding you to pass the task outputs directory.

Optional environment variable:

```bash
SCREEN_RECORDING_FRAMERATE=15
```

## Workflow

1. Identify the task outputs directory from the A2A file handling context.
2. For a still visual check, run `take-screenshot <output-folder>`.
3. For a flow, run `start-recording <output-folder>`.
4. Perform the browser or desktop actions that need observation.
5. Run `stop-recording <output-folder>` with the same folder.
6. Report the screenshot or recording path to the user and mention any relevant log path if troubleshooting is needed.

## Safety And Cleanup

Always stop the recording once the observed action is complete. Do not leave background recording processes running.

If a command fails, inspect the recording log before retrying. Do not delete recordings unless the user asks or the file is clearly a failed temporary artifact created by the current task.

Screen recordings may capture private browser content. Only start recording when it directly helps with the user's request, and avoid recording longer than necessary.
