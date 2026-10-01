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
import threading
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
if mirror and os.environ.get("STUB_LOCK"):
    os.chmod(os.path.dirname(mirror["path"]), 0o500)
sys.stderr.write("stub log {sentinel}\\n")
findings = os.environ.get("STUB_FINDINGS")
if findings:
    with open(findings, "rb") as fh:
        sys.stdout.buffer.write(fh.read())
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


def _report_path(out: str, directory: Path) -> Path:
    """The default report: the console names only the generated file, never a directory."""
    line = next(line for line in out.splitlines() if line.startswith("full report"))
    name = line.split(": ", 1)[1].split(" ", 1)[0]
    assert name.startswith("secret-scan-") and "/" not in name
    return directory / name


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
    report = _report_path(captured.out, stub["tmp"])
    assert SENTINEL in report.read_text(encoding="utf-8")
    assert not report.is_relative_to(repo)


def test_tool_stderr_goes_to_owner_only_log_not_console(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    ssl.main(["--repo", str(repo), "tree"])
    report = _report_path(capfd.readouterr().out, stub["tmp"])
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
    assert "refused a verification-style option" in capfd.readouterr().err
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
    with pytest.raises(ssl.ScanError, match="refused a verification-style option"):
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
        assert "written to the --output path" in capfd.readouterr().out
        ssl.main(["--repo", str(repo), "tree"])
        default = _report_path(capfd.readouterr().out, stub["tmp"])
    finally:
        os.umask(previous)
    assert default.exists()
    for report in (explicit, default):
        for path in (report, report.with_name(report.name + ".log")):
            assert stat.S_IMODE(path.stat().st_mode) == 0o600


REMOTE_BASE = "https://example.invalid/"


@pytest.fixture
def cloned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A work tree whose ``origin`` is an https URL that git rewrites to a local bare repository.

    The wrapper validates the configured (raw) https URL; a global
    ``url.<base>.insteadOf`` maps it to ``tmp_path`` so no test touches the network.
    """
    src = tmp_path / "src"
    src.mkdir()
    _git("init", "-q", "-b", "main", cwd=src)
    (src / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "a.txt", cwd=src)
    _git("commit", "-qm", "a", cwd=src)
    _git("clone", "-q", "--bare", str(src), str(tmp_path / "remote.git"))
    _git("clone", "-q", str(tmp_path / "remote.git"), str(tmp_path / "work"))
    work = tmp_path / "work"
    _git("remote", "set-url", "origin", REMOTE_BASE + "remote.git", cwd=work)
    global_config = tmp_path / "gitconfig"
    global_config.write_text(f'[url "{tmp_path}/"]\n\tinsteadOf = {REMOTE_BASE}\n', encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    return work


@pytest.fixture
def local_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let the mirror clone reach the rewritten local repository (production allows https only)."""
    monkeypatch.setattr(ssl, "CLONE_PROTOCOLS", "https:file")


def test_history_scans_a_bare_mirror_and_removes_it(
    stub: dict[str, Path], cloned: Path, local_transport: None, capfd: pytest.CaptureFixture[str]
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
    assert mirror.is_relative_to(stub["tmp"].resolve())
    assert cloned.resolve() not in mirror.resolve().parents
    assert not mirror.exists()
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


def test_history_removes_mirror_when_the_scan_fails(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("STUB_EXIT", "1")
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


def test_history_clone_failure_is_a_tool_error(
    stub: dict[str, Path], cloned: Path, local_transport: None, capfd: pytest.CaptureFixture[str]
) -> None:
    _git("remote", "set-url", "origin", REMOTE_BASE + "missing.git", cwd=cloned)
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert "mirror clone of the configured remote failed" in capfd.readouterr().err
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


# --- Console output is allowlist-only (no channel may carry a raw value) -------------------


def _assert_absent(captured: pytest.CaptureResult[str], *needles: str) -> None:
    _assert_no_secret(captured)
    for needle in needles:
        assert needle not in captured.out
        assert needle not in captured.err


def _custom_finding(detector: object = "PrivateKey", source: str = "Git", **location: object) -> str:
    record = json.loads(_finding(source, location))
    record["DetectorName"] = detector
    return json.dumps(record) + "\n"


LEAKY_FINDINGS = {
    "million-char-path": (_custom_finding(file="a/" + SENTINEL + "x" * 1_000_000, line=1), "path"),
    "path-holding-the-raw-value": (_custom_finding(file=f"conf/{SENTINEL}.txt", line=1), "path"),
    "path-with-control-chars": (_custom_finding(file="a\tb\n" + SENTINEL[:12], line=1), "path"),
    "detector-is-the-raw-value": (_custom_finding(detector=SENTINEL, file="a.txt", line=1), "detector"),
    "detector-with-newline": (_custom_finding(detector="Key\n" + SENTINEL[:12], file="a.txt"), "detector"),
    "detector-not-a-string": (_custom_finding(detector=["x"], file="a.txt"), None),
    "commit-is-the-raw-value": (_custom_finding(file="a.txt", commit=SENTINEL, line=1), "commit"),
    "commit-message-and-email": (
        _custom_finding(file="a.txt", commit="0123456789abcdef", message=SENTINEL, email=SENTINEL, line=1),
        None,
    ),
    "line-is-the-raw-value": (_custom_finding(file="a.txt", line=SENTINEL), "line"),
    "line-is-a-mapping": (_custom_finding(file="a.txt", line={"x": SENTINEL}), "line"),
}


@pytest.mark.parametrize("case", sorted(LEAKY_FINDINGS))
def test_no_finding_field_carries_a_raw_value_to_the_console(
    stub: dict[str, Path], repo: Path, case: str, capfd: pytest.CaptureFixture[str]
) -> None:
    leaky, withheld_field = LEAKY_FINDINGS[case]
    clean = _custom_finding(file="ok.txt", line=7)
    stub["findings"].write_text(leaky + clean + leaky, encoding="utf-8")
    code = ssl.main(["--repo", str(repo), "tree"])
    captured = capfd.readouterr()
    _assert_absent(captured)
    if case == "detector-not-a-string":
        # A finding without a string detector name is an unexpected structure, not a row.
        assert code == ssl.EXIT_ERROR
        assert "unexpected report structure at line 1" in captured.err
        return
    assert code == ssl.EXIT_FINDINGS
    assert "findings: 3" in captured.out  # every row still counts
    assert "\tok.txt\t-\t7" in captured.out
    assert len(captured.out) < 2000
    if withheld_field is not None:
        placeholder = f"<{withheld_field} withheld>"
        assert placeholder in captured.out
        assert "findings with withheld fields: 2" in captured.out
        if withheld_field == "detector":
            assert f"  {placeholder}: 2" in captured.out
        else:
            assert "  PrivateKey: 3" in captured.out


def test_safe_fields_are_shown_and_short_commit_is_ten_chars() -> None:
    record = json.loads(GIT_FINDINGS)
    finding = ssl.to_finding(record, record["SourceMetadata"]["Data"]["Git"])
    assert finding == ssl.Finding("PrivateKey", "conf/k.txt", "0123456789", "1")
    assert not finding.withheld


@pytest.mark.parametrize(
    ("field", "value", "placeholder"),
    [
        ("file", "x" * 241, "<path withheld>"),
        ("file", "dir/naïve.txt", "<path withheld>"),
        ("commit", "0123456789ABCDEF", "<commit withheld>"),
        ("commit", "012345", "<commit withheld>"),
        ("line", "1" * 10, "<line withheld>"),
        ("line", True, "<line withheld>"),
        ("line", -1, "<line withheld>"),
    ],
)
def test_allowlist_patterns_are_conservative(field: str, value: object, placeholder: str) -> None:
    location = {"file": "a.txt", "commit": "0123456789abcdef", "line": 1, field: value}
    record = json.loads(_custom_finding(**location))
    finding = ssl.to_finding(record, location)
    shown = {"file": finding.file, "commit": finding.commit, "line": finding.line}[field]
    assert shown == placeholder
    assert finding.withheld


def test_output_filename_is_never_printed(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / f"{SENTINEL}.jsonl"
    assert ssl.main(["--output", str(target), "--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_absent(captured, str(tmp_path))
    assert "written to the --output path" in captured.out
    assert target.exists()


def test_default_report_prints_only_the_generated_name(
    stub: dict[str, Path],
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    secret_tmp = tmp_path / f"tmp-{SENTINEL}"
    secret_tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(secret_tmp))
    monkeypatch.setattr(tempfile, "tempdir", None)
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_absent(captured, str(tmp_path))
    assert _report_path(captured.out, secret_tmp).exists()


@pytest.mark.parametrize(
    "argv",
    [
        ["--timeout-seconds", SENTINEL, "tree"],
        ["--timeout-seconds", "0", "tree"],
        ["--max-rows", SENTINEL, "tree"],
        ["--max-rows", "-1", "tree"],
        [f"--{SENTINEL}", "tree"],
        [f"--{SENTINEL}={SENTINEL}", "tree"],
        [SENTINEL],
        ["tree", SENTINEL],
        ["tree", "--remote", SENTINEL],
        ["--output"],
    ],
)
def test_usage_errors_never_echo_the_supplied_value(
    stub: dict[str, Path], repo: Path, argv: list[str], capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), *argv]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_USAGE}"
    assert _calls(stub) == []


def test_usage_error_from_the_command_line_has_the_fixed_message() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--max-rows", SENTINEL, "tree"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == ssl.EXIT_ERROR
    assert SENTINEL not in result.stdout + result.stderr
    assert ssl.MSG_USAGE in result.stderr


@pytest.mark.parametrize(
    "option", [f"--verify={SENTINEL}", f"--results={SENTINEL}", f"--{SENTINEL}-verifier", "--VERIFY"]
)
def test_refusal_message_never_echoes_the_option(
    stub: dict[str, Path], repo: Path, option: str, capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), "tree", option]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured, option)
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_VERIFICATION}"


def test_path_option_values_are_never_echoed(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    attempts = [
        ["--repo", str(tmp_path / SENTINEL), "tree"],
        ["--output", str(tmp_path / SENTINEL / "missing-dir" / "x.jsonl"), "tree"],
        ["--output", str(repo / f"{SENTINEL}.jsonl"), "tree"],
        ["--output", str(tmp_path / "loop" / "x.jsonl"), "tree"],
    ]
    (tmp_path / "loop").symlink_to(tmp_path / "loop")
    for argv in attempts:
        if argv[0] != "--repo":
            argv = ["--repo", str(repo), *argv]
        assert ssl.main(argv) == ssl.EXIT_ERROR
        captured = capfd.readouterr()
        _assert_absent(captured, str(tmp_path))
    assert _calls(stub) == []


def test_history_option_values_are_never_echoed(
    stub: dict[str, Path], cloned: Path, local_transport: None, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    for extra in (
        ["--remote", SENTINEL],
        ["--remote", f"{SENTINEL}/../x"],
        ["--remote", f"--upload-pack={SENTINEL}"],
        ["--mirror-parent", str(tmp_path / SENTINEL)],
    ):
        assert ssl.main(["--repo", str(cloned), "history", *extra]) == ssl.EXIT_ERROR
        _assert_absent(capfd.readouterr(), str(tmp_path))
    assert _calls(stub) == []


def test_tool_failure_messages_are_fixed(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    # git clone writes the URL and its own diagnostics to the owner-only log only.
    _git("remote", "set-url", "origin", f"{REMOTE_BASE}{SENTINEL}.git", cwd=cloned)
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured, REMOTE_BASE)
    assert captured.err.strip() == (
        "secret_scan_local: mirror clone of the configured remote failed (exit 128); "
        "details in the owner-only log beside the report"
    )


def test_unexpected_exception_prints_only_its_type(
    stub: dict[str, Path], repo: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    def boom(_fd: int) -> list[ssl.Finding]:
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(ssl, "read_findings", boom)
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == "secret_scan_local: internal error (RuntimeError)"


# --- Report structure ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        "[]",
        "3",
        json.dumps(SENTINEL),
        "null",
        "{}",
        json.dumps({"Raw": SENTINEL}),
        json.dumps({"DetectorName": "X", "Raw": SENTINEL}),
        json.dumps({"DetectorName": "X", "SourceMetadata": [SENTINEL]}),
        json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {}}}),
        json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {"Git": SENTINEL}}}),
        json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {"Git": {}, "Filesystem": {}}}}),
        "[" * 100_000 + "]" * 100_000,
    ],
    ids=lambda line: line[:40],
)
def test_unexpected_report_structure_is_a_typed_error(
    stub: dict[str, Path], repo: Path, line: str, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_text(line + "\n", encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert "Traceback" not in captured.err
    assert "report line 1" in captured.err or "unexpected report structure at line 1" in captured.err


def test_non_utf8_report_is_a_typed_error(stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]) -> None:
    stub["findings"].write_bytes(b'{"Raw": "\xff' + SENTINEL.encode() + b'"}\n')
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert "the report is not valid UTF-8" in captured.err


# --- Report creation is pinned to the checked directory (no TOCTOU write) -----------------


def _repo_files(repo: Path) -> set[Path]:
    return {path for path in repo.rglob("*") if ".git" not in path.relative_to(repo).parts}


def _swap_after_check(monkeypatch: pytest.MonkeyPatch, directory: Path, target: Path) -> Path:
    """After the containment check passes, replace ``directory`` with a symlink to ``target``."""
    moved = directory.with_name(directory.name + "-moved")
    original = ssl.dir_is_inside

    def check_then_swap(dir_fd: int, root_ids: frozenset[tuple[int, int]]) -> bool:
        inside = original(dir_fd, root_ids)
        checked = os.fstat(dir_fd)
        if not directory.is_symlink() and (checked.st_dev, checked.st_ino) == (
            directory.stat().st_dev,
            directory.stat().st_ino,
        ):
            directory.rename(moved)
            directory.symlink_to(target, target_is_directory=True)
        return inside

    monkeypatch.setattr(ssl, "dir_is_inside", check_then_swap)
    return moved


def test_output_parent_swapped_for_a_symlink_after_the_check_cannot_write_into_the_repository(
    stub: dict[str, Path],
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    before = _repo_files(repo)
    moved = _swap_after_check(monkeypatch, out_dir, repo)
    assert ssl.main(["--output", str(out_dir / "report.jsonl"), "--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    assert _repo_files(repo) == before
    assert out_dir.is_symlink()
    assert SENTINEL in (moved / "report.jsonl").read_text(encoding="utf-8")
    assert (moved / "report.jsonl.log").exists()


def test_mirror_parent_swapped_for_a_symlink_after_the_check_cannot_write_into_the_repository(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    parent = tmp_path / "mirrors"
    parent.mkdir()
    stub["findings"].write_text(GIT_FINDINGS, encoding="utf-8")
    before = _repo_files(cloned)
    moved = _swap_after_check(monkeypatch, parent, cloned)
    argv = ["--repo", str(cloned), "history", "--mirror-parent", str(parent)]
    assert ssl.main(argv) == ssl.EXIT_FINDINGS
    assert _repo_files(cloned) == before
    (call,) = _calls(stub)
    assert Path(call["mirror"]["path"]).is_relative_to(moved.resolve())
    assert call["mirror"]["bare"] is True
    assert not list(moved.iterdir())


def test_output_reached_through_a_symlinked_ancestor_into_the_repository_is_refused(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    (repo / "sub").mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(repo)
    before = _repo_files(repo)
    assert ssl.main(["--output", str(alias / "sub" / "x.jsonl"), "--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    assert ssl.MSG_OUTPUT_INSIDE in capfd.readouterr().err
    assert _repo_files(repo) == before


def test_racing_parent_swaps_never_put_a_report_in_the_repository(repo: Path, tmp_path: Path) -> None:
    root_ids = ssl.root_identities([repo])
    out_dir = tmp_path / "race"
    real = tmp_path / "race-real"
    real.mkdir()
    stop = threading.Event()

    def flip() -> None:
        while not stop.is_set():
            for target in (real, repo):
                try:
                    tmp_link = tmp_path / "race-next"
                    tmp_link.symlink_to(target, target_is_directory=True)
                    os.replace(tmp_link, out_dir)
                except OSError:
                    pass

    swapper = threading.Thread(target=flip)
    swapper.start()
    created = refused = 0
    try:
        for attempt in range(300):
            try:
                outputs = ssl.open_outputs(out_dir / f"r{attempt}.jsonl", "tree", root_ids)
            except ssl.ScanError:
                refused += 1
                continue
            os.close(outputs.report_fd)
            os.close(outputs.log_fd)
            created += 1
    finally:
        stop.set()
        swapper.join()
    assert not list(repo.glob("r*.jsonl*"))
    assert created + refused == 300
    assert len(list(real.glob("r*.jsonl"))) == created


# --- The configured remote cannot inject options or transports -----------------------------


@pytest.mark.parametrize(
    "url",
    [
        "--upload-pack=touch {mark}",
        "-cprotocol.ext.allow=always",
        "-c",
        "ext::sh -c touch% {mark}",
        "file://{tmp}/remote.git",
        "{tmp}/remote.git",
        f"https://user:{SENTINEL}@example.invalid/remote.git",
        f"https://{SENTINEL}@example.invalid/remote.git",
        "https://example.invalid/remote.git --upload-pack=touch {mark}",
        "https://example.invalid/remote.git\n",
        "https://exa‮mple.invalid/remote.git",
        "https://example.invalid:port/remote.git",
        "https:///remote.git",
        "http://example.invalid/remote.git",
        "HTTPS://example.invalid/remote.git",
        "ssh://example.invalid/remote.git",
        "git@example.invalid:remote.git",
        "https://example.invalid/" + "a" * 2048,
    ],
    ids=lambda url: url[:40],
)
def test_unsafe_remote_urls_are_refused_before_any_clone(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    tmp_path: Path,
    url: str,
    capfd: pytest.CaptureFixture[str],
) -> None:
    mark = tmp_path / "injected-mark"
    value = url.format(mark=mark, tmp=tmp_path)
    _git("config", "--", "remote.origin.url", value, cwd=cloned)
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured, value.strip(), "example.invalid", str(tmp_path))
    assert captured.err.strip().startswith(f"secret_scan_local: {ssl.MSG_REMOTE_URL}")
    assert not mark.exists()
    assert _calls(stub) == []
    assert not list(stub["tmp"].glob("secret-scan-*"))  # refused before any report or mirror exists


def test_clone_command_ends_option_parsing_before_the_remote() -> None:
    cmd = ssl.clone_command("--upload-pack=x", "mirror.git")
    assert cmd[cmd.index("clone") :] == ["clone", "--quiet", "--mirror", "--", "--upload-pack=x", "mirror.git"]


def test_mirror_clone_transport_is_https_only(
    stub: dict[str, Path], cloned: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    # The validated https URL is rewritten to a local path by the user's git config;
    # with the production transport allowlist git must refuse it.
    assert ssl.CLONE_PROTOCOLS == "https"
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert "mirror clone of the configured remote failed" in capfd.readouterr().err
    assert _calls(stub) == []
    assert not list(stub["tmp"].glob("secret-scan-mirror-*"))


# --- Tree candidates and mirror cleanup ----------------------------------------------------


def test_tracked_file_beneath_a_symlinked_parent_is_not_scanned(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    (repo / "lnk").mkdir()
    (repo / "lnk" / "inner.txt").write_text("in\n", encoding="utf-8")
    _git("add", "lnk/inner.txt", cwd=repo)
    _git("commit", "-qm", "lnk", cwd=repo)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "inner.txt").write_text(f"{SENTINEL}\n", encoding="utf-8")
    (repo / "lnk" / "inner.txt").unlink()
    (repo / "lnk").rmdir()
    (repo / "lnk").symlink_to(outside, target_is_directory=True)
    (repo / "inside").symlink_to(repo / "pkg", target_is_directory=True)
    assert (
        "lnk/inner.txt"
        in subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True, check=True, timeout=60).stdout
    )
    files = ssl.tree_candidates(repo.resolve())
    assert "lnk/inner.txt" not in files
    assert set(files) == {".trufflehogignore", "app.py", "data/notes.txt"}


@pytest.fixture
def locked_mirror(stub: dict[str, Path], monkeypatch: pytest.MonkeyPatch):
    """The stub makes the mirror's directory read-only, so removing ``mirror.git`` really fails."""
    if os.geteuid() == 0:
        pytest.skip("root ignores directory permissions")
    monkeypatch.setenv("STUB_LOCK", "1")
    yield
    for left in stub["tmp"].glob("secret-scan-mirror-*"):
        left.chmod(0o700)


def test_failed_mirror_removal_is_a_typed_error(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    locked_mirror: None,
    capfd: pytest.CaptureFixture[str],
) -> None:
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured, str(stub["tmp"]))
    assert ssl.MSG_MIRROR_REMOVAL in captured.err
    assert "findings" not in captured.out
    assert list(stub["tmp"].glob("secret-scan-mirror-*"))  # the failure is real, and reported


def test_failed_mirror_removal_after_a_scan_error_reports_both(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    locked_mirror: None,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("STUB_EXIT", "1")
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    err = capfd.readouterr().err
    assert "trufflehog exited 1" in err
    assert ssl.MSG_MIRROR_REMOVAL in err
    assert SENTINEL not in err


@pytest.mark.parametrize("name", ["x y", "a/../b", "-x", ".hidden", "x" * 65])
def test_remote_name_must_be_plain(
    stub: dict[str, Path], cloned: Path, local_transport: None, name: str, capfd: pytest.CaptureFixture[str]
) -> None:
    # git accepts these as configured remote subsections; the wrapper refuses them anyway.
    _git("config", "--", f"remote.{name}.url", REMOTE_BASE + "remote.git", cwd=cloned)
    assert ssl.main(["--repo", str(cloned), "history", f"--remote={name}"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured, name)
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_REMOTE_NAME}"
    assert _calls(stub) == []
