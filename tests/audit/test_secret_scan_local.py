"""Safety tests for scripts/audit/secret_scan_local.py (#9416).

A stub ``trufflehog`` placed first on PATH records its argv and emits canned
findings whose secret fields hold a sentinel. No test touches the network or a
real remote: ``history`` mirrors a local bare repository. Two tests use the
installed TruffleHog when it is on PATH and are skipped otherwise.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.audit import secret_scan_local as ssl

SCRIPT = Path(ssl.__file__)
SENTINEL = "s3ntinel-RAW-value-9416-do-not-print"
REAL_TRUFFLEHOG = shutil.which("trufflehog")

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


def _finding(source: str, location: dict, detector: object = "PrivateKey", raw: str = SENTINEL, **extra: object) -> str:
    record = {
        "DetectorName": detector,
        "Raw": raw,
        "RawV2": raw + "v2",
        "Redacted": raw[:12],
        "ExtraData": {"hint": raw},
        "StructuredData": {"key": raw},
        "SecretParts": {"key": raw},
        "SourceMetadata": {"Data": {source: location}},
        **extra,
    }
    return json.dumps(record) + "\n"


TREE_FINDINGS = _finding("Filesystem", {"file": "app.py", "line": 3}) * 2
GIT_FINDINGS = _finding(
    "Git", {"file": "conf/k.txt", "line": 1, "commit": "0123456789abcdef0123", "email": "t@example.invalid"}
)
REPORT_LINE = re.compile(
    re.escape(ssl.MSG_REPORT_LABEL) + r": (secret-scan-(tree|history)-[0-9a-f]{16}\.jsonl) in a new secret-scan-\* "
    r"directory under the system temp directory, log beside it with \.log appended"
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
    _use_temp_root(monkeypatch, scratch)
    return {"record": record, "findings": findings, "tmp": scratch}


def _use_temp_root(monkeypatch: pytest.MonkeyPatch, directory: Path) -> None:
    monkeypatch.setenv("TMPDIR", str(directory))
    monkeypatch.setattr(tempfile, "tempdir", None)


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


def _assert_absent(captured: pytest.CaptureResult[str], *needles: str) -> None:
    for needle in (SENTINEL, SENTINEL[:12], *needles):
        assert needle not in captured.out
        assert needle not in captured.err


def _report_path(out: str, temp_root: Path) -> Path:
    """The report: the console names only the generated file, never its directory."""
    (name,) = [match.group(1) for line in out.splitlines() if (match := REPORT_LINE.fullmatch(line))]
    (path,) = temp_root.glob(f"{ssl.OUTPUT_PREFIX}*/{name}")
    return path


def _console_body(out: str) -> list[str]:
    """stdout without the report-location line, which must be the first line."""
    first, *rest = out.splitlines()
    assert REPORT_LINE.fullmatch(first)
    return rest


def _all_paths(root: Path) -> set[Path]:
    return {path for path in root.rglob("*") if ".git" not in path.relative_to(root).parts}


# --- Console carries totals, closed-set detector counts and fixed text only ----------------


def test_tree_findings_print_only_totals_and_detector_counts(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_absent(captured, "app.py\t", "\t3")
    assert _console_body(captured.out) == ["mode: tree, files scanned: 3", "findings: 2", "  PrivateKey: 2"]
    assert captured.err == ""
    # The raw values are kept, but only in the owner-only report outside the repository.
    report = _report_path(captured.out, stub["tmp"])
    assert SENTINEL in report.read_text(encoding="utf-8")
    assert not report.is_relative_to(repo)


SECRET_A = "AKIA" + "Q7X2" * 6 + "-first-secret"
SECRET_B = "ghp_" + "Zb9" * 10 + "-second-secret"
SECRET_C = "xoxb-" + "1234567890" * 4 + "-third-secret"
MILLION = 1_000_000


def _adversarial_report() -> tuple[str, list[str]]:
    """Findings whose non-secret fields carry other findings' secrets, encodings and fragments."""
    b64 = base64.b64encode(SECRET_B.encode()).decode()
    fragments = [SECRET_C[:12], SECRET_C[12:24], SECRET_C[24:36], SECRET_C[36:]]
    lines = [
        _finding("Filesystem", {"file": "ok.txt", "line": 1}, detector="AWS", raw=SECRET_A),
        # Another finding's raw secret inside a path, and as a commit id.
        _finding("Git", {"file": f"conf/{SECRET_A}.txt", "line": 2, "commit": SECRET_A}, raw=SECRET_B),
        # Base64 of a secret: matches any path-like character class.
        _finding("Filesystem", {"file": f"b/{b64}", "line": 3}, detector="Github", raw=SECRET_B),
        # One secret split across detector, file, commit and line.
        _finding(
            "Git",
            {"file": fragments[1], "commit": fragments[2], "line": fragments[3]},
            detector=fragments[0],
            raw=SECRET_C,
        ),
        # Million-character fields, including the detector name.
        _finding(
            "Filesystem",
            {"file": "a/" + "x" * MILLION + SECRET_A, "line": "9" * MILLION},
            detector="Z" * MILLION,
            raw="r" * MILLION,
        ),
        # Detector name that is a secret with control characters; extra fields with secrets.
        _finding(
            "Git",
            {"file": "a.txt", "line": 1, "email": SECRET_B, "message": SECRET_C},
            detector=f"Key\n{SECRET_A}\t",
            raw=SECRET_C,
        ),
        # Unknown top-level key named after a secret; case-variant of a known detector.
        _finding("Filesystem", {"file": "a.txt", "line": 1}, detector="privatekey", **{SECRET_B: SECRET_C}),
        _finding("Filesystem", {"file": "a.txt", "line": 1}, detector="PrivateKey"),
    ]
    needles = [SECRET_A, SECRET_B, SECRET_C, b64, b64[:16], *fragments, "x" * 64, "Z" * 64, "9" * 64, "r" * 64]
    return "".join(lines), needles


