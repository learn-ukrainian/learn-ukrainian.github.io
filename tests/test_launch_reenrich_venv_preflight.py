"""Runner-venv preflight regression test for the #6876 campaign launcher.

Root cause covered: an atlas-runner job died with ``ModuleNotFoundError:
yaml`` mid-run, *after* systemd-run had already reported success -- the
launcher only checked that ``$REPO/.venv/bin/python`` existed, never that it
could import the driver's hard dependencies. The launcher must now fail
closed before systemd-run unless the resolved runner venv (``$REPO/.venv``
preferred, ``$CODE_ROOT/.venv`` fallback) can ``import yaml`` and
``import jsonschema``, printing a one-line pip install recipe otherwise.

Like the target-detection suite, this drives the real launcher via subprocess
against a fully stubbed tmp tree (stub venv python, stub driver/data files),
so no systemd or SSH side effect is possible: on a host without systemctl the
launcher falls through to its nohup path, and the stub python exits 0
immediately when invoked as the "driver".
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_LAUNCHER = ROOT / "scripts" / "lexicon" / "runner" / "launch_reenrich_class_b.sh"

# Stub venv pythons: invoked by the preflight as `-c 'import yaml, jsonschema'`.
# The "broken" one fails exactly that probe (simulating a venv without the
# deps) and succeeds otherwise so the launcher's own resolution order is the
# only variable under test.
_STUB_OK = "#!/bin/bash\nexit 0\n"
_STUB_BROKEN = (
    "#!/bin/bash\n"
    'for a in "$@"; do\n'
    '  if [[ "$a" == *"import yaml"* ]]; then exit 1; fi\n'
    "done\n"
    "exit 0\n"
)


def _build_fixture(tmp_path: Path, *, repo_stub: str | None, code_stub: str | None = None) -> dict[str, str]:
    """Materialize the minimal tmp tree the launcher checks before its venv
    preflight: driver with --slugs-file, synced enrichment package, residual
    slugs, sources.db, and a work-dir manifest."""
    repo = tmp_path / "repo"
    work = tmp_path / "work"
    code = tmp_path / "code"

    driver = repo / "scripts" / "lexicon" / "reenrich_thin_manifest_entries.py"
    driver.parent.mkdir(parents=True)
    driver.write_text("# driver\n# supports --slugs-file\n", encoding="utf-8")

    pkg = code / "scripts" / "lexicon"
    pkg.mkdir(parents=True)
    (pkg / "enrich_manifest.py").write_text("# synced package\n", encoding="utf-8")

    (repo / "data").mkdir(parents=True)
    (repo / "data" / "sources.db").write_bytes(b"stub")

    work.mkdir(parents=True)
    (work / "class-b-no-en.json").write_text("[]\n", encoding="utf-8")
    (work / "manifest.json").write_text("{}\n", encoding="utf-8")

    def _write_venv(base: Path, stub: str) -> None:
        py = base / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text(stub, encoding="utf-8")
        py.chmod(0o755)

    if repo_stub is not None:
        _write_venv(repo, repo_stub)
    if code_stub is not None:
        _write_venv(code, code_stub)

    return {
        "PATH": "/usr/bin:/bin",
        "ATLAS_RUN_ROOT": str(tmp_path),
        "ATLAS_REPO": str(repo),
        "ATLAS_RE_ENRICH_WORK_DIR": str(work),
        "ATLAS_RE_ENRICH_CODE_ROOT": str(code),
    }


def _run_launcher(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(LOCAL_LAUNCHER)],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env=env,
    )


def test_fails_closed_when_venv_cannot_import_yaml_jsonschema(tmp_path: Path) -> None:
    env = _build_fixture(tmp_path, repo_stub=_STUB_BROKEN)
    proc = _run_launcher(env)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "pip install pyyaml jsonschema" in proc.stderr
    # One-line recipe naming the resolved interpreter, and no launch happened.
    assert ".venv/bin/python" in proc.stderr
    assert "pid=" not in proc.stdout


def test_fails_closed_when_no_runner_venv_exists(tmp_path: Path) -> None:
    env = _build_fixture(tmp_path, repo_stub=None)
    proc = _run_launcher(env)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "runner venv python not found" in proc.stderr
    assert "pid=" not in proc.stdout


def test_launches_when_repo_venv_imports_ok(tmp_path: Path) -> None:
    env = _build_fixture(tmp_path, repo_stub=_STUB_OK)
    proc = _run_launcher(env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pid=" in proc.stdout


def test_falls_back_to_code_root_venv(tmp_path: Path) -> None:
    """$REPO/.venv missing -> the work-dir ($CODE_ROOT) .venv is used."""
    env = _build_fixture(tmp_path, repo_stub=None, code_stub=_STUB_OK)
    proc = _run_launcher(env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pid=" in proc.stdout


def test_prefers_repo_venv_over_code_root_venv(tmp_path: Path) -> None:
    """A broken $REPO/.venv must NOT be skipped in favor of a healthy
    $CODE_ROOT/.venv -- preference order is part of the contract."""
    env = _build_fixture(tmp_path, repo_stub=_STUB_BROKEN, code_stub=_STUB_OK)
    proc = _run_launcher(env)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "pip install pyyaml jsonschema" in proc.stderr


def test_runner_python_override_wins(tmp_path: Path) -> None:
    env = _build_fixture(tmp_path, repo_stub=_STUB_BROKEN)
    override = tmp_path / "override" / ".venv" / "bin" / "python"
    override.parent.mkdir(parents=True)
    override.write_text(_STUB_OK, encoding="utf-8")
    override.chmod(0o755)
    env["ATLAS_RE_ENRICH_RUNNER_PYTHON"] = str(override)
    proc = _run_launcher(env)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_launcher_invokes_resolved_runner_python() -> None:
    """The systemd/nohup command must use the preflight-resolved interpreter,
    not a hardcoded $REPO/.venv path that could diverge from the check."""
    source = LOCAL_LAUNCHER.read_text(encoding="utf-8")
    assert 'printf \'%q \' "$RUNNER_PYTHON" "$DRIVER"' in source
    assert 'import yaml, jsonschema' in source
