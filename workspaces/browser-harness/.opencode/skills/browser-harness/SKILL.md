---
name: browser-harness
description: Use Browser Harness for generic browser interaction only when no dedicated website skill is available.
license: MIT
compatibility: opencode
metadata:
  command: browser-harness
---

## Use This Skill For

Use this skill for generic browser interaction when no dedicated website skill exists, or when the user explicitly asks to use the generic browser.

Prefer dedicated website skills first. For Gemini, Facebook, LinkedIn, and Coles tasks, use the dedicated skill even if Browser Harness could technically operate the site.

## Runtime

The generic Chromium browser is started automatically in the visible noVNC desktop on `DISPLAY=:1`.

Browser Harness connects to the local CDP endpoint:

```text
http://127.0.0.1:9222
```

The persistent browser profile is:

```text
~/.browser-harness/profiles/default
```

Do not start another Chromium process with the same profile. If the browser exits, the container launcher restarts it automatically.

## Basic Usage

Invoke Browser Harness as `browser-harness` and use heredocs for multi-line commands:

```bash
browser-harness <<'PY'
print(page_info())
PY
```

Helpers are pre-imported. The harness attaches to the running Chromium CDP endpoint through `BU_CDP_URL`; do not pass a browser id for normal local usage.

For first navigation, use `new_tab(url)`, not `goto_url(url)`:

```bash
browser-harness <<'PY'
new_tab("https://example.com")
wait_for_load()
print(page_info())
PY
```

## Page Workflow

- Use `capture_screenshot()` first when visual state matters.
- For coordinate clicks, capture a screenshot, choose coordinates, call `click_at_xy(x, y)`, then capture another screenshot.
- After navigation, call `wait_for_load()`.
- If the current tab is stale or internal, call `ensure_real_tab()`.
- Use `js(...)` for DOM inspection or extraction when coordinates are the wrong tool.
- Raw CDP is available with `cdp("Domain.method", ...)`.

## Diagnostics

If Browser Harness cannot connect, run:

```bash
browser-harness --doctor
curl -s http://127.0.0.1:9222/json/version
```

If Chromium asks for remote-debugging permission in the visible browser, stop and ask the user to approve it in noVNC, then retry.

## Safety

Default to read-only browsing, extraction, and observation.

Ask before actions that submit forms, send messages, post content, purchase items, place orders, make payments, delete data, change account settings, or otherwise modify external services unless the user's instruction is explicit and unambiguous.

Do not ask for passwords, tokens, cookies, or other credentials. Use only browser sessions already owned by the user or interactive login flows the user completes directly.
