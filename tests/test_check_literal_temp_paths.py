"""Behavior tests for the static scratch-path prevention check (#8755)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from scripts.audit import check_literal_temp_paths as lint

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
        'os.getenv("LU_RUNTIME_TMP_ROOT")',
        'os.environ.get("TMPDIR")',
        'os.environ.get("TMPDIR", ensure_scratch_root())',
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
        'os.getenv("TMPDIR", ".")',
        'os.environ.get("TMPDIR", None)',
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


def test_comments_and_all_docstring_scopes_pass():
    source = f'''"""Mention {SYSTEM_TMP}/example."""
# A comment naming {VAR_TMP}/example
class Example:
    """Mention {SYSTEM_TMP}."""
    def run(self):
        """Mention {SYSTEM_TMP}/example."""
        pass
async def run():
    """Mention {VAR_TMP}."""
    pass
'''
    assert lint.scan_python(source, "scripts/probe.py") == []


def test_argparse_help_passes_but_default_is_checked():
    source = f'''import argparse
parser = argparse.ArgumentParser(description="Mention {SYSTEM_TMP}", epilog="Mention {VAR_TMP}")
parser.add_argument("--out", help="Example {SYSTEM_TMP}/foo", default="{SYSTEM_TMP}/foo")
'''
    findings = lint.scan_python(source, "scripts/probe.py")
    assert len(findings) == 1
    assert findings[0].line == 3


def test_help_interpolation_keeps_executable_paths_checked():
    source = f'''parser.add_argument("--out", help="Mention {SYSTEM_TMP}" + " safely")
parser.add_argument("--in", help=f"Read {{Path('{SYSTEM_TMP}/foo')}}")
parser.add_argument("--other", help=read_text(Path("{SYSTEM_TMP}/foo")))
'''
    assert [finding.line for finding in lint.scan_python(source, "scripts/probe.py")] == [2, 3]


def test_argparse_alias_help_is_ignored():
    source = f'from argparse import ArgumentParser as AP\np = AP(description="Use {SYSTEM_TMP}/foo")'
    assert lint.scan_python(source, "scripts/probe.py") == []


def test_executable_string_expression_is_not_a_docstring():
    source = f'print("start")\n"{SYSTEM_TMP}/foo"\n'
    assert lint.scan_python(source, "scripts/probe.py")[0].line == 2


@pytest.mark.parametrize("relative", sorted(lint.ALLOWLIST))
def test_allowed_modules_pass(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(f'ROOT = "{SYSTEM_TMP}/foo"\ntempfile.mkdtemp()\n')
    assert lint.scan_file(path, tmp_path) == []


def test_allowlist_does_not_match_suffix_or_basename(tmp_path):
    path = tmp_path / "other/scripts/common/scratch.py"
    path.parent.mkdir(parents=True)
    path.write_text(f'ROOT = "{SYSTEM_TMP}/foo"')
    assert len(lint.scan_file(path, tmp_path)) == 1
    path = tmp_path / "scratch.py"
    path.write_text("tempfile.mkdtemp()")
    assert len(lint.scan_file(path, tmp_path)) == 1


@pytest.mark.parametrize(
    "command",
    [
        'mkdir "{root}/foo"',
        "ROOT={root}",
        "cat {root}/foo",
        'ROOT="{root}/foo#literal"',
        'cp "{root}/foo" "$TMPDIR/"',
    ],
)
def test_shell_literals_are_checked(command):
    findings = lint.scan_shell("# heading\n" + command.format(root=SYSTEM_TMP) + "\n", "scripts/probe.sh")
    assert len(findings) == 1
    assert findings[0].line == 2


def test_shell_comments_and_managed_variables_pass():
    source = f'# Mention {SYSTEM_TMP}/foo\nmkdir "$TMPDIR/foo" # {SYSTEM_TMP}/bad\n'
    source += f'mkdir "{VAR_TMP}/lu/child"\n'
    assert lint.scan_shell(source, "scripts/probe.sh") == []


def test_shell_multiline_quotes_are_checked():
    source = f'mkdir \\\n  "{SYSTEM_TMP}/foo"\n'
    assert lint.scan_shell(source, "scripts/probe.sh")[0].line == 2


@pytest.mark.parametrize("name", ["usage", "help", "show_help", "print_help", "print_usage"])
def test_shell_help_function_passes_but_producer_after_it_fails(name):
    source = f'{name}() {{\n  echo "Use {SYSTEM_TMP}/example"\n}}\nmkdir "{SYSTEM_TMP}/bad"\n'
    findings = lint.scan_shell(source, "scripts/probe.sh")
    assert len(findings) == 1
    assert findings[0].line == 4


def test_shell_escaped_path_is_checked():
    source = "mkdir " + SYSTEM_TMP.replace("/", "\\/") + "/foo\n"
    assert lint.scan_shell(source, "scripts/probe.sh")


def test_help_function_producers_and_redirections_are_checked():
    source = f'usage() {{\nmkdir "{SYSTEM_TMP}/bad"; echo "help" > "{SYSTEM_TMP}/bad"\n}}\n'
    assert [finding.line for finding in lint.scan_shell(source, "scripts/probe.sh")] == [2]


def test_shell_same_line_help_commands_pass():
    source = f'usage() {{ echo "Use {SYSTEM_TMP}/foo"; printf "Use {VAR_TMP}/foo"; }}'
    assert lint.scan_shell(source, "scripts/probe.sh") == []


def test_shell_variable_suffix_does_not_hide_literal_root():
    assert lint.scan_shell(f'mkdir "{SYSTEM_TMP}${{NAME}}"', "scripts/probe.sh")


def test_directory_walk_prunes_generated_trees(tmp_path):
    for relative in ["scripts/a.py", "tests/a.sh", "scripts/a.bash", "docs/a.md", "node_modules/a.py"]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    assert [p.relative_to(tmp_path).as_posix() for p in lint.collect_files([tmp_path])] == [
        "scripts/a.bash",
        "scripts/a.py",
        "tests/a.sh",
    ]


def test_scan_file_dispatch_and_symlink_guard(tmp_path):
    shell = tmp_path / "a.bash"
    shell.write_text(f'mkdir "{SYSTEM_TMP}/foo"\n')
    assert lint.scan_file(shell, tmp_path)
    ignored = tmp_path / "a.md"
    ignored.write_text(SYSTEM_TMP)
    assert lint.scan_file(ignored, tmp_path) == []
    link = tmp_path / "link.py"
    link.symlink_to(shell)
    with pytest.raises(ValueError, match="symlink"):
        lint.scan_file(link, tmp_path)


def test_cli_explicit_files_and_error_status(tmp_path, capsys):
    path = tmp_path / "probe.py"
    path.write_text('path = tmp_path / "foo"\n')
    assert lint.main(["--files", str(path)]) == 0
    assert capsys.readouterr().out == "literal_temp_findings=0 errors=0\n"
    path.write_text(f'path = "{SYSTEM_TMP}/foo"\n')
    assert lint.main(["--files", str(path)]) == 1
    output = capsys.readouterr().out
    assert "probe.py:1:" in output
    assert "literal_temp_findings=1 errors=0" in output
    assert SYSTEM_TMP + "/foo" not in output
    path.write_text("def broken(:")
    assert lint.main(["--files", str(path)]) == 2
    assert "cannot read or parse source" in capsys.readouterr().err
    assert lint.main(["--files", str(tmp_path / "missing.py")]) == 2
    capsys.readouterr()


def test_cli_walk_and_help(tmp_path, capsys):
    (tmp_path / "probe.py").write_text("tempfile.mkstemp()")
    assert lint.main([str(tmp_path)]) == 1
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        lint.main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for text in ("--changed-vs-base", "--files", "Outputs:", "Exit codes:", "Related:"):
        assert text in output


def test_cli_rejects_conflicting_modes(capsys):
    with pytest.raises(SystemExit) as exc:
        lint.main(["scripts", "--files", "tests/probe.py"])
    assert exc.value.code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_changed_files_includes_staged_and_unstaged_not_deleted(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True, timeout=30)

    git("init", "-q")
    git("config", "user.name", "Lint fixture")
    git("config", "user.email", "fixture@example.invalid")
    for name in ("changed.py", "deleted.py"):
        (tmp_path / name).write_text("pass\n")
    git("add", ".")
    git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture\n\nX-Agent: codex/impl-8755-temp-lint")
    (tmp_path / "changed.py").write_text("tempfile.mkdtemp()\n")
    git("rm", "deleted.py")
    (tmp_path / "added name.py").write_text("tempfile.mkstemp()\n")
    git("add", "added name.py")
    assert {p.name for p in lint.changed_files("HEAD", tmp_path)} == {"changed.py", "added name.py"}


def test_changed_mode_reports_git_errors(capsys):
    assert lint.main(["--changed-vs-base", "refs/nonexistent-lint-test-base"]) == 2
    assert "Cannot select sources" in capsys.readouterr().err


def test_cli_subprocess_scans_its_own_files():
    result = subprocess.run(
        [
            sys.executable,
            str(lint.REPO_ROOT / "scripts/audit/check_literal_temp_paths.py"),
            "--files",
            "scripts/audit/check_literal_temp_paths.py",
            "tests/test_check_literal_temp_paths.py",
        ],
        cwd=lint.REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "literal_temp_findings=0 errors=0\n"
