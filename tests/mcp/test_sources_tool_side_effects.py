"""A sources tool's readOnlyHint matches the writes it attempts (#9551).

``sources_side_effects_probe.py`` calls every tool in a fresh interpreter with a
fake network and scratch stores, refusing and recording each persistent write.
Reviewers are granted exactly the tools annotated read-only, so an annotation
that hides a write would hand a reviewer a writer. The scratch stores hold
``sources_probe_fixture`` rows, so each read-only lookup finds its row and a
write after a successful lookup is audited, not skipped by an early error.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import mcp  # noqa: F401  # Declares the Sources wire dependency to the CI fastlane.
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).with_name("sources_side_effects_probe.py")
SERVER_PATH = PROJECT_ROOT / ".mcp" / "servers" / "sources" / "server.py"

sys.path.insert(0, str(PROBE.parent))
try:
    import sources_side_effects_probe as probe
finally:
    sys.path.remove(str(PROBE.parent))


def _run_probe(scratch: Path, *extra: str) -> dict[str, dict]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, str(PROBE), "--scratch", str(scratch), "--hermetic", *extra],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=600,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-4000:]
    results = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return {result["tool"]: result for result in results}


def _annotation_mismatches(results: dict[str, dict]) -> dict[str, list[str]]:
    """Tools whose observed writes disagree with their readOnlyHint: the audit's verdict."""
    writers = {name for name, result in results.items() if result["writes"]}
    annotated = {name for name, result in results.items() if result["read_only_hint"] is not True}
    return {name: results[name]["writes"] for name in writers ^ annotated}


@pytest.fixture(scope="module")
def probe_results(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict]:
    return _run_probe(tmp_path_factory.mktemp("sources-side-effects"))


def test_probe_covers_every_listed_tool(probe_results: dict[str, dict]) -> None:
    spec = importlib.util.spec_from_file_location("sources_server_side_effects_list", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    listed = sorted(tool.name for tool in asyncio.run(server.list_tools()))
    assert sorted(probe_results) == listed


def test_read_only_annotation_equals_observed_writes(probe_results: dict[str, dict]) -> None:
    """Every tool that attempts a persistent write is annotated not read-only, and every such annotation is earned."""
    assert _annotation_mismatches(probe_results) == {}


def test_every_read_only_lookup_succeeds(probe_results: dict[str, dict]) -> None:
    """Each audited read-only call found its fixture row, so its success path ran under the audit."""
    read_only = {name for name, result in probe_results.items() if result["read_only_hint"] is True}
    assert set(probe.HERMETIC_HITS) == read_only
    failed = {
        name: probe_results[name]["result_head"]
        for name in sorted(read_only)
        if probe_results[name]["is_error"] or probe_results[name]["hit"] is not True
    }
    assert failed == {}


def test_hermetic_run_reads_only_its_scratch_stores(probe_results: dict[str, dict]) -> None:
    """No tool reached a host database, so the outcome is the same on a machine without data/."""
    assert {name: result["escapes"] for name, result in probe_results.items() if result["escapes"]} == {}


def test_a_write_after_a_successful_lookup_fails_the_audit(tmp_path: Path) -> None:
    """Mutation test: read-only tools made to store a row after a successful lookup are reported as writers.

    The injected write happens only once the lookup has returned its fixture row, so a
    recorded write here is a write on the success path.
    """
    injected = ("get_full_text", "search_text", "verify_words")
    args = [arg for name in injected for arg in ("--tool", name, "--inject-writer", name)]
    results = _run_probe(tmp_path, *args)
    assert sorted(results) == sorted(injected)
    for name in injected:
        assert any("on sources.db" in write for write in results[name]["writes"]), results[name]
    assert sorted(_annotation_mismatches(results)) == sorted(injected)


def test_wikipedia_and_dictua_cache_writes_are_detected(probe_results: dict[str, dict]) -> None:
    """Positive controls: the probe sees the writes the review found, so a clean result means something."""
    assert any("wiki_cache.db" in write for write in probe_results["query_wikipedia"]["writes"])
    for name in ("query_ulif", "query_ulif_synonyms", "query_ulif_antonyms", "query_ulif_phraseology"):
        assert any(write.startswith("sqlite-write") for write in probe_results[name]["writes"]), name
    # The cache_only-free records lookup reads the same table without storing.
    assert probe_results["query_ulif_records"]["writes"] == []


def test_probe_refuses_writes_outside_the_request_log(tmp_path: Path) -> None:
    """The probe's own guard: a refused write leaves nothing behind."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    effects = probe.SideEffects([log_dir])
    with pytest.raises(PermissionError):
        effects.audit("open", (str(tmp_path / "stray.txt"), "w", os.O_WRONLY | os.O_CREAT))
    with pytest.raises(PermissionError):
        effects.audit("os.mkdir", (str(tmp_path / "new-dir"), 0o777, -1))
    effects.audit("open", (str(log_dir / "mcp-sources-requests.jsonl"), "a", os.O_WRONLY | os.O_APPEND))
    effects.audit("open", (str(tmp_path / "read.txt"), "r", os.O_RDONLY))
    assert effects.current == [
        f"open-for-write {tmp_path / 'stray.txt'}",
        f"mkdir {tmp_path / 'new-dir'}",
    ]
    database = tmp_path / "store.db"
    connect = effects.guard_connect(__import__("sqlite3").connect)
    conn = connect(str(database))
    try:
        with pytest.raises(Exception, match="not authorized"):
            conn.execute("CREATE TABLE t (id INTEGER)")
        assert conn.execute("SELECT 1").fetchone() == (1,)
    finally:
        conn.close()
    assert effects.current[-1].startswith("sqlite-write")
