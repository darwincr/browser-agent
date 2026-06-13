#!/usr/bin/env python3
"""A2A file/artifact proxy for opencode-a2a.

The proxy keeps opencode-a2a as the task engine, while adding conventional
FilePart staging on inbound messages and Artifact FileParts for files written
by the agent.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, parse, request
import uuid


HOST = os.environ.get("A2A_FILE_PROXY_HOST", "0.0.0.0")
PORT = int(os.environ.get("A2A_FILE_PROXY_PORT", os.environ.get("A2A_PORT", "8000")))
UPSTREAM = os.environ.get("A2A_FILE_PROXY_UPSTREAM", "http://127.0.0.1:8001").rstrip("/")
PUBLIC_URL = os.environ.get("A2A_PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")
WORKSPACE_ROOT = Path(os.environ.get("OPENCODE_WORKSPACE_ROOT", "/workspace"))
TASK_ROOT = Path(os.environ.get("A2A_FILE_TASK_ROOT", str(WORKSPACE_ROOT / "a2a-tasks")))
MAX_INLINE_BYTES = int(os.environ.get("A2A_FILE_MAX_INLINE_BYTES", str(10 * 1024 * 1024)))


class ProxyError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


class A2AFileProxy(BaseHTTPRequestHandler):
    server_version = "a2a-file-proxy/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/artifacts/"):
            self.serve_artifact()
            return

        self.proxy_get()

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self.read_json_body()
            staged = prepare_payload(body)
            if wants_stream(self.path, self.headers.get("Accept")):
                self.proxy_stream_post(staged.payload)
                return
            response = upstream_post(self.path, staged.payload, self.forward_headers())
            if staged.task_id and staged.outputs_dir.exists():
                attach_artifacts(response, staged.task_id, staged.outputs_dir)
            self.send_json(response)
        except ProxyError as exc:
            self.send_json({"error": exc.message}, status=exc.status)
        except error.HTTPError as exc:
            data = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() not in {"transfer-encoding", "connection"}:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:  # pragma: no cover - defensive server boundary
            self.send_json({"error": f"proxy failed: {exc}"}, status=500)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProxyError(400, f"invalid JSON: {exc}") from exc
        if not isinstance(body, dict):
            raise ProxyError(400, "request body must be a JSON object")
        return body

    def forward_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        authorization = self.headers.get("Authorization")
        if authorization:
            headers["Authorization"] = authorization
        accept = self.headers.get("Accept")
        if accept:
            headers["Accept"] = accept
        return headers

    def proxy_get(self) -> None:
        try:
            upstream_response = request.urlopen(
                request.Request(f"{UPSTREAM}{self.path}", headers=self.forward_headers(), method="GET"),
                timeout=300,
            )
            data = upstream_response.read()
            content_type = upstream_response.headers.get("Content-Type", "application/octet-stream")
            if self.path == "/.well-known/agent-card.json":
                data, content_type = augment_agent_card(data), "application/json"
            self.send_response(upstream_response.status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except error.HTTPError as exc:
            self.send_response(exc.code)
            self.end_headers()
            self.wfile.write(exc.read())

    def proxy_stream_post(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        upstream_request = request.Request(
            f"{UPSTREAM}{self.path}",
            data=data,
            headers=self.forward_headers(),
            method="POST",
        )
        with request.urlopen(upstream_request, timeout=300) as upstream_response:
            self.send_response(upstream_response.status)
            for key, value in upstream_response.headers.items():
                if key.lower() not in {"transfer-encoding", "connection", "content-length"}:
                    self.send_header(key, value)
            self.end_headers()
            shutil.copyfileobj(upstream_response, self.wfile)

    def serve_artifact(self) -> None:
        if not artifact_auth_allowed(self.headers.get("Authorization")):
            self.send_json({"error": "missing or invalid bearer token"}, status=401)
            return

        relative = parse.unquote(self.path.removeprefix("/artifacts/")).split("?", 1)[0]
        artifact_path = (TASK_ROOT / relative).resolve()
        try:
            artifact_path.relative_to(TASK_ROOT.resolve())
        except ValueError:
            self.send_json({"error": "invalid artifact path"}, status=400)
            return

        if not artifact_path.is_file():
            self.send_json({"error": "artifact not found"}, status=404)
            return

        content_type = mimetypes.guess_type(artifact_path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(artifact_path.stat().st_size))
        self.end_headers()
        with artifact_path.open("rb") as file_obj:
            shutil.copyfileobj(file_obj, self.wfile)

    def send_json(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class StagedPayload:
    def __init__(self, payload: dict[str, Any], task_id: str | None, outputs_dir: Path | None) -> None:
        self.payload = payload
        self.task_id = task_id
        self.outputs_dir = outputs_dir


def prepare_payload(payload: dict[str, Any]) -> StagedPayload:
    message = message_from_payload(payload)
    if not message:
        return StagedPayload(payload, None, None)

    task_id = safe_name(
        str(message.get("taskId") or message.get("contextId") or message.get("messageId") or uuid.uuid4())
    )
    task_dir = TASK_ROOT / task_id
    inputs_dir = task_dir / "inputs"
    outputs_dir = task_dir / "outputs"

    file_descriptions = stage_file_parts(message, inputs_dir)
    if not file_descriptions:
        return StagedPayload(payload, task_id, outputs_dir)

    outputs_dir.mkdir(parents=True, exist_ok=True)
    instruction = build_file_instruction(inputs_dir, outputs_dir, file_descriptions)
    message.setdefault("parts", []).append({"text": instruction})
    metadata = message.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata.setdefault("a2aFileProxy", {})["taskDirectory"] = str(task_dir)

    return StagedPayload(payload, task_id, outputs_dir)


def message_from_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(payload.get("message"), dict):
        return payload["message"]
    params = payload.get("params")
    if isinstance(params, dict) and isinstance(params.get("message"), dict):
        return params["message"]
    return None


def stage_file_parts(message: dict[str, Any], inputs_dir: Path) -> list[str]:
    descriptions: list[str] = []
    for index, part in enumerate(message.get("parts", []), start=1):
        if not isinstance(part, dict) or not isinstance(part.get("file"), dict):
            continue
        file_part = part["file"]
        name = safe_name(str(file_part.get("name") or f"input-{index}"))
        path = unique_path(inputs_dir, name)
        inputs_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(file_part.get("bytes"), str):
            decoded = base64.b64decode(file_part["bytes"], validate=True)
            if len(decoded) > MAX_INLINE_BYTES:
                raise ProxyError(413, f"inline file {name} exceeds {MAX_INLINE_BYTES} bytes")
            path.write_bytes(decoded)
        elif isinstance(file_part.get("uri"), str):
            download_file(file_part["uri"], path)
        else:
            raise ProxyError(400, f"file part {name} must include bytes or uri")

        mime_type = file_part.get("mimeType") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        descriptions.append(f"- {path} ({mime_type})")
    return descriptions


def download_file(uri: str, path: Path) -> None:
    parsed = parse.urlparse(uri)
    if parsed.scheme not in {"http", "https"}:
        raise ProxyError(400, f"unsupported file uri scheme: {parsed.scheme}")
    with request.urlopen(uri, timeout=300) as response:
        with path.open("wb") as file_obj:
            shutil.copyfileobj(response, file_obj)


def build_file_instruction(inputs_dir: Path, outputs_dir: Path, files: list[str]) -> str:
    return (
        "\nA2A file handling context:\n"
        f"The incoming A2A FileParts have been staged under `{inputs_dir}`.\n"
        "Input files:\n"
        + "\n".join(files)
        + "\nIf you produce files for another agent, write them under "
        f"`{outputs_dir}`. Files in that directory will be returned as A2A artifacts."
    )


def attach_artifacts(response: Any, task_id: str, outputs_dir: Path) -> None:
    task = task_from_response(response)
    if not isinstance(task, dict):
        return
    artifacts = task.setdefault("artifacts", [])
    if not isinstance(artifacts, list):
        return

    for file_path in sorted(path for path in outputs_dir.rglob("*") if path.is_file()):
        relative = file_path.relative_to(outputs_dir)
        artifact_id = safe_name(str(relative)).replace("/", "-")
        artifacts.append(
            {
                "artifactId": artifact_id,
                "name": file_path.name,
                "description": f"File produced by the agent: {relative}",
                "parts": [
                    {
                        "file": {
                            "name": file_path.name,
                            "mimeType": mimetypes.guess_type(file_path.name)[0] or "application/octet-stream",
                            "uri": f"{PUBLIC_URL}/artifacts/{task_id}/outputs/{parse.quote(str(relative))}",
                        }
                    }
                ],
            }
        )


def task_from_response(response: Any) -> dict[str, Any] | None:
    if not isinstance(response, dict):
        return None
    if isinstance(response.get("result"), dict):
        return response["result"]
    if isinstance(response.get("task"), dict):
        return response["task"]
    if "status" in response or "artifacts" in response:
        return response
    return None


def upstream_post(path: str, payload: dict[str, Any], headers: dict[str, str]) -> Any:
    data = json.dumps(payload).encode("utf-8")
    upstream_request = request.Request(f"{UPSTREAM}{path}", data=data, headers=headers, method="POST")
    with request.urlopen(upstream_request, timeout=300) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read()
        if "json" not in content_type:
            raise ProxyError(502, f"upstream returned non-JSON content: {content_type}")
        return json.loads(raw.decode("utf-8"))


def wants_stream(path: str, accept: str | None) -> bool:
    return path.endswith("/v1/message:stream") or (accept is not None and "text/event-stream" in accept)


def augment_agent_card(data: bytes) -> bytes:
    try:
        card = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return data
    if not isinstance(card, dict):
        return data

    input_modes = card.setdefault("defaultInputModes", [])
    output_modes = card.setdefault("defaultOutputModes", [])
    add_modes(input_modes, ["text/plain", "application/pdf", "text/markdown", "text/html", "application/json"])
    add_modes(output_modes, ["text/plain", "text/markdown", "application/json", "application/pdf", "application/octet-stream"])
    for skill in card.get("skills", []):
        if isinstance(skill, dict):
            add_modes(skill.setdefault("inputModes", []), input_modes)
            add_modes(skill.setdefault("outputModes", []), output_modes)
    return json.dumps(card, indent=2).encode("utf-8")


def add_modes(target: Any, modes: list[str]) -> None:
    if not isinstance(target, list):
        return
    for mode in modes:
        if mode not in target:
            target.append(mode)


def artifact_auth_allowed(authorization: str | None) -> bool:
    credentials = os.environ.get("A2A_STATIC_AUTH_CREDENTIALS")
    if not credentials:
        return True
    if not authorization or not authorization.lower().startswith("bearer "):
        return False
    token = authorization.split(" ", 1)[1]
    try:
        parsed = json.loads(credentials)
    except json.JSONDecodeError:
        return False
    return any(isinstance(item, dict) and item.get("scheme") == "bearer" and item.get("token") == token for item in parsed)


def unique_path(directory: Path, name: str) -> Path:
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    for number in range(2, 1000):
        candidate = directory / f"{stem}-{number}{suffix}"
        if not candidate.exists():
            return candidate
    raise ProxyError(409, f"too many files named like {name}")


def safe_name(value: str) -> str:
    name = Path(value).name if "/" in value or "\\" in value else value
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return name or "file"


def main() -> int:
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), A2AFileProxy)
    bound_host, bound_port = server.server_address[:2]
    print(f"a2a-file-proxy listening on {bound_host}:{bound_port}, upstream {UPSTREAM}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
