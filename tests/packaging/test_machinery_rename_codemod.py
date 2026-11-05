"""Machinery move step 6: the lu_machinery rename tools keep product on scripts and fail closed.

Covers the held-out cases of contract v3 step 6 rename items 1-4, idempotence on the
filter-repo layout, a computed loader target, a mixed ``from scripts import``, the structured
metadata transform, and every reviewer probe from PR 12756 rounds 1-5: each one is either
rewritten exactly or left unchanged and reported, never partly rewritten.
"""

from __future__ import annotations

import gzip
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
rename_structured = _load("machinery_move_rename_structured", "rename_structured.py")
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


def _add(root: Path, map_path: Path, rel: str, owner: str, content: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(content, encoding="utf-8")
    ownership = json.loads(map_path.read_text(encoding="utf-8"))
    map_path.write_text(json.dumps({**ownership, rel: owner}), encoding="utf-8")


def _kinds(report: dict) -> list[str]:
    return [item["kind"] for item in report["unresolved"]]


# -- PR 12756 review probes, rounds 1-5 ------------------------------------------------
#
# Each probe is rewritten exactly ("rewrite"), left unchanged and reported ("report"), left
# unchanged with only an inventory entry for prose ("inventory"), or left unchanged because it
# names nothing to rename ("quiet"). "rewrite+report" rewrites one complete name exactly and
# reports another one in the same text. Nothing may be partly rewritten.

PROBE_MAP = {
    "scripts/__init__.py": P,
    "scripts/dispatch.py": M,
    "scripts/dispatch.py.in": P,
    "scripts/audit/__init__.py": P,
    "scripts/audit/run.sh": P,
    "scripts/engine/__init__.py": M,
    "scripts/engine/control.py": M,
    "scripts/engine/help.py": P,
    "scripts/engine/__main__.py": P,
    "scripts/review/__init__.py": M,
    "scripts/review/catalog.py": M,
    "scripts/review/prompts/__init__.py": P,
    "scripts/data/config.json": M,
    "scripts/data/config.json5": P,
    "scripts/lib/rules_core.sh": M,
    "scripts/lib/rules_core.py": M,
    "scripts/x.py": P,
    "scripts/tools/run.sh": M,
    "scripts/dispatch.py,v": P,
}
PY, NP = "python", "nonpython"
X = "scripts/x.py"  # a product Python file
SH = "scripts/tools/run.sh"  # a machinery shell script

PROBES = [
    # Round 1 F1: splits inside one-line suites and compound lines
    (
        PY,
        "if ready: from scripts import dispatch, audit\n",
        X,
        ("rewrite", "if ready: from lu_machinery import dispatch; from scripts import audit\n"),
    ),
    (
        PY,
        "def run(): from scripts import dispatch, audit\n",
        X,
        ("rewrite", "def run(): from lu_machinery import dispatch; from scripts import audit\n"),
    ),
    (
        PY,
        "x = 1; from scripts import dispatch, audit\n",
        X,
        ("rewrite", "x = 1; from lu_machinery import dispatch; from scripts import audit\n"),
    ),
    # Round 1 F2: bare uses of the import binding
    (PY, "import scripts.dispatch\nregistry = scripts\n", X, "report"),
    (PY, "import scripts.dispatch\ndef f():\n    return scripts\n", X, "report"),
    (PY, "import scripts.audit\nhasattr(scripts, 'dispatch')\n", X, "report"),
    # Round 1 F3: module strings built from parts
    (PY, 'TARGET = "scripts." "dispatch"\n', X, ("rewrite", 'TARGET = "lu_machinery.dispatch"\n')),
    (PY, 'TARGET = f"scripts.dispatch"\n', X, ("rewrite", 'TARGET = "lu_machinery.dispatch"\n')),
    (PY, 'TARGET = "scripts." + "dispatch"\n', X, ("rewrite", 'TARGET = "lu_machinery.dispatch"\n')),
    (PY, 'T = f"scripts.engine.{x}"\n', X, "report"),
    (PY, 'T = "scripts.engine.%s" % x\n', X, "report"),
    (PY, 'T = "scripts.engine.{}".format(x)\n', X, "report"),
    (PY, 'T = "scripts.dispatch" + suffix\n', X, "report"),
    (PY, 'T = "scripts.dispatch:app"\n', X, "report"),
    (PY, 'T = "scripts.audit.{}".format(x)\n', X, "report"),
    (PY, 'T = "scripts.dispatch"\n', X, ("rewrite", 'T = "lu_machinery.dispatch"\n')),
    # Round 1 F4: loader targets
    (PY, "from importlib import import_module as load\ndef run(args):\n    return load(*args)\n", X, "report"),
    (PY, "from importlib import import_module as load\ndef run(kw):\n    return load(**kw)\n", X, "report"),
    (PY, 'import runpy\nrunpy.run_module("scripts.engine")\n', X, "report"),
    (PY, 'import importlib\nimportlib.import_module("scripts.no_such_module")\n', X, "report"),
    (PY, 'import importlib\nimportlib.import_module("scripts.dispatch.missing")\n', X, "report"),
    (PY, '__import__("scripts.engine", fromlist=["help"])\n', X, "report"),
    (
        PY,
        'import importlib\nimportlib.import_module("scripts.engine")\n',
        X,
        ("rewrite", 'import importlib\nimportlib.import_module("lu_machinery.engine")\n'),
    ),
    (PY, 'x = __import__("hashlib").sha256(b"")\n', X, "quiet"),
    # Round 1 F5: computed module invocations
    (NP, 'python -m "scripts.engine.${MODULE}"\n', SH, "report"),
    (NP, "python -m scripts.engine.$MODULE\n", SH, "report"),
    (NP, "uvicorn scripts.unknown:app\n", SH, "report"),
    (NP, "python -mscripts.engine.help\n", SH, "quiet"),
    (NP, "python -m scripts.dispatch_${X}\n", SH, "report"),
    (NP, "python -mscripts.dispatch run\n", SH, ("rewrite", "python -mlu_machinery.dispatch run\n")),
    (
        NP,
        "uvicorn scripts.engine.control:app --factory\n",
        SH,
        ("rewrite", "uvicorn lu_machinery.engine.control:app --factory\n"),
    ),
    (NP, "python -m scripts.review.${MOD}\n", SH, "report"),
    # Round 1 F6: globs and computed suffixes
    (NP, "cat scripts/data/config.json?\n", SH, "report"),
    (NP, "cat scripts/data/config.json[5]\n", SH, "report"),
    (NP, "cat scripts/data/config.json*\n", SH, "report"),
    (NP, "cat scripts/dispatch.py${SUFFIX}\n", SH, "report"),
    (NP, "source scripts/lib/${NAME}.sh\n", SH, "report"),
    (NP, "cat scripts/{a,b}.py\n", SH, "report"),
    (NP, "cat ./scripts/data/config.json\n", SH, ("rewrite", "cat ./lu_machinery/data/config.json\n")),
    (NP, "pwsh scripts\\lib\\rules_core.sh\n", SH, "report"),
    (NP, "cd scripts && ls\n", SH, "report"),
    (NP, "# cd scripts in a comment\n", SH, "inventory"),
    (PY, 'p = f"scripts/dispatch.py{suffix}"\n', X, "report"),
    (PY, 'c = f"python -m scripts.engine.{m}"\n', X, "report"),
    # Round 2 F3 siblings
    (PY, 'T = f"scripts.dispatch:{attr}"\n', X, "report"),
    (PY, 'T = "scripts.dispatch:%s" % attr\n', X, "report"),
    (PY, 'T = "scripts.dispatch:{}".format(attr)\n', X, "report"),
    (PY, 'T = "scr" + "ipts.dispatch"\n', X, ("rewrite", 'T = "lu_machinery.dispatch"\n')),
    (PY, 'T = f"\\x73cripts.dispatch"\n', X, ("rewrite", 'T = "lu_machinery.dispatch"\n')),
    (PY, 'T = ".".join(["scripts", "dispatch"])\n', X, "report"),
    (PY, 'T = ".".join(["scripts", name])\n', X, "report"),
    (PY, 'T = "%s.dispatch" % "scripts"\n', X, "report"),
    (PY, 'T = "{}.dispatch".format("scripts")\n', X, "report"),
    (PY, 'T = "%s.%s" % ("scripts", name)\n', X, "report"),
    (PY, "T = f\"{'scripts'}.dispatch\"\n", X, "report"),
    (PY, 'T = b"scripts." + b"dispatch"\n', X, ("rewrite", 'T = b"lu_machinery.dispatch"\n')),
    (PY, 'T = "scripts" + "." + "dispatch"\n', X, ("rewrite", 'T = "lu_machinery.dispatch"\n')),
    (PY, 'T = f"scripts.audit:{attr}"\n', X, "report"),
    (PY, 'T = "x" + f("scripts.dispatch")\n', X, ("rewrite", 'T = "x" + f("lu_machinery.dispatch")\n')),
    (PY, 'T = "scripts/" + name\n', X, "report"),
    (PY, 'T = b"scripts.dispatch"\n', X, ("rewrite", 'T = b"lu_machinery.dispatch"\n')),
    # Round 2 F4 siblings
    (PY, 'kw = {"fromlist": ["help"]}\nx = __import__("scripts.engine", **kw)\n', X, "report"),
    (PY, 'args = (globals(), locals(), ["help"])\nx = __import__("scripts.engine", *args)\n', X, "report"),
    (PY, 'x = __import__(name="scripts.engine", **kw)\n', X, "report"),
    (PY, 'x = __import__("scripts.dispatch", **kw)\n', X, "report"),
    (PY, 'x = __import__("scripts.dispatch", globals(), locals(), [], 1)\n', X, "report"),
    (PY, 'x = __import__("scripts.dispatch", level=lvl)\n', X, "report"),
    (PY, 'import importlib\nx = importlib.import_module(*args, "scripts.dispatch")\n', X, "report"),
    (
        PY,
        'x = __import__("scripts.dispatch", globals(), locals(), [], 0)\n',
        X,
        ("rewrite", 'x = __import__("lu_machinery.dispatch", globals(), locals(), [], 0)\n'),
    ),
    (
        PY,
        'import importlib\nx = importlib.import_module("scripts.dispatch", *rest)\n',
        X,
        ("rewrite", 'import importlib\nx = importlib.import_module("lu_machinery.dispatch", *rest)\n'),
    ),
    # Round 2 F6 siblings
    (NP, "NAME=../x\ncat scripts/lib/${NAME}.py\n", SH, "report"),
    (NP, "cat scripts/lib/$NAME\n", SH, "report"),
    (NP, "cat scripts/audit/${X}\n", SH, "report"),
    (NP, "cat scripts/lib/{a,b}.sh\n", SH, "report"),
    (NP, "cat scripts/lib/<name>.sh\n", SH, "report"),
    (NP, "cat scripts/lib/../x.py\n", SH, "report"),
    (NP, "source lu_machinery/lib/${NAME}.sh\n", SH, "quiet"),
    (PY, 'p = f"scripts/lib/{name}.py"\n', X, "report"),
    # Author-chosen siblings before round 3
    (PY, 't = "scripts."\nt += name\n', X, "report"),
    (PY, 'T = "%(pkg)s.dispatch" % {"pkg": "scripts"}\n', X, "report"),
    (PY, 'T = "{pkg}.dispatch".format(**{"pkg": "scripts"})\n', X, "report"),
    (PY, 'T = "scripts.dispatch".replace("dispatch", name)\n', X, "report"),
    (PY, "import importlib\nload = importlib.import_module\nload(name)\n", X, "report"),
    (PY, "from importlib import import_module\nmods = list(map(import_module, names))\n", X, "report"),
    (PY, 'T = "{0}.{1}".format("scripts", "dispatch")\n', X, "report"),
    (PY, 'T = "scripts.review.".__add__(name)\n', X, "report"),
    (PY, 'print(1, file=__import__("sys").stderr)\n', X, "quiet"),
    (PY, 't = "scripts.audit."\n', X, "quiet"),
    (PY, 'T = "scripts.audit".replace("audit", "dispatch")\n', X, "report"),
    (PY, 'p = "scripts/lib/" + name\n', X, "report"),
    (NP, "cd scripts/lib && cat ../audit/x.py\n", SH, "report"),
    # Round 3 F3 (reviewer) and siblings
    (PY, 'T = "scrXipts.dispatch".replace("X", "")\n', X, "report"),
    (PY, 'T = "%s.%s" % ("scr" + "ipts", name)\n', X, "report"),
    (PY, 'T = "{}.{}".format("scr" + "ipts", name)\n', X, "report"),
    (PY, 'T = "python -m " + "scripts.dispatch"\n', X, "report"),
    (PY, 'T = "scr" + name + "ipts.dispatch"\n', X, "report"),
    (PY, 'T = f"python -m {py} scripts.dispatch"\n', X, "report"),
    (PY, 'T = f"scripts.audit.{x} or scripts.dispatch"\n', X, "report"),
    (PY, 'T = f"Running scripts in {d}"\n', X, "report"),
    (PY, 'T = "run " + "scripts/audit/x.py"\n', X, "report"),
    (PY, 'T = "{0.decode}".format(b"scripts")\n', X, "report"),
    # Round 3 F6 (reviewer) and siblings
    (PY, 'name = "rules_core.sh"\np = "scripts/" + "lib/" + name\n', X, "report"),
    (PY, 'p = ("scripts/" "lib/") + name\n', X, "report"),
    (PY, 'p = "scripts/lib/%s" % name\n', X, "report"),
    (PY, 'p = "scripts/lib/{}".format(name)\n', X, "report"),
    (PY, 'p = f"{root}/scripts/lib/{name}"\n', X, "report"),
    (PY, 'd = {"k": f"{m[\'scripts/lib/rules_core.sh\']}"}\n', X, "report"),
    (NP, 'SUFFIX=.in\ncat scripts/dispatch.py"${SUFFIX}"\n', SH, "report"),
    (NP, 'cat "scripts/dispatch.py"${SUFFIX}\n', SH, "report"),
    (NP, "cat 'scripts/dispatch.py'.bak\n", SH, "report"),
    (NP, 'python -m "scripts.engine"${MOD}\n', SH, "report"),
    (NP, "cat scripts/dispatch.py`echo .in`\n", SH, "report"),
    (NP, "cd -- scripts/lib\n", SH, "report"),
    (NP, "pushd -n scripts/lib\n", SH, "report"),
    (NP, "git -C scripts/lib status\n", SH, "report"),
    (NP, "make --directory=scripts/lib\n", SH, "report"),
    (NP, "WorkingDirectory=@REPO_ROOT@/scripts/lib\n", "packaging/systemd/x.service", "report"),
    (NP, 'x = ["scripts/dispatch.py", "a"]\n', "config/x.yaml", "report"),
    (NP, '{"run": "scripts/dispatch.py"}\n', "config/x.json", ("rewrite", '{"run": "lu_machinery/dispatch.py"}\n')),
    (NP, '<a href="scripts/dispatch.py">x</a>\n', "docs/x.html", "report"),
    # Takeover round-4 candidate siblings
    (PY, 'T = "SCRIPTS.DISPATCH".lower()\n', X, "report"),
    (PY, 'T = "{}.{}".format(*["scripts", "dispatch"])\n', X, "report"),
    (PY, 'T = "%(p)s.dispatch" % {"p": "scripts"}\n', X, "report"),
    (PY, 'T = "scripts.engine.%-5s" % name\n', X, "report"),
    (PY, 'T = "scripts.{:>9}".format(name)\n', X, "report"),
    (PY, 'T = (f"scr" f"ipts.{x}").strip()\n', X, "report"),
    (PY, 'T = "scripts.dispatch" * 1\n', X, "report"),
    (PY, 'T = b"scripts.dispatch".decode()\n', X, "report"),
    (PY, 'T = "%s %s" % ("scripts.dispatch",)\n', X, "report"),
    (PY, 'T = "{1}".format("scripts")\n', X, "report"),
    (PY, 'T = "Running %s scripts" % n\n', X, "report"),
    (PY, 'T = "{:>5}".format(n)\n', X, "quiet"),
    (PY, 'T = ", ".join(names)\n', X, "quiet"),
    (PY, 'p = "%s/%s" % ("scripts", "dispatch.py")\n', X, "report"),
    (PY, 'p = "/".join(["scripts", "dispatch.py"])\n', X, "report"),
    (PY, 'p = "{}/lib/{}".format("scripts", name)\n', X, "report"),
    (PY, 'p = "scripts/lib/" + name + ".sh"\n', X, "report"),
    (PY, 'p = ("scripts/" + "lib/") + (name + "")\n', X, "report"),
    (PY, 'p = "scripts/dispatch.py{:>5}".format(n)\n', X, "report"),
    (PY, 'p = "scripts/" + "dispatch.py"\n', X, "report"),
    (PY, 'p = "scripts/" + "audit/x.py"\n', X, "report"),
    (NP, "cat scripts/dispatch.py:x\n", SH, "report"),
    (NP, "cat scripts/dispatch.py,w\n", SH, "report"),
    (NP, "cat scripts/dispatch.py.\n", SH, "report"),
    (NP, "cat scripts/dispatch.py@{u}\n", SH, "report"),
    (NP, "cat scripts/dispatch.py~\n", SH, "report"),
    (NP, "cat scripts/dispatch.py; ls\n", SH, ("rewrite", "cat lu_machinery/dispatch.py; ls\n")),
    (NP, "x=$(cat scripts/dispatch.py)\n", SH, ("rewrite", "x=$(cat lu_machinery/dispatch.py)\n")),
    (NP, "x=`cat scripts/dispatch.py`\n", SH, "report"),
    (NP, 'cat "scripts/dispatch.py" >out\n', SH, ("rewrite", 'cat "lu_machinery/dispatch.py" >out\n')),
    (NP, 'B="${B:-$ROOT/scripts/dispatch.py}"\n', SH, "report"),
    (NP, "X=${Y:-scripts/dispatch.py}\n", SH, "report"),
    (NP, "# Covers scripts/dispatch.py, and more.\n", SH, "inventory"),
    (NP, 'echo "Error: bad route in scripts/dispatch.py." >&2\n', SH, "report"),
    (NP, "# from scripts.dispatch's stderr\n", SH, "inventory"),
    (NP, "# No module named 'scripts'.\n", SH, "inventory"),
    (PY, "m = x + \"using 'scripts/dispatch.py'.\\n\"\n", X, "report"),
    (NP, "cd scripts/audit && cat ../dispatch.py\n", SH, "report"),
    (NP, "pushd scripts/review/prompts\n", SH, "report"),
    (NP, "Run `cd scripts/lib` first, then read scripts/lib in prose.\n", "docs/x.md", "report"),
    # Round 4 F3 (reviewer) and the takeover's siblings
    (PY, 'T = "scripts.audit".replace(old, "dispatch")\n', X, "report"),
    (PY, 'T = "prefixscripts.dispatch".removeprefix(prefix)\n', X, "report"),
    (PY, 'T = "prefixscripts.dispatch".lstrip(chars)\n', X, "report"),
    (PY, 'T = ("scripts.au" + x).replace("audit.foo", "dispatch")\n', X, "report"),
    (PY, 'T = "scripts.audit"[:n] + "dispatch"\n', X, "report"),
    (PY, 'T = "scripts.audit"[:8] + "dispatch"\n', X, "report"),
    (PY, 'T = "scripts.dispatchX"[:-1]\n', X, "report"),
    (PY, 'T = ("scripts.disp" if c else "") + "atch"\n', X, "report"),
    (PY, 'T = (x or "scripts.disp") + "atch"\n', X, "report"),
    (PY, 'T = str("scripts.disp") + "atch"\n', X, "report"),
    (PY, 'T = "{:.{n}}".format("scripts.dispatch_tools")\n', X, "report"),
    (PY, 'T = "SCRIPTS.AUDIT".lower().replace(a, b)\n', X, "report"),
    (PY, 'T = "scripts.%d" % n\n', X, "report"),
    (PY, 'T = (t := "scripts.") + "dispatch"\n', X, "report"),
    (PY, 'T = "scripts.audit".translate(table)\n', X, "report"),
    (PY, 'T = ".".join("scripts.x.dispatch".split(".")[::2])\n', X, "report"),
    (PY, 'T = "scripts.audit".split(sep)[0] + ".dispatch"\n', X, "report"),
    (PY, 'T = "scripts.audit".replace("x", new)\n', X, "report"),
    (PY, 'T = "scripts.audit." + "{}".format(x)\n', X, "report"),
    (PY, 'T = ", ".join([a, b])\n', X, "quiet"),
    (PY, 'T = "x"[:n] + "y"\n', X, "quiet"),
    (PY, 'T = (x or "y") + "z"\n', X, "quiet"),
    (PY, 'T = d["scripts.dispatch"]\n', X, ("rewrite", 'T = d["lu_machinery.dispatch"]\n')),
    (PY, 'T = "scripts.audit.%d" % n\n', X, "report"),
    (PY, 'T = f"{name!r}: scripts.audit.{n:>5}"\n', X, "report"),
    (PY, 'T = "{!r} in scripts.audit.{}".format(a, b)\n', X, "report"),
    (PY, 'T = sorted(["scripts.dispatch", x])\n', X, "report"),
    (PY, 'T = ("abc" + x).replace("\\n", sep) + "scripts.audit"\n', X, "report"),
    # Round 4 F6 (reviewer) and the takeover's siblings
    (PY, 'p = "scripts/audit".replace(old, "dispatch.py")\n', X, "report"),
    (PY, 'p = "scr" + piece + "ipts/dispatch.py"\n', X, "report"),
    (PY, 'p = "scripts/lib/rules_core.shX"[:-1]\n', X, "report"),
    (PY, 'p = ("scripts/" if c else "x/") + "dispatch.py"\n', X, "report"),
    (PY, 'p = "scripts/audit/%d.py" % n\n', X, "report"),
    (PY, 'p = os.environ.get("X") or "scripts/audit/x.py"\n', X, "report"),
    (PY, 'p = "scripts/" + "dispatch.py" + ",v"\n', X, "report"),
    (PY, 'm = "x" + "\\n".join(names) + " in scripts/dispatch.py.\\n"\n', X, "report"),
    (NP, 'cat "scripts/dispatch.py:x"\n', SH, "report"),
    (NP, 'cat "scripts/dispatch.py":x\n', SH, "report"),
    (NP, "cat scripts/dispatch.py\\ x\n", SH, "report"),
    (NP, "cat 'scripts/dispatch.py'\"${S}\"\n", SH, "report"),
    (NP, 'X="scripts/dispatch.py;rm"\n', SH, "report"),
    (NP, 'cat "scripts/dispatch.py"x\n', SH, "report"),
    (NP, 'cat "scripts/dispatch.py,v"\n', SH, "report"),
    (NP, "cat scripts/dispatch.py,v\n", SH, "report"),
    (NP, "run: scripts/dispatch.py,v\n", "config/x.yaml", "report"),
    (NP, '{"run": "scripts/dispatch.py,v"}\n', "config/x.json", "report"),
    (NP, "```bash\ncat scripts/dispatch.py,v\n```\n", "docs/x.md", "report"),
    (NP, "```bash\ncat scripts/dispatch.py:x\n```\n", "docs/x.md", "report"),
    (NP, "```sh\ncat 'scripts/dispatch.py'.bak\n```\n", "docs/x.md", "report"),
    (NP, '"$PY" "scripts/dispatch.py" run\n', SH, ("rewrite", '"$PY" "lu_machinery/dispatch.py" run\n')),
    (NP, 'echo "see scripts/dispatch.py, then"\n', SH, "report"),
    (NP, 'X="${X:-scripts/dispatch.py}"\n', SH, "report"),
    (NP, "```python\nopen('scripts/dispatch.py')\n```\n", "docs/x.md", "report"),
    (
        NP,
        "```bash\npython scripts/dispatch.py run\n```\n",
        "docs/x.md",
        ("rewrite", "```bash\npython lu_machinery/dispatch.py run\n```\n"),
    ),
    (NP, "WORKDIR scripts/lib\n", "Dockerfile", "report"),
    (NP, "    working-directory: scripts/lib\n", ".github/workflows/x.yml", "report"),
    (NP, '{"cwd": "scripts/lib"}\n', "config/x.json", "report"),
    (NP, "cd scripts && python dispatch.py\n", "scripts/audit/run.sh", "report"),
    (NP, 'pushd "$ROOT/scripts"\n', "scripts/audit/run.sh", "report"),
    (NP, 'git commit -m "fix\n- scripts/dispatch.py: renamed\n"\n', SH, "report"),
    (
        NP,
        "cat <<EOF\nRelated: scripts/dispatch.py, ../SKILL.md.\nEOF\ncat scripts/dispatch.py\n",
        SH,
        (
            "rewrite+report",
            "cat <<EOF\nRelated: scripts/dispatch.py, ../SKILL.md.\nEOF\ncat lu_machinery/dispatch.py\n",
        ),
    ),
    (NP, "wc -c scripts/dispatch.py\n", SH, ("rewrite", "wc -c lu_machinery/dispatch.py\n")),
    (NP, "cat <<EOF\nx\nEOF\ncat scripts/dispatch.py:x\n", SH, "report"),
    (
        NP,
        'ssh_q "mkdir -p $(printf %q "$DIR/scripts/lib")"\n',
        SH,
        ("rewrite", 'ssh_q "mkdir -p $(printf %q "$DIR/lu_machinery/lib")"\n'),
    ),
    (NP, 'x="$(cat "scripts/dispatch.py":x)"\n', SH, "report"),
    # Round 5 F3 (reviewer): literal-bearing builders, and their path equivalents
    (PY, 'T = "%.*s%s" % (n, "scripts.audit", "dispatch")\n', X, "report"),
    (PY, 'T = ("scr" + x + "ipts.audit")[:n] + "dispatch"\n', X, "report"),
    (PY, 'T = "".join(sorted(["ts.dispatch", x, "scrip"]))\n', X, "report"),
    (PY, 'T = {"k": "scripts.disp"}["k"] + "atch"\n', X, "report"),
    (PY, 'p = "%.*s%s" % (n, "scripts/audit", "/dispatch.py")\n', X, "report"),
    (PY, 'p = ("scr" + x + "ipts/audit")[:n] + "/dispatch.py"\n', X, "report"),
    (PY, 'p = "".join(sorted(["ts/dispatch.py", x, "scrip"]))\n', X, "report"),
    (PY, 'p = {"k": "scripts/disp"}["k"] + "atch.py"\n', X, "report"),
    # Round 5 F6 (reviewer): expanding heredocs, and blanks or newlines inside quoted arguments
    (NP, "cat <<EOF\n$(cat scripts/dispatch.py:x)\nEOF\n", SH, "report"),
    (NP, "cat <<EOF\n`cat scripts/dispatch.py:x`\nEOF\n", SH, "report"),
    (NP, "```bash\ncat <<EOF\n$(cat scripts/dispatch.py:x)\nEOF\n```\n", "docs/x.md", "report"),
    (NP, 'cat "scripts/dispatch.py more"\n', SH, "report"),
    (NP, 'cat "scripts/dispatch.py\nmore"\n', SH, "report"),
    # Reviewer held-outs H1-H4 (round 1)
    (
        PY,
        "from scripts.engine import control as ctl, help as product_help\n",
        X,
        (
            "rewrite",
            "from lu_machinery.engine import control as ctl\nfrom scripts.engine import help as product_help\n",
        ),
    ),
    (
        PY,
        'TARGET = r"scripts.engine.control.launch"\n',
        X,
        ("rewrite", 'TARGET = r"lu_machinery.engine.control.launch"\n'),
    ),
    (NP, "cat ./scripts/data/config.json\n", SH, ("rewrite", "cat ./lu_machinery/data/config.json\n")),
]


def _probe(tool: str, source: str, rel: str) -> tuple[str, list, list]:
    ownership = rename_python.OwnershipMap(PROBE_MAP)
    if tool == PY:
        new, _rewrites, unresolved, inventory = rename_python.rename_source(
            ownership, rel, source.encode(), frozenset()
        )
        return new.decode(), unresolved, inventory
    report = rename_python.Report("rename_nonpython", "check", "")
    new_text = rename_nonpython.scan_file(ownership, rel, source.encode(), source, report)
    return (source if new_text is None else new_text), report.unresolved, report.inventory


@pytest.mark.parametrize(("tool", "source", "rel", "expected"), PROBES, ids=[f"{i:03d}" for i in range(len(PROBES))])
def test_review_probe_is_rewritten_exactly_or_reported(tool: str, source: str, rel: str, expected: object) -> None:
    new, unresolved, inventory = _probe(tool, source, rel)
    kinds = [finding.kind for finding in unresolved]
    if isinstance(expected, tuple):
        mode, want = expected
        assert new == want, kinds
        assert bool(unresolved) == (mode == "rewrite+report"), kinds
    else:
        assert new == source, kinds
        assert bool(unresolved) == (expected == "report"), kinds
        if expected != "report":
            assert bool(inventory) == (expected == "inventory"), [f.kind for f in inventory]
    assert "tool_error" not in kinds


# -- fail-closed rules ------------------------------------------------------------------


def test_python_rewrites_only_exact_literal_values(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        'A = "scripts.dispatcher.primary"\n'
        'B = "scripts." "dispatcher.primary"\n'
        'C = "scripts.dispatcher." + name\n'
        'D = "scripts.dispatcher.primary".upper().lower()\n'
        'E = ("scripts."  # a comment between the parts\n'
        '     "dispatcher.primary")\n'
        'F = "python -m scripts.dispatcher.primary"\n'
        'G = "scripts/dispatcher/primary.py"\n'
    )
    _add(root, map_path, "scripts/pipeline/strings.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/strings.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/strings.py").splitlines()[:2] == [
        'A = "lu_machinery.dispatcher.primary"',
        'B = "lu_machinery.dispatcher.primary"',
    ]
    assert _read(root, "scripts/pipeline/strings.py").splitlines()[2:] == source.splitlines()[2:]
    assert [(item["kind"], item["line"]) for item in report["unresolved"]] == [
        ("computed_string", 3),
        ("static_expression", 4),
        ("assembled_module_string", 5),
        ("module_in_text", 7),
        ("path_string", 8),
    ]


def test_python_bare_package_use_holds_the_whole_file(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = 'import scripts.dispatcher.primary\nTARGET = "scripts.dispatcher.primary"\nREGISTRY = scripts\n'
    _add(root, map_path, "scripts/pipeline/registry.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/registry.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/registry.py") == source
    assert _kinds(report) == ["bare_package_use", "held_rewrite", "held_rewrite"]
    assert report["rewrites"] == []


def test_python_docstrings_are_listed_not_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = '"""Run python -m scripts.dispatcher.primary first."""\n'
    _add(root, map_path, "scripts/pipeline/doc.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/doc.py")

    assert code == 0
    assert _read(root, "scripts/pipeline/doc.py") == source
    assert [item["kind"] for item in report["inventory"]] == ["docstring_mention"]


def test_nonpython_heredoc_bodies_are_never_rewritten(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    script = (
        "python - <<'PY'\n"
        "open('scripts/dispatch.py' + suffix)\n"
        "PY\n"
        "cat <<EOF\n"
        "$(cat scripts/dispatch.py)\n"
        "EOF\n"
        "cat scripts/dispatch.py\n"
    )
    _add(root, map_path, "scripts/tools/heredoc.sh", M, script)

    code, report = _run(rename_nonpython, map_path, root, "apply", "scripts/tools/heredoc.sh")

    assert code == 1
    assert _read(root, "scripts/tools/heredoc.sh") == script.replace(
        "EOF\ncat scripts/dispatch.py", "EOF\ncat lu_machinery/dispatch.py"
    )
    assert _kinds(report) == ["heredoc_text", "heredoc_text"]


def test_nonpython_files_that_record_digests_are_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    data = '{"paths": ["scripts/dispatch.py"], "paths_sha256": "' + "a" * 64 + '"}\n'
    _add(root, map_path, "registry/freeze.json", P, data)

    code, report = _run(rename_nonpython, map_path, root, "apply", "registry/freeze.json")

    assert code == 1
    assert _read(root, "registry/freeze.json") == data
    assert _kinds(report) == ["digest_bound_file"]


# -- structured metadata ------------------------------------------------------------------


def _baseline(entries: list[dict[str, str]]) -> str:
    payload = {"schema": "mypy-ratchet-baseline.v1", "mypy": "2.1.0", "entries": entries}
    return json.dumps(payload, indent=2) + "\n"


def test_structured_baseline_renames_only_machinery_path_fields(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    text = _baseline(
        [
            {
                "path": "scripts/dispatch.py",
                "code": "index",
                "message": 'Module "scripts.dispatch" has no attribute "x"',
            },
            {
                "path": "scripts/plan_autofix.py",
                "code": "index",
                "message": 'Module "scripts.audit" has no attribute "x"',
            },
            {"path": "tests/test_gemini_output.py", "code": "arg-type", "message": "scripts/dispatch.py is fine"},
            {"path": "scripts/unmapped.py", "code": "index", "message": "x"},
        ]
    )
    _add(root, map_path, "scripts/lint/mypy_baseline.json", M, text)
    (root / "scripts/lint/__init__.py").write_text("", encoding="utf-8")

    code, report = _run(rename_structured, map_path, root, "apply")
    after = json.loads(_read(root, "scripts/lint/mypy_baseline.json"))

    assert code == 1
    assert [entry["path"] for entry in after["entries"]] == [
        "lu_machinery/dispatch.py",
        "scripts/plan_autofix.py",
        "tests/test_gemini_output.py",
        "scripts/unmapped.py",
    ]
    assert [entry["message"] for entry in after["entries"]] == [
        entry["message"] for entry in json.loads(text)["entries"]
    ]
    assert [(item["kind"], item["before"]) for item in report["unresolved"]] == [
        ("message_reference", "scripts.dispatch"),
        ("message_reference", "scripts/dispatch.py"),
        ("unknown_path", "scripts/unmapped.py"),
    ]
    assert _read(root, "scripts/lint/mypy_baseline.json") == text.replace(
        '"path": "scripts/dispatch.py"', '"path": "lu_machinery/dispatch.py"'
    )
    second = _run(rename_structured, map_path, root, "apply")[1]
    assert second["rewrites"] == [] and second["files_changed"] == []
    # rename_nonpython.py leaves the file to rename_structured.py.
    nonpython = _run(rename_nonpython, map_path, root, "check", "scripts/lint/mypy_baseline.json")[1]
    assert nonpython["rewrites"] == nonpython["unresolved"] == []


def test_structured_schema_mismatch_changes_nothing(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    text = _baseline([{"path": "scripts/dispatch.py", "code": "index", "message": "x", "line": "3"}])
    _add(root, map_path, "scripts/lint/mypy_baseline.json", M, text)

    code, report = _run(rename_structured, map_path, root, "apply")

    assert code == 1
    assert _read(root, "scripts/lint/mypy_baseline.json") == text
    assert _kinds(report) == ["schema_mismatch"]


# -- PR 12764 review round 1 ----------------------------------------------------------


def test_r1_f1_structured_file_behind_a_directory_symlink_is_not_written(tmp_path: Path) -> None:
    root = tmp_path / "clone"
    outside = tmp_path / "outside"
    (outside / "lint").mkdir(parents=True)
    root.mkdir()
    text = _baseline([{"path": "scripts/dispatch.py", "code": "index", "message": "x"}])
    (outside / "lint" / "mypy_baseline.json").write_text(text, encoding="utf-8")
    (root / "scripts").symlink_to(outside, target_is_directory=True)
    map_path = tmp_path / "ownership.json"
    map_path.write_text(json.dumps({"scripts/dispatch.py": M, "scripts/lint/mypy_baseline.json": M}), encoding="utf-8")

    code, report = _run(rename_structured, map_path, root, "apply")

    assert code == 1
    assert _kinds(report) == ["symlinked_path"]
    assert (outside / "lint" / "mypy_baseline.json").read_text(encoding="utf-8") == text


@pytest.mark.parametrize(
    ("source", "kinds"),
    [
        # ``scripts`` aliases the product package: ``scripts.dispatch`` is its attribute, not the machinery module.
        ("import scripts.audit as scripts\nimport lu_machinery.dispatcher.primary\nresult = scripts.dispatch()\n", []),
        ("from scripts import audit as scripts\nresult = scripts.dispatch()\n", []),
        # An alias of a machinery package that reaches a product submodule breaks when the import is renamed.
        ("import scripts.review as review\nreview.prompts.load()\n", ["alias_crosses_owner", "held_rewrite"]),
        ("from scripts import review\nreview.prompts.load()\n", ["alias_crosses_owner", "held_rewrite"]),
    ],
)
def test_r1_f2_attribute_chains_follow_their_real_binding(
    tree: tuple[Path, Path], source: str, kinds: list[str]
) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/pipeline/alias.py", P, source)

    _code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/alias.py")

    assert _read(root, "scripts/pipeline/alias.py") == source
    assert _kinds(report) == kinds


@pytest.mark.parametrize(
    ("rel", "text", "kind"),
    [
        ("config/escaped.json", '{"x": "\\u0073cripts.dispatcher.primary"}\n', "hidden_reference"),
        ("config/escaped.json", '{"x": "scr\\u0069pts/dispatch.py"}\n', "hidden_reference"),
        ("launchd/escaped.plist", "<string>scr&#105;pts/dispatch.py</string>\n", "hidden_reference"),
        (
            "config/escaped.json",
            '{"p": ["scripts/dispatch.py"], "s\\u0068a256": "' + "a" * 64 + '"}\n',
            "digest_bound_file",
        ),
        ("scripts/tools/case.sh", "cat Scripts/dispatch.py\n", "case_variant"),
    ],
)
def test_r1_f3_escaped_and_case_variant_names_are_reported(
    tree: tuple[Path, Path], rel: str, text: str, kind: str
) -> None:
    root, map_path = tree
    _add(root, map_path, rel, M if rel.startswith("scripts/") else P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 1
    assert _read(root, rel) == text
    assert _kinds(report) == [kind]


def test_r1_f4_expanding_operations_are_bounded_before_they_run(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        'A = ("a" * 1000 * 1000).replace("a", "b" * 1000 * 1000) + "scripts.dispatcher.primary"\n'
        'B = ("b" * 1000).join(["a"] * 1000 * 1000) + "scripts.dispatcher.primary"\n'
        'C = ("x" * 1000).translate({120: "y" * 10000}) + "scripts.dispatcher.primary"\n'
    )
    _add(root, map_path, "scripts/pipeline/large.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/large.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/large.py") == source
    assert _kinds(report) == ["computed_string", "computed_string", "computed_string"]


@pytest.mark.parametrize(
    "source",
    [
        'def f(): "scripts.dispatcher.primary"\n',
        'class C: "scripts.dispatcher.primary"\n',
        '"scripts.dispatcher.primary"; x = 1\n',
        'def f():\n    "scripts.dispatcher.primary"; y = 2\n',
    ],
)
def test_r1_f5_every_docstring_form_is_left_as_written(tree: tuple[Path, Path], source: str) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/pipeline/doc.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/doc.py")

    assert code == 0
    assert _read(root, "scripts/pipeline/doc.py") == source
    assert [item["kind"] for item in report["inventory"]] == ["docstring_mention"]


def test_r1_f5_python_comments_are_listed(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = "x = 1  # see scripts.dispatcher.primary\n"
    _add(root, map_path, "scripts/pipeline/comment.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/comment.py")

    assert code == 0
    assert _read(root, "scripts/pipeline/comment.py") == source
    assert [item["kind"] for item in report["inventory"]] == ["comment_mention"]


def test_python_bare_root_inside_text_is_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        'subprocess.run("cd scripts && python dispatcher/primary.py", shell=True)\n'
        'MATCH = re.compile(r"scripts\\.dispatcher\\.primary")\n'
    )
    _add(root, map_path, "scripts/pipeline/shell.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/shell.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/shell.py") == source
    assert _kinds(report) == ["root_in_text", "root_in_text"]


def test_nonpython_binary_files_and_symlink_targets_are_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    (root / "assets").mkdir()
    (root / "assets" / "blob.bin").write_bytes(b"\0scripts/dispatch.py")
    (root / "bin").mkdir()
    (root / "bin" / "dispatch").symlink_to("../scripts/dispatch.py")

    code, report = _run(rename_nonpython, map_path, root, "apply", "assets", "bin")

    assert code == 1
    assert [(item["kind"], item["path"]) for item in report["unresolved"]] == [
        ("binary_file", "assets/blob.bin"),
        ("symlink_target", "bin/dispatch"),
    ]
    assert (root / "assets" / "blob.bin").read_bytes() == b"\0scripts/dispatch.py"


def test_try_except_import_fallback_keeps_its_rewrites(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        "try:\n"
        "    from scripts.dispatcher.primary import ROUTES\n"
        "except ImportError:\n"
        "    from dispatcher.primary import ROUTES\n"
        "ROUTES.get('x')\n"
    )
    _add(root, map_path, "scripts/pipeline/fallback.py", P, source)

    _code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/fallback.py")

    # Without --external-names the unprefixed fallback is reported; the chain on the alias is not.
    assert _kinds(report) == ["unprefixed_cross_owner"]
    assert "    from lu_machinery.dispatcher.primary import ROUTES\n" in _read(root, "scripts/pipeline/fallback.py")
    assert "ROUTES.get('x')\n" in _read(root, "scripts/pipeline/fallback.py")


# -- PR 12764 review round 2 ----------------------------------------------------------


@pytest.mark.parametrize(
    ("rel", "text"),
    [
        # F3: escaped names continued across lines (TOML and YAML), and the other ways a reader joins a word.
        ("config/continued.toml", 'target = """\\u0073cr\\\n    ipts/dispatch.py"""\n'),
        ("config/continued.yaml", 'target: "\\u0073cr\\\n  ipts/dispatch.py"\n'),
        ("config/continued.toml", 't = """scr\\\n    ipts/dispatch.py"""\n'),
        ("scripts/tools/joined.sh", 'cat scr""ipts/dispatch.py\n'),
        ("scripts/tools/joined.sh", 'cat scr"i"pts/dispatch.py\n'),
        ("scripts/tools/joined.sh", "cat scr\\ipts/dispatch.py\n"),
        ("scripts/tools/joined.sh", "cat scr\\\nipts/dispatch.py\n"),
        ("scripts/tools/joined.sh", "cat scr${EMPTY}ipts/dispatch.py\n"),
        ("scripts/tools/joined.sh", "cat scr$(true)ipts/dispatch.py\n"),
        ("scripts/tools/joined.sh", "cat scr`true`ipts/dispatch.py\n"),
        ("scripts/tools/joined.sh", "echo $'\\163cripts/dispatch.py'\n"),
        ("config/joined.j2", "path: scr{{ x }}ipts/dispatch.py\n"),
    ],
)
def test_r2_f3_names_joined_by_a_reader_are_reported(tree: tuple[Path, Path], rel: str, text: str) -> None:
    root, map_path = tree
    _add(root, map_path, rel, M if rel.startswith("scripts/") else P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 1
    assert _read(root, rel) == text
    assert _kinds(report) == ["hidden_reference"]


@pytest.mark.parametrize(
    "text",
    [
        "echo the script's own output\n",  # an apostrophe joins nothing
        'cat scr""ipts/audit/probe_uk_writing_score.py\n',  # a joined product path names nothing to rename
    ],
)
def test_r2_f3_joined_view_controls_stay_quiet(tree: tuple[Path, Path], text: str) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/tools/quiet.sh", M, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", "scripts/tools/quiet.sh")

    assert code == 0, report["unresolved"]
    assert _read(root, "scripts/tools/quiet.sh") == text


def test_r2_f4_escaping_conversions_are_bounded_before_they_run(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = (
        'A = ascii(("\\U00010000" * 1000) * 100) + "scripts.dispatcher.primary"\n'
        'B = (("\\U00010000" * 1000) * 101).encode("raw_unicode_escape") + b"scripts.dispatcher.primary"\n'
    )
    _add(root, map_path, "scripts/pipeline/escaping.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/escaping.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/escaping.py") == source
    assert _kinds(report) == ["computed_string", "computed_string"]


def test_python_identifier_that_normalises_to_scripts_holds_the_file(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = "import ｓｃｒｉｐｔｓ.dispatcher.primary\nimport scripts.dispatcher.primary\n"
    _add(root, map_path, "scripts/pipeline/nfkc.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/nfkc.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/nfkc.py") == source
    assert _kinds(report) == ["unicode_identifier", "held_rewrite"]


def test_nonpython_compressed_archives_are_opened_and_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    (root / "fixtures").mkdir()
    (root / "fixtures" / "baseline.json.gz").write_bytes(gzip.compress(b'{"path": "scripts/dispatch.py"}'))
    (root / "fixtures" / "other.json.gz").write_bytes(gzip.compress(b'{"path": "docs/x.md"}'))
    (root / "fixtures" / "utf16.txt").write_bytes("scripts/dispatch.py\n".encode("utf-16"))

    code, report = _run(rename_nonpython, map_path, root, "apply", "fixtures")

    assert code == 1
    assert [(item["kind"], item["path"]) for item in report["unresolved"]] == [
        ("compressed_file", "fixtures/baseline.json.gz"),
        ("binary_file", "fixtures/utf16.txt"),
    ]


def test_nonpython_second_hidden_name_on_a_line_is_not_lost(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    text = 'cat scr""ipts/audit/probe_uk_writing_score.py scr""ipts/dispatch.py\n'
    _add(root, map_path, "scripts/tools/two.sh", M, text)

    code, report = _run(rename_nonpython, map_path, root, "check", "scripts/tools/two.sh")

    assert code == 1
    assert [(item["kind"], item["before"]) for item in report["unresolved"]] == [
        ("hidden_reference", "scripts/dispatch.py")
    ]


# -- author pre-check before review round 3 -------------------------------------------


@pytest.mark.parametrize(
    ("rel", "text"),
    [
        ("scripts/tools/glued.sh", "printf 'header\\nscripts/dispatch.py\\n'\n"),
        ("scripts/tools/glued.sh", "python -Bmscripts.dispatcher.primary\n"),
        ("scripts/tools/glued.sh", "x=.%2Fscripts%2Fdispatch.py\n"),
        ("config/glued.json", '{"cmd": "set -e\\nscripts/dispatch.py"}\n'),
        ("config/glued.yaml", "  files: '\\bscripts/lib/'\n"),
    ],
)
def test_names_glued_to_an_escape_letter_or_option_cluster_are_reported(
    tree: tuple[Path, Path], rel: str, text: str
) -> None:
    root, map_path = tree
    _add(root, map_path, rel, M if rel.startswith("scripts/") else P, text)

    code, _report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 1
    assert _read(root, rel) == text


@pytest.mark.parametrize(
    "source",
    [
        'PAT = re.compile(r"\\bscripts/dispatch\\.py\\b")\n',
        'ARGS = [sys.executable, "-Bmscripts.dispatcher.primary"]\n',
        'T = "hcraeser.stpircs"[::-1] + suffix\n',  # a literal-only part inside a run-time expression
    ],
)
def test_python_glued_and_transformed_literals_are_reported(tree: tuple[Path, Path], source: str) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/pipeline/glued.py", P, source)

    code, _report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/glued.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/glued.py") == source


@pytest.mark.parametrize(
    "body",
    [
        "def f(scripts):\n    return scripts.dispatcher.primary\n",
        "def f():\n    scripts = load()\n    return scripts.dispatcher.primary\n",
        "f = lambda scripts: scripts.dispatcher.primary\n",
        "x = [scripts.dispatcher.primary for scripts in objs]\n",
        "for scripts in objs:\n    pass\nscripts.dispatcher.primary.run()\n",
        "import scripts.audit as scripts\nscripts.dispatcher.primary.run()\n",
        "scripts = object()\nscripts.dispatcher.primary.run()\n",
    ],
)
def test_shadowed_scripts_name_holds_the_file(tree: tuple[Path, Path], body: str) -> None:
    root, map_path = tree
    source = "import scripts.dispatcher.primary\n" + body
    _add(root, map_path, "scripts/pipeline/shadow.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/shadow.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/shadow.py") == source
    assert "rebound_name" in _kinds(report) and "held_rewrite" in _kinds(report)


def test_comprehension_variable_does_not_shadow_the_module_import(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = "import scripts.dispatcher.primary\nx = [scripts for scripts in y]\nscripts.dispatcher.primary.run()\n"
    _add(root, map_path, "scripts/pipeline/comp.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/comp.py")

    assert code == 0, report["unresolved"]
    assert _read(root, "scripts/pipeline/comp.py").endswith("lu_machinery.dispatcher.primary.run()\n")


def test_machinery_file_importing_a_product_sibling_is_reported(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = "import prompts\n"  # scripts/review/prompts is product; the importer is machinery
    _add(root, map_path, "scripts/review/loader.py", M, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/review/loader.py")

    assert code == 1
    assert _read(root, "scripts/review/loader.py") == source
    assert _kinds(report) == ["unprefixed_cross_owner"]


def test_mixed_package_name_is_not_renamed(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    source = 'T = resources.files("scripts.review") / "prompts" / "plan-review.md.j2"\n'
    _add(root, map_path, "scripts/pipeline/res.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/res.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/res.py") == source
    assert _kinds(report) == ["ambiguous_module"]


@pytest.mark.parametrize(
    ("rel", "text", "kind"),
    [
        ("docs/imports.md", "Use `from scripts.review import prompts` here.\n", "python_import_in_text"),
        ("docs/imports.md", "```bash\n>>> from scripts.review import prompts\n```\n", "python_import_in_text"),
        ("scripts/tools/cwd.sh", "docker run -w scripts/lib img\n", "cwd_into_scripts"),
        ("compose.yml", "    working_dir: scripts/lib\n", "cwd_into_scripts"),
        ("tox.ini", "changedir = scripts/lib\n", "cwd_into_scripts"),
        ("scripts/tools/cwd.sh", "npm --prefix scripts/lib run build\n", "cwd_into_scripts"),
        ("docs/fence.md", "```bash\n```text\ncat scripts/dispatch.py:x\n```\n", "not_plain"),
        ("docs/indented.md", "Text.\n\n    cat scripts/dispatch.py\n", "non_shell_fence"),
        ("scripts/tools/doc.sh", "cat <<END-X\nEND\ncat scripts/dispatch.py:x\nEND-X\n", "heredoc_text"),
    ],
)
def test_more_contexts_are_reported_not_rewritten(tree: tuple[Path, Path], rel: str, text: str, kind: str) -> None:
    root, map_path = tree
    _add(root, map_path, rel, M if rel.startswith("scripts/") else P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 1
    assert _read(root, rel) == text
    assert kind in _kinds(report)


@pytest.mark.parametrize(
    ("rel", "text"),
    [("setup.cfg", "; python -m scripts.dispatcher.primary\n"), ("page.j2", "{# see scripts/dispatch.py #}\n")],
)
def test_ini_and_jinja_comments_are_left_as_written(tree: tuple[Path, Path], rel: str, text: str) -> None:
    root, map_path = tree
    _add(root, map_path, rel, P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 0
    assert _read(root, rel) == text
    assert [item["kind"] for item in report["inventory"]] == ["comment_mention"]


def test_split_literal_search_takes_linear_time() -> None:
    texts = ["s"] + ["c", "r", "i", "p", "t"] * 200
    assert rename_python.spells_word(texts)
    assert not rename_python.spells_word(["c", "r", "i", "p", "t"] * 200)


def test_structured_reads_the_moved_location_without_a_map_key(tmp_path: Path) -> None:
    root = tmp_path / "clone"
    (root / "lu_machinery" / "lint").mkdir(parents=True)
    text = _baseline([{"path": "scripts/dispatch.py", "code": "index", "message": "x"}])
    (root / "lu_machinery" / "lint" / "mypy_baseline.json").write_text(text, encoding="utf-8")
    map_path = tmp_path / "ownership.json"
    map_path.write_text(json.dumps({"scripts/dispatch.py": M}), encoding="utf-8")

    code, report = _run(rename_structured, map_path, root, "check")

    assert code == 0
    assert [item["after"] for item in report["rewrites"]] == ["lu_machinery/dispatch.py"]


@pytest.mark.parametrize(
    ("rel", "text", "kind"),
    [
        ("scripts/tools/colour.sh", 'echo -e "\\033[1mscripts/dispatch.py\\033[0m"\n', "not_plain"),
        (
            "scripts/tools/url.sh",
            'curl "https://x/run?cmd=python%20-m%20scripts.dispatcher.primary"\n',
            "hidden_reference",
        ),
        ("config/space.json", '{"cmd": "python\\u0020-m\\u0020scripts.dispatcher.primary"}\n', "hidden_reference"),
        ("scripts/tools/letter.sh", "x=файлscripts/dispatch.py\n", "not_plain"),
        ("scripts/tools/doc.sh", 'cat <<E"O"F\nE\ncat scripts/dispatch.py\nEOF\n', "heredoc_text"),
        ("scripts/tools/root.sh", "pytest --rootdir=scripts/lib\n", "cwd_into_scripts"),
    ],
)
def test_second_precheck_contexts_are_reported(tree: tuple[Path, Path], rel: str, text: str, kind: str) -> None:
    root, map_path = tree
    _add(root, map_path, rel, M if rel.startswith("scripts/") else P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", rel)

    assert code == 1
    assert _read(root, rel) == text
    assert kind in _kinds(report)


def test_dollar_hash_in_a_template_is_no_jinja_comment(tree: tuple[Path, Path]) -> None:
    root, map_path = tree
    text = "echo ${#arr[@]}\npython -m scripts.dispatcher.primary\n{# note #}\n"
    _add(root, map_path, "templates/run.sh.j2", P, text)

    code, report = _run(rename_nonpython, map_path, root, "apply", "templates/run.sh.j2")

    assert code == 0, report["unresolved"]
    assert "python -m lu_machinery.dispatcher.primary\n" in _read(root, "templates/run.sh.j2")


@pytest.mark.parametrize(
    "source",
    [
        'print(f"\\033[1mscripts/dispatch.py\\033[0m")\n',
        'T = "файлscripts.dispatcher.primary"\n',
    ],
)
def test_python_colour_codes_and_letters_before_the_name_are_reported(tree: tuple[Path, Path], source: str) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/pipeline/glued2.py", P, source)

    code, _report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/glued2.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/glued2.py") == source


@pytest.mark.parametrize(
    "source",
    [
        'import scripts.review\nT = resources.files(scripts.review) / "prompts"\n',
        'from scripts import review\nT = resources.files(review) / "prompts"\n',
        'import scripts.review\nT = Path(scripts.review.__file__).parent / "prompts"\n',
    ],
)
def test_mixed_package_object_through_a_binding_holds_the_file(tree: tuple[Path, Path], source: str) -> None:
    root, map_path = tree
    _add(root, map_path, "scripts/pipeline/anchor.py", P, source)

    code, report = _run(rename_python, map_path, root, "apply", "scripts/pipeline/anchor.py")

    assert code == 1
    assert _read(root, "scripts/pipeline/anchor.py") == source
    assert "mixed_package_use" in _kinds(report)
