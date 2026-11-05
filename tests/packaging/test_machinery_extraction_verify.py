"""verify_extraction.py finds each extraction defect class (V1-V9) and passes a correct extraction.

Every case builds a small synthetic source repository in tmp_path, replays it the way
git-filter-repo would (path filter plus the scripts/ -> lu_machinery/ rename, with a commit
map), adds one transformation commit, and runs the verifier as a CLI. The verifier is copied
next to stand-in rename tools and a stand-in history_policy.py that keep the real tools'
interfaces (PR 12764 and the parallel history-policy brief), so no case needs LibCST,
git-filter-repo, the network or live repository state. The verifier runs every git call and
child process in bubblewrap; the cases that run it skip, with the reason, where bwrap cannot
start a sandbox.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MOVE_DIR = REPO_ROOT / "packaging" / "machinery-move"
VERIFIER = MOVE_DIR / "verify_extraction.py"
TESTS_LIST = MOVE_DIR / "machinery_tests.txt"

pytestmark = pytest.mark.timeout(600)

CONTRACT_SECTION_4_TESTS = {
    "tests/test_fleet_repos.py",
    "tests/test_sibling_git_https.py",
    "tests/orchestration/test_merge_closeout.py",
    "tests/test_worktree_claims_lock_identity.py",
    "tests/orchestration/test_worktree_claims_cli.py",
    "tests/test_handoff_slot_registry.py",
    "tests/test_launcher_interactive_scope.py",
    "tests/test_session_supervisor.py",
    "tests/test_rules_core_loading.py",
    "tests/review/test_record_cf_verdict.py",
    "tests/publish/test_pr_merge_squash_scan.py",
    "tests/review/test_routing_consumers.py",
    "tests/githooks/test_owned_paths_hook.py",
}

# A stand-in for the three PR 12764 rename tools: same CLI, same report keys, token rewrites only.
STUB_RENAME = r"""
import argparse, hashlib, json, os, sys
from pathlib import Path
NAME = Path(__file__).name
TOKENS = [
    ("from scripts.lib import", "from lu_machinery.lib import"),
    ('"scripts.dispatch"', '"lu_machinery.dispatch"'),
    ("python -m scripts.dispatch", "python -m lu_machinery.dispatch"),
    ("see scripts/dispatch.py", "see lu_machinery/dispatch.py"),
]
parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument("--check", action="store_true")
mode.add_argument("--apply", action="store_true")
parser.add_argument("--map", required=True)
parser.add_argument("--root", required=True)
parser.add_argument("--report")
parser.add_argument("--jobs")
parser.add_argument("--external-names")
parser.add_argument("paths", nargs="*")
args = parser.parse_args()
expected_names = os.environ.get("STUB_EXPECT_EXTERNAL_NAMES")
if NAME == "rename_python.py" and expected_names and args.external_names != expected_names:
    sys.exit(2)  # the verifier must pass --external-names through
root = Path(args.root)
files = []
for target in [root / p for p in args.paths] or [root]:
    if target.is_file():
        files.append(target)
    else:
        files += [f for f in target.rglob("*") if f.is_file() and ".git" not in f.relative_to(root).parts]
rewrites, changed = [], []
for path in sorted(set(files)):
    rel = path.relative_to(root).as_posix()
    python = rel.endswith(".py")
    if not (python if NAME == "rename_python.py" else not python if NAME == "rename_nonpython.py" else False):
        continue
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    new = text
    for old, replacement in TOKENS:
        if old in new:
            rewrites.append({"path": rel, "line": 1, "kind": "stub", "before": old, "after": replacement})
            new = new.replace(old, replacement)
    if new != text:
        changed.append(rel)
        if args.apply:
            path.write_text(new, encoding="utf-8", errors="surrogateescape")
report = {
    "tool": NAME,
    "mode": "apply" if args.apply else "check",
    "map_sha256": hashlib.sha256(Path(args.map).read_bytes()).hexdigest(),
    "files_scanned": len(files),
    "files_changed": changed,
    "rewrites": rewrites,
    "unresolved": [],
}
Path(args.report).write_text(json.dumps(report), encoding="utf-8")
sys.exit(0)
"""

# A stand-in for history_policy.py: records its argv and exits with the code the case sets.
STUB_HISTORY_POLICY = r"""
import json, sys
from pathlib import Path
here = Path(__file__).parent
print("HP-ARGV " + json.dumps(sys.argv[1:]))
code = here / "history_policy.exit"
sys.exit(int(code.read_text()) if code.exists() else 0)
"""

DISPATCH = '''"""Dispatch entry point; this prose mentions scripts.dispatch and stays as written."""

import argparse

from scripts.lib import util

# version {version}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="dispatch")
    parser.parse_args(argv)
    return util.VALUE


if __name__ == "__main__":
    raise SystemExit(main() - 1)
'''

UTIL = 'VALUE = 1\nMODULE = "scripts.dispatch"\n'
DESELECTING_CONFTEST = """def pytest_collection_modifyitems(config, items):
    dropped = [item for item in items if item.name == "test_second"]
    config.hook.pytest_deselected(items=dropped)
    items[:] = [item for item in items if item not in dropped]
