"""Tests for per-lesson evidence lock generator, checker, and diff engine (issue #8413, Brief C)."""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.curriculum.evidence import lesson_lock, lock, pack, sources, words

pytestmark = pytest.mark.reads_content

PYTHON = sys.executable
REPO_ROOT = Path(__file__).resolve().parents[3]


def make_record(word_id: str, lemma: str, forms: list[str]) -> dict:
    return {
        "id": word_id,
        "lemma": lemma,
        "pos": "noun",
        "forms": [{"form": f, "tags": f"noun:inanim:m:tag_{i}"} for i, f in enumerate(forms)],
    }


# ---------------------------------------------------------------------------
# Deliverable 1: Record-grain hashing tests
# ---------------------------------------------------------------------------


def test_record_hash_stability_under_key_reordering():
    """Mapping-key reordering produces identical bytes and hash."""
    rec1 = {
        "id": "T-001",
        "quote": "some quote text",
        "source": {"table": "textbooks", "chunk_id": "c1", "page": 10},
        "supports": "First point",
    }
    rec2 = {
        "supports": "First point",
        "source": {"page": 10, "chunk_id": "c1", "table": "textbooks"},
        "id": "T-001",
        "quote": "some quote text",
    }
    assert pack.record_bytes(rec1) == pack.record_bytes(rec2)
    h1 = pack.record_hash({"texts": [rec1]}, "T-001")
    h2 = pack.record_hash({"texts": [rec2]}, "T-001")
    assert h1 == h2

    # Words mapping key reordering
    w1 = make_record("W-001", "слово", ["слово", "слова"])
    w2 = {
        "forms": [{"tags": "noun:inanim:m:tag_0", "form": "слово"}, {"tags": "noun:inanim:m:tag_1", "form": "слова"}],
        "lemma": "слово",
        "id": "W-001",
        "pos": "noun",
    }
    assert words.record_bytes(w1) == words.record_bytes(w2)
    assert words.record_hash({"words": [w1]}, "W-001") == words.record_hash({"words": [w2]}, "W-001")


def test_record_hash_changes_on_forms_reordering():
    """Reordering the forms list DOES change the hash (VESUM order preserved)."""
    w1 = make_record("W-001", "слово", ["слово", "слова"])
    w2 = make_record("W-001", "слово", ["слова", "слово"])
    assert words.record_bytes(w1) != words.record_bytes(w2)
    h1 = words.record_hash({"words": [w1]}, "W-001")
    h2 = words.record_hash({"words": [w2]}, "W-001")
    assert h1 != h2


def test_record_hash_changes_on_one_character_edit():
    """One character edit in a record changes the hash."""
    rec1 = {"id": "T-001", "quote": "hello world"}
    rec2 = {"id": "T-001", "quote": "hello world!"}
    assert pack.record_hash({"texts": [rec1]}, "T-001") != pack.record_hash({"texts": [rec2]}, "T-001")

    w1 = make_record("W-001", "слово", ["слово"])
    w2 = make_record("W-001", "слово", ["слове"])
    assert words.record_hash({"words": [w1]}, "W-001") != words.record_hash({"words": [w2]}, "W-001")


def test_record_hashes_batch_and_missing_id():
    """record_hashes returns dict of id->sha256; missing id raises KeyError."""
    pack_data = {
        "texts": [{"id": "T-001", "quote": "a"}, {"id": "T-002", "quote": "b"}],
        "examples": [{"id": "EX-001", "text": "ex"}],
    }
    hashes = pack.record_hashes(pack_data, ["T-001", "EX-001"])
    assert "T-001" in hashes and "EX-001" in hashes
    assert "T-002" not in hashes

    with pytest.raises(KeyError, match="Record id 'T-999' not found"):
        pack.record_hashes(pack_data, ["T-999"])

    word_data = {"words": [make_record("W-001", "a", ["a"])]}
    w_hashes = words.record_hashes(word_data)
    assert "W-001" in w_hashes
    with pytest.raises(KeyError, match="Word record id 'W-999' not found"):
        words.record_hashes(word_data, ["W-999"])


# ---------------------------------------------------------------------------
# Fixture helpers for lesson-lock tests
# ---------------------------------------------------------------------------


