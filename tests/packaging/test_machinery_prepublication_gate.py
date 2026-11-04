"""The machinery pre-publication gate blocks history-only findings and binds its clearance.

Each case builds a throwaway repository in tmp_path and runs
packaging/machinery-security/prepublication-gate.sh with the real scanners.
A case skips, with the reason, when the pinned TruffleHog executable, the
hash-locked Semgrep venv (MACHINERY_GATE_SEMGREP_VENV, or semgrep on PATH) or
the pinned semgrep-rules commit is unavailable.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SECURITY_DIR = Path(__file__).resolve().parents[2] / "packaging" / "machinery-security"
GATE = SECURITY_DIR / "prepublication-gate.sh"
PINS = SECURITY_DIR / "pins.txt"
SCAN_TIMEOUT = 900

pytestmark = pytest.mark.timeout(SCAN_TIMEOUT * 2)


def _pin(name: str) -> str:
    for line in PINS.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip()
    raise AssertionError(f"{name} is not pinned in {PINS}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and key not in {"HOME", "XDG_CONFIG_HOME"}
    }
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="Gate Test",
        GIT_AUTHOR_EMAIL="gate-test@example.invalid",
        GIT_COMMITTER_NAME="Gate Test",
        GIT_COMMITTER_EMAIL="gate-test@example.invalid",
    )
    return env


def _git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    assert git is not None
    result = subprocess.run(
        [git, "-C", str(repo), "-c", "commit.gpgsign=false", *args],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
        timeout=120,
    )
    return result.stdout.strip()


def _commit(repo: Path, files: dict[str, str | bytes | None], message: str) -> str:
    for name, content in files.items():
        path = repo / name
        if content is None:
            _git(repo, "rm", "--quiet", "--", name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        _git(repo, "add", "--", name)
    _git(repo, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _new_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "--initial-branch=main")
    return repo


@pytest.fixture(scope="session")
def trufflehog() -> Path:
    found = shutil.which("trufflehog")
    if found is None:
        pytest.skip("TruffleHog is not on PATH; the gate needs the pinned 3.99.0 executable")
    path = Path(found)
    if _sha256(path) != _pin("TRUFFLEHOG_LINUX_AMD64_BINARY_SHA256"):
        pytest.skip("trufflehog on PATH is not the pinned 3.99.0 release executable")
    return path


@pytest.fixture(scope="session")
def semgrep_venv() -> Path:
    configured = os.environ.get("MACHINERY_GATE_SEMGREP_VENV")
    if configured:
        venv = Path(configured)
    elif found := shutil.which("semgrep"):
        venv = Path(found).resolve().parent.parent
    else:
        pytest.skip("No Semgrep venv: set MACHINERY_GATE_SEMGREP_VENV to the hash-locked Semgrep 1.183.0 venv")
    cores = sorted(venv.glob("lib/python3*/site-packages/semgrep/bin/semgrep-core"))
    if not (venv / "bin" / "semgrep").is_file() or not cores:
        pytest.skip(f"{venv} is not a Semgrep venv")
    if _sha256(cores[-1]) != _pin("SEMGREP_CORE_LINUX_X86_64_SHA256"):
        pytest.skip(f"{venv} does not hold the pinned Semgrep 1.183.0 engine")
    return venv


@pytest.fixture(scope="session")
def rules_source(tmp_path_factory: pytest.TempPathFactory) -> str:
    """A local semgrep-rules mirror at the pinned commit, fetched once per session."""
    commit = _pin("SEMGREP_RULES_COMMIT")
    upstream = os.environ.get("MACHINERY_GATE_RULES_SOURCE", _pin("SEMGREP_RULES_REPOSITORY"))
    mirror = tmp_path_factory.mktemp("semgrep-rules")
    _git(mirror, "init", "--quiet")
    try:
        _git(mirror, "fetch", "--quiet", "--depth", "1", "--no-tags", upstream, commit)
        _git(mirror, "update-ref", "refs/heads/pinned", "FETCH_HEAD")
    except subprocess.CalledProcessError:
        pytest.skip(f"semgrep-rules commit {commit} could not be fetched from {upstream}")
    return str(mirror)


def _scan(
    repo: Path,
    out: Path,
    refs: list[str],
    *,
    trufflehog: Path,
    semgrep_venv: Path,
    rules_source: str,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    command = ["bash", str(GATE), "scan", "--repo", str(repo), "--out", str(out)]
    for ref in refs:
        command += ["--ref", ref]
    command += [
        "--trufflehog",
        str(trufflehog),
        "--semgrep-venv",
        str(semgrep_venv),
        "--rules-source",
        rules_source,
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=SCAN_TIMEOUT, check=False)
    summary_path = out / "summary.json"
    assert summary_path.is_file(), result.stdout + result.stderr
    return result, json.loads(summary_path.read_text(encoding="utf-8"))


def _verify(repo: Path, clearance: Path, refs: list[str]) -> subprocess.CompletedProcess[str]:
    command = ["bash", str(GATE), "verify", "--repo", str(repo), "--clearance", str(clearance)]
    for ref in refs:
        command += ["--ref", ref]
    return subprocess.run(command, capture_output=True, text=True, timeout=SCAN_TIMEOUT, check=False)


def _jsonl_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _private_key_pem() -> bytes:
    rsa = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")
    serialization = pytest.importorskip("cryptography.hazmat.primitives.serialization")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def test_secret_only_in_an_old_commit_blocks(
    tmp_path: Path, trufflehog: Path, semgrep_venv: Path, rules_source: str
) -> None:
    """Defect class: a history-only secret missed by a tree-only scan."""
    repo = _new_repo(tmp_path)
    _commit(repo, {"README.md": "# demo\n", "deploy/id_rsa": _private_key_pem()}, "add key")
    _commit(repo, {"deploy/id_rsa": None, "README.md": "# demo\nclean now\n"}, "remove key")
    assert _git(repo, "ls-tree", "-r", "--name-only", "HEAD") == "README.md"

    out = tmp_path / "out"
    result, summary = _scan(
        repo,
        out,
        ["refs/heads/main"],
        trufflehog=trufflehog,
        semgrep_venv=semgrep_venv,
        rules_source=rules_source,
    )

    assert result.returncode == 1, result.stdout
    assert summary["result"] == "blocked-findings"
    assert summary["counts"]["fail_closed_conditions"] == 0
    assert _jsonl_count(out / "trufflehog" / "ref-1.jsonl") >= 1
    assert not (out / "clearance.json").exists()
    assert "BEGIN" not in result.stdout + result.stderr


def test_semgrep_finding_only_in_a_historical_blob_blocks(
    tmp_path: Path, trufflehog: Path, semgrep_venv: Path, rules_source: str
) -> None:
    """Defect class: a historical source version that is not scanned."""
    repo = _new_repo(tmp_path)
    _commit(repo, {"tool/run.py": "import sys\n\neval(sys.argv[1])\n"}, "unsafe")
    _commit(repo, {"tool/run.py": "import sys\n\nprint(sys.argv[1])\n"}, "safe")

    out = tmp_path / "out"
    result, summary = _scan(
        repo,
        out,
        ["refs/heads/main"],
        trufflehog=trufflehog,
        semgrep_venv=semgrep_venv,
        rules_source=rules_source,
    )

    assert result.returncode == 1, result.stdout
    assert summary["result"] == "blocked-findings"
    assert summary["counts"]["trufflehog_findings"] == 0
    tree = json.loads((out / "semgrep" / "tree-1.json").read_text(encoding="utf-8"))
    history = json.loads((out / "semgrep" / "history.json").read_text(encoding="utf-8"))
    assert tree["results"] == []
    assert len(history["results"]) >= 1
    assert not (out / "clearance.json").exists()


FAKE_SEMGREP = """#!/bin/sh
if [ "$1" = --version ]; then echo 1.183.0; exit 0; fi
output=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = --output ]; then output="$2"; fi
  shift