"""
CORE = "Run `python -m scripts.dispatch`; see scripts/dispatch.py.\n"
PORTED_TEST = "from scripts.lib import util\n\n\ndef test_value():\n    assert util.VALUE == 1\n"

MANIFEST = [
    ("scripts/dispatch.py", "lu_machinery/dispatch.py"),
    ("scripts/lib/__init__.py", "lu_machinery/lib/__init__.py"),
    ("scripts/lib/util.py", "lu_machinery/lib/util.py"),
    ("agents_extensions/shared/rules/core.md", "agents_extensions/shared/rules/core.md"),
    ("-", "lu_machinery/__init__.py"),
]
HISTORY_PATHS = ["scripts/lib/legacy.py"]
EXCLUDE = ["docs/runbooks/secret.md", "scripts/product_mod.py", "scripts/__init__.py"]
EXPECTATIONS = [
    ("imports", "lu_machinery/dispatch.py", "present", "from lu_machinery.lib import util"),
    ("imports", "lu_machinery/dispatch.py", "absent", "from scripts.lib import util"),
    ("module-strings", "lu_machinery/lib/util.py", "present", '"lu_machinery.dispatch"'),
    ("non-python", "agents_extensions/shared/rules/core.md", "present", "python -m lu_machinery.dispatch"),
    ("resource-paths", "agents_extensions/shared/rules/core.md", "present", "lu_machinery/dispatch.py"),
]
OWNERSHIP = {
    "scripts/__init__.py": "product",
    "scripts/product_mod.py": "product",
    "scripts/dispatch.py": "machinery",
    "scripts/lib/__init__.py": "machinery",
    "scripts/lib/util.py": "machinery",
    "scripts/lib/legacy.py": "machinery",
    "scripts/lib/product_child.py": "product",
    "scripts/product_ns/child.py": "product",
}
TESTS_LIST_STUB = "# [run]\ntests/test_machinery.py\n# [support]\ntests/__init__.py\ntests/helper_data.txt\n"
POLICY_SHA = "a" * 64


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in {"HOME", "XDG_CONFIG_HOME"}}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_AUTHOR_NAME="Verify Test",
        GIT_AUTHOR_EMAIL="verify-test@example.invalid",
        GIT_COMMITTER_NAME="Verify Test",
        GIT_COMMITTER_EMAIL="verify-test@example.invalid",
    )
    return env


def git(repo: Path, *args: str) -> str:
    executable = shutil.which("git")
    assert executable is not None
    result = subprocess.run(
        [executable, "-C", str(repo), "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
        timeout=120,
    )
    return result.stdout.strip()


def write_files(repo: Path, files: dict[str, str | None]) -> None:
    for name, content in files.items():
        path = repo / name
        if content is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def commit(repo: Path, files: dict[str, str | None], message: str) -> str:
    write_files(repo, files)
    git(repo, "add", "-A")
    git(repo, "commit", "--quiet", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "--quiet", "--initial-branch=main")
    return path


def renamed(path: str) -> str:
    return "lu_machinery/" + path[len("scripts/") :] if path.startswith("scripts/") else path


@dataclass
class World:
    tmp: Path
    kit: Path
    src: Path
    extract: Path
    source: str
    source_commits: list[str]
    map_lines: list[str]
    rewritten: list[str]
    tip: str
    final_tree: str
    inputs: dict[str, Path] = field(default_factory=dict)

    def write_input(self, name: str, text: str) -> Path:
        path = self.tmp / "inputs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.inputs[name] = path
        return path

    def write_commit_map(self, lines: list[str]) -> None:
        self.write_input("commit-map", "".join(f"{line}\n" for line in ["old" + " " * 38 + "new", *lines]))

    def refreeze(self) -> None:
        """Make --final-tree the tree of the current HEAD (a case that edits history after setup)."""
        self.final_tree = git(self.extract, "rev-parse", "HEAD^{tree}")

    def args(self, *extra: str, **overrides: str) -> list[str]:
        values = {
            "--repo": str(self.extract),
            "--source-repo": str(self.src),
            "--source": self.source,
            "--commit-map": str(self.inputs["commit-map"]),
            "--tree-manifest": str(self.inputs["manifest.tsv"]),
            "--history-paths": str(self.inputs["history.txt"]),
            "--exclude": str(self.inputs["exclude.txt"]),
            "--expectations": str(self.inputs["expectations.tsv"]),
            "--rewrite-tip": self.tip,
            "--final-tree": self.final_tree,
            "--map": str(self.inputs["ownership.json"]),
            "--python": sys.executable,
            "--tool-python": sys.executable,
            "--jobs": "4",
            "--report": str(self.tmp / "report.json"),
        }
        values.update(overrides)
        out: list[str] = []
        for key, value in values.items():
            out += [key, value]
        return [*out, *extra]

    def run(self, *extra: str, env: dict[str, str] | None = None, **overrides: str) -> tuple[int, dict[str, dict], str]:
        report = self.tmp / "report.json"
        report.unlink(missing_ok=True)
        proc = subprocess.run(
            [sys.executable, str(self.kit / "verify_extraction.py"), *self.args(*extra, **overrides)],
            capture_output=True,
            text=True,
            timeout=540,
            env={**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, **(env or {})},
            check=False,
        )
        output = proc.stdout + proc.stderr
        checks: dict[str, dict] = {}
        if report.is_file():
            checks = {item["check"]: item for item in json.loads(report.read_text())["checks"]}
        return proc.returncode, checks, output


def build_source(src: Path) -> list[str]:
    init_repo(src)
    c1 = commit(
        src,
        {
            "scripts/__init__.py": "",
            "scripts/dispatch.py": DISPATCH.format(version=1),
            "scripts/lib/__init__.py": "",
            "scripts/lib/util.py": UTIL,
            "scripts/lib/legacy.py": "OLD = 1\n",
            "scripts/product_mod.py": "PRODUCT = 1\n",
            "docs/runbooks/secret.md": "confidential operational notes\n",
            "agents_extensions/shared/rules/core.md": CORE,
            "tests/__init__.py": "",
            "tests/test_machinery.py": PORTED_TEST,
            "tests/test_empty.py": "# collects no tests\n",
            "tests/helper_data.txt": "fixture\n",
            "tests/deselecting/conftest.py": DESELECTING_CONFTEST,
            "tests/deselecting/test_two.py": "def test_first():\n    pass\n\n\ndef test_second():\n    assert False\n",
        },
        "c1 initial",
    )
    c2 = commit(src, {"scripts/dispatch.py": DISPATCH.format(version=2), "scripts/lib/legacy.py": None}, "c2 dispatch")
    c3 = commit(src, {"scripts/product_mod.py": "PRODUCT = 2\n"}, "c3 product only")
    c4 = commit(src, {"scripts/dispatch.py": DISPATCH.format(version=3)}, "c4 dispatch")
    return [c1, c2, c3, c4]


def replay(src: Path, commits: list[str], extract: Path, keep: set[str]) -> tuple[list[str], list[str]]:
    """Filter-repo stand-in: keep only `keep` source paths, rename scripts/, prune empty commits."""
    init_repo(extract)
    lines: list[str] = []
    rewritten: list[str] = []
    for old in commits:
        wanted = {path for path in git(src, "ls-tree", "-r", "--name-only", old).splitlines() if path in keep}
        current = {path for path in git(extract, "ls-files").splitlines() if path}  # paths of the last rewritten commit
        for path in current - {renamed(p) for p in wanted}:
            (extract / path).unlink()
        for path in wanted:
            target = extract / renamed(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(git(src, "show", f"{old}:{path}") + "\n", encoding="utf-8")
        git(extract, "add", "-A")
        changed = subprocess.run(
            ["git", "-C", str(extract), "diff", "--cached", "--quiet"], env=_git_env(), check=False, timeout=120
        ).returncode
        if rewritten and not changed:
            lines.append(f"{old} {'0' * 40}")
            continue
        new = commit(extract, {}, git(src, "log", "-1", "--format=%s", old))
        rewritten.append(new)
        lines.append(f"{old} {new}")
    return lines, rewritten


def transform(extract: Path) -> dict[str, str | None]:
    dispatch = (extract / "lu_machinery/dispatch.py").read_text(encoding="utf-8")
    core = (extract / "agents_extensions/shared/rules/core.md").read_text(encoding="utf-8")
    return {
        "lu_machinery/__init__.py": "",
        "lu_machinery/dispatch.py": dispatch.replace("from scripts.lib import", "from lu_machinery.lib import"),
        "lu_machinery/lib/util.py": UTIL.replace('"scripts.dispatch"', '"lu_machinery.dispatch"'),
        "agents_extensions/shared/rules/core.md": core.replace("scripts.dispatch", "lu_machinery.dispatch").replace(
            "scripts/dispatch.py", "lu_machinery/dispatch.py"
        ),
    }


def _sandbox_unavailable() -> str:
    """Why the verifier's bubblewrap sandbox cannot start here, or an empty string."""
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        return "bubblewrap (bwrap) is not installed; the verifier refuses to run without its sandbox"
    probe = subprocess.run(
        [
            bwrap,
            "--die-with-parent",
            "--unshare-all",
            "--ro-bind",
            "/",
            "/",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "true",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return "" if probe.returncode == 0 else f"bubblewrap cannot start a sandbox here: {probe.stderr.strip()}"


Base = tuple[Path, list[str], list[str], list[str]]
BaseFactory = Callable[[frozenset[str]], Base]
Build = Callable[..., World]


@pytest.fixture(scope="module")
def bases(tmp_path_factory: pytest.TempPathFactory) -> BaseFactory:
    """Source repository and filter-repo replay, built once per kept-path set and copied by each case."""
    reason = _sandbox_unavailable()
    if reason:
        pytest.skip(reason)
    cache: dict[frozenset[str], Base] = {}

    def get(keep_extra: frozenset[str]) -> Base:
        if keep_extra not in cache:
            root = tmp_path_factory.mktemp("extraction-base")
            commits = build_source(root / "src")
            keep = {source for source, _dest in MANIFEST if source != "-"} | set(HISTORY_PATHS) | keep_extra
            lines, rewritten = replay(root / "src", commits, root / "extract", keep)
            cache[keep_extra] = (root, commits, lines, rewritten)
        return cache[keep_extra]

    return get


def make_world(
    tmp_path: Path,
    bases: BaseFactory,
    *,
    keep_extra: set[str] | None = None,
    edit: Callable[[Path], dict[str, str | None]] | None = None,
) -> World:
    kit = tmp_path / "kit"
    kit.mkdir()
    shutil.copy2(VERIFIER, kit / "verify_extraction.py")
    for tool in ("rename_python.py", "rename_nonpython.py", "rename_structured.py"):
        (kit / tool).write_text(STUB_RENAME, encoding="utf-8")
    (kit / "history_policy.py").write_text(STUB_HISTORY_POLICY, encoding="utf-8")
    (kit / "machinery_tests.txt").write_text(TESTS_LIST_STUB, encoding="utf-8")
    base, commits, lines, rewritten = bases(frozenset(keep_extra or ()))
    src = tmp_path / "src"
    extract = tmp_path / "extract"
    shutil.copytree(base / "src", src, symlinks=True)
    shutil.copytree(base / "extract", extract, symlinks=True)
    tip = rewritten[-1]
    changes = transform(extract)
    for path in keep_extra or set():
        if (extract / renamed(path)).exists():
            changes[renamed(path)] = None
    if edit is not None:
        write_files(extract, changes)
        changes = edit(extract)
    commit(extract, changes, "transformation")
    world = World(
        tmp=tmp_path,
        kit=kit,
        src=src,
        extract=extract,
        source=commits[-1],
        source_commits=commits,
        map_lines=lines,
        rewritten=rewritten,
        tip=tip,
        final_tree=git(extract, "rev-parse", "HEAD^{tree}"),
    )
    world.write_commit_map(lines)
    world.write_input("manifest.tsv", "".join(f"{s}\t{d}\n" for s, d in MANIFEST))
    world.write_input("history.txt", "".join(f"{p}\n" for p in HISTORY_PATHS))
    world.write_input("exclude.txt", "".join(f"{p}\n" for p in EXCLUDE))
    world.write_input("expectations.tsv", "".join("\t".join(row) + "\n" for row in EXPECTATIONS))
    world.write_input("ownership.json", json.dumps(OWNERSHIP))
    world.write_input("policy.tsv", "synthetic policy\n")
    return world


def findings(checks: dict[str, dict], name: str) -> str:
    return "\n".join(checks[name]["findings"])


@pytest.fixture
def build(tmp_path: Path, bases: BaseFactory) -> Build:
    def make(**kwargs: object) -> World:
        return make_world(tmp_path, bases, **kwargs)  # type: ignore[arg-type]

    return make


@pytest.fixture
def world(build: Build) -> World:
    return build()


def test_help_documents_inputs_checks_formats_and_exit_codes() -> None:
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), "--help"], capture_output=True, text=True, timeout=60, check=True
    )
    for needle in ("--tree-manifest", "--expectations", "--rewrite-tip", "--final-tree", "--history-policy"):
        assert needle in proc.stdout
    for needle in ("Examples:", "Input formats:", "Checks", "Exit codes:", "Outputs:", "Related:"):
        assert needle in proc.stdout
    for check in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "HP"):
        assert f"  {check} " in proc.stdout


