"""Tests for checkout_write_guard helper and regression tests."""

from __future__ import annotations

import importlib
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.build.linear_pipeline import ensure_claude_writer_agent_deployed
from scripts.wiki.extract_sections import extract_sections
from tests.helpers import checkout_write_guard
from tests.helpers.checkout_write_defaults import WriteDefaults
from tests.helpers.checkout_write_guard import (
    PROJECT_ROOT,
    CheckoutWriteError,
    CheckoutWriteGuard,
)
from tests.helpers.restore_import_state import restore_import_state

# Explicit paths keep the behavioral contract independent of the guard policy.
WATCHED_PATHS = [
    f"{root}/{child}"
    for root in (".claude", ".codex", ".agent", ".gemini")
    for child in (
        "agents/test.md", "skills/test/SKILL.md", "rules/test.md", "hooks/test.sh",
        "settings.json",
    )
] + [
    f"{root}/{child}"
    for root in (".claude", ".codex")
    for child in (
        "commands/test.md", "prompts/test.md", "memory/test.md", "contracts/test.json",
        "docs/test.md", "quick-ref/test.md", "statusline/test.sh",
        "session_streams/test.py", "schemas/test.json", "NON-NEGOTIABLE-RULES.md",
        "skills/test/runtime-epic/SKILL.md", "docs/settings.local.json",
    )
] + [
    ".agent/settings.local.json", ".gemini/settings.local.json",
    ".agents/skills/test/SKILL.md",
    ".agents/skills/test/references/test.md",
    ".claude/skills/drive-epic/SKILL.md",
    ".codex/config.toml", ".codex/hooks.json", "data/corpus_audit/report.md",
    "data/corpus_audit/nested/report.md",
    "data/embeddings/manifest.db",
    "data/embeddings/ukrainian_wiki/shard-000001.npy",
]

LIVE_RUNTIME_PATHS = [
    ".agent/sessions/test.json", ".agent/runtime/test.json",
    ".agent/thread-rollovers/test.json", ".claude/infra-epic/briefs/test.md",
    ".codex/infra-epic/briefs/test.md",
    ".claude/settings.local.json", ".codex/settings.local.json",
    ".claude/worktrees/test/state.json", ".codex/worktrees/test/state.json",
    ".claude/scheduled_tasks.lock", ".codex/retired-skills/test/SKILL.md",
    "data/telemetry/test.json", "data/lexicon/cache/test.json",
    "data/x.db", "data/x.db-wal", "data/x.db-shm", "data/sub/cache.json",
    "data/telemetry-other/report.md", "data/lexicon/cache-other/report.md",
    "data/corpus_audit-other/report.md",
    "data/embeddings-other/manifest.db",
]


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, capture_output=True, check=True, timeout=30)


def _source_alias(filename: str, name: str):
    source = PROJECT_ROOT / "scripts" / ("build" if filename == "linear_pipeline.py" else "wiki") / filename
    spec = importlib.util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Match the two corpus tests: the second collection load replaces the first
# sys.modules entry while both test modules retain their own module objects.
_COLLECTION_BUILDERS = tuple(_source_alias("build_sources_db.py", "guard_collection_builder") for _ in range(2))


@pytest.mark.parametrize("builder", _COLLECTION_BUILDERS, ids=["replaced-alias", "current-alias"])
def test_collection_file_alias_report_default(tmp_path: Path, builder) -> None:
    assert tmp_path / "corpus_audit/section_extraction_report.md" == builder.DEFAULT_REPORT_PATH
    assert tmp_path / "embeddings/manifest.db" == builder.DEFAULT_MANIFEST_DB