done
{body}
"""

FAKE_BEHAVIOURS = {
    "malformed-output": 'printf \'{"results": [\' > "$output"; exit 0',
    "scanner-error-exit": ('printf \'{"results": [], "errors": [], "paths": {"scanned": []}}\' > "$output"; exit 2'),
    "error-reported-with-exit-0": (
        'printf \'{"results": [], "errors": [{"type": "x"}], "paths": {"scanned": []}}\' > "$output"; exit 0'
    ),
}


@pytest.mark.parametrize("behaviour", sorted(FAKE_BEHAVIOURS))
def test_scanner_error_or_malformed_output_blocks(
    tmp_path: Path, trufflehog: Path, semgrep_venv: Path, rules_source: str, behaviour: str
) -> None:
    """Defect class: fail-open on a scanner error or malformed scanner output."""
    real_core = sorted(semgrep_venv.glob("lib/python3*/site-packages/semgrep/bin/semgrep-core"))[-1]
    fake_venv = tmp_path / "fake-venv"
    core = fake_venv / real_core.relative_to(semgrep_venv)
    core.parent.mkdir(parents=True)
    core.symlink_to(real_core)
    (fake_venv / "bin").mkdir()
    fake = fake_venv / "bin" / "semgrep"
    fake.write_text(FAKE_SEMGREP.format(body=FAKE_BEHAVIOURS[behaviour]), encoding="utf-8")
    fake.chmod(0o755)

    repo = _new_repo(tmp_path)
    _commit(repo, {"README.md": "# demo\n"}, "one")

    out = tmp_path / "out"
    result, summary = _scan(
        repo,
        out,
        ["refs/heads/main"],
        trufflehog=trufflehog,
        semgrep_venv=fake_venv,
        rules_source=rules_source,
    )

    assert result.returncode == 3, result.stdout
    assert summary["result"] == "blocked-fail-closed"
    assert summary["counts"]["fail_closed_conditions"] >= 2  # the tree scan and the history scan
    assert all("Semgrep" in reason for reason in summary["fail_closed_reasons"])
    assert not (out / "clearance.json").exists()


def test_clean_repository_clears_and_verify_is_bound_to_refs_and_digest(
    tmp_path: Path, trufflehog: Path, semgrep_venv: Path, rules_source: str
) -> None:
    """Control: a clean history clears; the clearance holds only for the same refs and history."""
    repo = _new_repo(tmp_path)
    _commit(repo, {"pkg/hello.py": 'def greet(name):\n    return "hello " + name\n'}, "one")
    _commit(repo, {"README.md": "# demo\n", "conf/settings.yml": "level: 1\n"}, "two")
    _git(repo, "tag", "--annotate", "--message", "first release", "v1")
    refs = ["refs/heads/main", "refs/tags/v1"]

    out = tmp_path / "out"
    result, _summary = _scan(
        repo,
        out,
        refs,
        trufflehog=trufflehog,
        semgrep_venv=semgrep_venv,
        rules_source=rules_source,
    )

    assert result.returncode == 0, result.stdout
    assert out.stat().st_mode & 0o777 == 0o700
    assert not (out / "work").exists()
    clearance = out / "clearance.json"
    record = json.loads(clearance.read_text(encoding="utf-8"))
    assert record["result"] == "clear"
    assert record["refs"] == {
        "refs/heads/main": _git(repo, "rev-parse", "refs/heads/main"),
        "refs/tags/v1": _git(repo, "rev-parse", "refs/tags/v1"),
    }
    assert record["history_digest"].startswith("sha256:")
    assert record["counts"]["tag_objects"] == 1

    accepted = _verify(repo, clearance, refs)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr

    narrower = _verify(repo, clearance, ["refs/heads/main"])
    assert narrower.returncode == 1
    assert "differ from the cleared refs" in narrower.stdout

    _commit(repo, {"README.md": "# demo\nmoved\n"}, "three")
    moved = _verify(repo, clearance, refs)
    assert moved.returncode == 1
    assert "refs/heads/main moved" in moved.stdout