def test_correct_extraction_passes_every_check_and_reports_denominators(world: World) -> None:
    head = git(world.extract, "rev-parse", "HEAD")
    names = world.write_input("names.txt", "json\n")
    code, checks, output = world.run(
        "--run-tests",
        "--external-names",
        str(names),
        "--history-policy",
        str(world.inputs["policy.tsv"]),
        "--policy-sha256",
        POLICY_SHA,
        env={"STUB_EXPECT_EXTERNAL_NAMES": str(names.resolve())},
    )
    assert code == 0, output
    assert {name: item["status"] for name, item in checks.items()} == dict.fromkeys(checks, "pass")
    assert checks["V1"]["inspected"] == {"manifest_rows": 5, "tree_paths": 5}
    assert checks["V2"]["inspected"]["exclude_entries"] == 3
    assert checks["V2"]["inspected"]["history_commits"] == 4
    assert checks["V3"]["inspected"] == {"python_modules": 4, "dispatch_help": 1}
    assert checks["V4"]["inspected"] == {"python_files": 4}
    assert checks["V5"]["inspected"]["expectation_rows"] == 5
    assert checks["V6"]["inspected"]["source_commits"] == 3
    assert checks["V8"]["inspected"]["tests_collected"] == 1
    assert checks["V8"]["inspected"]["tests_passed"] == 1
    assert checks["V9"]["inspected"]["commits_after_tip"] == 1
    # The history-policy tool receives exactly the agreed interface.
    hp_lines = [note for note in checks["HP"]["notes"] if note.startswith("HP-ARGV ")]
    hp_args = json.loads(hp_lines[0][len("HP-ARGV ") :])
    assert hp_args == [
        "verify",
        "--repo",
        str(world.extract),
        "--rev",
        world.tip,
        "--policy",
        str(world.inputs["policy.tsv"]),
        "--policy-sha256",
        POLICY_SHA,
        "--commit-map",
        str(world.inputs["commit-map"]),
        "--path-rename",
        "scripts/:lu_machinery/",
    ]
    # Read-only: the extraction is unchanged and still clean.
    assert git(world.extract, "rev-parse", "HEAD") == head
    assert git(world.extract, "status", "--porcelain", "--ignored", "--untracked-files=all") == ""


