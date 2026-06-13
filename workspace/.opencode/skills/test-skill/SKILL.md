---
name: test-skill
description: Test skill for verifying that OpenCode discovers project-local skills in the container workspace.
license: MIT
compatibility: opencode
metadata:
  purpose: discovery-test
---

## What This Skill Does

This is a minimal project-local OpenCode skill used to verify skill discovery.

When loaded, respond with this exact confirmation sentence:

```text
The test-skill skill was loaded successfully from the workspace.
```

## When To Use

Use this skill when the user asks to test OpenCode skill discovery, verify custom skills, or load `test-skill`.

## Expected Behavior

- Confirm that the skill was loaded.
- Mention that it came from the workspace project skill path.
- Do not perform any file edits unless explicitly asked.
