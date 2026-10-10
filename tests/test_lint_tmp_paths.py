from __future__ import annotations

from pathlib import Path

import pytest

from scripts.hygiene import lint_tmp_paths as lint

LITERAL = "/" + "tmp/fixture"


def test_repository_literal_guard(capsys):
    assert lint.main([]) == 0, capsys.readouterr().out


def test_python_shell_tests_and_help_are_scanned(tmp_path):
    for relative in ("scripts/a.py", "scripts/a.sh", "tests/a.py"):
        path = tmp_path / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# example: {LITERAL}\n")
    assert len(lint.find_literal_tmp_paths(tmp_path)) == 3


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


def test_managed_and_harness_paths_do_not_match(tmp_path):
    path = tmp_path / "scripts/a.py"
    path.parent.mkdir()
    path.write_text('ROOT = "$TMPDIR/probe"\n# ~/.gemini' + LITERAL.replace("fixture", "project") + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == []


def test_cli_exit_status(tmp_path, capsys):
    assert lint.main(["--repo", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "literal_tmp_findings=0\n"
    path = tmp_path / "tests/a.py"
    path.parent.mkdir()
    path.write_text(f'ROOT = "{LITERAL}"\n')
    assert lint.main(["--repo", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "tests/a.py:1" in out and "literal_tmp_findings=1" in out
    assert "$TMPDIR/" in out and "tempfile.TemporaryDirectory()/NamedTemporaryFile()" in out
    assert "scripts/hygiene/lint_tmp_paths.py" in out and "ALLOWLIST" in out
    assert "specific reason" in out and "#9702" in out
    assert f"counted fingerprint={lint.line_digest(path.read_text().strip())}:1" in out
    assert "maximum allowed count" in out and "never a whole-file exemption" in out
    assert LITERAL not in out


def test_cli_repeated_allowlisted_line_reports_total_count(tmp_path, monkeypatch, capsys):
    path = tmp_path / "tests/a.py"
    path.parent.mkdir()
    line = f'ROOT = "{LITERAL}"'
    digest = lint.line_digest(line)
    monkeypatch.setattr(lint, "ALLOWLIST", (("tests/a.py", "fixture only", f"{digest}:1"),))
    path.write_text(line + "\n" + line + "  \n")
    assert lint.main(["--repo", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "tests/a.py:2" in out and "tests/a.py:1" not in out
    assert f"counted fingerprint={digest}:2" in out
    assert "Merge the fingerprint into the file's existing entry" in out
    assert "literal_tmp_findings=1" in out and LITERAL not in out


def test_prevention_examples_and_worker_preamble_use_managed_lease():
    from scripts import delegate
    from scripts.review import integration_check
    from scripts.wiki.diagnostics import retrieval_probe_9233

    prompt = delegate._augment_prompt_with_worktree("test", Path.cwd(), mode="workspace-write")
    assert "use `$TMPDIR`, the managed lease, never a literal system temp path" in prompt
    for parser in (integration_check.build_parser(), retrieval_probe_9233.build_parser()):
        help_text = parser.format_help()
        assert "$TMPDIR/" in help_text
        assert LITERAL.split("fixture")[0] not in help_text


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


@pytest.mark.parametrize(
    "source",
    [
        "import tempfile as tf\ntf.mkdtemp()",
        "from tempfile import mkstemp\nmkstemp()",
        "from tempfile import TemporaryDirectory as TD\nTD()",
    ],
)
def test_tempfile_import_aliases_are_checked(source):
    assert len(lint.scan_python(source, "scripts/probe.py")) == 1


def test_environment_and_path_aliases_pass():
    source = (
        "import os as operating\nfrom pathlib import Path as P\n"
        "from tempfile import mkdtemp as create\n"
        'create(dir=P(operating.environ["TMPDIR"]))'
    )
    assert lint.scan_python(source, "scripts/probe.py") == []


def test_unrelated_tempfile_method_name_is_not_flagged():
    assert lint.scan_python("other.mkdtemp()", "scripts/probe.py") == []


@pytest.mark.parametrize("root", [SYSTEM_TMP, VAR_TMP])
@pytest.mark.parametrize("suffix", ["", "/", "/foo"])
@pytest.mark.parametrize("expression", ["Path({value!r})", "root = {value!r}", "root = b{value!r}"])
def test_literal_paths_are_flagged(root, suffix, expression):
    findings = lint.scan_python(expression.format(value=root + suffix), "scripts/probe.py")
    assert len(findings) == 1
    assert findings[0].line == 1
    assert "literal system temp path" in findings[0].message


def test_fstring_literal_is_flagged():
    assert lint.scan_python(f'root = f"{SYSTEM_TMP}/{{name}}"', "scripts/probe.py")


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


def test_tmp_path_in_test_passes():
    assert lint.scan_python('def test_file(tmp_path):\n    path = tmp_path / "foo"', "tests/probe.py") == []


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


@pytest.mark.parametrize(
    "value", ["/private" + SYSTEM_TMP + "files", "/home/user/private" + SYSTEM_TMP + "/file", "/dev/" + "shm-other"]
)
def test_expanded_roots_keep_path_boundaries(value):
    assert not lint.has_literal_temp_path(value)


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


@pytest.mark.parametrize(
    "source",
    [
        "# mktemp -d\n",
        'echo "mktemp -d"\n',
        "cat <<'EOF'\nmktemp -d\nIt's just data\nEOF\n",
        'cat <<"EOF"\n"unbalanced\nEOF\n',
    ],
)
def test_shell_comments_quotes_and_quoted_heredocs(source):
    assert lint.scan_shell(source, "scripts/probe.sh") == []


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


def test_producer_baseline_fingerprints_whole_call(tmp_path, monkeypatch):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text('import tempfile\ntempfile.mkdtemp(\n    prefix="old-",\n)\n')
    rows = lint.scan_lines(tmp_path)
    assert len(rows) == 1 and rows[0][1] == 2
    monkeypatch.setattr(
        lint, "ALLOWLIST", ((rows[0][0], "legacy producer (#8755)", lint.line_digest(rows[0][2]) + ":1"),)
    )
    assert lint.find_literal_tmp_paths(tmp_path) == []
    path.write_text(path.read_text().replace("old-", "new-"))
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/probe.py", 2)]


def test_repeated_producer_exceeds_counted_baseline(tmp_path, monkeypatch):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text("import tempfile\ntempfile.mkdtemp()\n")
    row = lint.scan_lines(tmp_path)[0]
    monkeypatch.setattr(lint, "ALLOWLIST", ((row[0], "legacy producer (#8755)", lint.line_digest(row[2]) + ":1"),))
    path.write_text(path.read_text() + "tempfile.mkdtemp()\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/probe.py", 3)]


def test_cli_invalid_python_is_private_error(tmp_path, capsys):
    path = tmp_path / "scripts/probe.py"
    path.parent.mkdir()
    path.write_text("def broken(:\n")
    assert lint.main(["--repo", str(tmp_path)]) == 2
    out = capsys.readouterr()
    assert "cannot read or parse source" in out.err
    assert str(tmp_path) not in out.err


def test_shell_calls_reach_repository_cli(tmp_path, capsys):
    path = tmp_path / "scripts/probe.bash"
    path.parent.mkdir()
    path.write_text("mktemp -d\n")
    assert lint.main(["--repo", str(tmp_path)]) == 1
    assert "scripts/probe.bash:1" in capsys.readouterr().out


@pytest.mark.parametrize("command", ['ROOT="$(mktemp -d)"', 'echo "`mktemp -d`"', 'echo "$(echo $(mktemp -d))"'])
def test_shell_quoted_and_nested_substitutions_are_checked(command):
    assert lint.scan_shell(command, "scripts/probe.sh")


def test_shell_single_quotes_do_not_execute_substitutions():
    assert lint.scan_shell("echo '$(mktemp -d)'", "scripts/probe.sh") == []


@pytest.mark.parametrize("source", ['echo "<<EOF"\nmktemp -d\n', "if mktemp -d; then :; fi", "f() { mktemp -d; }"])
def test_shell_control_flow_and_quoted_operator_do_not_hide_calls(source):
    assert lint.scan_shell(source, "scripts/probe.sh")


@pytest.mark.parametrize("delimiter", ["'END TAG'", "\\EOF"])
def test_quoted_and_escaped_heredoc_delimiters(delimiter):
    marker = "END TAG" if "TAG" in delimiter else "EOF"
    source = f"cat <<{delimiter}\nIt's quoted data\n{marker}\nmktemp -d\n"
    findings = lint.scan_shell(source, "scripts/probe.sh")
    assert len(findings) == 1 and findings[0].line == 4


def test_tab_stripping_and_multiple_heredocs():
    source = "cat <<-'A' <<'B'\n\tIt's data\n\tA\n\"more data\nB\nmktemp -d\n"
    findings = lint.scan_shell(source, "scripts/probe.sh")
    assert len(findings) == 1 and findings[0].line == 6


def test_python_multiline_unicode_call_fingerprint():
    source = 'import tempfile\nlabel = "é"; tempfile.mkdtemp(\n    prefix="ü-",\n)\n'
    finding = lint.scan_python(source, "scripts/probe.py")[0]
    assert finding.line == 2
    assert finding.message.endswith('tempfile.mkdtemp(\n    prefix="ü-",\n)')


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\x85"])
@pytest.mark.parametrize("newline", ["\n", "\r", "\r\n"])
def test_python_literal_fingerprint_uses_physical_lines(tmp_path, monkeypatch, separator, newline):
    path = tmp_path / "tests/probe.py"
    path.parent.mkdir()
    line = f'ROOT = "{LITERAL}"'
    path.write_bytes((f'label = "before{separator}after"' + newline + line + newline).encode())
    assert lint.scan_lines(tmp_path) == [("tests/probe.py", 2, line)]
    monkeypatch.setattr(lint, "ALLOWLIST", (("tests/probe.py", "fixture only", lint.line_digest(line) + ":1"),))
    assert lint.find_literal_tmp_paths(tmp_path) == []
    path.write_bytes((path.read_text() + line + newline).encode())
    assert lint.find_literal_tmp_paths(tmp_path) == [("tests/probe.py", 3)]


def test_shell_unicode_separator_preserves_physical_line_numbers(tmp_path):
    path = tmp_path / "scripts/probe.sh"
    path.parent.mkdir()
    path.write_text('echo "before\u2028after"\nmktemp -d\n')
    rows = lint.scan_lines(tmp_path)
    assert rows == [("scripts/probe.sh", 2, "mktemp-call: mktemp -d")]


def test_allowlist_residuals_reference_followup_issue():
    assert all("#8755" not in reason for _, reason, _ in lint.ALLOWLIST)
    assert all("#9702" in reason for _, reason, _ in lint.ALLOWLIST if "migration" in reason or "follow-up" in reason)