def test_v1_final_tree_defect_reports_missing_and_extra_paths(world: World) -> None:
    rows = [row for row in MANIFEST if row[1] != "agents_extensions/shared/rules/core.md"]
    rows.append(("scripts/lib/gone.py", "lu_machinery/lib/gone.py"))
    world.write_input("manifest.tsv", "".join(f"{s}\t{d}\n" for s, d in rows))
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V1")
    assert "missing from the final tree: lu_machinery/lib/gone.py" in text
    assert "extra in the final tree (not in the manifest): agents_extensions/shared/rules/core.md" in text


def test_v1_manifest_row_outside_the_rename_is_a_final_tree_defect(world: World) -> None:
    rows = [
        ("scripts/lib/util.py", "agents_extensions/util.py") if r[0] == "scripts/lib/util.py" else r for r in MANIFEST
    ]
    world.write_input("manifest.tsv", "".join(f"{s}\t{d}\n" for s, d in rows))
    code, checks, output = world.run()
    assert code == 1, output
    assert "is not the scripts/:lu_machinery/ rename of its source" in findings(checks, "V1")


def test_v2_exclusion_defect_in_history_before_and_after_rename(build: Build) -> None:
    world = build(keep_extra={"docs/runbooks/secret.md", "scripts/product_mod.py"})
    code, checks, output = world.run()
    assert code == 1, output
    assert checks["V1"]["status"] == "pass"
    text = findings(checks, "V2")
    assert "excluded docs/runbooks/secret.md is in the extracted history as docs/runbooks/secret.md" in text
    assert "excluded scripts/product_mod.py is in the extracted history as lu_machinery/product_mod.py" in text


