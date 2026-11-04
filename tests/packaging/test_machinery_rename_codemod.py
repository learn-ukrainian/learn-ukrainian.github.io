"""Machinery move step 6: the lu_machinery rename codemod keeps product on scripts.

Covers the held-out cases of contract v3 step 6 rename items 1-4, idempotence on the
filter-repo layout, a computed loader target and a mixed ``from scripts import``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

pytest.importorskip(
    "libcst",
    reason="libcst==1.8.6 is not a project dependency; run this file from the isolated, hash-locked "
    "codemod environment described in packaging/machinery-move/README.md",
)

TOOLS = Path(__file__).resolve().parents[2] / "packaging" / "machinery-move"


def _load(name: str, filename: str) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, TOOLS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rename_python = _load("machinery_move_rename_python", "rename_python.py")
rename_nonpython = _load("machinery_move_rename_nonpython", "rename_nonpython.py")

M, P = "machinery", "product"

SEMINAR_SKILL = """\
# Seminar content review

1. For a built module run `.venv/bin/python -m scripts.build.verify_shippable <track> <slug>`;
   for a raw text sample run `.venv/bin/python -m scripts.audit.probe_uk_writing_score <file>`.
"""
TASK_FAMILY_MANIFEST = """\
# Manifest

```bash
.venv/bin/python -m scripts.orchestration.task_family inspect \\
  --family example
```
"""
WATCHDOG_UNIT = """\
[Service]
Type=oneshot
WorkingDirectory=@REPO_ROOT@
ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.orchestration.sources_watchdog run-once --apply
"""
HOOK_LIB = """\
#!/usr/bin/env bash
run_ownership() {
  if [[ ! -f "$source_root/scripts/dispatcher/ownership.py" ]]; then return 0; fi
  (cd "$source_root" && run_project_python -m scripts.dispatcher.ownership --worktree "$worktree_root" "$@")
}
"""
LAUNCHER = """\
#!/usr/bin/env bash
source "$ROOT/scripts/lib/rules_core.sh"
"$PY" scripts/dispatch.py dispatch --agent claude
"$PY" scripts/audit/probe_uk_writing_score.py "$file"
cat "$ROOT/agents_extensions/shared/rules/core-curriculum.md"
cat scripts/review/prompts/plan-review.md.j2
"$PY" -c 'import sys' scripts/lib/rules_core.py
"""
CORE_CURRICULUM = """\
# Core curriculum

