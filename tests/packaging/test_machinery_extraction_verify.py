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
    "scripts/pkg/__init__.py": "product",
    "scripts/pkg/worker.py": "machinery",
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
            "tests/dropping/conftest.py": "def pytest_collection_modifyitems(config, items):\n    items[:] = items[:1]\n",
            "tests/dropping/test_two.py": "def test_first():\n    pass\n\n\ndef test_second():\n    assert False\n",
            "tests/skipping/test_skipped.py": "import pytest\n\n\n@pytest.mark.skip(reason='x')\ndef test_one():\n    assert False\n",
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
            "\n\ndef parents_relative_loaders(name):\n"
            "    import importlib\n"
            "    import pkg.worker\n"
            "    from pkg.worker import run\n"
            "    from ..product_mod import PRODUCT\n"
            "    from . import product_child\n"
            "    from . import util\n"
            '    importlib.import_module("product_ns.child")\n'
            '    return __import__(name="pkg.worker")\n'
            "\n\ndef loaders(name):\n"
            "    import importlib\n"
            '    importlib.import_module(".product_child", "lu_machinery.lib")\n'
            '    importlib.import_module(name=".product_child", package=__package__)\n'
            '    __import__("product_child", globals(), locals(), [], 1)\n'
            '    __import__("lib", fromlist=["product_child"])\n'
            "    from lu_machinery.lib import product_child\n"
            "    import lu_machinery.pkg.worker\n"
            '    importlib.import_module(".util", "lu_machinery.lib")\n'
            '    importlib.util.find_spec(".x", name)\n'
            '    __import__("x", None, None, [], name)\n'
            '    __import__("", globals(), locals(), ["product_child"], 1)\n'
            '    __import__(name="", fromlist=("product_child",), level=1)\n'
            '    __import__("scripts", fromlist=["dispatch"])\n'
            '    return "scripts." + "dispatch"\n'
        )
        return {"lu_machinery/lib/util.py": util}

    world = build(edit=leak)
    code, checks, output = world.run()
    assert code == 1, output
    text = findings(checks, "V4")
    allowed = "\n".join(checks["V4"]["listed"])
    assert "lu_machinery/lib/util.py:6: import of product_mod is a product package" in text
    assert "lu_machinery/lib/util.py:7: import of scripts.lib.legacy" in text
    # Amendment A1: a string naming an extracted machinery file is a missed rename; product, mixed and
    # unextracted names are listed, not failed.
    assert "lu_machinery/lib/util.py:8: string references machinery module scripts.lib.util (missed rename)" in text
    assert "lu_machinery/lib/util.py:8: string holds machinery path scripts/dispatch.py (missed rename)" in text
    assert "lu_machinery/lib/util.py:8: product path reference scripts/product_mod.py" in allowed
    assert "lu_machinery/lib/util.py:8: mixed path reference scripts/lib" in allowed
    assert "lu_machinery/lib/util.py:12: import of product_ns is a product package" in text  # namespace package
    assert "lu_machinery/lib/util.py:13: import of product_ns is a product package" in text
    assert "lu_machinery/lib/util.py:14: import of lib.product_child is a product package" in text  # product child
    assert "lu_machinery/lib/util.py:15:" not in text  # a machinery child of a machinery package
    assert "lu_machinery/lib/util.py:16: mixed path reference scripts/" in allowed  # the root holds product too
    # A machinery module under a product package still runs the product __init__.py first.
    parent = "initializes product package pkg (scripts/pkg/__init__.py)"
    assert f"lu_machinery/lib/util.py:21: import of pkg.worker {parent}" in text
    assert f"lu_machinery/lib/util.py:22: import of pkg.worker {parent}" in text
    absent = "names product code absent from the machinery tree"
    assert f"lu_machinery/lib/util.py:23: relative import of scripts.product_mod {absent}" in text
    assert f"lu_machinery/lib/util.py:24: relative import of scripts.lib.product_child {absent}" in text
    assert "lu_machinery/lib/util.py:25:" not in text  # a relative import of a machinery sibling
    notes = "\n".join(checks["V4"]["notes"])
    assert "lu_machinery/lib/util.py:15: lib.util" in notes  # unprefixed machinery import: a note, not a finding
    # An unprefixed loader target that names product code is an allowed reference under A1.
    assert "lu_machinery/lib/util.py:26: loader target product_ns.child is a product package" in allowed
    assert f"lu_machinery/lib/util.py:27: loader target pkg.worker {parent}" in allowed
    assert "lu_machinery/lib/util.py:26:" not in text
    # Loader calls resolve relative targets, levels, fromlists and lu_machinery-qualified names.
    child = "is a product package (scripts/lib/product_child)"
    inside = f"{absent} (scripts/lib/product_child.py)"
    assert f"lu_machinery/lib/util.py:32: relative import of scripts.lib.product_child {inside}" in text
    assert f"lu_machinery/lib/util.py:33: relative import of scripts.lib.product_child {inside}" in text
    assert f"lu_machinery/lib/util.py:34: relative import of scripts.lib.product_child {inside}" in text
    assert f"lu_machinery/lib/util.py:35: loader target lib.product_child {child}" in allowed
    assert f"lu_machinery/lib/util.py:36: import of lu_machinery.lib.product_child {inside}" in text
    # Invariant 1: lu_machinery.pkg has no extracted prefix (the synthetic manifest extracts neither
    # scripts/pkg/__init__.py nor scripts/pkg/worker.py), so the next component names product code. The
    # namespace exemption for an extracted directory is test_v4_unextracted_product_init_is_a_namespace_*.
    assert f"lu_machinery/lib/util.py:37: import of lu_machinery.pkg.worker {absent} (scripts/pkg/__init__.py)" in text
    assert "lu_machinery/lib/util.py:38:" not in text  # a machinery sibling through a loader
    assert "lu_machinery/lib/util.py:39: relative loader target '.x' cannot be resolved statically" in text
    assert "lu_machinery/lib/util.py:40: __import__ level is not a literal integer" in text
    # An empty name with a level imports the package, then its fromlist (positional and keyword spellings).
    assert f"lu_machinery/lib/util.py:41: relative import of scripts.lib.product_child {inside}" in text
    assert f"lu_machinery/lib/util.py:42: relative import of scripts.lib.product_child {inside}" in text
    # A name assembled from a target and its fromlist, and literals joined by +, are judged like literals.
    assert "lu_machinery/lib/util.py:43: loader target scripts.dispatch names machinery (missed rename)" in text
    assert "lu_machinery/lib/util.py:44: string references machinery module scripts.dispatch (missed rename)" in text
    assert "string holds machinery path scripts/product_mod.py" not in text  # a product path literal is allowed
    assert "lu_machinery/dispatch.py" not in text  # its docstring prose keeps scripts.dispatch