def test_v2_exclusion_defect_history_only_path_in_final_tree(build: Build) -> None:
    def keep_legacy(extract: Path) -> dict[str, str | None]:
        return {"lu_machinery/lib/legacy.py": "OLD = 1\n"}

    world = build(edit=keep_legacy)
    code, checks, output = world.run()
    assert code == 1, output
    assert "history-only scripts/lib/legacy.py is in the final tree as lu_machinery/lib/legacy.py" in findings(
        checks, "V2"
    )


def test_v3_import_origin_defect_out_of_root_module_is_found(build: Build, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "outsider_mod.py").write_text("X = 1\n", encoding="utf-8")

    def reach_out(extract: Path) -> dict[str, str | None]:
        util = f"import sys\nsys.path.insert(0, {str(outside)!r})\nimport outsider_mod\n" + UTIL.replace(
            '"scripts.dispatch"', '"lu_machinery.dispatch"'
        )
        return {"lu_machinery/lib/util.py": util}

    world = build(edit=reach_out)
    code, checks, output = world.run()
    assert code == 1, output
    assert "outsider_mod from" in findings(checks, "V3")
    assert "outside the extracted root" in findings(checks, "V3")


def test_v3_import_origin_defect_failing_import_and_dispatch_help(build: Build) -> None:
    def break_util(extract: Path) -> dict[str, str | None]:
        return {"lu_machinery/lib/util.py": 'MODULE = "lu_machinery.dispatch"\nraise RuntimeError("boom")\n'}

    world = build(edit=break_util)
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V3")
    assert "lu_machinery/lib/util.py: import of lu_machinery.lib.util failed: RuntimeError: boom" in text
    assert "python -m lu_machinery.dispatch --help exited" in text
    # Every module was still inspected, so the denominator holds.
    assert checks["V3"]["inspected"]["python_modules"] == 4


