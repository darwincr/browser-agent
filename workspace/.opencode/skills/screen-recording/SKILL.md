---
name: screen-recording
description: Use `start-recording` and `stop-recording` to capture the browser or XFCE desktop when the user asks to record, observe, review, debug, or preserve what the browser is doing visually.
license: MIT
compatibility: opencode
metadata:
  start_command: start-recording
  stop_command: stop-recording
---

## Use This Skill For

Use this skill when the user asks to capture or inspect what is happening in the browser, desktop, VNC/noVNC session, Playwright browser, or any browser-based tool visually.

Use it proactively when a task is easier to verify by watching the browser rather than relying only on logs or CLI output, especially for browser automation, login flows, visual regressions, page loading problems, modal dialogs, navigation failures, or unexpected UI behavior.

## Commands

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
start-recording /workspace/browser-recording.mp4
```

## Output Files

By default, `start-recording` writes the MP4 file, log, and PID metadata in the current directory.

Optional environment variables:

```bash
SCREEN_RECORDING_FRAMERATE=15
SCREEN_RECORDING_OUTPUT_DIR=/workspace/recordings
SCREEN_RECORDING_LOG_FILE=/workspace/recordings/screen-recording.log
SCREEN_RECORDING_PID_FILE=/workspace/recordings/screen-recording.pid
```

Prefer writing recordings under `/workspace` so the user and downstream agents can access them. Use task-specific names such as `/workspace/recordings/login-debug.mp4` when multiple recordings may be created.

## Workflow

1. Choose an output path before starting if the recording should be kept.
2. Run `start-recording`, optionally with the chosen MP4 path.
3. Perform the browser or desktop actions that need observation.
4. Run `stop-recording` from the same working directory, or use the same PID/log environment variables if they were customized.
5. Report the recording path to the user and mention any relevant log path if troubleshooting is needed.

## Safety And Cleanup

Always stop the recording once the observed action is complete. Do not leave background recording processes running.

If a command fails, inspect the recording log before retrying. Do not delete recordings unless the user asks or the file is clearly a failed temporary artifact created by the current task.

Screen recordings may capture private browser content. Only start recording when it directly helps with the user's request, and avoid recording longer than necessary.