def _index(module):
    return module.OwnershipIndex(OWNERSHIP, {"lu_machinery", "agents_extensions"}, [s for s, _d in MANIFEST])


def test_v4_unextracted_product_init_is_a_namespace_inside_lu_machinery() -> None:
    """scripts/tools/__init__.py is product while scripts/tools/agent_watcher.py is machinery (real map)."""
    module = _load_verifier()
    ownership = {**OWNERSHIP, "scripts/tools/__init__.py": "product", "scripts/tools/agent_watcher.py": "machinery"}
    extracted = [*(s for s, _d in MANIFEST), "scripts/tools/agent_watcher.py"]
    index = module.OwnershipIndex(ownership, {"lu_machinery", "agents_extensions"}, extracted)
    inside = b"def later():\n    from lu_machinery.tools import agent_watcher\n    from . import agent_watcher\n"
    assert module.scan_python_source("lu_machinery/tools/x.py", inside, index) == []
    outside = b"def later():\n    from tools import agent_watcher\n"
    # Outside that namespace the unprefixed name resolves through scripts/, whose tools/__init__.py is product.
    assert module.scan_python_source("lu_machinery/tools/x.py", outside, index) == [
        "lu_machinery/tools/x.py:2: import of tools is a product package (scripts/tools)"
    ]


def test_v4_static_expressions_split_paths_and_anchored_loaders_are_judged() -> None:
    module = _load_verifier()
    source = (
        b"import importlib, os\n"
        b"def later(ROOT):\n"
        b'    a = "%s.%s" % ("scripts", "dispatch")\n'
        b'    b = ".".join(["scripts", "dispatch"])\n'
        b"    c = f\"scripts.{'dispatch'}\"\n"
        b'    d = ROOT / "scripts" / "dispatch.py"\n'
        b'    e = os.path.join(ROOT, "scripts", "product_mod.py")\n'
        b'    f = importlib.import_module(".child", "scripts.product_ns")\n'
        b'    g = importlib.import_module(".util", "scripts.lib")\n'
    )
    listed: list[str] = []
    found = module.scan_python_source("lu_machinery/x.py", source, _index(module), listed=listed)
    machinery = "string references machinery module scripts.dispatch (missed rename)"
    assert sorted(found) == [
        f"lu_machinery/x.py:3: {machinery}",
        f"lu_machinery/x.py:4: {machinery}",
        f"lu_machinery/x.py:5: {machinery}",
        "lu_machinery/x.py:6: string holds machinery path scripts/dispatch.py (missed rename)",
        "lu_machinery/x.py:9: loader target scripts.lib.util names machinery (missed rename)",
        # The package literal itself names the machinery package scripts.lib, which leaves the product.
        "lu_machinery/x.py:9: string references machinery module scripts.lib (missed rename)",
    ]
    assert "lu_machinery/x.py:7: product path reference scripts/product_mod.py" in listed
    assert "lu_machinery/x.py:8: product loader target scripts.product_ns.child" in listed


def test_v4_a1_import_statements_of_scripts_or_product_code_fail() -> None:
    module = _load_verifier()
    source = b"def later():\n    import product_mod\n    from scripts.build import verify_shippable\n"
    assert module.scan_python_source("lu_machinery/x.py", source, _index(module)) == [
        "lu_machinery/x.py:2: import of product_mod is a product package (scripts/product_mod)",
        "lu_machinery/x.py:3: import of scripts.build",
    ]


def test_v4_a1_references_to_extracted_machinery_files_fail_as_missed_renames() -> None:
    module = _load_verifier()
    source = b'TARGET = "scripts.dispatch"\nPATH = "scripts/lib/util.py"\n'
    assert module.scan_python_source("lu_machinery/x.py", source, _index(module)) == [
        "lu_machinery/x.py:1: string references machinery module scripts.dispatch (missed rename)",
        "lu_machinery/x.py:2: string holds machinery path scripts/lib/util.py (missed rename)",
    ]