def setup_curriculum_fixture(root: Path, level: str = "a1", slug: str = "mod-one"):
    """Create a minimal valid curriculum tree with 3 lessons."""
    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_dir = root / f"curriculum/l2-uk-en/evidence/{level}"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    plan_doc = {
        "plan_schema": 2,
        "module": slug,
        "level": level,
        "sequence": 1,
        "slug": slug,
        "title": "Module One",
        "lessons": [
            {
                "n": 1,
                "slug": "lesson-1",
                "kind": "teach",
                "inventory": {
                    "grammar": [{"id": "G-001", "evidence": ["T-001"]}],
                    "vocabulary": {
                        "core": [{"lemma": "word-one", "evidence": "W-001", "forms": ["f1"]}],
                        "incidental": [],
                        "recycled": [],
                    },
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "evidence": ["T-001"],
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-001"]},
                    }
                ],
            },
            {
                "n": 2,
                "slug": "lesson-2",
                "kind": "teach",
                "inventory": {
                    "grammar": [],
                    "vocabulary": {
                        "core": [{"lemma": "word-two", "evidence": "W-002", "forms": ["f2"]}],
                        "incidental": [],
                        "recycled": [],
                    },
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "evidence": ["T-002"],
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-002"]},
                    }
                ],
            },
            {
                "n": 3,
                "slug": "lesson-3",
                "kind": "recap",
                "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
                "steps": [
                    {
                        "id": "s1",
                        "kind": "practice",
                        "evidence": ["T-003"],
                    }
                ],
            },
        ],
    }

    pack_doc = {
        "evidence_schema": 1,
        "module": f"{level}/{slug}",
        "built_with": {
            "mcp_commit": "1" * 40,
            "sources_db": "2" * 64,
            "vesum": "3" * 64,
            "trie": "4" * 64,
            "ulif_forms": "pending",
            "standard_sha256": "5" * 64,
        },
        "texts": [
            {"id": "T-001", "quote": "Quote one"},
            {"id": "T-002", "quote": "Quote two"},
            {"id": "T-003", "quote": "Quote three"},
            {"id": "T-999", "quote": "Uncited quote"},
        ],
        "standard": [{"id": "S-001", "lines": "1-5", "text": "standard text", "file_sha256": "5" * 64}],
    }

    words_doc = {
        "evidence_schema": 1,
        "level": level,
        "built_with": {"mcp_commit": "1" * 40},
        "words": [
            make_record("W-001", "word-one", ["f1"]),
            make_record("W-002", "word-two", ["f2"]),
            make_record("W-003", "word-three", ["f3"]),
        ],
    }

    registry_doc = [
        {"id": "W-001", "lemma": "word-one", "pos": "noun", "entry": "unresolved", "allocated_at_build": "b1"},
        {"id": "W-002", "lemma": "word-two", "pos": "noun", "entry": "unresolved", "allocated_at_build": "b1"},
        {"id": "W-003", "lemma": "word-three", "pos": "noun", "entry": "unresolved", "allocated_at_build": "b1"},
    ]

    # Write files with locks
    (plans_dir / f"{slug}.yaml").write_text(yaml.safe_dump(plan_doc), encoding="utf-8")
    lock.write(evidence_dir / f"{slug}.yaml", lock.yaml_bytes(pack_doc))
    lock.write(evidence_dir / "_words.yaml", lock.yaml_bytes(words_doc))
    lock.write(evidence_dir / "_words.registry.yaml", lock.yaml_bytes(registry_doc))

    return plans_dir, evidence_dir


# ---------------------------------------------------------------------------
# Deliverables 2 & 5: Lock generation, checking, permissions, byte stability
# ---------------------------------------------------------------------------


def test_lock_file_permissions_and_sidecar(tmp_path):
    """Writing a lock produces 0o644 file, 0o644 .lock sidecar, and 0o755 directory."""
    _plans_dir, _evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, digest = lesson_lock.write_lesson_lock(
        "a1",
        "mod-one",
        repo_root=tmp_path,
    )
    assert lock_path.is_file()
    assert Path(f"{lock_path}.lock").is_file()

    # Permissions
    file_mode = stat.S_IMODE(lock_path.stat().st_mode)
    sidecar_mode = stat.S_IMODE(Path(f"{lock_path}.lock").stat().st_mode)
    dir_mode = stat.S_IMODE(lock_path.parent.stat().st_mode)

    assert file_mode == 0o644
    assert sidecar_mode == 0o644
    assert dir_mode == 0o755

    # Sidecar content
    sidecar_content = Path(f"{lock_path}.lock").read_text(encoding="ascii")
    assert sidecar_content == f"{digest}\n"
    assert lock.check(lock_path)


