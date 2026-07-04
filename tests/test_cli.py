import argparse
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

_module_path = Path(__file__).resolve().parent.parent / "browser-agent-cli"
_loader = importlib.machinery.SourceFileLoader("browser_agent_cli", str(_module_path))
_spec = importlib.util.spec_from_loader("browser_agent_cli", _loader)
cli = importlib.util.module_from_spec(_spec)
assert _spec is not None
_spec.loader.exec_module(cli)


def test_bearer_token_reads_first_bearer_credential() -> None:
    args = argparse.Namespace()
    env = {
        "A2A_STATIC_AUTH_CREDENTIALS": json.dumps(
            [
                {"scheme": "apiKey", "token": "ignored"},
                {"scheme": "bearer", "token": "expected", "principal": "test"},
            ]
        )
    }

    assert cli.bearer_token(args, env) == "expected"


def test_cli_token_argument_overrides_environment() -> None:
    args = argparse.Namespace(token="from-arg")
    env = {"A2A_STATIC_AUTH_CREDENTIALS": '[{"scheme":"bearer","token":"from-env"}]'}

    assert cli.bearer_token(args, env) == "from-arg"


def test_compact_task_marks_backend_timeout_as_recoverable() -> None:
    task = {
        "id": "task-1",
        "status": {"state": "TASK_STATE_FAILED", "message": {"parts": [{"text": "OpenCode request timed out"}]}},
    }

    result = cli.compact_task(task, ok=True)

    assert result["terminal"] is False
    assert result["recoverable"] is True
    assert result["nextAction"] == "wait"


def test_build_submit_payload_includes_shared_metadata() -> None:
    args = argparse.Namespace(
        message="hello",
        file=[],
        context_id="ctx-1",
        session_id="session-1",
        model_provider="provider-1",
        model="model-1",
        directory="coles",
    )

    payload = cli.build_submit_payload(args)
    message = payload["message"]

    assert message["contextId"] == "ctx-1"
    assert message["metadata"]["shared"]["session"]["id"] == "session-1"
    assert message["metadata"]["shared"]["model"] == {"providerID": "provider-1", "modelID": "model-1"}
    assert message["metadata"]["opencode"]["directory"] == "coles"


def test_ensure_directory_requires_directory() -> None:
    missing = cli.ensure_directory(argparse.Namespace(directory=None))
    assert missing is not None
    assert missing["ok"] is False
    assert "--directory" in missing["error"]

    blank = cli.ensure_directory(argparse.Namespace(directory="   "))
    assert blank is not None
    assert blank["ok"] is False


def test_ensure_directory_accepts_workspace() -> None:
    assert cli.ensure_directory(argparse.Namespace(directory="coles")) is None


def test_dotenv_file_overrides_existing_environment(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.coolify"
    env_file.write_text("A2A_PUBLIC_URL=https://from-file.example\n")

    env = cli.load_dotenv_file({"A2A_PUBLIC_URL": "http://from-shell.example"}, env_file)

    assert env["A2A_PUBLIC_URL"] == "https://from-file.example"


def test_next_command_preserves_env_file(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["./browser-agent-cli", "--env-file", ".env.coolify", "submit"])
    result = {"taskId": "task-1"}

    cli.add_wait_guidance(result, "wait")

    assert result["nextCommand"] == "./browser-agent-cli --env-file .env.coolify wait task-1"


def test_next_command_preserves_url_and_token(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["browser-agent-cli", "--url", "https://server.example", "--token", "secret value", "submit"],
    )
    result = {"taskId": "task-1"}

    cli.add_wait_guidance(result, "wait")

    assert result["nextCommand"] == "browser-agent-cli --url https://server.example --token 'secret value' wait task-1"
