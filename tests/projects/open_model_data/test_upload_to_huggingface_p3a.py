"""Exercise uploader authentication and private-target admission without Hub access."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.projects.open_model_data import upload_to_huggingface as uploader
from tests.helpers.restore_import_state import restore_import_state

SCRIPT = Path(uploader.__file__).resolve()
CANARY = "test-only-sensitive-10772"

# Importable in a real CLI subprocess, with no installed Hub client or credentials.
FAKE_HUB = """
import json
from pathlib import Path
from types import SimpleNamespace
from .errors import GatedRepoError, RepositoryNotFoundError

root = Path(__file__).parent
config = json.loads((root / "scenario.json").read_text())

def record(method, **kwargs):
    with (root / "calls.jsonl").open("a") as handle:
        handle.write(json.dumps({"method": method, **kwargs}) + "\\n")

def login(*args, **kwargs):
    record("FORBIDDEN_AUTH_WRITE")
    raise AssertionError("authentication must not be persisted")

set_access_token = login

class HfFolder:
    save_token = staticmethod(login)

class HfApi:
    def __init__(self, *, token):
        record("HfApi", scoped_token=token == config["token"])
        assert token == config["token"]
        self.lookups = iter(config.get("lookups", [True]))
        if config.get("fail") == "HfApi":
            raise RuntimeError(config["token"])

    def whoami(self):
        record("whoami")
        if config.get("fail") == "whoami":
            raise RuntimeError(config["token"])
        return {"name": config["token"], "isPro": False}

    def repo_info(self, *, repo_id, repo_type):
        record("repo_info", repo_id=repo_id, repo_type=repo_type)
        result = next(self.lookups)
        if isinstance(result, str) and result.startswith("not_found_"):
            status = result.removeprefix("not_found_")
            response = None if status == "none" else SimpleNamespace(status_code=int(status))
            raise RepositoryNotFoundError(config["token"], response=response)
        if result == "gated":
            raise GatedRepoError(config["token"], response=SimpleNamespace(status_code=403))
        if result == "error":
            raise RuntimeError(config["token"])
        if result == "missing":
            return SimpleNamespace()
        return SimpleNamespace(private=result)

    def create_repo(self, *, repo_id, repo_type, private, exist_ok):
        record("create_repo", repo_id=repo_id, repo_type=repo_type, private=private, exist_ok=exist_ok)
        if config.get("fail") == "create_repo":
            raise RuntimeError(config["token"])

    def upload_folder(self, *, folder_path, repo_id, repo_type, commit_message):
        record("upload_folder", folder_path=folder_path, repo_id=repo_id, repo_type=repo_type)
        if config.get("fail") == "upload_folder":
            raise RuntimeError(config["token"])