def test_v4_product_import_defect_reports_file_and_line(build: Build) -> None:
    def leak(extract: Path) -> dict[str, str | None]:
        util = UTIL.replace('"scripts.dispatch"', '"lu_machinery.dispatch"') + (
            "\n\ndef later():\n"
            "    import product_mod\n"
            "    import scripts.lib.legacy\n"
            '    return "scripts.lib.util", "scripts/dispatch.py", "scripts/product_mod.py", "$ROOT/scripts/lib/"\n'
            "\n\ndef namespace_and_children():\n"
            "    import product_ns\n"
            "    from product_ns import child\n"
            "    from lib import product_child\n"
            "    from lib import util\n"
            '    return "scripts/"\n'
        )
        return {"lu_machinery/lib/util.py": util}

    world = build(edit=leak)
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V4")
    assert "lu_machinery/lib/util.py:6: import of product package product_mod" in text
    assert "lu_machinery/lib/util.py:7: import of scripts.lib.legacy" in text
    assert "lu_machinery/lib/util.py:8: string references module scripts.lib.util" in text
    assert "lu_machinery/lib/util.py:8: string holds machinery path scripts/dispatch.py" in text
    assert "lu_machinery/lib/util.py:8: string holds machinery path scripts/lib" in text
    assert "lu_machinery/lib/util.py:12: import of product package product_ns" in text  # namespace package
    assert "lu_machinery/lib/util.py:13: import of product package product_ns" in text
    assert "lu_machinery/lib/util.py:14: import of product package lib.product_child" in text  # product child
    assert "lu_machinery/lib/util.py:15:" not in text  # a machinery child of a machinery package
    assert "lu_machinery/lib/util.py:16: string holds machinery path scripts/ (the root" in text
    assert "scripts/product_mod.py" not in text  # a product path literal is allowed
    assert "lu_machinery/dispatch.py" not in text  # its docstring prose keeps scripts.dispatch


def test_v5_rename_defect_failed_expectation_rows(world: World) -> None:
    rows = [
        *EXPECTATIONS,
        ("module-strings", "lu_machinery/lib/util.py", "absent", "lu_machinery.dispatch"),
        ("resource-paths", "agents_extensions/shared/rules/core.md", "present", "lu_machinery/missing.py"),
        ("non-python", "agents_extensions/shared/rules/absent.md", "present", "x"),
    ]
    world.write_input("expectations.tsv", "".join("\t".join(row) + "\n" for row in rows))
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V5")
    assert "line 6 (module-strings lu_machinery/lib/util.py): forbidden literal" in text
    assert "line 7 (resource-paths agents_extensions/shared/rules/core.md): expected literal" in text
    assert "line 8 (non-python agents_extensions/shared/rules/absent.md): file is not in the final tree" in text


def test_v5_rename_defect_missing_class_is_unusable_input(world: World) -> None:
    rows = [row for row in EXPECTATIONS if row[0] != "non-python"]
    world.write_input("expectations.tsv", "".join("\t".join(row) + "\n" for row in rows))
    code, _checks, output = world.run()
    assert code == 2, output
    assert "no row for class(es): non-python" in output


def test_v5_rename_defect_pending_rewrite_breaks_idempotence(build: Build) -> None:
    def leave_token(extract: Path) -> dict[str, str | None]:
        core = (extract / "agents_extensions/shared/rules/core.md").read_text(encoding="utf-8")
        return {"agents_extensions/shared/rules/core.md": core + "Dry run: python -m scripts.dispatch --dry-run\n"}

    world = build(edit=leave_token)
    code, checks, output = world.run()
    assert code == 1, output
    assert "rename_nonpython.py --check would still rewrite agents_extensions/shared/rules/core.md" in findings(
        checks, "V5"
    )


def test_v5_rename_defect_absent_rename_tool_is_unusable_input(world: World) -> None:
    (world.kit / "rename_nonpython.py").unlink()
    code, _checks, output = world.run()
    assert code == 2, output
    assert "rename_nonpython.py is absent" in output


def test_v6_dispatch_history_defect_unmapped_and_pruned_commits(world: World) -> None:
    c1, c2, _c3, _c4 = world.source_commits
    lines = [line for line in world.map_lines if not line.startswith(c1)]
    lines = [f"{c2} {'0' * 40}" if line.startswith(c2) else line for line in lines]
    world.write_commit_map(lines)
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V6")
    assert f"source commit {c1} is not in the commit map" in text
    assert f"source commit {c2} was pruned by the rewrite" in text


def test_v6_dispatch_history_defect_mapping_outside_the_dispatch_history(world: World) -> None:
    _c1, _c2, _c3, c4 = world.source_commits
    lines = [line for line in world.map_lines if not line.startswith(c4)]
    world.write_commit_map([*lines, f"{c4} {'f' * 40}"])
    code, checks, output = world.run()
    assert code == 1, output
    assert f"source commit {c4} maps to {'f' * 40}, which is not in the lu_machinery/dispatch.py history" in findings(
        checks, "V6"
    )


