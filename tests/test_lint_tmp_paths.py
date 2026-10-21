from __future__ import annotations

import pytest

from scripts.hygiene import lint_tmp_paths as lint

LITERAL = "/" + "tmp/fixture"


def test_repository_literal_guard(capsys):
    assert lint.main([]) == 0, capsys.readouterr().out


def test_allowlist_is_exact_counted_and_line_independent(tmp_path, monkeypatch):
    path = tmp_path / "scripts/a.py"
    path.parent.mkdir()
    line = f'ROOT = "{LITERAL}"'
    path.write_text("# heading\n" + line + "\n")
    monkeypatch.setattr(lint, "ALLOWLIST", (("scripts/a.py", "fixture only", lint.line_digest(line) + ":1"),))
    assert lint.find_literal_tmp_paths(tmp_path) == []
    path.write_text(line + "\n" + line + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/a.py", 2)]
    path.write_text(line.replace("fixture", "new-producer") + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/a.py", 1)]
    monkeypatch.setattr(lint, "ALLOWLIST", (("scripts/a.py", "", ""),))
    with pytest.raises(ValueError, match="reason"):
        lint.find_literal_tmp_paths(tmp_path)


SYSTEM_TMP = "/" + "tmp"
VAR_TMP = "/var" + SYSTEM_TMP


@pytest.mark.parametrize("method", sorted(lint.TEMP_CALLS))
@pytest.mark.parametrize("arguments", ["", 'prefix="probe-"', "dir=None", 'dir="scratch"', "**options"])
def test_tempfile_requires_explicit_approved_dir(method, arguments):
    findings = lint.scan_python(f"import tempfile\ntempfile.{method}({arguments})\n", "scripts/probe.py")
    assert len(findings) == 1
    assert findings[0].line == 2
    assert "dir=" in findings[0].message


@pytest.mark.parametrize("method", sorted(lint.TEMP_CALLS))
@pytest.mark.parametrize(
    "directory",
    [
        'os.environ["TMPDIR"]',
        'os.environ["LU_TASK_SCRATCH_DIR"]',
        'os.getenv("LU_RUNTIME_TMP_ROOT", ensure_scratch_root())',
        'os.getenv("TMPDIR", os.environ["LU_TASK_SCRATCH_DIR"])',
        'os.environ.get("TMPDIR", ensure_scratch_root())',
        f'os.getenv("TMPDIR", {lint.MANAGED_ROOT!r})',
        f'os.environ.get("TMPDIR", {(lint.MANAGED_ROOT + "/probe")!r})',
        "TMPDIR",
        "LU_TASK_SCRATCH_DIR",
        "LU_RUNTIME_TMP_ROOT",
        "ensure_scratch_root()",
        "scratch.resolve_scratch_root()",
        'Path(os.environ["TMPDIR"]) / "child"',
        "tmp_path",
        'tmp_path / "foo"',
        'tmp_path_factory.mktemp("probe")',
        "tmp_path_factory.getbasetemp()",
    ],
)
def test_approved_scratch_expressions_pass(method, directory):
    source = f"import tempfile\nimport os\ntempfile.{method}(dir={directory})\n"
    assert lint.scan_python(source, "tests/probe.py") == []


@pytest.mark.parametrize(
    "directory",
    [
        'settings["TMPDIR"]',
        'os.environ["HOME"]',
        'os.getenv("TMPDIR")',
        'os.getenv("LU_RUNTIME_TMP_ROOT")',
        'os.environ.get("TMPDIR")',
        'os.environ.get("LU_RUNTIME_TMP_ROOT")',
        'os.getenv("TMPDIR", ".")',
        'os.getenv("TMPDIR", None)',
        'os.environ.get("TMPDIR", None)',
        'os.getenv("TMPDIR", os.environ.get("LU_TASK_SCRATCH_DIR"))',
        'os.environ.get("TMPDIR", os.getenv("LU_RUNTIME_TMP_ROOT"))',
        'os.getenv("TMPDIR", "")',
        f'os.getenv("TMPDIR", {(lint.MANAGED_ROOT + "/../../outside")!r})',
        f'os.environ.get("TMPDIR", {SYSTEM_TMP!r})',
        'tmp_path / "../outside"',
        'tmp_path / "/outside"',
        'ensure_scratch_root("unapproved")',
        "tempfile.gettempdir()",
        "strange_call(TMPDIR)",
        'Path("unmanaged")',
        "os.getenv()",
    ],
)
def test_unapproved_expressions_are_rejected(directory):
    assert lint.scan_python(f"tempfile.mkdtemp(dir={directory})", "scripts/probe.py")


@pytest.mark.parametrize("root", [SYSTEM_TMP, VAR_TMP])
@pytest.mark.parametrize("suffix", ["", "/", "/foo"])
@pytest.mark.parametrize("expression", ["Path({value!r})", "root = {value!r}", "root = b{value!r}"])
def test_literal_paths_are_flagged(root, suffix, expression):
    findings = lint.scan_python(expression.format(value=root + suffix), "scripts/probe.py")
    assert len(findings) == 1
    assert findings[0].line == 1
    assert "literal system temp path" in findings[0].message


@pytest.mark.parametrize(
    "value",
    [
        VAR_TMP + "/lu",
        VAR_TMP + "/lu/",
        VAR_TMP + "/lu/child",
        SYSTEM_TMP + "files",
        "/home/user" + SYSTEM_TMP + "/foo",
        "$TMPDIR/probe",
        "${LU_TASK_SCRATCH_DIR}/probe",
    ],
)
def test_path_boundaries_and_managed_root_pass(value):
    assert not lint.has_literal_temp_path(value)


@pytest.mark.parametrize(
    "value",
    [
        VAR_TMP + "/lu-other",
        VAR_TMP + "/lu/../outside",
        VAR_TMP + "/lu/../../outside",
        VAR_TMP + "/lu " + SYSTEM_TMP + "/bad",
        SYSTEM_TMP + "/../var" + SYSTEM_TMP + "/lu/child",
        "output=" + SYSTEM_TMP + "/file",
        "copy " + SYSTEM_TMP + "/file",
    ],
)
def test_managed_root_exception_cannot_hide_other_paths(value):
    assert lint.has_literal_temp_path(value)


@pytest.mark.parametrize("method", sorted(lint.TEMP_CALLS))
@pytest.mark.parametrize(
    "import_style", ["import tempfile as tf", "from tempfile import {method} as create", "from tempfile import *"]
)
def test_every_tempfile_import_style(method, import_style):
    prefix = import_style.format(method=method)
    name = "tf." + method if prefix.startswith("import ") else "create" if " as " in prefix else method
    assert len(lint.scan_python(prefix + "\n" + name + "()", "scripts/probe.py")) == 1
    assert lint.scan_python(prefix + "\n" + name + "(dir=tmp_path)", "tests/probe.py") == []


@pytest.mark.parametrize("root", [SYSTEM_TMP, VAR_TMP, "/private" + SYSTEM_TMP, "/dev/" + "shm"])
@pytest.mark.parametrize("suffix", ["", "/", "/probe"])
def test_all_temp_roots_in_repository_guard(tmp_path, root, suffix):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text(f'ROOT = "{root}{suffix}"\n')
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/probe.py", 1)]


def test_decoded_python_string_cannot_bypass_guard(tmp_path):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text('ROOT = "\\x2ftmp/probe"\n')
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/probe.py", 1)]


@pytest.mark.parametrize(
    "command",
    ["mktemp", "mktemp -d", "ROOT=$(mktemp -d)", "ROOT=`mktemp -d`", "command mktemp -d", "/usr/bin/mktemp -d"],
)
def test_shell_mktemp_invocations(command):
    assert lint.scan_shell(command + "\n", "scripts/probe.sh")


@pytest.mark.parametrize(
    "command",
    [
        'mktemp -d "$TMPDIR/probe.XXXXXX"',
        'mktemp -p "${TMPDIR}"',
        'mktemp --tmpdir="$LU_TASK_SCRATCH_DIR"',
        'ROOT=$(mktemp -d "$TMPDIR/probe.XXXXXX")',
    ],
)
def test_shell_managed_mktemp_passes(command):
    assert lint.scan_shell(command + "\n", "scripts/probe.sh") == []


@pytest.mark.parametrize("command", ['mktemp -d "$TMPDIR/../outside.XXXXXX"', 'mktemp -p "$HOME"'])
def test_shell_unmanaged_mktemp_fails(command):
    assert lint.scan_shell(command + "\n", "scripts/probe.sh")


@pytest.mark.parametrize("quote", ["'", '"', ""])
def test_shell_heredoc_does_not_hide_next_command(quote):
    source = f"cat <<{quote}EOF{quote}\nIt's data\nEOF\nmktemp -d\n"
    findings = lint.scan_shell(source, "scripts/probe.sh")
    assert len(findings) == 1 and findings[0].line == 4


def test_shell_unquoted_heredoc_executes_substitution():
    findings = lint.scan_shell("cat <<EOF\n$(mktemp -d)\nEOF\n", "scripts/probe.sh")
    assert len(findings) == 1 and findings[0].line == 2


def test_shell_incomplete_quote_retains_findings():
    findings = lint.scan_shell('mktemp -d\necho "unclosed\n', "scripts/probe.sh")
    assert len(findings) == 1 and findings[0].line == 1


def test_repeated_producer_exceeds_counted_baseline(tmp_path, monkeypatch):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text("import tempfile\ntempfile.mkdtemp()\n")
    row = lint.scan_lines(tmp_path)[0]
    monkeypatch.setattr(lint, "ALLOWLIST", ((row[0], "legacy producer (#8755)", lint.line_digest(row[2]) + ":1"),))
    path.write_text(path.read_text() + "tempfile.mkdtemp()\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/probe.py", 3)]


@pytest.mark.parametrize("source", ['echo "<<EOF"\nmktemp -d\n', "if mktemp -d; then :; fi", "f() { mktemp -d; }"])
def test_shell_control_flow_and_quoted_operator_do_not_hide_calls(source):
    assert lint.scan_shell(source, "scripts/probe.sh")
