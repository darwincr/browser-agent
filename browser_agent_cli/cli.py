#!/usr/bin/env python3
"""Agent-friendly CLI client for browser-agent's A2A API."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import shlex
import sys
import time
import urllib.error
from urllib.parse import quote as parse_quote
import urllib.request
from typing import Any


TERMINAL_TASK_STATES = frozenset({
    "TASK_STATE_COMPLETED",
    "TASK_STATE_CANCELED",
    "TASK_STATE_FAILED",
    "TASK_STATE_REJECTED",
})
SUCCESS_TASK_STATES = frozenset({"TASK_STATE_COMPLETED"})
DEFAULT_SUBMIT_WAIT_SECONDS = 240.0
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_WAIT_TIMEOUT = 240.0
BACKEND_TIMEOUT_PREFIXES = ("OpenCode request timed out",)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    env = load_dotenv(getattr(args, "env_file", None))
    command = args.command or "submit"

    try:
        if command == "card":
            print_json(compact_card(fetch_card(args, env)))
            return 0
        if command == "models":
            return models(args, env)
        if command == "submit":
            return submit(args, env)
        if command == "status":
            return status(args, env)
        if command == "wait":
            return wait(args, env)
    except urllib.error.HTTPError as exc:
        print_json({"ok": False, "error": f"HTTP {exc.code} {exc.reason}", "body": response_body(exc)})
        return 1
    except urllib.error.URLError as exc:
        print_json({"ok": False, "error": f"Request failed: {exc.reason}"})
        return 1

    parser.error(f"Unknown command: {command}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    common_parser = argparse.ArgumentParser(add_help=False)
    add_common_arguments(common_parser)

    parser = argparse.ArgumentParser(
        prog="browser-agent-cli",
        description="Interact with browser-agent over A2A.",
        parents=[common_parser],
    )
    subparsers = parser.add_subparsers(dest="command")
    add_submit_parser(subparsers, common_parser)
    add_status_parser(subparsers, common_parser)
    add_wait_parser(subparsers, common_parser)
    subparsers.add_parser("card", parents=[common_parser], help="Fetch compact A2A agent card details")
    add_models_parser(subparsers, common_parser)
    return parser


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--env-file",
        default=argparse.SUPPRESS,
        help="Path to env file with A2A_PUBLIC_URL and A2A_STATIC_AUTH_CREDENTIALS (default: .env)",
    )
    parser.add_argument("--url", default=argparse.SUPPRESS, help="Base A2A server URL; defaults to A2A_PUBLIC_URL from --env-file")
    parser.add_argument("--token", default=argparse.SUPPRESS, help="Bearer token; defaults to first bearer token in A2A_STATIC_AUTH_CREDENTIALS")


def add_submit_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common_parser: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser("submit", parents=[common_parser], help="Submit a task and wait briefly by default")
    add_message_arguments(parser)
    parser.add_argument("--wait-seconds", type=float, default=DEFAULT_SUBMIT_WAIT_SECONDS, help="Seconds to wait for completion (default 240)")
    parser.add_argument("--no-wait", action="store_true", help="Return immediately after task submission")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Seconds between polls while waiting (default 2)")


def add_status_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common_parser: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser("status", parents=[common_parser], help="Fetch current task state")
    parser.add_argument("task_id")


def add_wait_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common_parser: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser("wait", parents=[common_parser], help="Wait for task completion")
    parser.add_argument("task_id")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Seconds between polls (default 2)")
    parser.add_argument("--poll-timeout", type=float, default=DEFAULT_WAIT_TIMEOUT, help="Maximum seconds to wait (default 240)")


def add_models_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common_parser: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser("models", parents=[common_parser], help="List provider/model IDs from the A2A server")
    parser.add_argument("--provider", help="Only list models for this provider ID")


def add_message_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("message", nargs="?", default="Explain what this repository does.")
    parser.add_argument("--context-id", help="Optional A2A contextId for conversation continuity")
    parser.add_argument("--session-id", help="Optional metadata.shared.session.id")
    parser.add_argument("--model-provider", help="Optional metadata.shared.model.providerID")
    parser.add_argument("--model", help="Optional metadata.shared.model.modelID")
    parser.add_argument("--directory", help="Optional metadata.opencode.directory")
    parser.add_argument("--file", action="append", default=[], help="Attach a local file as an inline A2A raw Part")


def submit(args: argparse.Namespace, env: dict[str, str]) -> int:
    token = require_token(args, env)
    payload = build_submit_payload(args)
    response = post_json(f"{base_url(args, env)}/v1/message:send", token, payload)
    task = extract_task(response)
    task_id = task.get("id")
    if not task_id:
        print_json({"ok": False, "error": "Could not extract taskId from submit response"})
        return 1

    wait_seconds = 0.0 if args.no_wait else max(args.wait_seconds, 0.0)
    if wait_seconds > 0 and not is_terminal(task):
        task = poll_task(base_url(args, env), token, task_id, args.poll_interval, wait_seconds)

    result = compact_task(task, ok=True)
    print_json(result)
    return task_exit_code(result, timeout_is_error=False)


def status(args: argparse.Namespace, env: dict[str, str]) -> int:
    token = require_token(args, env)
    task = fetch_task(base_url(args, env), token, args.task_id)
    result = compact_task(task, ok=True)
    print_json(result)
    return task_exit_code(result, timeout_is_error=False)


def wait(args: argparse.Namespace, env: dict[str, str]) -> int:
    token = require_token(args, env)
    task = poll_task(base_url(args, env), token, args.task_id, args.poll_interval, args.poll_timeout)
    result = compact_task(task, ok=True)
    if not result["terminal"]:
        result["recoverable"] = True
        result["errorType"] = result.get("errorType") or "LOCAL_WAIT_TIMEOUT_TASK_STILL_RUNNING"
        result["waitWindowExpired"] = True
        result["agentInstruction"] = result.get("agentInstruction") or (
            "The local wait window ended before the Browser Agent task reached a final result. "
            "Do not start a duplicate task. Poll this exact taskId again with the wait command."
        )
        add_wait_guidance(result, "The local wait window expired; poll this same taskId again, do not resubmit the original request.")
    print_json(result)
    return task_exit_code(result, timeout_is_error=True)


def models(args: argparse.Namespace, env: dict[str, str]) -> int:
    token = require_token(args, env)
    query = f"?provider={parse_quote(args.provider)}" if args.provider else ""
    response = get_json(f"{base_url(args, env)}/models{query}", token)
    print_json(response)
    return 0


def load_dotenv(env_file: str | None) -> dict[str, str]:
    env = dict(os.environ)
    if not env_file:
        for env_path in default_env_paths():
            if env_path.exists():
                return load_dotenv_file(env, env_path)
        return env

    env_path = Path(env_file).expanduser()
    if not env_path.exists():
        return env

    return load_dotenv_file(env, env_path)


def default_env_paths() -> list[Path]:
    script_path = Path(__file__).resolve()
    return [
        Path.cwd() / ".env",
        script_path.parent / ".env",
        script_path.parent.parent / ".env",
    ]


def load_dotenv_file(env: dict[str, str], env_path: Path) -> dict[str, str]:
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        env.setdefault(key, value)
    return env


def require_token(args: argparse.Namespace, env: dict[str, str]) -> str:
    token = bearer_token(args, env)
    if not token:
        print_json({"ok": False, "error": "Missing bearer token. Set A2A_STATIC_AUTH_CREDENTIALS in --env-file or pass --token."})
        raise SystemExit(1)
    return token


def bearer_token(args: argparse.Namespace, env: dict[str, str]) -> str | None:
    token = getattr(args, "token", None)
    if token:
        return token
    credentials = env.get("A2A_STATIC_AUTH_CREDENTIALS")
    if not credentials:
        return None

    try:
        parsed = json.loads(credentials)
    except json.JSONDecodeError as exc:
        print_json({"ok": False, "error": f"Invalid A2A_STATIC_AUTH_CREDENTIALS JSON: {exc}"})
        return None

    if not isinstance(parsed, list):
        print_json({"ok": False, "error": "A2A_STATIC_AUTH_CREDENTIALS must be a JSON array"})
        return None

    for credential in parsed:
        if isinstance(credential, dict) and credential.get("scheme") == "bearer" and isinstance(credential.get("token"), str):
            return credential["token"]
    return None


def base_url(args: argparse.Namespace, env: dict[str, str]) -> str:
    return (getattr(args, "url", None) or env.get("A2A_PUBLIC_URL") or "http://localhost:18000").rstrip("/")


def build_submit_payload(args: argparse.Namespace) -> dict[str, Any]:
    message: dict[str, Any] = {
        "messageId": f"msg-{int(time.time() * 1000)}",
        "role": "ROLE_USER",
        "parts": [{"text": args.message}],
    }
    for file_path in args.file:
        message["parts"].append(file_part_from_path(Path(file_path)))
    if args.context_id:
        message["contextId"] = args.context_id

    metadata: dict[str, Any] = {}
    if args.session_id:
        metadata.setdefault("shared", {}).setdefault("session", {})["id"] = args.session_id
    if args.model or args.model_provider:
        model = metadata.setdefault("shared", {}).setdefault("model", {})
        if args.model_provider:
            model["providerID"] = args.model_provider
        if args.model:
            model["modelID"] = args.model
    if args.directory:
        metadata.setdefault("opencode", {})["directory"] = args.directory
    if metadata:
        message["metadata"] = metadata

    return {"message": message, "configuration": {"returnImmediately": True}}


def file_part_from_path(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Attached file does not exist or is not a file: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "filename": path.name,
        "mediaType": mime_type,
        "raw": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


def fetch_card(args: argparse.Namespace, env: dict[str, str]) -> Any:
    return get_json(f"{base_url(args, env)}/.well-known/agent-card.json", bearer_token(args, env), required_token=False)


def fetch_task(url: str, token: str, task_id: str) -> dict[str, Any]:
    task = get_json(f"{url}/v1/tasks/{task_id}", token)
    return task if isinstance(task, dict) else {}


def poll_task(url: str, token: str, task_id: str, poll_interval: float, timeout: float) -> dict[str, Any]:
    task = fetch_task(url, token, task_id)
    deadline = time.monotonic() + timeout
    while not is_terminal(task):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return task
        time.sleep(min(max(poll_interval, 0.1), remaining))
        task = fetch_task(url, token, task_id)
    return task


def post_json(url: str, token: str, payload: dict[str, Any]) -> Any:
    request = make_json_request(url, token, payload)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str, token: str | None, *, required_token: bool = True) -> Any:
    headers = {
        "Accept": "application/json",
        "A2A-Version": "1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif required_token:
        raise ValueError("Bearer token is required")
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def make_json_request(url: str, token: str, payload: dict[str, Any]) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "A2A-Version": "1.0",
            "Accept": "application/json",
        },
        method="POST",
    )


def extract_task(response: Any) -> dict[str, Any]:
    if isinstance(response, dict) and isinstance(response.get("task"), dict):
        return response["task"]
    return response if isinstance(response, dict) else {}


def compact_card(card: Any) -> dict[str, Any]:
    if not isinstance(card, dict):
        return {"ok": False, "error": "Invalid agent card response"}
    return {
        "ok": True,
        "name": card.get("name"),
        "version": card.get("version"),
        "url": first_interface_url(card),
        "streaming": card.get("capabilities", {}).get("streaming"),
        "inputModes": card.get("defaultInputModes", []),
        "outputModes": card.get("defaultOutputModes", []),
    }


def compact_task(task: dict[str, Any], *, ok: bool) -> dict[str, Any]:
    state = task.get("status", {}).get("state")
    text = extract_text(task)
    backend_timeout = is_backend_timeout(text)
    terminal = state in TERMINAL_TASK_STATES and not backend_timeout
    result: dict[str, Any] = {
        "ok": ok,
        "taskId": task.get("id"),
        "contextId": task.get("contextId"),
        "state": state,
        "terminal": terminal,
    }

    if text:
        result["text"] = text

    if backend_timeout:
        add_backend_timeout_guidance(result)
    elif not terminal:
        add_wait_guidance(result, "Task is still running. Do not submit a duplicate task; wait on this taskId.")

    artifacts = compact_artifacts(task)
    if artifacts:
        result["artifacts"] = artifacts

    return {key: value for key, value in result.items() if value is not None}


def is_backend_timeout(text: str | None) -> bool:
    return bool(text and any(text.startswith(prefix) for prefix in BACKEND_TIMEOUT_PREFIXES))


def add_backend_timeout_guidance(result: dict[str, Any]) -> None:
    result["recoverable"] = True
    result["errorType"] = "BACKEND_REQUEST_TIMEOUT_STILL_POLL_EXISTING_TASK"
    result["agentInstruction"] = (
        "The Browser Agent backend timed out while waiting for the underlying worker, but this task may still be running. "
        "Do not start a new task with the same request. Poll this exact taskId with the wait command, then report the final result."
    )
    add_wait_guidance(result, "Poll this same taskId; do not resubmit the original request.")


def add_wait_guidance(result: dict[str, Any], message: str) -> None:
    task_id = result.get("taskId")
    if not isinstance(task_id, str) or not task_id:
        return
    result["nextAction"] = "wait"
    result["nextCommand"] = f"{shlex.quote(sys.argv[0] or 'browser-agent-cli')} wait {shlex.quote(task_id)}"
    result["nextInstruction"] = message


def compact_artifacts(task: dict[str, Any]) -> list[dict[str, str]]:
    compact: list[dict[str, str]] = []
    for artifact in task.get("artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        for part in artifact.get("parts", []) or []:
            if not isinstance(part, dict):
                continue
            item = {
                "name": artifact.get("name") or artifact.get("artifactId") or part.get("filename"),
                "filename": part.get("filename"),
                "url": part.get("url"),
                "mediaType": part.get("mediaType"),
            }
            compact_item = {key: value for key, value in item.items() if isinstance(value, str) and value}
            if compact_item.get("url") or compact_item.get("filename"):
                compact.append(compact_item)
    return compact


def extract_text(task: dict[str, Any]) -> str | None:
    texts: list[str] = []
    for artifact in task.get("artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        for part in artifact.get("parts", []) or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    if texts:
        return "\n".join(texts)

    status_message = task.get("status", {}).get("message", {})
    if isinstance(status_message, dict):
        for part in status_message.get("parts", []) or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                texts.append(part["text"])
    return "\n".join(texts) if texts else None


def is_terminal(task: dict[str, Any]) -> bool:
    if is_backend_timeout(extract_text(task)):
        return False
    return task.get("status", {}).get("state") in TERMINAL_TASK_STATES


def task_exit_code(result: dict[str, Any], *, timeout_is_error: bool) -> int:
    state = result.get("state")
    if result.get("recoverable"):
        return 0
    if result.get("ok") is False:
        return 4 if timeout_is_error and not result.get("terminal") else 1
    if state in SUCCESS_TASK_STATES or not result.get("terminal"):
        return 0
    return 3


def first_interface_url(card: dict[str, Any]) -> str | None:
    for interface in card.get("supportedInterfaces", []) or []:
        if isinstance(interface, dict) and isinstance(interface.get("url"), str):
            return interface["url"]
    return None


def response_body(exc: urllib.error.HTTPError) -> str | None:
    body = exc.read().decode("utf-8", errors="replace")
    return body or None


def print_json(value: Any) -> None:
    print(json.dumps(value, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