def test_v4_a1_references_to_product_code_are_listed_not_failed() -> None:
    module = _load_verifier()
    source = (
        b"import subprocess, sys\n"
        b'subprocess.run([sys.executable, "-m", "scripts.product_mod"], check=True, timeout=60)\n'
        b'TEMPLATE = "scripts/product_mod.py"\n'
        b'UNKNOWN = "scripts.build.verify_shippable"\n'
    )
    listed: list[str] = []
    assert module.scan_python_source("lu_machinery/x.py", source, _index(module), listed=listed) == []
    assert sorted(listed) == [
        "lu_machinery/x.py:2: product module reference scripts.product_mod",
        "lu_machinery/x.py:3: product path reference scripts/product_mod.py",
        "lu_machinery/x.py:4: unknown module reference scripts.build.verify_shippable",
    ]


# --------------------------------------------------------------------------- V4 invariants, generative
#
# The oracles below restate the module docstring's invariants from the synthetic map and tree alone; they
# share no code with the verifier. Every case is one statement in one file of the lu_machinery namespace.

GEN_OWNERSHIP = {**OWNERSHIP, "scripts/tools/__init__.py": "product", "scripts/tools/agent_watcher.py": "machinery"}
GEN_EXTRACTED = [*(source for source, _dest in MANIFEST), "scripts/tools/agent_watcher.py"]
# Invariant 1 inputs, in scripts/-relative components: what exists in the final tree, and what the map lists.
GEN_FINAL_MODULES = {
    (): "package",  # the bare lu_machinery
    ("lib",): "package",
    ("lib", "util"): "file",
    ("dispatch",): "file",
    ("tools",): "package",  # a namespace directory: scripts/tools/__init__.py is product and not extracted
    ("tools", "agent_watcher"): "file",
}
GEN_MAPPED_MODULES = {
    ("product_mod",), ("lib", "product_child"), ("lib", "legacy"), ("product_ns",), ("product_ns", "child"),
    ("pkg",), ("pkg", "worker"), ("tools",), ("tools", "agent_watcher"), ("dispatch",), ("lib",), ("lib", "util"),
}  # fmt: skip
GEN_FINAL_PATHS = {
    (): "dir", ("lib",): "dir", ("lib", "__init__.py"): "file", ("lib", "util.py"): "file",
    ("dispatch.py",): "file", ("tools",): "dir", ("tools", "agent_watcher.py"): "file",
}  # fmt: skip
GEN_MAPPED_PATHS = {
    ("__init__.py",), ("product_mod.py",), ("lib", "product_child.py"), ("lib", "legacy.py"), ("product_ns",),
    ("product_ns", "child.py"), ("pkg",), ("pkg", "__init__.py"), ("pkg", "worker.py"), ("tools", "__init__.py"),
}  # fmt: skip
GEN_TARGETS = [
    (), ("CONST",), ("lib",), ("lib", "CONST"), ("lib", "util"), ("lib", "util", "VALUE"),
    ("lib", "util", "VALUE", "deep"), ("dispatch",), ("dispatch", "main"), ("tools",), ("tools", "CONST"),
    ("tools", "agent_watcher"), ("tools", "agent_watcher", "X"), ("product_mod",), ("product_mod", "VALUE"),
    ("product_mod", "VALUE", "deep"), ("lib", "product_child"), ("lib", "product_child", "X"), ("lib", "legacy"),
    ("lib", "legacy", "X"), ("product_ns",), ("product_ns", "child"), ("product_ns", "child", "X"), ("pkg",),
    ("pkg", "worker"), ("pkg", "worker", "run"),
]  # fmt: skip
GEN_PATH_TARGETS = [
    "", "lib", "lib/util.py", "dispatch.py", "tools", "tools/agent_watcher.py", "product_mod.py",
    "lib/product_child.py", "lib/legacy.py", "product_ns", "product_ns/child.py", "pkg/worker.py", "data/x.json",
]  # fmt: skip
GEN_FILES = {"lu_machinery/x.py": (), "lu_machinery/lib/y.py": ("lib",), "lu_machinery/tools/z.py": ("tools",)}
GEN_WRAPPERS = [
    "{}\n",
    "def later():\n    {}\n",
    "class Lazy:\n    def method(self):\n        try:\n            {}\n        except ImportError:\n            pass\n",
]
GEN_MAX_CASES = 1500
GEN_MAX_SECONDS = 30.0
GEN_MANIFEST_PATHS = [path for row in MANIFEST for path in row if path != "-"] + ["scripts/tools/agent_watcher.py"]


def _gen_index(module):
    tops = {"lu_machinery", "agents_extensions"}
    return module.OwnershipIndex(GEN_OWNERSHIP, tops, GEN_EXTRACTED, manifest_paths=GEN_MANIFEST_PATHS)


def oracle_name(parts: tuple[str, ...], kinds: dict, mapped: set, file_kind: str) -> bool:
    """Invariant 1: True when the name is a finding."""
    depth = max(depth for depth in range(len(parts) + 1) if parts[:depth] in kinds)
    if depth == len(parts) or kinds[parts[:depth]] == file_kind:
        return False
    return parts[: depth + 1] in mapped