"""


@pytest.fixture(params=["main", "cli"])
def run_upload(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Callable[..., tuple[int, list[dict], str]]:
    """Run the same attack cases through main and the real __main__ entry point."""
    package = tmp_path / "package"
    package.mkdir()
    (package / "train.jsonl").write_text('{"text": "new safety fixture"}\n', encoding="utf-8")
    hub_dir = tmp_path / "fake_imports" / "huggingface_hub"
    hub_dir.mkdir(parents=True)
    (hub_dir / "__init__.py").write_text(textwrap.dedent(FAKE_HUB), encoding="utf-8")
    (hub_dir / "errors.py").write_text(
        "class RepositoryNotFoundError(Exception):\n"
        "    def __init__(self, message, *, response):\n"
        "        super().__init__(message)\n"
        "        self.response = response\n"
        "class GatedRepoError(RepositoryNotFoundError):\n"
        "    pass\n",
        encoding="utf-8",
    )
    cache = tmp_path / "fake_hf_home"
    cache.mkdir()
    (cache / "token").write_text("fake cached token must remain untouched", encoding="utf-8")
    monkeypatch.setenv("HF_HOME", str(cache))
    launcher = (
        "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
        "sys.argv = sys.argv[2:]; runpy.run_path(sys.argv[0], run_name='__main__')"
    )

    def run(
        *,
        lookups: list | None = None,
        fail: str | None = None,
        token_source: str = "argument",
        private: bool = False,
        dataset: str = "valid",
    ) -> tuple[int, list[dict], str]:
        (hub_dir / "scenario.json").write_text(
            json.dumps({"lookups": [True] if lookups is None else lookups, "fail": fail, "token": CANARY}),
            encoding="utf-8",
        )
        monkeypatch.setenv("HF_TOKEN", CANARY if token_source == "environment" else "ignored-fake-env-token")
        arguments = [str(SCRIPT), "--dataset-dir", str(package), "--repo-id", "fixture/private-dataset"]
        if token_source == "argument":
            arguments += ["--token", CANARY]
        elif token_source == "missing":
            monkeypatch.delenv("HF_TOKEN")
        elif token_source == "blank":
            monkeypatch.setenv("HF_TOKEN", "   ")
        if private:
            arguments.append("--private")
        if dataset == "missing":
            arguments[2] = str(package / "absent")
        elif dataset == "file":
            arguments[2] = str(package / "train.jsonl")
        elif dataset == "quarantined":
            (package / "manifest.json").write_text(
                json.dumps({"dataset_name": uploader.QUARANTINED_PACKAGE_NAME}), encoding="utf-8"
            )
        elif dataset == "malformed":
            (package / "manifest.json").write_text("{", encoding="utf-8")
        elif dataset == "invalid_utf8":
            (package / "manifest.json").write_bytes(b'{"dataset_name": "\xff"}')
        if request.param == "cli":
            result = subprocess.run(
                [sys.executable, "-c", launcher, str(hub_dir.parent), *arguments],
                capture_output=True,
                text=True,
                timeout=30,
            )
            code, output = result.returncode, result.stdout + result.stderr
        else:
            with restore_import_state("huggingface_hub", "huggingface_hub.errors"), monkeypatch.context() as scoped:
                scoped.delitem(sys.modules, "huggingface_hub.errors", raising=False)
                spec = importlib.util.spec_from_file_location("huggingface_hub", hub_dir / "__init__.py")
                assert spec is not None and spec.loader is not None
                hub = importlib.util.module_from_spec(spec)
                scoped.setitem(sys.modules, "huggingface_hub", hub)
                spec.loader.exec_module(hub)
                scoped.setattr(sys, "argv", arguments)
                code = uploader.main()
                captured = capsys.readouterr()
                output = captured.out + captured.err
        calls_file = hub_dir / "calls.jsonl"
        calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
        assert CANARY not in output
        assert "ignored-fake-env-token" not in output
        assert "FORBIDDEN_AUTH_WRITE" not in [call["method"] for call in calls]
        assert {path.name: path.read_text() for path in cache.iterdir()} == {
            "token": "fake cached token must remain untouched"
        }
        return code, calls, output

    return run


def test_upload_requires_explicit_package_directory() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "--dataset-dir" in result.stderr
    assert "huggingface" not in result.stdout.lower()


def test_upload_requires_explicit_repository(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--dataset-dir", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 2
    assert "the following arguments are required: --repo-id" in result.stderr


def test_help_uses_portable_example() -> None:
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0
    assert "Example: .venv/bin/python scripts/projects/open_model_data/upload_to_huggingface.py" in result.stdout
    assert "--repo-id '<verified-project-org>/<dataset-name>'" in result.stdout


def test_invalid_utf8_manifest_refuses_before_any_hub_call(run_upload: Callable) -> None:
    code, calls, output = run_upload(dataset="invalid_utf8")
    assert code == 1
    assert calls == []
    assert "unreadable package manifest" in output
    assert "refusing upload" in output
    assert "Traceback" not in output


@pytest.mark.parametrize("token_source", ["argument", "environment"])
@pytest.mark.parametrize("private", [False, True])
def test_new_repository_is_private_with_scoped_auth(
    run_upload: Callable, tmp_path: Path, token_source: str, private: bool
) -> None:
    code, calls, output = run_upload(lookups=["not_found_404", True], token_source=token_source, private=private)
    assert code == 0
    assert "SUCCESS" in output
    assert calls == [
        {"method": "HfApi", "scoped_token": True},
        {"method": "whoami"},
        {"method": "repo_info", "repo_id": "fixture/private-dataset", "repo_type": "dataset"},
        {
            "method": "create_repo",
            "repo_id": "fixture/private-dataset",
            "repo_type": "dataset",
            "private": True,
            "exist_ok": True,
        },
        {"method": "repo_info", "repo_id": "fixture/private-dataset", "repo_type": "dataset"},
        {
            "method": "upload_folder",
            "folder_path": str(tmp_path / "package"),
            "repo_id": "fixture/private-dataset",
            "repo_type": "dataset",
        },
    ]


def test_existing_private_repository_uploads_without_mutating_visibility(run_upload: Callable) -> None:
    code, calls, _ = run_upload()
    assert code == 0
    assert [call["method"] for call in calls] == ["HfApi", "whoami", "repo_info", "upload_folder"]


@pytest.mark.parametrize("privacy", [False, None, "missing", "true", 1])
@pytest.mark.parametrize("after_create", [False, True])
def test_unproved_privacy_refuses_upload(run_upload: Callable, privacy: object, after_create: bool) -> None:
    lookups = ["not_found_404", privacy] if after_create else [privacy]
    code, calls, output = run_upload(lookups=lookups)
    assert code == 1
    assert "refusing upload" in output
    assert [call["method"] for call in calls] == (
        ["HfApi", "whoami", "repo_info", "create_repo", "repo_info"]
        if after_create
        else ["HfApi", "whoami", "repo_info"]
    )


@pytest.mark.parametrize(
    "response", ["error", "not_found_401", "not_found_403", "not_found_500", "not_found_none", "gated"]
)
def test_lookup_failures_never_authorize_creation(run_upload: Callable, response: str) -> None:
    code, calls, output = run_upload(lookups=[response])
    assert code == 1
    assert "Could not prepare" in output
    assert [call["method"] for call in calls] == ["HfApi", "whoami", "repo_info"]


@pytest.mark.parametrize(
    ("fail", "methods"),
    [
        ("HfApi", ["HfApi"]),
        ("whoami", ["HfApi", "whoami"]),
        ("create_repo", ["HfApi", "whoami", "repo_info", "create_repo"]),
        ("upload_folder", ["HfApi", "whoami", "repo_info", "create_repo", "repo_info", "upload_folder"]),
    ],
)
def test_hub_failures_stop_with_safe_diagnostics(run_upload: Callable, fail: str, methods: list[str]) -> None:
    code, calls, output = run_upload(lookups=["not_found_404", True], fail=fail)
    assert code == 1
    assert "ERROR:" in output
    assert "SUCCESS" not in output
    assert [call["method"] for call in calls] == methods


@pytest.mark.parametrize("response", ["error", "not_found_404"])
def test_post_create_lookup_failure_refuses_upload(run_upload: Callable, response: str) -> None:
    code, calls, _ = run_upload(lookups=["not_found_404", response])
    assert code == 1
    assert [call["method"] for call in calls] == ["HfApi", "whoami", "repo_info", "create_repo", "repo_info"]


@pytest.mark.parametrize("token_source", ["missing", "blank"])
def test_missing_auth_never_uses_a_cached_token(run_upload: Callable, token_source: str) -> None:
    code, calls, output = run_upload(token_source=token_source)
    assert code == 1
    assert calls == []
    assert "Provide a Hugging Face token" in output


@pytest.mark.parametrize("dataset", ["missing", "file", "quarantined", "malformed"])
def test_package_refusals_precede_authentication(run_upload: Callable, dataset: str) -> None:
    code, calls, output = run_upload(dataset=dataset, token_source="missing")
    assert code == 1
    assert calls == []
    assert "Provide a Hugging Face token" not in output
