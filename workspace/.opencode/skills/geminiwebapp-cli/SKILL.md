---
name: geminiwebapp-cli
description: Use Gemini Web App through `geminiwebapp-cli` whenever the user asks to ask Gemini, use Gemini models, compare with Gemini, send prompts with attached files, run Gemini Deep Research, inspect Gemini chats, or generate Gemini images, music, or videos.
license: MIT
compatibility: opencode
metadata:
  command: geminiwebapp-cli
---

## Use This Skill For

Use this skill when the user asks to do any of these through Gemini or Gemini Web App:

- Ask Gemini a question or send a prompt to a Gemini model.
- Compare this agent's answer with Gemini's answer.
- Send Gemini files, images, PDFs, screenshots, audio, video, or other attachments with a prompt.
- Analyze an attached file using Gemini.
- Run Gemini Deep Research.
- Inspect, continue, or create Gemini chats.
- Generate images, music, or videos with Gemini.

Do not skip this skill just because the user does not mention the exact command name. If the task is better answered by Gemini, explicitly asks for Gemini, or involves an attached file that the current model cannot inspect directly, use this skill.

Do not tell the user that they could use the Gemini Web App skill and ask whether they want that. If the user's request requires Gemini, invoke this skill yourself after the required auth check. The user's request is already permission to perform the analysis.

The Docker image installs the `geminiwebapp-cli` command from `darwincr/geminiwebapp-cli`.

## Required Preflight

Before creating a chat, uploading a file, starting Deep Research, or generating media, always verify that Gemini is signed in:

```bash
geminiwebapp-cli auth status --json
```

If the auth status shows the user is not signed in, do not continue with the requested Gemini action. Start an interactive login and wait for the user to complete it:

```bash
geminiwebapp-cli login --interactive --wait --timeout 300
```

After login completes, run `geminiwebapp-cli auth status --json` again. Only proceed when the status confirms an authenticated session.

If login cannot be completed, explain that Gemini is not signed in and the requested Gemini action cannot be performed yet. Do not ask for or print credentials.

## Commands

Start a new Gemini chat:

```bash
geminiwebapp-cli chats new --text "Prompt text" --json
```

Start a new Gemini chat with a file attachment:

```bash
geminiwebapp-cli chats new --text "Analyze this file" --file /path/to/file.pdf --json
```

Ask Gemini to describe an image:

```bash
geminiwebapp-cli chats new --text "Describe this image in detail. What do you see?" --file /path/to/image.jpg --json
```

Start Gemini Deep Research:

```bash
geminiwebapp-cli chats new --tool deep-research --model pro --wait --text "Research prompt" --json
```

## File Outputs

If the user asks for files for another agent, write final files to the A2A outputs directory mentioned in the prompt. Do not only paste file contents into chat when a downstream agent needs a file artifact.

## Safety

Use authenticated browser sessions already owned by the user. Do not ask for or print credentials.