def oracle_module(parts: tuple[str, ...]) -> bool:
    return oracle_name(parts, GEN_FINAL_MODULES, GEN_MAPPED_MODULES, "file")


def oracle_path(path: str) -> bool:
    parts = tuple(part for part in path.split("/") if part)
    return oracle_name(parts, GEN_FINAL_PATHS, GEN_MAPPED_PATHS, "file")


GEN_SCRIPTS_MODULES = {  # the map's modules and packages: True when the tree manifest extracts machinery there
    ("dispatch",): True, ("lib",): True, ("lib", "util"): True, ("tools", "agent_watcher"): True,
    ("lib", "legacy"): False, ("lib", "product_child"): False, ("product_mod",): False, ("pkg",): False,
    ("pkg", "worker"): False, ("tools",): False, ("product_ns",): False, ("product_ns", "child"): False,
}  # fmt: skip


def oracle_scripts_module(parts: tuple[str, ...]) -> bool:
    """A1 (b): scripts.<name> fails when its longest map prefix is extracted machinery (a package's
    __init__.py included: scripts.lib.CONST reads the extracted scripts/lib/__init__.py)."""
    for depth in range(len(parts), 0, -1):
        if parts[:depth] in GEN_SCRIPTS_MODULES:
            return GEN_SCRIPTS_MODULES[parts[:depth]]
    return False


def oracle_scripts_path(path: str) -> bool:
    """A1 (b): scripts/<path> fails when it names an extracted machinery file (lib/ and tools/ also hold product)."""
    return path in {"lib/util.py", "dispatch.py", "tools/agent_watcher.py", "lib/__init__.py"}


def oracle_composition_listed(known: str) -> bool:
    """Invariant 2: a known part holds scripts, lu_machinery, a manifest path or a component-wise prefix of one."""
    prefixes = set()
    for path in GEN_MANIFEST_PATHS + [p.replace("scripts/", "lu_machinery/", 1) for p in GEN_MANIFEST_PATHS]:
        parts = path.split("/")
        prefixes |= {tuple(parts[:depth]) for depth in range(1, len(parts) + 1)}
        if path.endswith(".py"):
            dotted = path[:-3].split("/")
            dotted = dotted[:-1] if dotted[-1] == "__init__" else dotted
            prefixes |= {tuple(dotted[:depth]) for depth in range(1, len(dotted) + 1)}
    words = [word for word in known.replace("/", " ").replace(".", " ").split() if word]
    if {"scripts", "lu_machinery"} & set(words):
        return True
    tails = [tuple(part for part in known.split("/") if part)]
    tails.append(tuple(part for part in known.split(".") if part))
    return any(tail[start:] in prefixes for tail in tails for start in range(len(tail)))


def _dotted(*parts: str) -> str:
    return ".".join(part for part in parts if part)


def _absolute_module_cases(parts: tuple[str, ...]) -> list[tuple[str, bool]]:
    """Every name form and loader for lu_machinery.<parts>, and literal compositions of the name."""
    name = _dotted("lu_machinery", *parts)
    tail = ".".join(parts)
    expected = oracle_module(parts)
    cases = [
        (f"value = importlib.import_module({name!r})", expected),
        (f"value = importlib.util.find_spec({name!r})", expected),
        (f"value = __import__({name!r})", expected),
        (f"value = pkgutil.resolve_name({name!r})", expected),
        (f"value = runpy.run_module({name!r})", expected),
        (f"value = subprocess.run([sys.executable, '-m', {name!r}], check=False)", expected),
    ]
    if parts:
        parent = _dotted("lu_machinery", *parts[:-1])
        cases += [
            (f"import {name}", expected),
            (f"from {parent} import {parts[-1]}", expected),
            (
                f"from {parent} import ({parts[-1]} as alias, other_name)",
                expected or oracle_module((*parts[:-1], "other_name")),
            ),
            (f"value = __import__({parent!r}, globals(), locals(), [{parts[-1]!r}], 0)", expected),
            (f"value = __import__({parent!r}, fromlist=({parts[-1]!r},))", expected),
            (f"value = importlib.import_module('lu_machinery.' + {tail!r})", expected),
            (f'value = f"lu_machinery.{{{tail!r}}}"', expected),
            (f"value = '.'.join(['lu_machinery', *{list(parts)!r}])", expected),
            (f"value = '%s.%s' % ('lu_machinery', {tail!r})", expected),
            (f"value = '{{}}.{{}}'.format('lu_machinery', {tail!r})", expected),
            (f"value = f\"{{'lu_machinery'}}.{{{tail!r}:s}}\"", expected),
            (f"value = str('lu_machinery').__add__('.' + {tail!r})", expected),
        ]
        if len(parts) > 1:  # pkgutil's module:attribute spelling imports only the module part
            module_part = _dotted("lu_machinery", *parts[:-1])
            cases.append(
                (f"value = pkgutil.resolve_name({module_part + ':' + parts[-1]!r})", oracle_module(parts[:-1]))
            )
    return cases


