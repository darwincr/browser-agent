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

Take a screenshot:

```bash
take-screenshot
```

Take a screenshot with an explicit output path:

```bash
take-screenshot ./screenshots/page-state.png
```

Start a recording:

```bash
start-recording
```

Stop a recording from the same working directory where recording was started:

```bash
stop-recording
```

Start with an explicit output path when the recording should be easy to find or preserved for another agent:

```bash
start-recording ./recordings/login-debug.mp4
```

## Output Files

By default, `take-screenshot` writes a PNG file in the current directory. By default, `start-recording` writes the MP4 file, log, and PID metadata in the current directory. The current directory is your workspace (for example `/workspaces/xero`), which the agent is allowed to write to.

Optional environment variables:

```bash
SCREEN_RECORDING_FRAMERATE=15
SCREEN_RECORDING_OUTPUT_DIR=./recordings
SCREEN_RECORDING_LOG_FILE=./recordings/screen-recording.log
SCREEN_RECORDING_PID_FILE=./recordings/screen-recording.pid
SCREENSHOT_OUTPUT_DIR=./screenshots
```

Write screenshots and recordings inside your workspace directory (the default current directory) so they stay within the paths the agent is allowed to access. When a downstream agent needs the file as an A2A artifact, write it into the task `outputs` directory provided in the request instead. Use task-specific names such as `./screenshots/expense-state.png` or `./recordings/login-debug.mp4` when multiple captures may be created.

## Workflow

1. For a still visual check, run `take-screenshot`, optionally with the chosen PNG path.
2. For a flow, choose an output path before starting if the recording should be kept.
3. Run `start-recording`, optionally with the chosen MP4 path.
4. Perform the browser or desktop actions that need observation.
5. Run `stop-recording` from the same working directory, or use the same PID/log environment variables if they were customized.
6. Report the screenshot or recording path to the user and mention any relevant log path if troubleshooting is needed.

## Safety And Cleanup

Always stop the recording once the observed action is complete. Do not leave background recording processes running.

If a command fails, inspect the recording log before retrying. Do not delete recordings unless the user asks or the file is clearly a failed temporary artifact created by the current task.

Screen recordings may capture private browser content. Only start recording when it directly helps with the user's request, and avoid recording longer than necessary.
