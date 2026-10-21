"""Anti-rot guard for #5740 — every test subprocess call must be bounded.

Background: a timeout-less ``subprocess.*`` hang held a CI runner for 357 minutes
(run ``30109965086``) because three guards were missing at once: call-site
``timeout=``, job ``timeout-minutes``, and ``pytest-timeout``. Job caps landed in
PR #5735; ``pytest-timeout`` is pinned in ``requirements*.txt`` and enforced via
``pyproject.toml`` (``timeout = 120``, ``timeout_method = "thread"``) plus the
CI pytest invocation. This module keeps the *call-site* fence from regrowing and
proves a hang fails fast *and names the test*.

``subprocess.Popen`` cannot take ``timeout=`` at construction; callers must bound
``.wait()`` / ``.communicate()`` (or an equivalent deadline). The AST guard in
``scripts/ci/subprocess_timeout_guard.py`` covers ``run`` / ``check_output`` /
``call`` / ``check_call`` only. Scripts/ keys include a call-shape hash so a
different timeout-less call cannot rotate into a vacated qualname slot (#7213).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from scripts.ci.subprocess_timeout_guard import (
    compare_allowlist,
    main,
    timeout_less_calls,
    timeout_less_calls_from_source,
)

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
def test_no_timeout_less_subprocess_calls_under_tests() -> None:
    """Fail CI when a new ``subprocess.run``/``check_*``/``call`` lacks ``timeout=``."""
    offenders: list[str] = []
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        try:
            hits = timeout_less_calls(path)
        except SyntaxError as exc:
            offenders.append(f"{path}: syntax error while scanning ({exc})")
            continue
        for hit in hits:
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{hit.lineno} {hit.name}")

    assert not offenders, (
        "Timeout-less subprocess calls under tests/ (issue #5740). "
        "Pass an explicit timeout= (typically 30 for git fixtures, 60–120 for "
        "heavier scripts). Popen must bound wait()/communicate() instead.\n" + "\n".join(offenders)
    )


# Import shapes the former line-anchored prefilter skipped (#10782).
_NON_LINE_ANCHORED_IMPORTS = {
    "nested-block": "if True: import subprocess\nsubprocess.run(['echo'])\n",
    "semicolon": "x = 1; import subprocess\nsubprocess.run(['echo'])\n",
    "backslash-continuation": "import \\\nsubprocess\nsubprocess.run(['echo'])\n",
    "from-import-after-semicolon": "x = 1; from subprocess import run\nrun(['echo'])\n",
    "nfkc-normalised-identifier": "import \uff53ubprocess\nsubprocess.run(['echo'])\n",
    "module-alias": "import subprocess as sp\nsp.run(['echo'])\n",
    "comma-separated-modules": "import os, subprocess as sp\nsp.call(['echo'])\n",
    "from-import-alias": "from subprocess import check_output as execute\nexecute(['echo'])\n",
    "from-import-continuation": "from \\\nsubprocess import check_call\ncheck_call(['echo'])\n",
    "comma-separated-functions": (
        "from subprocess import run, call, check_output, check_call\ncheck_output(['echo'])\n"
    ),
    "parenthesized-from-import": "from subprocess import (\nrun as execute,\ncall,\n)\nexecute(['echo'])\n",
    "nfkc-module-and-call": "import \uff53ubprocess as sp\nsp.\uff52un(['echo'])\n",
    "nfkc-from-import": "from \uff53ubprocess import run as execute\nexecute(['echo'])\n",
}


@pytest.mark.parametrize("source", _NON_LINE_ANCHORED_IMPORTS.values(), ids=_NON_LINE_ANCHORED_IMPORTS.keys())
def test_non_line_anchored_subprocess_imports_are_reported_by_both_entry_points(
    source: str, tmp_path: Path
) -> None:
    from_source = timeout_less_calls_from_source(source)
    path = tmp_path / "calls.py"
    path.write_text(source, encoding="utf-8")
    from_path = timeout_less_calls(path)
    assert len(from_source) == 1
    assert from_path == from_source


_ROTATION_BEFORE = textwrap.dedent(
    """\
    import subprocess

    def helper():
        subprocess.run(["git", "status"], check=False)
        subprocess.run(["sleep", "999"], check=False)
    """
)

_ROTATION_AFTER = textwrap.dedent(
    """\
    import subprocess

    def helper():
        subprocess.run(["git", "status"], check=False, timeout=30)
        subprocess.run(["other", "cmd"], check=False)
    """
)


def test_rotated_call_under_same_qualname_cannot_reuse_old_key() -> None:
    """F4: bounding one site and adding a different timeout-less call fails both ways."""
    before = timeout_less_calls_from_source(_ROTATION_BEFORE)
    after = timeout_less_calls_from_source(_ROTATION_AFTER)
    rel = "scripts/demo.py"
    before_keys = [hit.allowlist_key(rel) for hit in before]
    after_keys = [hit.allowlist_key(rel) for hit in after]
    assert len(before_keys) == 2
    assert len(after_keys) == 1
    # Old count-only key would have been path::helper::subprocess.run with count 2→1.
    # The remaining after-call must not share a shape with either before-call.
    assert after_keys[0] not in before_keys

    unallowlisted, stale = compare_allowlist(before_keys, {after_keys[0]: after})
    assert len(unallowlisted) == 1
    assert after_keys[0] in unallowlisted[0]
    assert unallowlisted[0].startswith(after_keys[0])
    stale_keys = {line.split(" ", 1)[0] for line in stale}
    assert set(before_keys) == stale_keys


def test_cli_help_standard(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI meets the --help standard (cli-help-standard.md) (#8750)."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "Check Python files under tests/ and scripts/ for timeout-less subprocess calls." in out
    assert "Examples:" in out
    assert "Outputs:" in out
    assert "Exit codes:" in out
    assert "Related:" in out