def _relative_module_cases(rel: str, package: tuple[str, ...], parts: tuple[str, ...]) -> list[tuple[str, str, bool]]:
    """Relative spellings of lu_machinery.<parts> from a file whose package is package, at every level up to
    the namespace root (lu_machinery/tools/z.py stops at level 1: its level 2 equals lu_machinery/lib/y.py's)."""
    cases = []
    top = 1 if package == ("tools",) else len(package) + 1
    for level in range(1, top + 1):
        base = package[: len(package) - (level - 1)]
        if parts[: len(base)] != base or len(parts) <= len(base):
            continue
        rest = parts[len(base) :]
        dots = "." * level
        anchor = _dotted("lu_machinery", *package)  # import_module climbs from the package it is given
        expected = oracle_module(parts)
        cases += [
            (rel, f"from {dots}{'.'.join(rest[:-1])} import {rest[-1]}", expected),
            (rel, f"from {dots}{'.'.join(rest)} import attribute", oracle_module((*parts, "attribute"))),
            (rel, f"value = importlib.import_module({dots + '.'.join(rest)!r}, __package__)", expected),
            (rel, f"value = importlib.import_module({dots + '.'.join(rest)!r}, {anchor!r})", expected),
            (rel, f"value = importlib.util.find_spec({dots + '.'.join(rest)!r}, package={anchor!r})", expected),
            (
                rel,
                f"value = __import__({'.'.join(rest[:-1])!r}, globals(), locals(), [{rest[-1]!r}], {level})",
                expected,
            ),
            (rel, f"value = __import__({'.'.join(rest)!r}, globals(), locals(), [], {level})", expected),
        ]
    return cases


def _scripts_module_cases(parts: tuple[str, ...]) -> list[tuple[str, bool]]:
    """A1 (b) through the same evaluator: scripts.<parts> as a literal, a loader target and compositions."""
    if not parts:
        return []
    name, tail = _dotted("scripts", *parts), ".".join(parts)
    expected = oracle_scripts_module(parts)
    return [
        (f"value = {name!r}", expected),
        (f"value = subprocess.run([sys.executable, '-m', {name!r}], check=False)", expected),
        (f"value = 'scripts.' + {tail!r}", expected),
        (f"value = f\"{{'scripts'}}.{{{tail!r}:s}}\"", expected),
        (f"value = '{{}}.{{}}'.format('scripts', {tail!r})", expected),
    ]


def _path_cases(root: str, path: str) -> list[tuple[str, bool]]:
    """Every path composition of root/path; an empty path is the root itself."""
    expected = oracle_path(path) if root == "lu_machinery" else oracle_scripts_path(path)
    full = f"{root}/{path}" if path else f"{root}/"
    cases = [(f"value = {full!r}", expected), (f"value = runpy.run_path({full!r})", expected)]
    if path:
        cases += [
            (f"value = Path({root!r}) / {path!r}", expected),
            (f"value = Path({root!r}) / Path({path!r})", expected),
            (f"value = Path(Path({root!r}), {path!r})", expected),
            (f"value = Path({root!r}, {path!r})", expected),
            (f"value = Path({root!r}).joinpath({path!r})", expected),
            (f"value = os.path.join({root!r}, {path!r})", expected),
            (f"value = {root + '/'!r} + {path!r}", expected),
            (f'value = f"{{{root!r}}}/{{{path!r}:s}}"', expected),
            (f"value = '/'.join([{root!r}, {path!r}])", expected),
            (f"value = ROOT / {root!r} / {path!r}", expected),  # an unknown leading root keeps the literal tail
        ]
    return cases


COMPOSITION_KNOWN = [
    "scripts", "scripts/", "scripts.", "a/scripts/", "lu_machinery", "lu_machinery/", "lu_machinery.lib.",
    "agents_extensions", "agents_extensions/shared", "x/scripts", "docs", "data/",
]  # fmt: skip
COMPOSITION_TEMPLATES = [
    "Path(name) / {k}", "Path({k}) / name", "Path(Path({k}), name)", "os.path.join(name, {k})",
    "os.path.join({k}, name)", "{k} + name", "name + {k}", "f'{{name}}{{{k}}}'", "f'{{{k}}}{{name}}'",
    "'%s%s' % ({k}, name)", "'{{}}{{}}'.format({k}, name)", "'/'.join([{k}, name])", "Path({k}).joinpath(name)",
]  # fmt: skip


def _generated_cases() -> list[tuple[str, str, str, bool]]:
    """(file, statement, kind, expected) where kind is exact (expected: a finding) or partial (expected: listed)."""
    cases: list[tuple[str, str, str, bool]] = []
    for parts in GEN_TARGETS:
        cases += [("lu_machinery/x.py", stmt, "exact", want) for stmt, want in _absolute_module_cases(parts)]
        cases += [("lu_machinery/lib/y.py", stmt, "exact", want) for stmt, want in _scripts_module_cases(parts)]
        for rel, package in GEN_FILES.items():
            cases += [(r, s, "exact", w) for r, s, w in _relative_module_cases(rel, package, parts)]
    for root in ("lu_machinery", "scripts"):
        for path in GEN_PATH_TARGETS:
            cases += [("lu_machinery/x.py", stmt, "exact", want) for stmt, want in _path_cases(root, path)]
    for known in COMPOSITION_KNOWN:
        for template in COMPOSITION_TEMPLATES:
            stmt = "value = " + template.format(k=repr(known))
            cases.append(("lu_machinery/x.py", stmt, "partial", oracle_composition_listed(known)))
    return cases


