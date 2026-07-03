import base64
import importlib.util
from pathlib import Path

import pytest


def load_proxy_module():
    module_path = Path(__file__).resolve().parents[1] / "docker" / "a2a_file_proxy.py"
    spec = importlib.util.spec_from_file_location("a2a_file_proxy", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy = load_proxy_module()


def test_safe_name_strips_paths_and_unsafe_characters() -> None:
    assert proxy.safe_name("../weird file?.pdf") == "weird-file.pdf"
    assert proxy.safe_name("...") == "file"


def test_stage_file_parts_writes_inline_raw_file(tmp_path: Path) -> None:
    message = {
        "parts": [
            {"text": "summarize"},
            {"filename": "source.txt", "mediaType": "text/plain", "raw": base64.b64encode(b"hello").decode("ascii")},
        ]
    }

    descriptions = proxy.stage_file_parts(message, tmp_path)

    assert descriptions == [f"- {tmp_path / 'source.txt'} (text/plain)"]
    assert (tmp_path / "source.txt").read_bytes() == b"hello"


def test_stage_file_parts_rejects_invalid_base64(tmp_path: Path) -> None:
    message = {"parts": [{"filename": "bad.txt", "raw": "not base64"}]}

    with pytest.raises(proxy.ProxyError) as exc_info:
        proxy.stage_file_parts(message, tmp_path)

    assert exc_info.value.status == 400
    assert "invalid base64" in exc_info.value.message


def test_attach_artifacts_adds_file_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    (outputs_dir / "summary.md").write_text("# Summary")
    monkeypatch.setattr(proxy, "PUBLIC_URL", "https://agent.example.com")
    response = {"task": {"artifacts": []}}

    proxy.attach_artifacts(response, "task-1", outputs_dir)

    artifact = response["task"]["artifacts"][0]

    assert artifact["artifactId"] == "summary.md"
    assert artifact["parts"][0]["url"] == "https://agent.example.com/artifacts/task-1/outputs/summary.md"
