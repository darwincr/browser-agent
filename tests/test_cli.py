import argparse
import importlib.machinery
import importlib.util
import json
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
        directory="/workspace/project",
    )

    payload = cli.build_submit_payload(args)
    message = payload["message"]

    assert message["contextId"] == "ctx-1"
    assert message["metadata"]["shared"]["session"]["id"] == "session-1"
    assert message["metadata"]["shared"]["model"] == {"providerID": "provider-1", "modelID": "model-1"}
    assert message["metadata"]["opencode"]["directory"] == "/workspace/project"