def test_v4_invariants_hold_for_every_generated_combination() -> None:
    """Class-first proof: every combination of name form, relative level, attribute suffix, loader, wrapper
    and literal composition obeys invariants 1 and 2 (module docstring), within the stated case and time bounds."""
    import time

    module = _load_verifier()
    index = _gen_index(module)
    cases = _generated_cases()
    assert 1000 <= len(cases) <= GEN_MAX_CASES, len(cases)
    started = time.monotonic()
    wrong: list[str] = []
    for number, (rel, statement, kind, expected) in enumerate(cases):
        wrapper = GEN_WRAPPERS[number % len(GEN_WRAPPERS)]
        indent = wrapper.split("{}")[0].rsplit("\n", 1)[-1]
        source = wrapper.format(statement.replace("\n", "\n" + indent))
        listed: list[str] = []
        found = module.scan_python_source(rel, source.encode(), index, listed=listed)
        if kind == "exact":
            ok = bool(found) == expected
        else:
            composed = [item for item in listed if ": composition with an unknown part " in item]
            ok = not found and bool(composed) == expected
        if not ok:
            wrong.append(f"{rel}: {statement!r} ({kind}, expected {expected}): {found} {listed}")
    elapsed = time.monotonic() - started
    assert wrong == [], f"{len(wrong)} of {len(cases)} cases break the invariant:\n" + "\n".join(wrong[:40])
    assert elapsed < GEN_MAX_SECONDS, elapsed


# Every V4 probe of review rounds 1-5, fixed: (file, source, expected findings substring or None, listed substring).
REVIEWER_PROBES = [
    # Round 1: namespace packages, imported children, the scripts/ root.
    (
        "lu_machinery/x.py",
        "def f():\n    from product_ns import child\n",
        "import of product_ns is a product package",
        None,
    ),
    ("lu_machinery/x.py", "def f():\n    import product_ns\n", "import of product_ns is a product package", None),
    (
        "lu_machinery/x.py",
        "def f():\n    from lib import product_child\n",
        "import of lib.product_child is a product",
        None,
    ),
    ("lu_machinery/x.py", 'ROOT = "scripts/"\n', None, "mixed path reference scripts/"),
    # Round 2: product parent packages.
    ("lu_machinery/x.py", "def f():\n    import pkg.worker\n", "initializes product package pkg", None),
    ("lu_machinery/x.py", "def f():\n    from pkg.worker import run\n", "initializes product package pkg", None),
    # Round 3: relative loader targets and lu_machinery-qualified names.
    (
        "lu_machinery/lib/y.py",
        'def f():\n    importlib.import_module(".product_child", "lu_machinery.lib")\n',
        "scripts.lib.product_child names product code",
        None,
    ),
    (
        "lu_machinery/lib/y.py",
        'def f():\n    importlib.import_module(name=".product_child", package="lu_machinery.lib")\n',
        "scripts.lib.product_child names product code",
        None,
    ),
    (
        "lu_machinery/lib/y.py",
        'def f():\n    __import__("product_child", globals(), locals(), [], 1)\n',
        "scripts.lib.product_child names product code",
        None,
    ),
    (
        "lu_machinery/lib/y.py",
        'def f():\n    __import__("lib", fromlist=["product_child"])\n',
        None,
        "loader target lib.product_child is a product package",
    ),
    (
        "lu_machinery/lib/y.py",
        "def f():\n    from lu_machinery.lib import product_child\n",
        "import of lu_machinery.lib.product_child names product code",
        None,
    ),
    # Round 4: empty relative names and assembled targets.
    (
        "lu_machinery/lib/y.py",
        'def f():\n    __import__("", globals(), locals(), ["product_child"], 1)\n',
        "scripts.lib.product_child names product code",
        None,
    ),
    (
        "lu_machinery/lib/y.py",
        'def f():\n    __import__(name="", fromlist=("product_child",), level=1)\n',
        "scripts.lib.product_child names product code",
        None,
    ),
    (
        "lu_machinery/x.py",
        'def f():\n    __import__("scripts", fromlist=["dispatch"])\n',
        "loader target scripts.dispatch names machinery (missed rename)",
        None,
    ),
    # Round 5: product modules behind an attribute suffix, and composed literals.
    (
        "lu_machinery/x.py",
        'def f():\n    pkgutil.resolve_name("lu_machinery.product_mod.VALUE")\n',
        "lu_machinery.product_mod.VALUE names product code absent from the machinery tree (scripts/product_mod.py)",
        None,
    ),
    (
        "lu_machinery/x.py",
        "def f():\n    import lu_machinery.product_mod.VALUE\n",
        "import of lu_machinery.product_mod.VALUE names product code",
        None,
    ),
    (
        "lu_machinery/x.py",
        'def f():\n    __import__("lu_machinery.product_mod.VALUE")\n',
        "lu_machinery.product_mod.VALUE names product code",
        None,
    ),
    (
        "lu_machinery/x.py",
        "def f():\n    from .product_mod.VALUE import anything\n",
        "relative import of scripts.product_mod.VALUE names product code",
        None,
    ),
    (
        "lu_machinery/x.py",
        'P = Path("scripts") / Path("dispatch.py")\n',
        "string holds machinery path scripts/dispatch.py (missed rename)",
        None,
    ),
    (
        "lu_machinery/x.py",
        'P = Path(Path("scripts"), "dispatch.py")\n',
        "string holds machinery path scripts/dispatch.py (missed rename)",
        None,
    ),
    (
        "lu_machinery/x.py",
        "P = f\"{'scripts'}.{'dispatch':s}\"\n",
        "string references machinery module scripts.dispatch (missed rename)",
        None,
    ),
    # Beyond the namespace root, a relative name cannot be resolved: a finding.
    (
        "lu_machinery/x.py",
        "def f():\n    from .. import anything\n",
        "relative import cannot be resolved statically",
        None,
    ),
]