def test_lock_byte_stability_across_two_writes_and_unrelated_pack_edit(tmp_path):
    """Two writes produce identical bytes; editing an uncited pack record leaves lock identical."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, d1 = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    bytes1 = lock_path.read_bytes()

    # Write again
    _, d2 = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    bytes2 = lock_path.read_bytes()
    assert bytes1 == bytes2
    assert d1 == d2

    # Edit unrelated pack record (T-999 is not cited by any lesson)
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    for rec in pack_data["texts"]:
        if rec["id"] == "T-999":
            rec["quote"] = "Unrelated edit to uncited record"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    # Recompute and write lock
    _, d3 = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    bytes3 = lock_path.read_bytes()
    assert bytes1 == bytes3
    assert d1 == d3


def test_lock_check_passes_when_identical_and_fails_with_diff_when_stale(tmp_path):
    """check_lesson_lock passes when byte-identical; returns unified diff when stale."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    ok, diff = lesson_lock.check_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    assert ok is True
    assert diff == ""

    # Stale edit: change T-001 (cited by lesson 1) in pack
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    pack_data["texts"][0]["quote"] = "Modified quote one"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    ok, diff = lesson_lock.check_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    assert ok is False
    assert "--- committed:" in diff
    assert "+++ fresh:" in diff


def test_retired_word_id_cited_fails(tmp_path):
    """A plan citing a retired word id fails with unknown_word_id."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)

    # Retire W-001 in registry
    reg_path = evidence_dir / "_words.registry.yaml"
    reg_records = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
    reg_records[0]["retired"] = True
    lock.write(reg_path, lock.yaml_bytes(reg_records))

    with pytest.raises(ValueError, match=r"unknown_word_id: word id 'W-001' is retired"):
        lesson_lock.compute_lesson_lock("a1", "mod-one", repo_root=tmp_path)


def test_unknown_word_or_pack_id_fails(tmp_path):
    """A plan citing an unknown word id or pack id fails with validator codes."""
    plans_dir, _evidence_dir = setup_curriculum_fixture(tmp_path)
    plan_path = plans_dir / "mod-one.yaml"
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))

    # Unknown pack id
    plan_data["lessons"][0]["steps"][0]["evidence"].append("T-888")
    plan_path.write_text(yaml.safe_dump(plan_data), encoding="utf-8")
    with pytest.raises(ValueError, match=r"unknown_pack_id: evidence id 'T-888' not found"):
        lesson_lock.compute_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    # Revert and add unknown word id
    plan_data["lessons"][0]["steps"][0]["evidence"].remove("T-888")
    plan_data["lessons"][0]["inventory"]["vocabulary"]["core"].append(
        {"lemma": "ghost", "evidence": "W-888", "forms": ["f"]}
    )
    plan_path.write_text(yaml.safe_dump(plan_data), encoding="utf-8")
    with pytest.raises(ValueError, match=r"unknown_word_id: word id 'W-888' not found"):
        lesson_lock.compute_lesson_lock("a1", "mod-one", repo_root=tmp_path)


# ---------------------------------------------------------------------------
# Deliverables 3 & 5: Diff engine tests
# ---------------------------------------------------------------------------


def test_diff_pack_fix_lesson_2_only(tmp_path):
    """A pack fix to a record cited by lesson 2 only -> --diff names lesson 2 only."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    # Save baseline state directory
    baseline_dir = tmp_path / "baseline_state"
    baseline_dir.mkdir()
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir()
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # Fix record T-002 cited by lesson 2 only
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    for rec in pack_data["texts"]:
        if rec["id"] == "T-002":
            rec["quote"] = "Fixed quote two for lesson two"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    # Re-write current lock
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    # Diff against baseline
    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert len(rebuild) == 1
    assert rebuild[0]["slug"] == "mod-one"
    assert rebuild[0]["lesson"] == 2
    assert rebuild[0]["reasons"] == ["record_changed T-002"]