def test_v7_denominator_defect_extra_python_file(build: Build) -> None:
    def extra(extract: Path) -> dict[str, str | None]:
        return {"lu_machinery/extra.py": "EXTRA = 1\n"}

    world = build(edit=extra)
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V7")
    assert "V4 inspected python_files=5, expected 4" in text
    assert "V1 inspected tree_paths=6, expected 5" in text
    assert "the transformation adds lu_machinery/extra.py, which is not a manifest addition row" in findings(
        checks, "V9"
    )


def test_v7_denominator_defect_zero_exclusions(world: World) -> None:
    world.write_input("exclude.txt", "")
    code, checks, output = world.run()
    assert code == 1, output
    assert "V2 inspected zero exclude_entries" in findings(checks, "V7")


def test_v8_harness_defect_failing_ported_test(build: Build) -> None:
    def change_value(extract: Path) -> dict[str, str | None]:
        return {"lu_machinery/lib/util.py": 'VALUE = 2\nMODULE = "lu_machinery.dispatch"\n'}

    world = build(edit=change_value)
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    assert checks["V8"]["inspected"]["tests_collected"] == 1
    assert checks["V8"]["inspected"]["tests_failed"] == 1
    assert "1 test(s) failed, 0 errored, 0 unexpectedly passed" in findings(checks, "V8")


def test_v8_harness_defect_zero_collected_tests(world: World) -> None:
    (world.kit / "machinery_tests.txt").write_text("# [run]\ntests/test_empty.py\n# [support]\n", encoding="utf-8")
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    assert "pytest collected zero tests" in findings(checks, "V8")
    assert "V8 inspected zero tests_collected" in findings(checks, "V7")


def test_v8_harness_defect_symlinked_test_directory_is_never_written_through(build: Build) -> None:
    def link_tests(extract: Path) -> dict[str, str | None]:
        (extract / "tests").symlink_to(extract.parent / "src" / "scripts")
        return {}

    world = build(edit=link_tests)
    before = sorted(path.name for path in (world.src / "scripts").iterdir())
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    assert "the extracted tree blocks the harness" in findings(checks, "V8")
    assert sorted(path.name for path in (world.src / "scripts").iterdir()) == before


def test_v8_harness_defect_deselected_tests_are_a_finding(world: World) -> None:
    (world.kit / "machinery_tests.txt").write_text(
        "# [run]\ntests/deselecting/test_two.py\n# [support]\ntests/deselecting/conftest.py\n", encoding="utf-8"
    )
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    assert "1 test(s) were deselected; every test of the listed files must run" in findings(checks, "V8")
    assert checks["V8"]["inspected"]["tests_deselected"] == 1


def test_v8_harness_defect_listed_file_absent_at_source_is_unusable(world: World) -> None:
    (world.kit / "machinery_tests.txt").write_text("# [run]\ntests/test_missing.py\n", encoding="utf-8")
    code, _checks, output = world.run("--run-tests")
    assert code == 2, output
    assert "tests/test_missing.py" in output


def test_v9_transformation_defect_insert_then_restore_across_two_commits(world: World) -> None:
    core_path = world.extract / "agents_extensions/shared/rules/core.md"
    approved = core_path.read_text(encoding="utf-8")
    commit(world.extract, {"agents_extensions/shared/rules/core.md": approved + "unapproved bytes\n"}, "insert")
    commit(world.extract, {"agents_extensions/shared/rules/core.md": approved}, "restore")
    assert git(world.extract, "rev-parse", "HEAD^{tree}") == world.final_tree  # the final tree cannot see it
    code, checks, output = world.run()
    assert code == 1, output
    assert checks["V1"]["status"] == "pass"
    text = findings(checks, "V9")
    assert "not the rewrite tip" in text
    assert "3 commits follow the rewrite tip; exactly one transformation commit is required" in text


def test_v9_transformation_defect_merge_and_foreign_parent(world: World) -> None:
    tree = world.final_tree
    transformation = git(world.extract, "rev-parse", "HEAD")
    merge = git(world.extract, "commit-tree", tree, "-p", world.tip, "-p", transformation, "-m", "merge")
    git(world.extract, "reset", "--quiet", "--hard", merge)
    code, checks, output = world.run()
    assert code == 1, output
    assert "has 2 parents; exactly one (the rewrite tip) is required" in findings(checks, "V9")

    foreign = git(world.extract, "commit-tree", tree, "-p", world.rewritten[0], "-m", "foreign parent")
    git(world.extract, "reset", "--quiet", "--hard", foreign)
    code, checks, output = world.run()
    assert code == 1, output
    assert f"HEAD's parent is {world.rewritten[0]}, not the rewrite tip {world.tip}" in findings(checks, "V9")


def test_v9_transformation_defect_tree_differs_from_frozen_tree(world: World) -> None:
    code, checks, output = world.run(**{"--final-tree": "0" * 40})
    assert code == 1, output
    assert "not the frozen --final-tree" in findings(checks, "V9")


