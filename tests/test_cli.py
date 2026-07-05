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


def test_artifact_url_joins_base_and_path() -> None:
    assert (
        cli.artifact_url("https://agent.example.com/", "artifacts/task-1/outputs/result.txt")
        == "https://agent.example.com/artifacts/task-1/outputs/result.txt"
    )
    assert (
        cli.artifact_url("https://agent.example.com", "/artifacts/task-1/outputs/result.txt")
        == "https://agent.example.com/artifacts/task-1/outputs/result.txt"
    )


def test_download_targets_accepts_artifact_url_and_path(monkeypatch) -> None:
    def fail_fetch_task(*args, **kwargs):
        raise AssertionError("task fetch should not be needed for direct artifacts")

    monkeypatch.setattr(cli, "fetch_task", fail_fetch_task)

    assert cli.download_targets(
        "https://agent.example.com/artifacts/task/file.txt", "http://localhost:18000", "token"
    ) == [{"url": "https://agent.example.com/artifacts/task/file.txt"}]
    assert cli.download_targets("/artifacts/task/file.txt", "http://localhost:18000", "token") == [
        {"url": "http://localhost:18000/artifacts/task/file.txt"}
    ]


def test_download_targets_fetches_artifacts_for_task_id(monkeypatch) -> None:
    task = {
        "artifacts": [
            {
                "name": "result",
                "parts": [
                    {
                        "filename": "result.txt",
                        "mediaType": "text/plain",
                        "url": "http://localhost:18000/artifacts/task/result.txt",
                    }
                ],
            }
        ]
    }

    monkeypatch.setattr(cli, "fetch_task", lambda base, token, task_id: task)

    assert cli.download_targets("task-1", "http://localhost:18000", "token") == [
        {
            "name": "result",
            "filename": "result.txt",
            "mediaType": "text/plain",
            "url": "http://localhost:18000/artifacts/task/result.txt",
        }
    ]


def test_safe_download_name_strips_paths_and_unsafe_characters() -> None:
    assert cli.safe_download_name("../weird file?.txt") == "weird-file-.txt"
    assert cli.safe_download_name("...") == "artifact"


def test_unique_download_path_avoids_existing_files(tmp_path: Path) -> None:
    existing = tmp_path / "result.txt"
    existing.write_text("old")

    assert cli.unique_download_path(existing, set()) == tmp_path / "result-2.txt"