def test_diff_built_with_change_invalidates_all_lessons(tmp_path):
    """A qualifying source identity change in pack built_with invalidates every lesson with shared_changed;
    non-qualifying keys like mcp_commit and built_at do not.
    """
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))

    # Changing mcp_commit and built_at in pack does NOT invalidate lessons
    pack_data["built_with"]["mcp_commit"] = "9" * 40
    pack_data["built_with"]["built_at"] = "2026-09-22T19:00:00Z"
    lock.write(pack_path, lock.yaml_bytes(pack_data))
    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert rebuild == []

    # Changing a qualifying source identity (e.g. vesum) invalidates all lessons
    pack_data["built_with"]["vesum"] = "9" * 64
    lock.write(pack_path, lock.yaml_bytes(pack_data))
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert len(rebuild) == 3
    assert [r["lesson"] for r in rebuild] == [1, 2, 3]
    for r in rebuild:
        assert r["reasons"] == ["shared_changed"]


def test_diff_uncited_record_change_yields_no_rebuild(tmp_path):
    """A change to a record no lesson cites results in nothing to rebuild."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # Change T-999 in pack (uncited)
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    for rec in pack_data["texts"]:
        if rec["id"] == "T-999":
            rec["quote"] = "Changed uncited quote"
    lock.write(pack_path, lock.yaml_bytes(pack_data))
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert rebuild == []


def test_diff_plan_citation_added_lesson_3(tmp_path):
    """A plan edit that adds a citation to lesson 3 -> plan_changed for lesson 3 only."""
    plans_dir, _evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # Edit plan: add citation to lesson 3 (cites T-001)
    plan_path = plans_dir / "mod-one.yaml"
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan_data["lessons"][2]["steps"][0]["evidence"].append("T-001")
    plan_path.write_text(yaml.safe_dump(plan_data), encoding="utf-8")

    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert len(rebuild) == 1
    assert rebuild[0]["lesson"] == 3
    assert rebuild[0]["reasons"] == ["plan_changed"]


def test_diff_all_word_record_change_across_modules(tmp_path):
    """A word-record change names every lesson in every module citing it, and none other."""
    plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path, slug="mod-one")

    # Add second module mod-two
    mod2_plan = {
        "plan_schema": 2,
        "module": "mod-two",
        "level": "a1",
        "sequence": 2,
        "slug": "mod-two",
        "title": "Module Two",
        "lessons": [
            {
                "n": 1,
                "slug": "lesson-1",
                "kind": "teach",
                "inventory": {
                    "grammar": [],
                    "vocabulary": {
                        "core": [{"lemma": "word-two", "evidence": "W-002", "forms": ["f2"]}],
                        "incidental": [],
                        "recycled": [],
                    },
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "evidence": ["T-001"],
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-002"]},
                    }
                ],
            },
            {
                "n": 2,
                "slug": "lesson-2",
                "kind": "recap",
                "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
                "steps": [{"id": "s1", "kind": "practice", "evidence": ["T-001"]}],
            },
        ],
    }
    (plans_dir / "mod-two.yaml").write_text(yaml.safe_dump(mod2_plan), encoding="utf-8")

    mod2_pack = {
        "evidence_schema": 1,
        "module": "a1/mod-two",
        "built_with": {
            "mcp_commit": "1" * 40,
            "sources_db": "2" * 64,
            "vesum": "3" * 64,
            "trie": "4" * 64,
            "ulif_forms": "pending",
            "standard_sha256": "5" * 64,
        },
        "texts": [{"id": "T-001", "quote": "Quote one"}],
    }
    lock.write(evidence_dir / "mod-two.yaml", lock.yaml_bytes(mod2_pack))

    # Write initial locks for both modules
    lock1, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    lock2, _ = lesson_lock.write_lesson_lock("a1", "mod-two", repo_root=tmp_path)

    # Save baseline directory
    baseline_dir = tmp_path / "baseline_state"
    b_mod1 = baseline_dir / "mod-one"
    b_mod2 = baseline_dir / "mod-two"
    b_mod1.mkdir(parents=True)
    b_mod2.mkdir(parents=True)
    lock.write(b_mod1 / "lessons.lock.yaml", lock1.read_bytes())
    lock.write(b_mod2 / "lessons.lock.yaml", lock2.read_bytes())

    # Modify W-002 in _words.yaml (cited by mod-one lesson 2 and mod-two lesson 1)
    words_path = evidence_dir / "_words.yaml"
    words_data = yaml.safe_load(words_path.read_text(encoding="utf-8"))
    for w in words_data["words"]:
        if w["id"] == "W-002":
            w["forms"].append({"form": "f2_extra", "tags": "noun:inanim:m:tag_extra"})
    lock.write(words_path, lock.yaml_bytes(words_data))

    # Re-write locks for both modules
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    lesson_lock.write_lesson_lock("a1", "mod-two", repo_root=tmp_path)

    # CLI call --all --diff
    argv = ["a1", "--all", "--diff", str(baseline_dir), "--repo-root", str(tmp_path), "--json"]
    out_json = []

    def mock_print(s):
        out_json.append(s)

    original_print = print
    try:
        # Run main and capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            rc = lesson_lock.main(argv)
    finally:
        pass

    assert rc == 3
    res = json.loads(f.getvalue())
    assert res["level"] == "a1"
    rebuild = res["rebuild"]

    # Rebuild should contain ONLY: mod-one lesson 2, and mod-two lesson 1
    assert len(rebuild) == 2
    assert rebuild[0] == {"slug": "mod-one", "lesson": 2, "reasons": ["word_record_changed W-002"]}
    assert rebuild[1] == {"slug": "mod-two", "lesson": 1, "reasons": ["word_record_changed W-002"]}


def test_diff_git_ref_in_temp_repo(tmp_path):
    """--diff <git ref> in a temporary repository names only changed lessons."""
    # Initialize a temporary git repository
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, timeout=10)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, timeout=10)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, timeout=10)

    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, timeout=10)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, timeout=10)

    # Fix record T-002 cited by lesson 2 only
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    for rec in pack_data["texts"]:
        if rec["id"] == "T-002":
            rec["quote"] = "Fixed quote two in git test"
    lock.write(pack_path, lock.yaml_bytes(pack_data))
    lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    # Diff against HEAD
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        rc = lesson_lock.main(["a1", "mod-one", "--diff", "HEAD", "--repo-root", str(tmp_path), "--json"])

    assert rc == 3
    res = json.loads(f.getvalue())
    assert len(res["rebuild"]) == 1
    assert res["rebuild"][0] == {
        "slug": "mod-one",
        "lesson": 2,
        "reasons": ["record_changed T-002"],
    }


def test_cli_clean_environment_subprocess(tmp_path):
    """Subprocess CLI execution with clean environment tests exit codes 0, 1, 3."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)

    # Clean env with only PATH
    clean_env = {"PATH": os.environ["PATH"]}

    # 1. Generate lock with --write (exit code 0)
    proc_write = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--write",
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc_write.returncode == 0, f"Write failed: {proc_write.stderr}\n{proc_write.stdout}"
    data_write = json.loads(proc_write.stdout)
    assert data_write["status"] == "ok"

    # 2. Check lock byte-for-byte (exit code 0)
    proc_check = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc_check.returncode == 0
    assert "byte-identical" in proc_check.stdout

    # 3. Check diff against baseline when identical (exit code 0)
    baseline_dir = tmp_path / "baseline_dir"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock_file = evidence_dir / "_state/mod-one/lessons.lock.yaml"
    lock.write(baseline_mod / "lessons.lock.yaml", lock_file.read_bytes())

    proc_diff_clean = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--diff",
            str(baseline_dir),
            "--repo-root",
            str(tmp_path),
            "--json",
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc_diff_clean.returncode == 0
    diff_data = json.loads(proc_diff_clean.stdout)
    assert diff_data["rebuild"] == []

    # 4. Modify pack record cited by lesson 1, re-write, diff (exit code 3)
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    pack_data["texts"][0]["quote"] = "Clean subprocess quote edit"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--write",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        check=True,
        timeout=30,
    )

    proc_diff_rebuild = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--diff",
            str(baseline_dir),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc_diff_rebuild.returncode == 3
    assert "mod-one lesson 1: record_changed T-001" in proc_diff_rebuild.stdout

    # 5. Tampered sidecar -> exit code 1
    (lock_file.parent / f"{lock_file.name}.lock").write_bytes(b"0" * 64 + b"\n")
    proc_err = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "lessons-lock",
            "a1",
            "mod-one",
            "--repo-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc_err.returncode == 1


