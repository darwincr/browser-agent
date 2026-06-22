#!/usr/bin/env python3
"""Small A2A test client for the local opencode-a2a server."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from typing import Any


TERMINAL_TASK_STATES = frozenset({
    "TASK_STATE_COMPLETED",
    "TASK_STATE_CANCELED",
    "TASK_STATE_FAILED",
    "TASK_STATE_REJECTED",
})


def main() -> int:
    env = load_dotenv()
    parser = argparse.ArgumentParser(description="Send test A2A requests to opencode-a2a.")
    parser.add_argument("message", nargs="?", default="Explain what this repository does.")
    parser.add_argument("--url", default=env.get("A2A_PUBLIC_URL", "http://localhost:18000"), help="Base server URL")
    parser.add_argument("--token", default=None, help="Bearer token for A2A auth")
    parser.add_argument("--stream", action="store_true", help="Use /v1/message:stream SSE endpoint")
    parser.add_argument("--json-rpc", action="store_true", help="Use JSON-RPC SendMessage endpoint")
    parser.add_argument("--context-id", help="Optional A2A contextId for conversation continuity")
    parser.add_argument("--session-id", help="Optional metadata.shared.session.id")
    parser.add_argument("--model-provider", help="Optional metadata.shared.model.providerID")
    parser.add_argument("--model", help="Optional metadata.shared.model.modelID")
    parser.add_argument("--directory", help="Optional metadata.opencode.directory")
    parser.add_argument("--file", action="append", default=[], help="Attach a local file as an inline A2A raw Part")
    parser.add_argument("--async", dest="async_submit", action="store_true", help="Submit with returnImmediately and poll until a terminal task state")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Seconds between polls (default 2)")
    parser.add_argument("--poll-timeout", type=float, default=300.0, help="Maximum seconds to poll before giving up (default 300)")
    args = parser.parse_args()

    payload = build_payload(args)
    endpoint = endpoint_for(args)
    token = args.token or bearer_token_from_env(env)
    if not token:
        print("Missing bearer token. Set A2A_STATIC_AUTH_CREDENTIALS in .env or pass --token.", file=sys.stderr)
        return 1

    if args.async_submit and args.stream:
        print("--async cannot be combined with --stream.", file=sys.stderr)
        return 1

    try:
        if args.async_submit:
            return async_submit_and_poll(args, endpoint, token, payload)
        if args.stream:
            stream_response(endpoint, token, payload)
        else:
            response = post_json(endpoint, token, payload)
            print(json.dumps(response, indent=2, sort_keys=True))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} {exc.reason}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1
    return 0


def load_dotenv() -> dict[str, str]:
    env = dict(os.environ)
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return env

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


def bearer_token_from_env(env: dict[str, str]) -> str | None:
    credentials = env.get("A2A_STATIC_AUTH_CREDENTIALS")
    if not credentials:
        return None

    try:
        parsed = json.loads(credentials)
    except json.JSONDecodeError as exc:
        print(f"Invalid A2A_STATIC_AUTH_CREDENTIALS JSON in .env: {exc}", file=sys.stderr)
        return None

    if not isinstance(parsed, list):
        print("A2A_STATIC_AUTH_CREDENTIALS must be a JSON array.", file=sys.stderr)
        return None

    for credential in parsed:
        if not isinstance(credential, dict):
            continue
        if credential.get("scheme") == "bearer" and isinstance(credential.get("token"), str):
            return credential["token"]
    return None


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
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

    if args.json_rpc:
        method = "SendStreamingMessage" if args.stream else "SendMessage"
        return {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": {"message": message},
        }

    return {"message": message}


def file_part_from_path(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Attached file does not exist or is not a file: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "filename": path.name,
        "mediaType": mime_type,
        "raw": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


def endpoint_for(args: argparse.Namespace) -> str:
    base_url = args.url.rstrip("/")
    if args.json_rpc:
        return f"{base_url}/"
    if args.stream:
        return f"{base_url}/v1/message:stream"
    return f"{base_url}/v1/message:send"


def post_json(url: str, token: str, payload: dict[str, Any]) -> Any:
    request = make_request(url, token, payload)
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "A2A-Version": "1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))


def stream_response(url: str, token: str, payload: dict[str, Any]) -> None:
    request = make_request(url, token, payload)
    with urllib.request.urlopen(request, timeout=300) as response:
        event = "message"
        data_lines: list[str] = []
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
            if not line:
                print_sse_event(event, data_lines)
                event = "message"
                data_lines = []
                continue
            if line.startswith("event:"):
                event = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())

        print_sse_event(event, data_lines)


def print_sse_event(event: str, data_lines: list[str]) -> None:
    if not data_lines:
        return
    for data in data_lines:
        print(f"\n[event: {event}]")
        try:
            print(json.dumps(json.loads(data), indent=2, sort_keys=True))
        except json.JSONDecodeError:
            print(data)


def async_submit_and_poll(args: argparse.Namespace, endpoint: str, token: str, payload: dict[str, Any]) -> int:
    inject_return_immediately(payload, args.json_rpc)
    response = post_json(endpoint, token, payload)
    task_id = extract_task_id(response, args.json_rpc)
    if not task_id:
        print(json.dumps(response, indent=2, sort_keys=True))
        print("Could not extract task id; cannot poll.", file=sys.stderr)
        return 1
    print(f"Submitted task {task_id}. Polling every {args.poll_interval}s (timeout {args.poll_timeout}s).", file=sys.stderr)
    base_url = args.url.rstrip("/")
    deadline = time.monotonic() + args.poll_timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print(f"Polling timed out after {args.poll_timeout}s.", file=sys.stderr)
            return 1
        time.sleep(min(args.poll_interval, remaining))
        task = fetch_task(base_url, token, task_id, args.json_rpc)
        state = task.get("status", {}).get("state", "UNKNOWN")
        print(f"[poll] state={state}", file=sys.stderr)
        if state in TERMINAL_TASK_STATES:
            print(json.dumps(task, indent=2, sort_keys=True))
            return 0


def inject_return_immediately(payload: dict[str, Any], json_rpc: bool) -> None:
    container = payload.setdefault("params", {}) if json_rpc else payload
    configuration = container.setdefault("configuration", {})
    configuration["returnImmediately"] = True


def extract_task_id(response: Any, json_rpc: bool) -> str | None:
    container = response.get("result", response) if json_rpc else response
    if isinstance(container, dict):
        task = container.get("task")
        if isinstance(task, dict):
            return task.get("id")
    return None


def fetch_task(base_url: str, token: str, task_id: str, json_rpc: bool) -> dict[str, Any]:
    if json_rpc:
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "GetTask",
            "params": {"id": task_id},
        }
        response = post_json(f"{base_url}/", token, payload)
        return response.get("result", response)
    return get_json(f"{base_url}/v1/tasks/{task_id}", token)


def make_request(url: str, token: str, payload: dict[str, Any]) -> urllib.request.Request:
    body = json.dumps(payload).encode("utf-8")
    return urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "A2A-Version": "1.0",
            "Accept": "text/event-stream" if url.endswith("message:stream") else "application/json",
        },
        method="POST",
    )


if __name__ == "__main__":
    raise SystemExit(main())