@pytest.mark.parametrize("filename", ["linear_pipeline.py", "extract_sections.py", "build_sources_db.py"])
def test_late_file_alias_defaults(tmp_path: Path, filename: str, monkeypatch: pytest.MonkeyPatch) -> None:
    name = "guard_late_alias"
    with restore_import_state(name):
        monkeypatch.delitem(sys.modules, name, raising=False)
        module = _source_alias(filename, name)
        if filename == "linear_pipeline.py":
            expected = tmp_path / ".claude/agents/curriculum-writer.md"
            assert expected == module.CLAUDE_WRITER_AGENT_TARGET
            assert module.ensure_claude_writer_agent_deployed()["path"] == str(expected)
            assert expected.read_bytes() == module.CLAUDE_WRITER_AGENT_SOURCE.read_bytes()
        else:
            expected = tmp_path / "corpus_audit/section_extraction_report.md"
            assert expected == module.DEFAULT_REPORT_PATH
            db = tmp_path / "sections.db"
            with sqlite3.connect(db) as conn:
                conn.execute("""CREATE TABLE textbooks (
                    id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT,
                    source_file TEXT, grade TEXT, author TEXT, author_uk TEXT, char_count INTEGER
                )""")
            if filename == "extract_sections.py":
                report = module.extract_sections(db)
            else:
                report = module._extract_sections_with_university_grade_adapter(db)
                manifest = tmp_path / "embeddings/manifest.db"
                assert manifest == module.DEFAULT_MANIFEST_DB
                module.ensure_ukrainian_wiki_manifest(module.DEFAULT_MANIFEST_DB)
                assert manifest.is_file()
                assert (manifest.parent / "ukrainian_wiki/shard-000001.npy").is_file()
            assert report.total_chunks == 0
            assert "Status: **OK**" in expected.read_text(encoding="utf-8")


def test_default_redirect_matches_exact_file_and_restores_alias(tmp_path: Path) -> None:
    defaults = WriteDefaults()
    module = _COLLECTION_BUILDERS[0]
    original = module.DEFAULT_REPORT_PATH
    original_manifest = module.DEFAULT_MANIFEST_DB
    defaults.loaded(module)
    with pytest.MonkeyPatch.context() as patches:
        defaults.patches = patches
        defaults.tmp_path = tmp_path / "inner"
        defaults.loaded(module)
        assert tmp_path / "inner/corpus_audit/section_extraction_report.md" == module.DEFAULT_REPORT_PATH
        assert tmp_path / "inner/embeddings/manifest.db" == module.DEFAULT_MANIFEST_DB
        unrelated = SimpleNamespace(
            __file__=str(tmp_path / "build_sources_db.py"), DEFAULT_REPORT_PATH=original,
            DEFAULT_MANIFEST_DB=original_manifest,
        )
        defaults.loaded(unrelated)
        assert original == unrelated.DEFAULT_REPORT_PATH
        assert original_manifest == unrelated.DEFAULT_MANIFEST_DB
        defaults.loaded(SimpleNamespace())
    assert original == module.DEFAULT_REPORT_PATH
    assert original_manifest == module.DEFAULT_MANIFEST_DB


@pytest.mark.parametrize("name", ["scripts.build.linear_pipeline", "build.linear_pipeline"])
def test_shared_writer_default_deploys_outside_checkout(tmp_path: Path, name: str) -> None:
    module = importlib.import_module(name)
    deploy = ensure_claude_writer_agent_deployed if name.startswith("scripts.") else module.ensure_claude_writer_agent_deployed
    result = deploy()
    target = tmp_path / ".claude" / "agents" / "curriculum-writer.md"
    assert result["path"] == str(target)
    assert target.read_bytes() == module.CLAUDE_WRITER_AGENT_SOURCE.read_bytes()
    assert deploy()["changed"] is False