def test_rebuilt_pack_does_not_mark_lessons_stale(synthetic_sources, synthetic_standard, tmp_path):
    """Rebuilding a pack with build_pack updates mcp_commit but does not invalidate lessons."""
    plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path, level="a1", slug="mod-one")

    req_file = tmp_path / "pack_req.yaml"
    req_file.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/mod-one",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "First point.",
                    },
                    {
                        "id": "T-002",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Second point.",
                    },
                    {
                        "id": "T-003",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Third point.",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    src = sources.Sources(sources_db=synthetic_sources, standard_path=synthetic_standard)

    # 1. Build pack first time with commit A
    with patch("scripts.curriculum.evidence.pack.get_mcp_commit", return_value="a" * 40):
        res1 = pack.build_pack(
            "a1",
            "mod-one",
            req_file,
            evidence_dir=evidence_dir,
            sources_instance=src,
            offline=True,
        )
    assert res1["status"] == "ok"
    assert res1["pack"]["built_with"]["mcp_commit"] == "a" * 40

    # 2. Write initial lesson lock
    lock_path, _ = lesson_lock.write_lesson_lock(
        "a1",
        "mod-one",
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=tmp_path,
    )

    # 3. Save baseline directory
    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # 4. Rebuild pack with commit B (simulating git HEAD advance)
    with patch("scripts.curriculum.evidence.pack.get_mcp_commit", return_value="b" * 40):
        res2 = pack.build_pack(
            "a1",
            "mod-one",
            req_file,
            evidence_dir=evidence_dir,
            sources_instance=src,
            offline=True,
        )
    assert res2["status"] == "ok"
    assert res2["pack"]["built_with"]["mcp_commit"] == "b" * 40

    # 5. Check lock is byte-identical: rebuild did not mark lesson stale
    ok, diff = lesson_lock.check_lesson_lock(
        "a1",
        "mod-one",
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=tmp_path,
    )
    assert ok is True
    assert diff == ""

    # 6. Diff against baseline produces empty rebuild list
    rebuild = lesson_lock.diff_module(
        "a1",
        "mod-one",
        str(baseline_dir),
        evidence_dir=evidence_dir,
        plans_dir=plans_dir,
        repo_root=tmp_path,
    )
    assert rebuild == []


def test_diff_standard_record_fix_invalidates_only_citing_lesson(tmp_path):
    """An S- record fix invalidates only the lesson citing it, not unciting lessons."""
    plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)

    # Modify plan so lesson 2 cites S-001 instead of T-002
    plan_path = plans_dir / "mod-one.yaml"
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan_data["lessons"][1]["steps"][0]["evidence"] = ["S-001"]
    plan_path.write_text(yaml.safe_dump(plan_data), encoding="utf-8")

    # Initial write of lock and baseline
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)
    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # Fix S-001 in pack
    pack_path = evidence_dir / "mod-one.yaml"
    pack_data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    pack_data["standard"][0]["text"] = "Updated standard line text"
    lock.write(pack_path, lock.yaml_bytes(pack_data))

    # Diff against baseline: names lesson 2 only, no shared_changed
    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert len(rebuild) == 1
    assert rebuild[0]["lesson"] == 2
    assert rebuild[0]["reasons"] == ["record_changed S-001"]