@pytest.mark.parametrize(("rel", "source", "finding", "listing"), REVIEWER_PROBES)
def test_v4_invariants_hold_for_every_earlier_reviewer_probe(rel: str, source: str, finding, listing) -> None:
    module = _load_verifier()
    listed: list[str] = []
    found = module.scan_python_source(rel, source.encode(), _gen_index(module), listed=listed)
    if finding is None:
        assert found == []
    else:
        assert any(finding in item for item in found), found
    if listing is not None:
        assert any(listing in item for item in listed), listed


def test_v4_invariant_namespace_exemption_and_package_attributes_are_clean() -> None:
    """Invariant 1: a bare lu_machinery or an extracted namespace directory resolves to the package."""
    module = _load_verifier()
    source = (
        b"def later():\n"
        b"    from lu_machinery import CONST\n"  # defined in the added lu_machinery/__init__.py
        b"    import lu_machinery\n"
        b"    import lu_machinery.tools\n"  # scripts/tools/__init__.py is product and not extracted
        b"    from lu_machinery.tools import agent_watcher\n"
        b"    from lu_machinery.tools import CONST\n"
        b"    from lu_machinery.lib.util import VALUE\n"
        b'    importlib.import_module("lu_machinery.tools.agent_watcher")\n'
        b'    pkgutil.resolve_name("lu_machinery.lib.util.VALUE")\n'
    )
    listed: list[str] = []
    assert module.scan_python_source("lu_machinery/tools/z.py", source, _gen_index(module), listed=listed) == []
    assert listed == []


def test_v4_invariant_scope_variable_bound_values_are_unknown() -> None:
    """Constant propagation is out of scope: a variable is an unknown part; only a qualifying known part lists."""
    module = _load_verifier()
    source = b'x = "scripts"\nP = Path(x) / "dispatch.py"\nQ = Path(x) / "scripts" / name\n'
    listed: list[str] = []
    assert module.scan_python_source("lu_machinery/x.py", source, _gen_index(module), listed=listed) == []
    assert listed == ["lu_machinery/x.py:3: composition with an unknown part '<?>/scripts/<?>'"]


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
    assert (
        "line 8 (non-python agents_extensions/shared/rules/absent.md): no regular file at this path in the final tree"
        in text
    )


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


@pytest.mark.parametrize("case", ["dropping-hook", "collect-only", "all-skipped"])
def test_v8_harness_defect_tests_that_never_execute_are_a_finding(build: Build, case: str) -> None:
    def collect_only(extract: Path) -> dict[str, str | None]:
        return {"pytest.ini": "[pytest]\naddopts = --collect-only\n"}

    world = build(edit=collect_only) if case == "collect-only" else build()
    run = {
        "dropping-hook": "# [run]\ntests/dropping/test_two.py\n# [support]\ntests/dropping/conftest.py\n",
        "collect-only": TESTS_LIST_STUB,
        "all-skipped": "# [run]\ntests/skipping/test_skipped.py\n",
    }[case]
    (world.kit / "machinery_tests.txt").write_text(run, encoding="utf-8")
    code, checks, output = world.run("--run-tests")
    assert code == 1, output
    text = findings(checks, "V8")
    if case == "all-skipped":
        assert "tests/skipping/test_skipped.py: no test of this listed file passed" in text
    else:
        assert "collected test(s) never ran (deselected, dropped or collect-only)" in text
        assert checks["V8"]["inspected"]["tests_not_run"] >= 1


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


@pytest.mark.parametrize(
    "where",
    ["input-file", "hardlink", "source-repo", "extract-git-dir", "symlink", "alternate", "indirect-alternate"],
)
def test_read_only_report_cannot_alias_an_input(world: World, where: str) -> None:
    manifest = world.inputs["manifest.tsv"]
    before = manifest.read_bytes()
    if where in ("alternate", "indirect-alternate"):
        # Relative alternates resolve against the object store that names them, as git does.
        for name in ("shared.git", "shared2.git"):
            git(world.tmp, "init", "--quiet", "--bare", str(world.tmp / name))
        (world.extract / ".git/objects/info/alternates").write_text("../../../shared.git/objects\n")
        (world.tmp / "shared.git/objects/info/alternates").write_text("../../shared2.git/objects\n")
    if where == "input-file":
        report = manifest
    elif where == "hardlink":
        report = world.tmp / "hard.json"
        os.link(manifest, report)
    elif where == "alternate":
        report = world.tmp / "shared.git/objects/report.json"
    elif where == "indirect-alternate":
        report = world.tmp / "shared2.git/objects/report.json"
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
    assert not (world.tmp / "shared2.git/objects/report.json").exists()