@pytest.mark.parametrize("prefix", ["scripts.wiki", "wiki"])
@pytest.mark.parametrize("via_builder", [False, True], ids=["direct-default", "builder-global"])
def test_shared_section_report_default_writes_outside_checkout(
    tmp_path: Path, prefix: str, via_builder: bool,
) -> None:
    db = tmp_path / "sections.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT,
            source_file TEXT, grade TEXT, author TEXT, author_uk TEXT, char_count INTEGER
        )""")
    if via_builder:
        builder = importlib.import_module(f"{prefix}.build_sources_db")
        report = builder._extract_sections_with_university_grade_adapter(db)
    else:
        extractor = importlib.import_module(f"{prefix}.extract_sections")
        # The qualified alias was imported during collection, before fixtures.
        extract = extract_sections if prefix.startswith("scripts.") else extractor.extract_sections
        report = extract(db)
    output = tmp_path / "corpus_audit" / "section_extraction_report.md"
    assert output.is_file()
    assert "Status: **OK**" in output.read_text(encoding="utf-8")
    assert report.total_chunks == 0


@pytest.mark.parametrize("rel", [
    ".claude/agents/curriculum-writer.md",
    "data/corpus_audit/section_extraction_report.md",
])
@pytest.mark.parametrize("change", ["create", "rewrite", "same-content", "delete", "unchanged"])
def test_protocol_attributes_only_current_test_changes(
    tmp_path: Path, rel: str, change: str,
) -> None:
    output = tmp_path / rel
    output.parent.mkdir(parents=True)
    if change != "create":
        output.write_text("before", encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    item = SimpleNamespace(config=SimpleNamespace(_checkout_write_guard=guard), nodeid="sample.py::test_writer")
    protocol = checkout_write_guard.pytest_runtest_protocol(item, None)
    next(protocol)
    if change == "delete":
        output.unlink()
    elif change != "unchanged":
        previous_mtime = output.stat().st_mtime_ns if output.exists() else 0
        output.write_text("before" if change == "same-content" else "after", encoding="utf-8")
        os.utime(output, ns=(previous_mtime + 1, previous_mtime + 1))
    with pytest.raises(StopIteration):
        next(protocol)
    if change == "unchanged":
        assert guard._test_violations == []
    else:
        action = {
            "create": "created", "rewrite": "modified/appended",
            "same-content": "modified/appended", "delete": "deleted",
        }[change]
        assert guard._test_violations == [
            f"guarded checkout file {action}: {rel} (test: sample.py::test_writer)",
        ]
    # A later unchanged test must not inherit attribution from the first one.
    item.nodeid = "sample.py::test_reader"
    protocol = checkout_write_guard.pytest_runtest_protocol(item, None)
    next(protocol)
    with pytest.raises(StopIteration):
        next(protocol)
    assert not any("test_reader" in violation for violation in guard._test_violations)


def test_protocol_without_session_guard() -> None:
    protocol = checkout_write_guard.pytest_runtest_protocol(SimpleNamespace(config=SimpleNamespace()), None)
    next(protocol)
    with pytest.raises(StopIteration):
        next(protocol)


def test_worker_attribution_handles_crashed_or_unguarded_nodes(tmp_path: Path) -> None:
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    config = SimpleNamespace(_checkout_write_guard=guard)
    checkout_write_guard.pytest_testnodedown(SimpleNamespace(config=config), "worker crashed")
    checkout_write_guard.pytest_testnodedown(SimpleNamespace(config=SimpleNamespace()), None)
    assert guard._test_violations == []
    violation = "guarded checkout file created: sample (test: sample.py::test_writer)"
    checkout_write_guard.pytest_testnodedown(
        SimpleNamespace(config=config, workeroutput={"checkout_write_violations": [violation]}), None,
    )
    assert guard._test_violations == [violation]


def test_protocol_stats_only_two_known_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    item = SimpleNamespace(config=SimpleNamespace(_checkout_write_guard=guard), nodeid="sample.py::test_reader")
    inspected = []
    original_stat = Path.stat

    def recording_stat(path, *args, **kwargs):
        inspected.append(path.relative_to(tmp_path).as_posix())
        return original_stat(path, *args, **kwargs)

    def forbid_io(*args, **kwargs):
        raise AssertionError("per-test attribution must not read, scan, or invoke Git")

    monkeypatch.setattr(Path, "stat", recording_stat)
    monkeypatch.setattr(Path, "read_bytes", forbid_io)
    monkeypatch.setattr(os, "walk", forbid_io)
    monkeypatch.setattr(subprocess, "run", forbid_io)
    protocol = checkout_write_guard.pytest_runtest_protocol(item, None)
    next(protocol)
    with pytest.raises(StopIteration):
        next(protocol)
    assert inspected == [
        ".claude/agents/curriculum-writer.md", "data/corpus_audit/section_extraction_report.md",
    ] * 2


@pytest.mark.parametrize("workers", [0, 2], ids=["serial", "xdist"])
def test_protocol_names_setup_call_and_teardown_writers(tmp_path: Path, workers: int) -> None:
    """Exercise the real pytest hook order without writing to this checkout."""
    sample = tmp_path / "test_sample.py"
    sample.write_text('''import pytest
import checkout_write_guard as plugin

@pytest.fixture
def writer(request):
    phase, rel = request.param
    output = plugin.PROJECT_ROOT / rel
    output.parent.mkdir(parents=True, exist_ok=True)
    if phase == "setup":
        output.write_text(phase)
    yield phase, output
    if phase == "teardown":
        output.write_text(phase)

@pytest.mark.parametrize("writer", [
    (phase, rel)
    for rel in (".claude/agents/curriculum-writer.md", "data/corpus_audit/section_extraction_report.md")
    for phase in ("setup", "call", "teardown")
], indirect=True)
def test_writes(writer):
    phase, output = writer
    if phase == "call":
        output.write_text(phase)
''', encoding="utf-8")
    plugin = (PROJECT_ROOT / "tests/helpers/checkout_write_guard.py").read_text(encoding="utf-8")
    (tmp_path / "checkout_write_guard.py").write_text(
        plugin.replace("Path(__file__).resolve().parents[2]", "Path(__file__).resolve().parent"),
        encoding="utf-8",
    )
    # Separate worker roots prevent concurrent writers from being observed by
    # another worker's stat snapshots; the controller still receives all six.
    (tmp_path / "conftest.py").write_text(
        'import checkout_write_guard as plugin\n'
        'pytest_plugins = ["checkout_write_guard"]\n'
        'def pytest_configure(config):\n'
        '    if hasattr(config, "workerinput"):\n'
        '        plugin.PROJECT_ROOT /= config.workerinput["workerid"]\n'
        '        plugin.PROJECT_ROOT.mkdir()\n', encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(sample),
         *(["-n", str(workers), "--dist=worksteal"] if workers else [])], cwd=tmp_path,
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "6 passed" in result.stdout
    attributed = [line for line in result.stdout.splitlines() if "(test:" in line]
    assert len(attributed) == 6, result.stdout
    for index in range(6):
        assert any(f"test_sample.py::test_writes[writer{index}]" in line for line in attributed)


def test_guard_detects_tracked_file_edit_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("initial content\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    tracked.write_text("modified content\n", encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "tracked file modified: tracked.txt" in str(exc_info.value)


def test_guard_detects_request_log_creation_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "add gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    log_file = tmp_path / "logs" / "mcp-sources-requests.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text('{"tool": "test"}\n', encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact created: logs/mcp-sources-requests.jsonl" in str(exc_info.value)


def test_guard_detects_request_log_append_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    log_file = tmp_path / "logs" / "mcp-sources-requests.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text('{"tool": "test1"}\n', encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write('{"tool": "test2"}\n')

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact modified/appended: logs/mcp-sources-requests.jsonl" in str(exc_info.value)


def test_guard_detects_manifest_creation_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("site/src/data/lexicon-manifest.json\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    manifest = tmp_path / "site" / "src" / "data" / "lexicon-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text('{"entries": []}\n', encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact created: site/src/data/lexicon-manifest.json" in str(exc_info.value)


def test_guard_accepts_unchanged_run_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    dummy = tmp_path / "file.txt"
    dummy.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    with CheckoutWriteGuard(repo_root=tmp_path) as guard:
        # Writing to exempt cache directory must not trigger guard
        cache_file = tmp_path / ".pytest_cache" / "cache.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{}", encoding="utf-8")

    assert guard.check() == []


@pytest.mark.parametrize("rel", [".coverage", ".coverage.worker.12345.67890"])
@pytest.mark.parametrize("change", ["create", "rewrite", "delete"])
def test_guard_accepts_untracked_coverage_data(tmp_path: Path, rel: str, change: str) -> None:
    _init_git_repo(tmp_path)
    output = tmp_path / rel
    if change != "create":
        output.write_bytes(b"baseline coverage")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "delete":
        output.unlink()
    else:
        output.write_bytes(b"updated coverage")
    assert guard.check() == []
    guard.verify()


@pytest.mark.parametrize("rel", [".coverage", ".coverage.worker.12345.67890"])
def test_guard_still_detects_tracked_coverage_changes(tmp_path: Path, rel: str) -> None:
    _init_git_repo(tmp_path)
    output = tmp_path / rel
    output.write_bytes(b"baseline coverage")
    subprocess.run(["git", "add", rel], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "tracked coverage"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    output.write_bytes(b"updated coverage")
    with pytest.raises(CheckoutWriteError, match="tracked file modified"):
        guard.verify()


@pytest.mark.parametrize("rel", [
    "new_source.py", ".coveragerc", ".coverage-report.py",
    ".coverage.worker/new_source.py", "nested/.coverage",
])
def test_guard_still_detects_unrelated_untracked_files(tmp_path: Path, rel: str) -> None:
    _init_git_repo(tmp_path)
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    output = tmp_path / rel
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("unexpected checkout write", encoding="utf-8")
    assert guard.check() == [f"untracked checkout file created: {rel}"]
    with pytest.raises(CheckoutWriteError, match="untracked checkout file created"):
        guard.verify()


def test_guard_accounts_for_preexisting_changes_and_sparse_files(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    dirty = tmp_path / "dirty.txt"
    dirty.write_text("v1\n", encoding="utf-8")
    sparse_tracked = tmp_path / "sparse.txt"
    sparse_tracked.write_text("sparse\n", encoding="utf-8")
    subprocess.run(["git", "add", "dirty.txt", "sparse.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    # Simulate dirty state before guard starts
    dirty.write_text("v2-uncommitted\n", encoding="utf-8")
    # Simulate sparse checkout: tracked file is missing from working tree
    sparse_tracked.unlink()

    with CheckoutWriteGuard(repo_root=tmp_path) as guard:
        pass

    assert guard.check() == []


@pytest.mark.parametrize("malformed", [False, True], ids=["missing", "malformed"])
def test_sparse_store_is_loaded_only_by_dependent_tests(tmp_path: Path, malformed: bool) -> None:
    """Exercise the actual lazy reader, rather than a copied skip implementation."""
    store = tmp_path / "_words.yaml"
    if malformed:
        store.write_text("invalid: yaml: [unclosed\n", encoding="utf-8")
    sample = tmp_path / "test_store.py"
    sample.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(PROJECT_ROOT)!r})\n"
        "from pathlib import Path\n"
        "from tests.build import test_fresh_a1_choice_checks as choices\n"
        f"choices.A1_STORE = Path({str(store)!r})\n"
        "def test_independent():\n"
        "    assert choices._record(1, 'sample', [])['id'] == 'W-1'\n"
        "def test_store():\n"
        "    choices._store_record('W-061')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", str(sample)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert "collected 2 items" in result.stdout, result.stdout + result.stderr
    if malformed:
        assert result.returncode == 1, result.stdout + result.stderr
        assert "1 failed, 1 passed" in result.stdout
        assert "ScannerError" in result.stdout or "ParserError" in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "1 passed, 1 skipped" in result.stdout
        assert "Missing repository-relative prerequisite: curriculum/l2-uk-en/evidence/a1/_words.yaml" in result.stdout


@pytest.mark.parametrize("workers", [0, 2], ids=["serial", "xdist"])
@pytest.mark.parametrize(
    "write_path",
    [
        None,
        "logs/mcp-sources-requests.jsonl",
        ".claude/agents/curriculum-writer.md",
        ".claude/commands/test.md",
        ".codex/agents/test.toml",
        ".codex/memory/test.md",
        ".agent/skills/test.md",
        ".agents/skills/test/SKILL.md",
        ".gemini/agents/test.md",
        "data/corpus_audit/section_extraction_report.md",
        "data/embeddings/manifest.db",
        "data/embeddings/ukrainian_wiki/shard-000001.npy",
        "data/tracked.txt",
        "external-tmp",
        *LIVE_RUNTIME_PATHS,
    ],
)
def test_registered_guard_enforces_normal_pytest_session(
    tmp_path: Path, write_path: str | None, workers: int,
) -> None:
    """No -p: temporary conftest registration must fail a passing writer test."""
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n.claude/\n.codex/\n.agent/\n.agents/\n.gemini/\ndata/\n", encoding="utf-8")
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "existing.jsonl").write_text('{}\n', encoding="utf-8")
    plugin = (PROJECT_ROOT / "tests/helpers/checkout_write_guard.py").read_text(encoding="utf-8")
    (tmp_path / "checkout_write_guard.py").write_text(
        plugin.replace("Path(__file__).resolve().parents[2]", "Path(__file__).resolve().parent"),
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text('pytest_plugins = ["checkout_write_guard"]\n', encoding="utf-8")
    # A session must start cleanly even when the named output directory is absent.
    assert not (tmp_path / "data/embeddings").exists()
    if write_path in LIVE_RUNTIME_PATHS or write_path == "data/tracked.txt":
        existing = tmp_path / write_path
        existing.parent.mkdir(parents=True, exist_ok=True)
        existing.write_text("baseline", encoding="utf-8")
    if write_path == "data/tracked.txt":
        subprocess.run(["git", "add", "-f", write_path], cwd=tmp_path, capture_output=True, check=True, timeout=30)
        subprocess.run(["git", "commit", "-m", "tracked data"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    if write_path == "external-tmp":
        sample = "def test_sample(tmp_path):\n    (tmp_path / 'unrelated.txt').write_text('sample')\n"
    elif write_path is None:
        sample = "def test_sample():\n    assert True\n"
    else:
        sample = (
            "from pathlib import Path\n"
            "def test_sample():\n"
            f"    output = Path({write_path!r})\n"
            "    output.parent.mkdir(parents=True, exist_ok=True)\n"
            "    output.write_text('sample')\n"
        )
        if Path(write_path).name not in ("settings.local.json", "scheduled_tasks.lock"):
            sample += "    output.with_name('new-' + output.name).write_text('new')\n"
    (tmp_path / "test_sample.py").write_text(sample, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_sample.py", *(["-n", str(workers)] if workers else [])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert "1 passed" in result.stdout, result.stdout + result.stderr
    if write_path not in (None, "external-tmp", *LIVE_RUNTIME_PATHS):
        assert result.returncode == 1, result.stdout + result.stderr
        assert "ERROR: checkout mutations detected by checkout_write_guard" in result.stdout
        label = "artifact" if write_path.startswith("logs/") else "file"
        change = "modified/appended" if write_path == "data/tracked.txt" else "created"
        assert f"guarded checkout {label} {change}: {write_path}" in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "checkout mutations detected" not in result.stdout


@pytest.mark.parametrize("rel", WATCHED_PATHS)
@pytest.mark.parametrize("change", ["unchanged", "create", "rewrite", "append", "delete"])
def test_guard_baselines_ignored_deploy_and_data_files(tmp_path: Path, rel: str, change: str) -> None:
    _init_git_repo(tmp_path)
    root = Path(rel).parts[0]
    (tmp_path / ".gitignore").write_text(f"{root}/\n", encoding="utf-8")
    output = tmp_path / rel
    output.parent.mkdir(parents=True)
    if change != "create":
        output.write_text("before", encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "create":
        output.write_text("new", encoding="utf-8")
        expected = f"guarded checkout file created: {rel}"
    elif change == "delete":
        output.unlink()
        expected = f"guarded checkout file deleted: {rel}"
    elif change in ("rewrite", "append"):
        before_stat = output.stat()
        output.write_text("after!" if change == "rewrite" else "before appended", encoding="utf-8")
        # Deterministic mtime evidence even for a same-size rewrite on fast filesystems.
        os.utime(output, ns=(before_stat.st_atime_ns, before_stat.st_mtime_ns + 1_000_000_000))
        expected = f"guarded checkout file modified/appended: {rel}"
    else:
        assert guard.check() == []
        guard.verify()
        return
    assert guard.check() == [expected]
    with pytest.raises(CheckoutWriteError, match="guarded checkout file"):
        guard.verify()


@pytest.mark.parametrize("ignored", [False, True], ids=["unignored", "ignored"])
@pytest.mark.parametrize("rel", LIVE_RUNTIME_PATHS)
@pytest.mark.parametrize("change", ["create", "rewrite", "delete"])
def test_guard_accepts_untracked_runtime_changes(
    tmp_path: Path, ignored: bool, rel: str, change: str,
) -> None:
    """Real Git status must not turn permitted service state into a violation."""
    _init_git_repo(tmp_path)
    if ignored:
        (tmp_path / ".gitignore").write_text(f"{Path(rel).parts[0]}/\n", encoding="utf-8")
    output = tmp_path / rel
    output.parent.mkdir(parents=True)
    if change != "create":
        output.write_text("baseline", encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "delete":
        output.unlink()
    else:
        output.write_text("service changed this file", encoding="utf-8")
    assert guard.check() == []
    guard.verify()


@pytest.mark.parametrize("dirty", [False, True], ids=["clean", "preexisting-change"])
@pytest.mark.parametrize("rel", [
    "data/tracked.txt", "data/x.db", "data/telemetry/report.json",
    "data/lexicon/cache/report.json", "data/corpus_audit-other/report.md",
    "data/sub/tracked file\nwith newline.json",
])
@pytest.mark.parametrize("change", ["unchanged", "rewrite", "delete"])
def test_guard_watches_every_tracked_data_file(
    tmp_path: Path, dirty: bool, rel: str, change: str,
) -> None:
    _init_git_repo(tmp_path)
    output = tmp_path / rel
    output.parent.mkdir(parents=True)
    output.write_text("tracked baseline", encoding="utf-8")
    subprocess.run(["git", "add", "--", rel], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "tracked data"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    if dirty:
        output.write_text("preexisting change", encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "unchanged":
        assert guard.check() == []
        return
    if change == "delete":
        output.unlink()
        expected = f"guarded checkout file deleted: {rel}"
    else:
        output.write_text("test changed tracked data", encoding="utf-8")
        expected = f"guarded checkout file modified/appended: {rel}"
    assert expected in guard.check()
    with pytest.raises(CheckoutWriteError):
        guard.verify()


def test_guard_accounts_for_sparse_tracked_data(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    output = tmp_path / "data/tracked.txt"
    output.parent.mkdir()
    output.write_text("tracked", encoding="utf-8")
    subprocess.run(["git", "add", "data"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    output.unlink()
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    assert guard.check() == []
    output.write_text("materialized during test", encoding="utf-8")
    assert "guarded checkout file created: data/tracked.txt" in guard.check()


@pytest.mark.parametrize("phase", ["start", "finish"])
@pytest.mark.parametrize("root", ["data/corpus_audit", "logs"])
@pytest.mark.parametrize("vanished", ["file", "directory"])
def test_session_hooks_skip_vanished_files_and_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str, root: str, vanished: str,
) -> None:
    """Inject real deletion after listing; both hooks must keep walking siblings."""
    monkeypatch.setattr(checkout_write_guard, "PROJECT_ROOT", tmp_path)
    output = []
    session = SimpleNamespace(
        config=SimpleNamespace(pluginmanager=SimpleNamespace(
            get_plugin=lambda _name: SimpleNamespace(write_line=output.append),
        )),
        exitstatus=0,
    )
    survivor = tmp_path / root / "survivor.txt"
    survivor.parent.mkdir(parents=True)
    survivor.write_text("kept", encoding="utf-8")
    if phase == "finish":
        checkout_write_guard.pytest_sessionstart(session)
    directory = tmp_path / root / "vanishing"
    directory.mkdir(parents=True)
    victim = directory / "victim.txt"
    victim.write_text("gone", encoding="utf-8")
    deleted = []
    original_stat = Path.stat
    original_scandir = os.scandir

    def racing_stat(path: Path, *args, **kwargs):
        if path == victim and not deleted:
            victim.unlink()
            deleted.append(victim)
        return original_stat(path, *args, **kwargs)

    def racing_scandir(path):
        if not isinstance(path, int) and Path(path) == directory and not deleted:
            shutil.rmtree(directory)
            deleted.append(directory)
        return original_scandir(path)

    monkeypatch.setattr(Path, "stat", racing_stat if vanished == "file" else original_stat)
    monkeypatch.setattr(os, "scandir", racing_scandir if vanished == "directory" else original_scandir)
    if phase == "start":
        checkout_write_guard.pytest_sessionstart(session)
    else:
        checkout_write_guard.pytest_sessionfinish(session, 0)
        assert session.exitstatus == 0
        assert output == []
    guard = session.config._checkout_write_guard
    assert guard.check() == []
    assert deleted
    assert not victim.exists()
    # Skipping a vanished entry must not lose the surviving sibling's baseline.
    survivor.write_text("changed sibling", encoding="utf-8")
    assert any(f"{root}/survivor.txt" in violation for violation in guard.check())


def test_guard_prunes_runtime_directories_before_scanning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    excluded = set()
    for rel in LIVE_RUNTIME_PATHS:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("live", encoding="utf-8")
        if path.parent != tmp_path / Path(rel).parts[0]:
            excluded.add(path.parent)
    original_scandir = os.scandir

    def forbid_runtime_scan(path):
        if not isinstance(path, int):
            assert Path(path) not in excluded, f"traversed live runtime directory: {path}"
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", forbid_runtime_scan)
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    assert guard.check() == []


def test_guard_does_not_suppress_other_walk_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def inaccessible_scandir(path):
        raise PermissionError("denied")

    monkeypatch.setattr(os, "scandir", inaccessible_scandir)
    with pytest.raises(PermissionError, match="denied"):
        CheckoutWriteGuard(repo_root=tmp_path)


def test_guard_snapshots_watched_trees_without_hashing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "data/corpus_audit/report.md"
    output.parent.mkdir(parents=True)
    output.write_text("report", encoding="utf-8")

    def forbid_content_read(_path: Path) -> bytes:
        raise AssertionError("watched trees must not be hashed")

    monkeypatch.setattr(Path, "read_bytes", forbid_content_read)
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    assert guard.check() == []


@pytest.mark.parametrize("change", ["unchanged", "append", "new"], ids=["unchanged-log", "append-log", "new-log"])
def test_guard_baselines_preexisting_ignored_logs(tmp_path: Path, change: str) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    logs = tmp_path / "logs/nested"
    logs.mkdir(parents=True)
    existing = logs / "existing.jsonl"
    existing.write_text('{}\n', encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "append":
        with existing.open("a", encoding="utf-8") as stream:
            stream.write('{}\n')
        assert guard.check() == ["pre-existing checkout log modified/appended: logs/nested/existing.jsonl"]
    elif change == "new":
        (logs / "new.jsonl").write_text('{}\n', encoding="utf-8")
        assert guard.check() == ["unexpected file created in checkout logs/: logs/nested/new.jsonl"]
    else:
        assert guard.check() == []


def test_guard_active_during_fresh_build_and_sources_samples() -> None:
    """Verify CheckoutWriteGuard and its pytest plugin run cleanly against rep tests."""
    with CheckoutWriteGuard() as guard:
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--trace-config",
                "tests/build/test_fresh_runner.py",
                "tests/test_mcp_sources_server.py",
                "-k",
                "test_runner_real_draft_report_has_numeric_single_lesson_totals or test_unknown_tool_returns_error",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        assert res.returncode == 0, f"pytest failed:\n{res.stdout}\n{res.stderr}"
        assert "2 passed" in res.stdout
        assert "module 'tests.helpers.checkout_write_guard'" in res.stdout
    assert guard.check() == []