def test_diff_word_record_fix_without_rewriting_lock_reports_changed(tmp_path):
    """--diff detects word_record_changed even when the module's lock file was not rewritten."""
    _plans_dir, evidence_dir = setup_curriculum_fixture(tmp_path)
    lock_path, _ = lesson_lock.write_lesson_lock("a1", "mod-one", repo_root=tmp_path)

    baseline_dir = tmp_path / "baseline_state"
    baseline_mod = baseline_dir / "mod-one"
    baseline_mod.mkdir(parents=True)
    lock.write(baseline_mod / "lessons.lock.yaml", lock_path.read_bytes())

    # Modify W-002 in _words.yaml (cited by lesson 2)
    words_path = evidence_dir / "_words.yaml"
    words_data = yaml.safe_load(words_path.read_text(encoding="utf-8"))
    words_data["words"][1]["forms"].append({"form": "f2_extra", "tags": "noun:inanim:m:tag_extra"})
    lock.write(words_path, lock.yaml_bytes(words_data))

    # We intentionally DO NOT rewrite lessons.lock.yaml for mod-one.
    # --diff must compute current lock dynamically and report word_record_changed
    rebuild = lesson_lock.diff_module("a1", "mod-one", str(baseline_dir), repo_root=tmp_path)
    assert len(rebuild) == 1
    assert rebuild[0]["lesson"] == 2
    assert rebuild[0]["reasons"] == ["word_record_changed W-002"]
