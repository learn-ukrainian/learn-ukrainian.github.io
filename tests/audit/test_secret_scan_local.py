"""Safety tests for scripts/audit/secret_scan_local.py (#9416).

A stub ``trufflehog`` placed first on PATH records its argv and emits canned
findings whose secret fields hold a sentinel. No test touches the network or a
real remote: ``history`` mirrors a local bare repository.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.audit import secret_scan_local as ssl

SCRIPT = Path(ssl.__file__)
SENTINEL = "s3ntinel-RAW-value-9416-do-not-print"

STUB = """#!{python}
import json, os, sys
args = sys.argv[1:]
mirror = None
for arg in args:
    if arg.startswith("file://"):
        path = arg[len("file://"):]
        mirror = {{
            "path": path,
            "bare": os.path.isfile(os.path.join(path, "HEAD")) and os.path.isdir(os.path.join(path, "objects")),
        }}
with open(os.environ["STUB_RECORD"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps({{"argv": args, "cwd": os.getcwd(), "mirror": mirror}}) + "\\n")
sys.stderr.write("stub log {sentinel}\\n")
findings = os.environ.get("STUB_FINDINGS")
if findings:
    with open(findings, encoding="utf-8") as fh:
        sys.stdout.write(fh.read())
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
"""


def _finding(source: str, location: dict) -> str:
    secret = {
        "DetectorName": "PrivateKey",
        "Raw": SENTINEL,
        "RawV2": SENTINEL + "v2",
        "Redacted": SENTINEL[:12],
        "ExtraData": {"hint": SENTINEL},
        "StructuredData": {"key": SENTINEL},
        "SecretParts": {"key": SENTINEL},
        "SourceMetadata": {"Data": {source: location}},
    }
    return json.dumps(secret) + "\n"


TREE_FINDINGS = _finding("Filesystem", {"file": "app.py", "line": 3}) * 2
GIT_FINDINGS = _finding(
    "Git", {"file": "conf/k.txt", "line": 1, "commit": "0123456789abcdef0123", "email": "t@example.invalid"}
)


def _git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(
        [
            "git",
            "-c", "user.name=t",
            "-c", "user.email=t@example.invalid",
            "-c", "commit.gpgsign=false",
            "-c", "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
        timeout=60,
    )  # fmt: skip


@pytest.fixture
def stub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "trufflehog"
    exe.write_text(STUB.format(python=sys.executable, sentinel=SENTINEL), encoding="utf-8")
    exe.chmod(0o755)
    record = tmp_path / "stub-record.jsonl"
    findings = tmp_path / "stub-findings.jsonl"
    findings.write_text(TREE_FINDINGS, encoding="utf-8")
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("STUB_RECORD", str(record))
    monkeypatch.setenv("STUB_FINDINGS", str(findings))
    monkeypatch.setenv("STUB_EXIT", "0")
    monkeypatch.setenv("TMPDIR", str(scratch))
    monkeypatch.setattr(tempfile, "tempdir", None)
    return {"record": record, "findings": findings, "tmp": scratch}


def _calls(stub: dict[str, Path]) -> list[dict]:
    if not stub["record"].exists():
        return []
    return [json.loads(line) for line in stub["record"].read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git("init", "-q", "-b", "main", cwd=root)
    files = {
        "app.py": "print('hi')\n",
        "data/notes.txt": "notes\n",
        "data/sources.db": "db\n",
        ".venv/lib.py": "x = 1\n",
        "node_modules/m.js": "x\n",
        "pkg/node_modules/n.js": "x\n",
        ".worktrees/w/file.txt": "x\n",
        ".trufflehogignore": "\\.lock$\n",
    }
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    (root / "link.py").symlink_to("app.py")
    _git("add", "app.py", ".trufflehogignore", cwd=root)
    _git("commit", "-qm", "init", cwd=root)
    return root


def _assert_no_secret(captured: pytest.CaptureResult[str]) -> None:
    assert SENTINEL not in captured.out
    assert SENTINEL[:12] not in captured.out
    assert SENTINEL not in captured.err
    assert SENTINEL[:12] not in captured.err


def _report_path(out: str) -> Path:
    line = next(line for line in out.splitlines() if line.startswith("full report"))
    return Path(line.rsplit(": ", 1)[1])


def test_tree_findings_print_counts_and_rows_but_never_raw_values(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_no_secret(captured)
    assert "findings: 2" in captured.out
    assert "  PrivateKey: 2" in captured.out
    assert "PrivateKey\tapp.py\t-\t3" in captured.out
    # The raw values are kept, but only in the owner-only report outside the repository.
    report = _report_path(captured.out)
    assert SENTINEL in report.read_text(encoding="utf-8")
    assert not report.is_relative_to(repo)


def test_tool_stderr_goes_to_owner_only_log_not_console(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    ssl.main(["--repo", str(repo), "tree"])
    report = _report_path(capfd.readouterr().out)
    log = report.with_name(report.name + ".log")
    assert SENTINEL in log.read_text(encoding="utf-8")


def test_no_findings_exit_zero(stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]) -> None:
    stub["findings"].write_text("", encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_CLEAN
    assert "findings: 0" in capfd.readouterr().out


def test_tool_error_exit_two_without_leaking(
    stub: dict[str, Path], repo: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("STUB_EXIT", "1")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_no_secret(captured)
    assert "trufflehog exited 1" in captured.err


def test_unparseable_report_line_is_not_echoed(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_text(f"not json {SENTINEL}\n", encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_no_secret(captured)
    assert "unparseable JSON at report line 1" in captured.err


def test_missing_binary_gives_typed_message(
    tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    assert "trufflehog not found on PATH" in capfd.readouterr().err


@pytest.mark.parametrize(
    "option",
    ["--verify", "--verification", "--no-no-verification", "--results=verified", "--verifier=x", "--only-verified"],
)
def test_verification_options_are_refused(
    stub: dict[str, Path], repo: Path, option: str, capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), "tree", option]) == ssl.EXIT_ERROR
    assert "refused option" in capfd.readouterr().err
    assert _calls(stub) == []


def test_every_call_carries_the_fixed_offline_flags(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    ssl.main(["--repo", str(repo), "tree"])
    (call,) = _calls(stub)
    argv = call["argv"]
    assert argv[0] == "filesystem"
    for flag in ("--no-verification", "--no-update", "--results=unverified", "--exclude-detectors=Lob"):
        assert flag in argv
    assert f"--exclude-paths={repo / '.trufflehogignore'}" in argv
    assert not any("verifier" in arg for arg in argv)


@pytest.mark.parametrize("dropped", ssl.SAFE_FLAGS)
def test_assert_safe_command_rejects_a_missing_safe_flag(dropped: str) -> None:
    cmd = ["trufflehog", "filesystem", *(flag for flag in ssl.SAFE_FLAGS if flag != dropped)]
    with pytest.raises(ssl.ScanError, match="unsafe TruffleHog command"):
        ssl.assert_safe_command(cmd)


def test_assert_safe_command_rejects_a_verifier_option() -> None:
    with pytest.raises(ssl.ScanError, match="refused option"):
        ssl.assert_safe_command(["trufflehog", "git", *ssl.SAFE_FLAGS, "--verifier=https://x"])


def test_assert_safe_command_ignores_file_names_after_separator() -> None:
    ssl.assert_safe_command(["trufflehog", "filesystem", *ssl.SAFE_FLAGS, "--", "-verify-notes.txt"])


def test_tree_never_scans_denied_areas_or_symlinks(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    ssl.main(["--repo", str(repo), "tree"])
    (call,) = _calls(stub)
    files = call["argv"][call["argv"].index("--") + 1 :]
    assert sorted(files) == [".trufflehogignore", "app.py", "data/notes.txt"]
    assert Path(call["cwd"]).resolve() == repo.resolve()


def test_tree_splits_long_file_lists_into_batches() -> None:
    paths = [f"dir/file-{i:04d}.txt" for i in range(30)]
    chunks = ssl.batches(paths, budget=100)
    assert [p for chunk in chunks for p in chunk] == paths
    assert all(sum(len(p) + 1 for p in chunk) <= 100 for chunk in chunks)
    assert len(chunks) > 1


@pytest.mark.parametrize("inside", ["out.jsonl", "sub/out.jsonl"])
def test_output_inside_repository_is_refused(
    stub: dict[str, Path], repo: Path, inside: str, capfd: pytest.CaptureFixture[str]
) -> None:
    (repo / "sub").mkdir(exist_ok=True)
    target = repo / inside
    assert ssl.main(["--output", str(target), "--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    assert "refused --output inside the repository" in capfd.readouterr().err
    assert not target.exists()
    assert _calls(stub) == []


def test_output_inside_primary_checkout_of_a_worktree_is_refused(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    worktree = repo / ".worktrees" / "dispatch" / "t"
    _git("worktree", "add", "-q", "-b", "t", str(worktree), cwd=repo)
    target = repo / "outside-worktree-but-in-primary.jsonl"
    assert ssl.main(["--output", str(target), "--repo", str(worktree), "tree"]) == ssl.EXIT_ERROR
    assert not target.exists()


def test_existing_output_file_is_never_reused(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "exists.jsonl"
    target.write_text("keep\n", encoding="utf-8")
    assert ssl.main(["--output", str(target), "--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    assert target.read_text(encoding="utf-8") == "keep\n"


def test_report_and_log_are_owner_only(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    previous = os.umask(0o022)
    try:
        explicit = tmp_path / "explicit.jsonl"
        ssl.main(["--output", str(explicit), "--repo", str(repo), "tree"])
        assert _report_path(capfd.readouterr().out) == explicit
        ssl.main(["--repo", str(repo), "tree"])
        default = _report_path(capfd.readouterr().out)
    finally:
        os.umask(previous)
    assert default.parent == stub["tmp"]
    for report in (explicit, default):
        for path in (report, report.with_name(report.name + ".log")):
            assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.fixture
def cloned(tmp_path: Path) -> Path:
    """A work tree whose ``origin`` is a local bare repository."""
    src = tmp_path / "src"
    src.mkdir()
    _git("init", "-q", "-b", "main", cwd=src)
    (src / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "a.txt", cwd=src)
    _git("commit", "-qm", "a", cwd=src)
    _git("clone", "-q", "--bare", str(src), str(tmp_path / "remote.git"))
    _git("clone", "-q", str(tmp_path / "remote.git"), str(tmp_path / "work"))
    return tmp_path / "work"


def test_history_scans_a_bare_mirror_and_removes_it(
    stub: dict[str, Path], cloned: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_text(GIT_FINDINGS, encoding="utf-8")
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_no_secret(captured)
    assert "t@example.invalid" not in captured.out
    assert "PrivateKey\tconf/k.txt\t0123456789\t1" in captured.out
    (call,) = _calls(stub)
    assert call["argv"][0] == "git"
    assert "--bare" in call["argv"]
    assert "--no-verification" in call["argv"]
    mirror = Path(call["mirror"]["path"])
    assert call["mirror"]["bare"] is True
    assert mirror.is_relative_to(stub["tmp"])
    assert cloned.resolve() not in mirror.resolve().parents
    assert not mirror.exists()
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


def test_history_removes_mirror_when_the_scan_fails(
    stub: dict[str, Path], cloned: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("STUB_EXIT", "1")
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


def test_history_clone_failure_is_a_tool_error(
    stub: dict[str, Path], cloned: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    _git("remote", "set-url", "origin", str(cloned.parent / "missing.git"), cwd=cloned)
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert "mirror clone of remote 'origin' failed" in capfd.readouterr().err
    assert _calls(stub) == []
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


def test_history_mirror_parent_inside_repository_is_refused(
    stub: dict[str, Path], cloned: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(cloned), "history", "--mirror-parent", str(cloned)]) == ssl.EXIT_ERROR
    assert "refused mirror directory inside the repository" in capfd.readouterr().err
    assert not list(cloned.glob("secret-scan-mirror-*"))


def test_help_meets_cli_standard() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0
    for section in ("Examples:", "Outputs:", "Exit codes:", "Related:", "--no-verification"):
        assert section in result.stdout