@pytest.mark.parametrize("pointer", ["gitdir", "commondir", "alternate"])
def test_read_only_git_pointer_spellings_git_reads_differently_are_refused(tmp_path: Path, pointer: str) -> None:
    """Git keeps a trailing blank in a pointer path; protecting the stripped path would miss it."""
    module = _load_verifier()
    repo = tmp_path / "repo"
    git_dir = tmp_path / "private "
    (git_dir / "objects" / "info").mkdir(parents=True)
    repo.mkdir()
    if pointer == "gitdir":
        (repo / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
    elif pointer == "commondir":
        (repo / ".git").mkdir()
        (repo / ".git" / "commondir").write_text(f"{git_dir}\n", encoding="utf-8")
    else:
        (repo / ".git" / "objects" / "info").mkdir(parents=True)
        (repo / ".git" / "objects" / "info" / "alternates").write_text(f"{git_dir}\n", encoding="utf-8")
    with pytest.raises(module.Unusable, match=f"unsupported {pointer} spelling"):
        module.repo_storage(repo)


@pytest.mark.parametrize("pointer", ["gitdir", "commondir", "alternates"])
def test_read_only_symlinked_git_pointer_files_are_protected(tmp_path: Path, pointer: str) -> None:
    """A pointer file reached through a symlink is repository storage; its target joins the protected set."""
    module = _load_verifier()
    repo = tmp_path / "repo"
    git_dir = tmp_path / "private.git"
    (git_dir / "objects" / "info").mkdir(parents=True)
    (tmp_path / "shared" / "objects").mkdir(parents=True)
    external = tmp_path / "elsewhere" / "pointer"
    external.parent.mkdir()
    repo.mkdir()
    if pointer == "gitdir":
        external.write_text(f"gitdir: {git_dir}\n", encoding="utf-8")
        (repo / ".git").symlink_to(external)
    elif pointer == "commondir":
        (repo / ".git" / "objects").mkdir(parents=True)
        external.write_text(f"{git_dir}\n", encoding="utf-8")
        (repo / ".git" / "commondir").symlink_to(external)
    else:
        (repo / ".git" / "objects" / "info").mkdir(parents=True)
        external.write_text(f"{tmp_path / 'shared' / 'objects'}\n", encoding="utf-8")
        (repo / ".git" / "objects" / "info" / "alternates").symlink_to(external)
    assert external.resolve() in module.repo_storage(repo)


def test_read_only_symlink_targets_inside_git_storage_are_protected(world: World) -> None:
    config = world.extract / ".git" / "config"
    external = world.tmp / "external-config"
    external.write_bytes(config.read_bytes())
    config.unlink()
    config.symlink_to(external)
    before = external.read_bytes()
    code, _checks, output = world.run(**{"--report": str(external)})
    assert code == 2, output
    assert "--report" in output and "read-only" in output
    assert external.read_bytes() == before


def test_read_only_alternates_are_protected_and_cross_checked_with_git(world: World) -> None:
    git(world.tmp, "init", "--quiet", "--bare", str(world.tmp / "shared.git"))
    (world.extract / ".git/objects/info/alternates").write_text("../../../shared.git/objects\n")
    code, _checks, output = world.run()
    assert code == 0, output  # git's own git dir, common dir and alternate list are all protected
    (world.extract / ".git/objects/info/alternates").write_text("../../../shared.git/objects \n")
    code, _checks, output = world.run()
    assert code == 2, output
    assert "unsupported alternate spelling" in output


def test_read_only_report_overwrites_only_its_own_earlier_report(world: World) -> None:
    own = world.tmp / "own-report.json"
    code, _checks, output = world.run(**{"--report": str(own)})
    assert code == 0, output
    code, _checks, output = world.run(**{"--report": str(own)})  # a rerun replaces its own report
    assert code == 0, output
    other = world.tmp / "someone-elses.cfg"
    other.write_text("[include]\n\tpath = x\n", encoding="utf-8")
    code, _checks, output = world.run(**{"--report": str(other)})
    assert code == 2, output
    assert "is not an earlier verify_extraction report" in output
    assert other.read_text(encoding="utf-8") == "[include]\n\tpath = x\n"


def test_read_only_report_staging_never_follows_a_planted_link(tmp_path: Path, monkeypatch) -> None:
    module = _load_verifier()
    victim = tmp_path / "input.tsv"
    victim.write_text("frozen\n", encoding="utf-8")
    monkeypatch.setattr(module.secrets, "token_hex", lambda _size: "fixed")
    (tmp_path / ".report.json.fixed.tmp").symlink_to(victim)
    with pytest.raises(FileExistsError):
        module.write_report(tmp_path / "report.json", {"verdict": "pass"})
    assert victim.read_text(encoding="utf-8") == "frozen\n"
    assert not (tmp_path / "report.json").exists()


def test_read_only_scratch_never_lands_inside_the_source_repository(world: World) -> None:
    inside = world.src / "tmpdir"
    inside.mkdir()
    code, _checks, output = world.run(env={"TMPDIR": str(inside)})
    assert code == 2, output
    assert "set TMPDIR elsewhere" in output
    assert list(inside.iterdir()) == []


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
