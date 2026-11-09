"""Commit-time hygiene hooks retain the scanners' exact file scope."""

import re
from pathlib import Path

import pytest
import yaml

from scripts.pre_commit.declared_hook_stages import declared_stages


@pytest.fixture
def config():
    return yaml.safe_load((Path(__file__).resolve().parents[1] / ".pre-commit-config.yaml").read_text())


@pytest.mark.parametrize(
    "hook_id,module,pass_filenames",
    [
        ("lint-tmp-paths", "lint_tmp_paths", True),
        ("lint-control-plane-sqlite", "lint_control_plane_sqlite", True),
        ("lint-raw-rm-rf", "lint_raw_rm_rf", False),
    ],
)
def test_hygiene_hooks_use_project_python_at_commit(config, hook_id, module, pass_filenames):
    hooks = [
        hook for repo in config["repos"] if repo["repo"] == "local" for hook in repo["hooks"] if hook["id"] == hook_id
    ]
    assert len(hooks) == 1
    hook = hooks[0]
    assert hook["entry"] == f"bash scripts/pre_commit/project_python.sh -m scripts.hygiene.{module}"
    assert hook["language"] == "system"
    assert hook["stages"] == ["pre-commit"]
    assert hook["pass_filenames"] is pass_filenames
    assert declared_stages(config) == {"pre-commit", "commit-msg", "pre-push"}
    if not pass_filenames:
        assert "files" not in hook


@pytest.mark.parametrize(
    "path,tmp_matches,sqlite_matches",
    [
        ("scripts/a.py", True, True),
        ("scripts/nested/a.sh", True, False),
        ("scripts/a.bash", True, False),
        ("tests/a.py", True, False),
        ("tests/a.sh", True, False),
        ("tests/a.bash", True, False),
        ("agents_extensions/shared/session_streams/a.py", False, True),
        ("agents_extensions/shared/other/a.py", False, False),
        ("scripts/control_plane/storage.py", True, False),
        ("scripts/control_plane_extra.py", True, False),
        ("docs/a.py", False, False),
        ("services.sh", False, False),
        ("scripts/a.txt", False, False),
        ("other/scripts/a.py", False, False),
    ],
)
def test_hygiene_hook_file_scope(config, path, tmp_matches, sqlite_matches):
    hooks = {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}
    for hook_id, expected in [("lint-tmp-paths", tmp_matches), ("lint-control-plane-sqlite", sqlite_matches)]:
        assert bool(re.search(hooks[hook_id]["files"], path)) is expected