def test_history_policy_findings_fail_and_unusable_policy_exits_2(world: World) -> None:
    extra = ("--history-policy", str(world.inputs["policy.tsv"]), "--policy-sha256", POLICY_SHA)
    (world.kit / "history_policy.exit").write_text("1", encoding="utf-8")
    code, checks, output = world.run(*extra)
    assert code == 1, output
    assert "history_policy.py verify reported findings (exit 1)" in findings(checks, "HP")
    (world.kit / "history_policy.exit").write_text("2", encoding="utf-8")
    code, _checks, output = world.run(*extra)
    assert code == 2, output
    (world.kit / "history_policy.py").unlink()
    code, _checks, output = world.run(*extra)
    assert code == 2, output
    assert "history_policy.py is absent" in output
    code, _checks, output = world.run("--history-policy", str(world.inputs["policy.tsv"]))
    assert code == 2, output


@pytest.mark.parametrize(
    "defect",
    [
        "missing-manifest",
        "dirty-tree",
        "ignored-file",
        "assume-unchanged",
        "skip-worktree",
        "bad-commit-map",
        "shallow-source",
    ],
)
def test_unusable_input_exits_2(world: World, defect: str) -> None:
    overrides: dict[str, str] = {}
    if defect == "missing-manifest":
        overrides["--tree-manifest"] = str(world.tmp / "absent.tsv")
    elif defect == "dirty-tree":
        (world.extract / "untracked.py").write_text("X = 1\n", encoding="utf-8")
    elif defect == "ignored-file":
        (world.extract / ".git" / "info" / "exclude").write_text("*.pyc\n", encoding="utf-8")
        (world.extract / "lu_machinery" / "stale.pyc").write_bytes(b"\0")
    elif defect in ("assume-unchanged", "skip-worktree"):
        # The index flag hides the edit from git status; the byte comparison must still see it.
        git(world.extract, "update-index", f"--{defect}", "lu_machinery/lib/util.py")
        (world.extract / "lu_machinery/lib/util.py").write_text("VALUE = 999\n", encoding="utf-8")
        assert git(world.extract, "status", "--porcelain") == ""
    elif defect == "bad-commit-map":
        world.write_input("commit-map", "not a map\n")
    else:
        shallow = world.tmp / "shallow"
        git(world.tmp, "clone", "--quiet", "--depth", "1", f"file://{world.src}", str(shallow))
        overrides["--source-repo"] = str(shallow)
    code, _checks, output = world.run(**overrides)
    assert code == 2, output
    assert "UNUSABLE INPUT" in output
    if defect in ("assume-unchanged", "skip-worktree"):
        assert "lu_machinery/lib/util.py: 100644" in output


@pytest.mark.parametrize("where", ["input-file", "source-repo", "extract-git-dir", "symlink"])
def test_read_only_report_cannot_alias_an_input(world: World, where: str) -> None:
    manifest = world.inputs["manifest.tsv"]
    before = manifest.read_bytes()
    if where == "input-file":
        report = manifest
    elif where == "source-repo":
        report = world.src / "report.json"
    elif where == "extract-git-dir":
        report = world.extract / ".git" / "report.json"
    else:
        report = world.tmp / "link.json"
        report.symlink_to(manifest)
    code, _checks, output = world.run(**{"--report": str(report)})
    assert code == 2, output
    assert "--report" in output
    assert manifest.read_bytes() == before
    assert not (world.src / "report.json").exists()
    assert not (world.extract / ".git" / "report.json").exists()


def test_read_only_imported_module_cannot_write_the_source_repository(build: Build) -> None:
    target_holder: dict[str, Path] = {}

    def write_source(extract: Path) -> dict[str, str | None]:
        target = extract.parent / "src" / "scripts" / "product_mod.py"
        target_holder["path"] = target
        util = f"open({str(target)!r}, 'w').write('overwritten')\n" + UTIL.replace(
            '"scripts.dispatch"', '"lu_machinery.dispatch"'
        )
        return {"lu_machinery/lib/util.py": util}

    world = build(edit=write_source)
    target = target_holder["path"]
    before = target.read_bytes()
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    assert target.read_bytes() == before  # the sandbox kept the source read-only
    assert "import of lu_machinery.lib.util failed: OSError" in findings(checks, "V3")
    assert git(world.src, "status", "--porcelain") == ""


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_extraction_under_test", VERIFIER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_machinery_tests_list_names_the_contract_files_and_existing_paths() -> None:
    run, support = _load_verifier().load_tests_list(TESTS_LIST)
    assert set(run) == CONTRACT_SECTION_4_TESTS
    assert not set(run) & set(support)
    missing = [path for path in run + support if not (REPO_ROOT / path).is_file()]
    assert missing == []
    assert "tests/conftest.py" in support
    product_prefixes = ("tests/build/", "tests/curriculum/", "tests/eval/", "tests/lexdata/")
    assert [path for path in run + support if path.startswith(product_prefixes)] == []