Run `.venv/bin/python -m scripts.audit.probe_uk_writing_score` before review.
"""
REVIEW_TOOL = '''\
"""Settle reviews. This sentence names scripts.dispatch and is prose."""

import scripts.audit
import scripts.orchestration.merge_closeout  # unlike scripts.dispatch, this one is imported
from importlib import import_module

VERIFY = import_module("scripts.build.verify_shippable")
PRIMARY = import_module("scripts.dispatcher.primary")


def close() -> None:
    scripts.orchestration.merge_closeout.main()
    scripts.audit.run()
'''

# The eleven section-2 import sites whose targets are product (contract v3 section 2).
SECTION_2_SITES = {
    "scripts/pipeline/fixes.py": "from shared.fix_apply import apply_fix_pair\n",
    "scripts/wiki/review_merger.py": "from shared.fix_apply import apply_fix_pair\n",
    "scripts/pipeline/core.py": (
        "def a():\n    from plan_autofix import fix_russianisms_in_plan\n\n\n"
        "def b():\n    from plan_autofix import fix_russianisms_in_plan\n"
    ),
    "tests/test_russicism_autofix.py": "from plan_autofix import fix_russianisms_in_plan\n",
    "scripts/batch_gemini_runner/execution.py": "from gemini_output import (\n    extract_delimited,\n)\n",
    "scripts/build/phases/plan_patch.py": "from gemini_output import extract_delimited\n",
    "scripts/ai_agent_bridge/_gemini.py": (
        "def parse():\n    from gemini_output import ALL_TAGS, find_complete_pairs\n"
        "    from gemini_output import extract_delimited as _extract\n"
    ),
    "tests/test_gemini_output.py": "from scripts.gemini_output import (\n    extract_delimited,\n)\n",
    "tests/test_fix_external_resources.py": "from fix_external_resources import (\n    main,\n)\n",
}

# path -> (owner, content); owner None means the file is not in the map (tests/).
TREE: dict[str, tuple[str | None, str]] = {
    "scripts/__init__.py": (P, ""),
    "scripts/audit/__init__.py": (P, ""),
    "scripts/audit/probe_uk_writing_score.py": (P, ""),
    "scripts/build/__init__.py": (P, ""),
    "scripts/build/verify_shippable.py": (P, ""),
    "scripts/build/phases/__init__.py": (P, ""),
    "scripts/build/phases/plan_patch.py": (P, ""),
    "scripts/pipeline/__init__.py": (P, ""),
    "scripts/pipeline/fixes.py": (P, ""),
    "scripts/pipeline/core.py": (P, ""),
    "scripts/wiki/__init__.py": (P, ""),
    "scripts/wiki/review_merger.py": (P, ""),
    "scripts/batch_gemini_runner/__init__.py": (P, ""),
    "scripts/batch_gemini_runner/execution.py": (P, ""),
    "scripts/shared/__init__.py": (P, ""),
    "scripts/shared/fix_apply.py": (P, "def apply_fix_pair():\n    pass\n"),
    "scripts/plan_autofix.py": (P, ""),
    "scripts/gemini_output.py": (P, ""),
    "scripts/fix_external_resources.py": (P, ""),
    "scripts/review/__init__.py": (M, ""),
    "scripts/review/settle_fleet.py": (M, REVIEW_TOOL),
    "scripts/review/prompts/__init__.py": (P, ""),
    "scripts/review/prompts/plan-review.md.j2": (P, "plan review\n"),
    "scripts/orchestration/__init__.py": (M, ""),
    "scripts/orchestration/merge_closeout.py": (M, ""),
    "scripts/orchestration/task_family.py": (M, ""),
    "scripts/orchestration/sources_watchdog.py": (M, ""),
    "scripts/dispatcher/__init__.py": (M, ""),
    "scripts/dispatcher/primary.py": (M, ""),
    "scripts/dispatcher/ownership.py": (M, ""),
    "scripts/dispatch.py": (M, ""),
    "scripts/lib/rules_core.py": (M, ""),
    "scripts/lib/rules_core.sh": (M, ""),
    "scripts/ai_agent_bridge/__init__.py": (M, ""),
    "scripts/ai_agent_bridge/_gemini.py": (M, ""),
    "scripts/launchers/claude.sh": (M, LAUNCHER),
    ".githooks/_lib.sh": (M, HOOK_LIB),
    "agents_extensions/shared/rules/core-curriculum.md": (P, CORE_CURRICULUM),
    "agents_extensions/shared/skills/seminar-content-review/SKILL.md": (P, SEMINAR_SKILL),
    "agents_extensions/shared/skills/task-family-manager/references/manifest.md": (M, TASK_FAMILY_MANIFEST),
    "packaging/systemd/learn-ukrainian-sources-watchdog.service": (P, WATCHDOG_UNIT),
    "tests/test_russicism_autofix.py": (None, ""),
    "tests/test_gemini_output.py": (None, ""),
    "tests/test_fix_external_resources.py": (None, ""),
}


def _write_tree(root: Path, layout_moved: bool = False) -> Path:
    """Write the fixture tree and its ownership map; return the map path.

    With ``layout_moved`` the machinery files sit under lu_machinery/, as after
    ``git filter-repo --path-rename scripts/:lu_machinery/``.
    """

    ownership = {path: owner for path, (owner, _) in TREE.items() if owner is not None}
    for path, (owner, content) in TREE.items():
        content = SECTION_2_SITES.get(path, content)
        rel = path
        if layout_moved and owner == M and path.startswith("scripts/"):
            rel = "lu_machinery/" + path[len("scripts/") :]
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    map_path = root.parent / f"{root.name}-ownership.json"
    map_path.write_text(json.dumps(ownership), encoding="utf-8")
    return map_path


def _run(tool: ModuleType, map_path: Path, root: Path, mode: str, *paths: str) -> tuple[int, dict]:
    report_path = root.parent / f"{root.name}-{tool.__name__}-report.json"
    code = tool.main(["--map", str(map_path), "--root", str(root), f"--{mode}", "--report", str(report_path), *paths])
    return code, json.loads(report_path.read_text(encoding="utf-8"))


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture
def tree(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "clone"
    root.mkdir()
    return root, _write_tree(root)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def test_item_1_and_2_python_held_outs(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    code, report = _run(rename_python, map_path, root, "apply")

    assert code == 0, report["unresolved"]
    text = _read(root, "scripts/review/settle_fleet.py")
    # Item 1: import nodes.
    assert "import scripts.audit\n" in text
    assert "import lu_machinery.orchestration.merge_closeout  # unlike scripts.dispatch, this one is imported" in text
    assert "lu_machinery.orchestration.merge_closeout.main()" in text
    assert "    scripts.audit.run()" in text
    # Item 2: module strings.
    assert 'import_module("scripts.build.verify_shippable")' in text
    assert 'import_module("lu_machinery.dispatcher.primary")' in text
    assert '"""Settle reviews. This sentence names scripts.dispatch and is prose."""' in text
    # Item 2: the eleven section-2 product sites stay on the product side.
    for path, content in SECTION_2_SITES.items():
        assert _read(root, path) == content, path
    assert _read(root, "scripts/pipeline/fixes.py") == "from shared.fix_apply import apply_fix_pair\n"
    assert report["files_changed"] == ["scripts/review/settle_fleet.py"]


def test_item_3_and_4_nonpython_held_outs(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    before = _snapshot(root)
    code, report = _run(rename_nonpython, map_path, root, "apply")

    assert code == 0, report["unresolved"]
    # Item 3: -m invocations.
    assert _read(root, "agents_extensions/shared/skills/seminar-content-review/SKILL.md") == SEMINAR_SKILL
    assert "-m lu_machinery.orchestration.task_family inspect" in _read(
        root, "agents_extensions/shared/skills/task-family-manager/references/manifest.md"
    )
    unit = _read(root, "packaging/systemd/learn-ukrainian-sources-watchdog.service")
    assert "-m lu_machinery.orchestration.sources_watchdog run-once --apply" in unit
    assert "WorkingDirectory=@REPO_ROOT@\n" in unit
    hook = _read(root, ".githooks/_lib.sh")
    assert "run_project_python -m lu_machinery.dispatcher.ownership --worktree" in hook
    assert '"$source_root/lu_machinery/dispatcher/ownership.py"' in hook
    # Item 4: resource paths.
    launcher = _read(root, "scripts/launchers/claude.sh")
    assert '"$PY" scripts/audit/probe_uk_writing_score.py "$file"' in launcher
    assert 'source "$ROOT/lu_machinery/lib/rules_core.sh"' in launcher
    assert "lu_machinery/lib/rules_core.py" in launcher
    assert '"$PY" lu_machinery/dispatch.py dispatch --agent claude' in launcher
    assert 'cat "$ROOT/agents_extensions/shared/rules/core-curriculum.md"' in launcher
    assert "cat scripts/review/prompts/plan-review.md.j2" in launcher
    assert _read(root, "agents_extensions/shared/rules/core-curriculum.md") == CORE_CURRICULUM
    # Only the four expected files changed; Python files are never written by this tool.
    after = _snapshot(root)
    changed = sorted(path for path in after if after[path] != before[path])
    assert changed == [
        ".githooks/_lib.sh",
        "agents_extensions/shared/skills/task-family-manager/references/manifest.md",
        "packaging/systemd/learn-ukrainian-sources-watchdog.service",
        "scripts/launchers/claude.sh",
    ]
    assert {item["before"] for item in report["inventory"] if item["kind"] == "direct_script_invocation"} == {
        "scripts/dispatch.py",
        "scripts/lib/rules_core.sh",
    }


def test_second_application_is_a_no_op_on_the_filter_repo_layout(tmp_path: Path) -> None:
    original = tmp_path / "original"
    original.mkdir()
    _write_tree(original)
    moved = tmp_path / "moved"
    moved.mkdir()
    map_path = _write_tree(moved, layout_moved=True)

    first_py = _run(rename_python, map_path, moved, "apply")
    first_np = _run(rename_nonpython, map_path, moved, "apply")
    assert first_py[0] == first_np[0] == 0
    assert "import lu_machinery.orchestration.merge_closeout" in _read(moved, "lu_machinery/review/settle_fleet.py")
    after_first = _snapshot(moved)

    second_py = _run(rename_python, map_path, moved, "apply")
    second_np = _run(rename_nonpython, map_path, moved, "apply")
    assert _snapshot(moved) == after_first
    assert second_py[0] == second_np[0] == 0
    assert second_py[1]["rewrites"] == second_np[1]["rewrites"] == []
    assert second_py[1]["files_changed"] == second_np[1]["files_changed"] == []

    # The same rewrites happen whether machinery has already been moved or not.
    original_map = tmp_path / "original-ownership.json"
    reference = _run(rename_python, original_map, original, "check")[1]["rewrites"]
    assert [(r["kind"], r["before"], r["after"]) for r in first_py[1]["rewrites"]] == [
        (r["kind"], r["before"], r["after"]) for r in reference
    ]


def test_computed_loader_target_is_reported_not_rewritten(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        "import importlib\n"
        "from importlib import import_module as load\n\n"
        "def run(name):\n"
        '    importlib.import_module(f"scripts.dispatcher.{name}")\n'
        "    return load(name)\n"
    )
    (root / "scripts/dispatcher/plugins.py").write_text(source, encoding="utf-8")
    map_path.write_text(
        json.dumps({**json.loads(map_path.read_text(encoding="utf-8")), "scripts/dispatcher/plugins.py": M}),
        encoding="utf-8",
    )

    code, report = _run(rename_python, map_path, root, "apply", "scripts/dispatcher/plugins.py")

    assert code == 1
    assert _read(root, "scripts/dispatcher/plugins.py") == source
    assert [(item["kind"], item["line"]) for item in report["unresolved"]] == [
        ("computed_loader", 5),
        ("computed_loader", 6),
    ]
    assert report["rewrites"] == []


def test_mixed_from_scripts_import_is_split_by_owner(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        "from scripts import audit, dispatch as entry  # noqa: F401\n"
        "from scripts import (\n"
        "    gemini_output,  # product helper\n"
        "    dispatch,  # fleet entry point\n"
        ")\n"
    )
    (root / "scripts/pipeline/mixed.py").write_text(source, encoding="utf-8")
    map_path.write_text(
        json.dumps({**json.loads(map_path.read_text(encoding="utf-8")), "scripts/pipeline/mixed.py": P}),
        encoding="utf-8",
    )

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/mixed.py")

    assert code == 0, report["unresolved"]
    assert _read(root, "scripts/pipeline/mixed.py") == (
        "from scripts import audit  # noqa: F401\n"
        "from lu_machinery import dispatch as entry  # noqa: F401\n"
        "from scripts import (\n"
        "    gemini_output,  # product helper\n"
        ")\n"
        "from lu_machinery import (\n"
        "    dispatch,  # fleet entry point\n"
        ")\n"
    )
    assert [item["kind"] for item in report["rewrites"]] == ["import_from_split", "import_from_split"]