def test_console_never_contains_any_finding_field(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    report, needles = _adversarial_report()
    stub["findings"].write_text(report, encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    # Exact match: nothing but the allowlisted totals, detector counts and fixed text.
    assert _console_body(captured.out) == [
        "mode: tree, files scanned: 3",
        "findings: 8",
        "  AWS: 1",
        "  Github: 1",
        "  PrivateKey: 2",
        "  other: 4",
    ]
    assert captured.err == ""
    _assert_absent(captured, *needles, "ok.txt", "conf/", "a.txt")
    assert len(captured.out) < 500


def test_show_keys_prints_only_closed_set_keys_and_counts(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    report, needles = _adversarial_report()
    path = tmp_path / "report.jsonl"
    path.write_text(report, encoding="utf-8")
    assert ssl.main(["show-keys", str(path)]) == ssl.EXIT_CLEAN
    captured = capfd.readouterr()
    shown = sorted(
        {"DetectorName", "ExtraData", "Raw", "RawV2", "Redacted", "SecretParts", "SourceMetadata", "StructuredData"}
    )
    assert captured.out.splitlines() == [
        f"keys: {', '.join(shown)}",
        "keys outside the TruffleHog result format: 1",
        "findings: 8",
        "  AWS: 1",
        "  Github: 1",
        "  PrivateKey: 2",
        "  other: 4",
    ]
    assert captured.err == ""
    _assert_absent(captured, *needles, str(tmp_path))
    assert _calls(stub) == []  # show-keys never runs TruffleHog


def test_detector_closed_set_is_well_formed() -> None:
    assert len(ssl.KNOWN_DETECTORS) > 1000
    assert all(re.fullmatch(r"[A-Za-z0-9]{1,64}", name) for name in ssl.KNOWN_DETECTORS)
    assert ssl.OTHER_DETECTOR.lower() not in {name.lower() for name in ssl.KNOWN_DETECTORS}
    assert {"AWS", "Github", "PrivateKey", "Lob"} <= ssl.KNOWN_DETECTORS


@pytest.mark.skipif(REAL_TRUFFLEHOG is None, reason="TruffleHog is not installed")
def test_detector_closed_set_matches_the_installed_trufflehog(tmp_path: Path) -> None:
    """Every compiled-in name is a detector type the installed TruffleHog recognizes."""
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")

    def accepted(names: list[str]) -> bool:
        result = subprocess.run(
            [
                str(REAL_TRUFFLEHOG),
                *("filesystem", "--no-update", "--no-verification", "--json"),
                f"--include-detectors={','.join(names)}",
                str(empty),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return "unrecognized detector type" not in result.stderr

    assert not accepted(["NotARealDetector9416"])  # the probe can fail
    assert accepted(sorted(ssl.KNOWN_DETECTORS))


@pytest.mark.skipif(REAL_TRUFFLEHOG is None, reason="TruffleHog is not installed")
def test_real_trufflehog_finding_is_counted_without_printing_it(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    crypto = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")
    serialization = pytest.importorskip("cryptography.hazmat.primitives.serialization")
    key = crypto.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
    ).decode()
    (repo / "fixture.pem").write_text(pem, encoding="utf-8")
    temp_root = tmp_path / "real-tmp"
    temp_root.mkdir()
    _use_temp_root(monkeypatch, temp_root)
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    assert _console_body(captured.out) == ["mode: tree, files scanned: 4", "findings: 1", "  PrivateKey: 1"]
    body = pem.splitlines()[1]
    assert body not in captured.out + captured.err
    assert "fixture.pem" not in captured.out + captured.err
    assert body in _report_path(captured.out, temp_root).read_text(encoding="utf-8")


# --- Output location: a fresh private directory under the system temp root -----------------


def test_output_location_is_only_the_generated_temp_directory(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    before = _all_paths(tmp_path)
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_FINDINGS
    report = _report_path(capfd.readouterr().out, stub["tmp"])
    created = _all_paths(tmp_path) - before - {stub["record"]}
    assert created == {report.parent, report, report.with_name(report.name + ".log")}
    assert report.parent.parent == stub["tmp"].resolve()
    assert report.parent.name.startswith(ssl.OUTPUT_PREFIX)


def test_report_directory_and_files_are_owner_only(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    previous = os.umask(0o022)
    try:
        ssl.main(["--repo", str(repo), "tree"])
    finally:
        os.umask(previous)
    report = _report_path(capfd.readouterr().out, stub["tmp"])
    assert stat.S_IMODE(report.parent.stat().st_mode) == 0o700
    for path in (report, report.with_name(report.name + ".log")):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_report_creation_is_exclusive_and_never_follows_a_symlink(tmp_path: Path) -> None:
    existing = tmp_path / "exists.jsonl"
    existing.write_text("keep\n", encoding="utf-8")
    target = tmp_path / "target"
    link = tmp_path / "link.jsonl"
    link.symlink_to(target)
    for path in (existing, link):
        with pytest.raises(ssl.ScanError, match=r"cannot create output file \(EEXIST\)"):
            ssl._create_private(path)
    assert existing.read_text(encoding="utf-8") == "keep\n"
    assert not target.exists()


def test_tool_stderr_goes_to_owner_only_log_not_console(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    ssl.main(["--repo", str(repo), "tree"])
    report = _report_path(capfd.readouterr().out, stub["tmp"])
    log = report.with_name(report.name + ".log")
    assert SENTINEL in log.read_text(encoding="utf-8")


@pytest.mark.parametrize("where", ["repo", "repo-subdir", "symlink-alias-of-repo", "primary-of-worktree"])
@pytest.mark.parametrize("mode", ["tree", "history"])
def test_temp_root_inside_the_repository_is_refused_before_any_write(
    stub: dict[str, Path],
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    where: str,
    mode: str,
    capfd: pytest.CaptureFixture[str],
) -> None:
    _git("remote", "add", "origin", "https://example.invalid/remote.git", cwd=repo)
    scanned = repo
    temp_root = {"repo": repo, "repo-subdir": repo / "pkg", "primary-of-worktree": repo / "pkg"}.get(where)
    if where == "symlink-alias-of-repo":
        temp_root = tmp_path / "alias"
        temp_root.symlink_to(repo, target_is_directory=True)
    if where == "primary-of-worktree":
        scanned = tmp_path / "wt"
        _git("worktree", "add", "-q", "-b", "t", str(scanned), cwd=repo)
    assert temp_root is not None
    before = _all_paths(repo)
    _use_temp_root(monkeypatch, temp_root)
    assert ssl.main(["--repo", str(scanned), mode]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_TEMP_INSIDE}"
    assert captured.out == ""
    _assert_absent(captured, str(tmp_path))
    assert _all_paths(repo) == before
    assert _calls(stub) == []


# --- Exit codes and fixed diagnostics ------------------------------------------------------


def test_no_findings_exit_zero(stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]) -> None:
    stub["findings"].write_text("", encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_CLEAN
    assert _console_body(capfd.readouterr().out) == ["mode: tree, files scanned: 3", "findings: 0"]


def test_tool_error_exit_two_without_leaking(
    stub: dict[str, Path], repo: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("STUB_EXIT", "1")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == (
        "secret_scan_local: trufflehog exited 1 (scan error); details in the owner-only log beside the report"
    )
    assert len(_console_body(captured.out)) == 0


def test_unparseable_report_line_is_not_echoed(
    stub: dict[str, Path], repo: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_text(f"not json {SENTINEL}\n", encoding="utf-8")
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == "secret_scan_local: unparseable JSON at report line 1"


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
    offline = ("--json", "--no-verification", "--no-update", "--results=unverified", "--exclude-detectors=Lob")
    for flag in (*offline, "--fail-on-scan-errors"):
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


def test_help_meets_cli_standard() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0
    for section in ("Examples:", "Outputs:", "Exit codes:", "Related:", "--no-verification", "show-keys"):
        assert section in result.stdout


@pytest.mark.parametrize(
    "argv",
    [
        ["--timeout-seconds", SENTINEL, "tree"],
        ["--timeout-seconds", "0", "tree"],
        [f"--{SENTINEL}", "tree"],
        [f"--{SENTINEL}={SENTINEL}", "tree"],
        [SENTINEL],
        ["tree", SENTINEL],
        ["tree", "--remote", SENTINEL],
        ["--output", SENTINEL, "tree"],
        ["--max-rows", "5", "tree"],
        ["history", "--mirror-parent", SENTINEL],
        ["show-keys"],
        ["show-keys", "a", SENTINEL],
    ],
)
def test_usage_errors_never_echo_the_supplied_value(
    stub: dict[str, Path], repo: Path, argv: list[str], capfd: pytest.CaptureFixture[str]
) -> None:
    assert ssl.main(["--repo", str(repo), *argv]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_USAGE}"
    assert captured.out == ""
    assert _calls(stub) == []


def test_usage_error_from_the_command_line_has_the_fixed_message() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--timeout-seconds", SENTINEL, "tree"],
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


def test_path_values_are_never_echoed(
    stub: dict[str, Path], repo: Path, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "loop").symlink_to(tmp_path / "loop")
    attempts = {
        ("--repo", str(tmp_path / SENTINEL), "tree"): "git rev-parse failed (exit 128)",
        ("show-keys", str(tmp_path / SENTINEL)): "cannot open the report (ENOENT)",
        ("show-keys", str(tmp_path / "loop")): "cannot open the report (ELOOP)",
        ("show-keys", str(tmp_path)): "cannot open the report (EISDIR)",
    }
    for argv, message in attempts.items():
        assert ssl.main(list(argv)) == ssl.EXIT_ERROR
        captured = capfd.readouterr()
        _assert_absent(captured, str(tmp_path))
        assert captured.err.strip() == f"secret_scan_local: {message}"
    assert _calls(stub) == []


def test_show_keys_refuses_a_non_regular_file(tmp_path: Path, capfd: pytest.CaptureFixture[str]) -> None:
    fifo = tmp_path / f"{SENTINEL}.fifo"
    os.mkfifo(fifo)
    fd = os.open(fifo, os.O_RDWR)  # keeps the open from blocking
    try:
        assert ssl.main(["show-keys", str(fifo)]) == ssl.EXIT_ERROR
    finally:
        os.close(fd)
    captured = capfd.readouterr()
    _assert_absent(captured, str(tmp_path))
    assert captured.err.strip() == "secret_scan_local: the report is not a regular file"


def test_unexpected_exception_prints_only_its_type(
    stub: dict[str, Path], repo: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    def boom(_fh: object) -> ssl.Summary:
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(ssl, "summarize", boom)
    assert ssl.main(["--repo", str(repo), "tree"]) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == "secret_scan_local: internal error (RuntimeError)"


# --- Report structure ----------------------------------------------------------------------

MALFORMED_LINES = [
    "[]",
    "3",
    json.dumps(SENTINEL),
    "null",
    "{}",
    json.dumps({"Raw": SENTINEL}),
    json.dumps({"DetectorName": ["x"], "Raw": SENTINEL}),
    json.dumps({"DetectorName": "X", "Raw": SENTINEL}),
    json.dumps({"DetectorName": "X", "SourceMetadata": [SENTINEL]}),
    json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {}}}),
    json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {"Git": SENTINEL}}}),
    json.dumps({"DetectorName": "X", "SourceMetadata": {"Data": {"Git": {}, "Filesystem": {}}}}),
    "[" * 100_000 + "]" * 100_000,
]


@pytest.mark.parametrize("line", MALFORMED_LINES, ids=lambda line: line[:40])
@pytest.mark.parametrize("entry", ["tree", "show-keys"])
def test_unexpected_report_structure_is_a_typed_error(
    stub: dict[str, Path], repo: Path, line: str, entry: str, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_text(line + "\n", encoding="utf-8")
    argv = ["--repo", str(repo), "tree"] if entry == "tree" else ["show-keys", str(stub["findings"])]
    assert ssl.main(argv) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() in {
        "secret_scan_local: unparseable JSON at report line 1",
        "secret_scan_local: unexpected report structure at line 1",
    }


@pytest.mark.parametrize("entry", ["tree", "show-keys"])
def test_non_utf8_report_is_a_typed_error(
    stub: dict[str, Path], repo: Path, entry: str, capfd: pytest.CaptureFixture[str]
) -> None:
    stub["findings"].write_bytes(b'{"Raw": "\xff' + SENTINEL.encode() + b'"}\n')
    argv = ["--repo", str(repo), "tree"] if entry == "tree" else ["show-keys", str(stub["findings"])]
    assert ssl.main(argv) == ssl.EXIT_ERROR
    captured = capfd.readouterr()
    _assert_absent(captured)
    assert captured.err.strip() == "secret_scan_local: the report is not valid UTF-8"


# --- Tree candidates -----------------------------------------------------------------------


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


# --- history: validated https remote, absolute-path mirror, always removed -----------------

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


@pytest.fixture
def clone_dests(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Records the destination of every mirror clone."""
    dests: list[str] = []
    original = ssl.clone_command

    def record(url: str, dest: str) -> list[str]:
        dests.append(dest)
        return original(url, dest)

    monkeypatch.setattr(ssl, "clone_command", record)
    return dests


def _assert_mirror_was_temporary(dests: list[str], temp_root: Path) -> None:
    (dest,) = dests
    assert os.path.isabs(dest)
    mirror_dir = Path(dest).parent
    assert mirror_dir.parent == temp_root.resolve()
    assert mirror_dir.name.startswith(ssl.MIRROR_PREFIX)
    assert not mirror_dir.exists()
    assert not list(temp_root.glob(f"{ssl.MIRROR_PREFIX}*"))


def test_history_scans_a_bare_mirror_and_removes_it(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    clone_dests: list[str],
    capfd: pytest.CaptureFixture[str],
) -> None:
    stub["findings"].write_text(GIT_FINDINGS, encoding="utf-8")
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_FINDINGS
    captured = capfd.readouterr()
    _assert_absent(captured, "t@example.invalid", "conf/k.txt", "0123456789")
    assert _console_body(captured.out) == ["mode: history", "findings: 1", "  PrivateKey: 1"]
    (call,) = _calls(stub)
    assert call["argv"][0] == "git"
    assert "--bare" in call["argv"]
    assert "--no-verification" in call["argv"]
    assert call["mirror"] == {"path": clone_dests[0], "bare": True}
    assert call["cwd"] == str(Path(clone_dests[0]).parent)
    _assert_mirror_was_temporary(clone_dests, stub["tmp"])


@pytest.mark.parametrize("failure", ["scan", "clone"])
def test_history_removes_mirror_when_a_step_fails(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    clone_dests: list[str],
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    capfd: pytest.CaptureFixture[str],
) -> None:
    if failure == "scan":
        monkeypatch.setenv("STUB_EXIT", "1")
        expected = "trufflehog exited 1 (scan error)"
    else:
        _git("remote", "set-url", "origin", REMOTE_BASE + "missing.git", cwd=cloned)
        expected = "mirror clone of the configured remote failed (exit 128)"
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert capfd.readouterr().err.strip() == (
        f"secret_scan_local: {expected}; details in the owner-only log beside the report"
    )
    _assert_mirror_was_temporary(clone_dests, stub["tmp"])


def test_history_removes_mirror_when_interrupted(
    stub: dict[str, Path],
    cloned: Path,
    local_transport: None,
    clone_dests: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupt(*_args: object, **_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(ssl, "_run_trufflehog", interrupt)
    with pytest.raises(KeyboardInterrupt):
        ssl.main(["--repo", str(cloned), "history"])
    _assert_mirror_was_temporary(clone_dests, stub["tmp"])


def test_tool_failure_messages_are_fixed(
    stub: dict[str, Path], cloned: Path, local_transport: None, capfd: pytest.CaptureFixture[str]
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


def test_history_option_values_are_never_echoed(
    stub: dict[str, Path], cloned: Path, local_transport: None, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    for remote in (SENTINEL, f"{SENTINEL}/../x", f"--upload-pack={SENTINEL}"):
        assert ssl.main(["--repo", str(cloned), "history", "--remote", remote]) == ssl.EXIT_ERROR
        _assert_absent(capfd.readouterr(), str(tmp_path))
    assert _calls(stub) == []


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
        "https://exa\u202emple.invalid/remote.git",
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
    assert captured.err.strip() == f"secret_scan_local: {ssl.MSG_REMOTE_URL}"
    assert not mark.exists()
    assert _calls(stub) == []
    assert not list(stub["tmp"].glob("secret-scan-*"))  # refused before any report or mirror exists


def test_clone_command_ends_option_parsing_and_drops_credential_helpers() -> None:
    cmd = ssl.clone_command("--upload-pack=x", "/abs/mirror.git")
    assert cmd[: cmd.index("clone")] == ["git", "-c", "credential.helper="]
    assert cmd[cmd.index("clone") :] == ["clone", "--quiet", "--mirror", "--", "--upload-pack=x", "/abs/mirror.git"]


def test_mirror_clone_transport_is_https_only(
    stub: dict[str, Path], cloned: Path, clone_dests: list[str], capfd: pytest.CaptureFixture[str]
) -> None:
    # The validated https URL is rewritten to a local path by the user's git config;
    # with the production transport allowlist git must refuse it.
    assert ssl.CLONE_PROTOCOLS == "https"
    assert ssl.main(["--repo", str(cloned), "history"]) == ssl.EXIT_ERROR
    assert "mirror clone of the configured remote failed" in capfd.readouterr().err
    assert _calls(stub) == []
    _assert_mirror_was_temporary(clone_dests, stub["tmp"])


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


@pytest.fixture
def locked_mirror(stub: dict[str, Path], monkeypatch: pytest.MonkeyPatch):
    """The stub makes the mirror's directory read-only, so removing ``mirror.git`` really fails."""
    if os.geteuid() == 0:
        pytest.skip("root ignores directory permissions")
    monkeypatch.setenv("STUB_LOCK", "1")
    yield
    for left in stub["tmp"].glob(f"{ssl.MIRROR_PREFIX}*"):
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
    assert list(stub["tmp"].glob(f"{ssl.MIRROR_PREFIX}*"))  # the failure is real, and reported


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
