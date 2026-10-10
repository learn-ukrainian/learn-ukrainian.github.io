"""Selector validation must not pull source tools into lane import graphs."""

import subprocess
import sys
from pathlib import Path

from tests.test_source_ingest_entrypoints import source_tool_clis

ROOT = Path(__file__).resolve().parents[1]


def test_selector_imports_do_not_expand_canary_source_tool_inventory():
    clis = source_tool_clis(ROOT)
    for path in (
        "scripts/session_canary/__main__.py",
        "scripts/session_canary/grok_lane.py",
        "scripts/session_canary/kimi_lane.py",
        "scripts/common/epic_selector.py",
    ):
        assert path not in clis


def test_leaf_file_import_and_validation_without_repository_on_sys_path(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            """
import runpy
import sys

validate_epic = runpy.run_path(sys.argv[1], run_name="__main__")["validate_epic"]
for epic in ("x", "0", "infra", "7919", "open-model-data", "a--b"):
    assert validate_epic(epic) is None
for epic in ("../x", "/absolute", "Harness", "bad_name", "harness\\n", "інфра"):
    try:
        validate_epic(epic)
    except ValueError as exc:
        assert str(exc) == "epic must be a selector such as infra or 7919"
    else:
        raise AssertionError(f"accepted unsafe selector {epic!r}")
assert not any(name == "scripts" or name.startswith("scripts.") for name in sys.modules)
print("isolated file import: 6 accepted, 6 rejected; no scripts imports")
""",
            str(ROOT / "scripts/common/epic_selector.py"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    assert result.stdout == "isolated file import: 6 accepted, 6 rejected; no scripts imports\n"
    assert result.stderr == ""
