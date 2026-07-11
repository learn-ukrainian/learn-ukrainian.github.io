"""ADR-011 P1 — Project Research Registry validator contract tests.

Hermetic: no GitHub, no network, no build/knowledge/state runtime. Function-level
tests build synthetic registries under tmp_path; a few end-to-end tests operate on
copies of the committed registry so comment/order preservation is exercised on real
comment-bearing YAML.
"""

from __future__ import annotations

import ast
import contextlib
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit import check_research_registry as crr

REPO_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_HASH = "sha256:" + "0" * 64

# Deterministic offline stand-ins for the injected seams.
DEFAULT_STREAMS = {"core-quality": [4274], "atlas-practice": [4387, 4700], "eval-harness": [4913]}
DEFAULT_DECISIONS = {"dec-001", "dec-002"}


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def digest_body(rid: str) -> str:
    return f"# {rid}\n\nSource: https://example.org/{rid}\n\nParaphrase only, no verbatim.\n"


def make_record(rid: str = "rec-a", state: str = "deferred", **over: Any) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "id": rid,
        "title": f"Title {rid}",
        "summary": f"Summary {rid}",
        "content_hash": PLACEHOLDER_HASH,
        "state": state,
        "provenance": {
            "digest": f"docs/references/research-digests/{rid}.md",
            "digest_anchor": None,
            "source_url": f"https://example.org/{rid}",
        },
        "routing": {"roles": ["quality"]},
        "cold_start_roles": [],
        "ownership": None,
        "consumer": None,
        "reason": "Deliberately deferred for the test." if state == "deferred" else None,
        "replacement": None,
        "access_class": "tracked-digest",
    }
    rec.update(over)
    return rec


def build_project(
    tmp_path: Path,
    records: list[dict[str, Any]],
    *,
    bodies: dict[str, str] | None = None,
    extra_files: dict[str, str] | None = None,
    sync: bool = True,
) -> tuple[Path, dict[str, Any]]:
    """Materialize a registry project under tmp_path and return (project_root, data).

    Writes each record's digest, optional consumer-target files, then (by default)
    syncs each record's content_hash to the on-disk projection so the only failures
    are the ones a test intends.
    """
    bodies = bodies or {}
    for rec in records:
        digest_rel = rec["provenance"]["digest"]
        path = tmp_path / digest_rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(bodies.get(rec["id"], digest_body(rec["id"])), "utf-8")
    for rel, content in (extra_files or {}).items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, "utf-8")
    if sync:
        for rec in records:
            with contextlib.suppress(crr.ProvenanceError):
                # invalid-provenance tests keep the placeholder
                rec["content_hash"] = crr.expected_content_hash(rec, tmp_path)
    data = {"schema_version": 1, "records": records}
    reg_path = tmp_path / "docs" / "references" / "research-registry.yaml"
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        "# synthetic test registry — header comment preserved\n"
        + yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        "utf-8",
    )
    return tmp_path, data


def run(data: dict[str, Any], project_root: Path, **kw: Any) -> crr.CheckResult:
    kw.setdefault("streams", DEFAULT_STREAMS)
    kw.setdefault("decision_ids", DEFAULT_DECISIONS)
    return crr.validate_registry(data, project_root=project_root, **kw)


def copy_real_project(dst: Path) -> Path:
    for rel in (
        "docs/references/research-registry.yaml",
        "scripts/config/issue_streams.yaml",
        "docs/decisions/decisions.yaml",
        "scripts/audit/text_difficulty.py",
    ):
        src = REPO_ROOT / rel
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, out)
    shutil.copytree(
        REPO_ROOT / "docs/references/research-digests",
        dst / "docs/references/research-digests",
    )
    return dst


# --------------------------------------------------------------------------- #
# 1. Committed registry validates
# --------------------------------------------------------------------------- #
def test_committed_registry_validates_and_has_no_drift() -> None:
    _raw, data = crr.load_registry(REPO_ROOT / "docs/references/research-registry.yaml")
    assert crr.validate_schema(data, crr.load_schema()) == []
    result = crr.validate_registry(data, project_root=REPO_ROOT)
    assert result.errors == [], result.errors
    assert result.drift == [], result.drift
    assert {r["id"] for r in data["records"]} == {
        "unlp-2026-cefr-assessment",
        "unlp-2025-stress-tts",
        "unlp-2026-gec-minimal-edit",
    }


# --------------------------------------------------------------------------- #
# 2. Schema failure + duplicate ids
# --------------------------------------------------------------------------- #
def test_schema_failure_is_reported() -> None:
    data = {"schema_version": 1, "records": [make_record(state="bogus-state")]}
    assert crr.validate_schema(data, crr.load_schema())
    result = crr.validate_registry(data, project_root=REPO_ROOT, streams=DEFAULT_STREAMS, decision_ids=DEFAULT_DECISIONS)
    assert result.errors and any("schema" in e for e in result.errors)


def test_bad_content_hash_pattern_is_schema_rejected() -> None:
    rec = make_record()
    rec["content_hash"] = "sha256:NOTHEX"
    assert crr.validate_schema({"schema_version": 1, "records": [rec]}, crr.load_schema())


def test_duplicate_ids_rejected(tmp_path: Path) -> None:
    root, data = build_project(tmp_path, [make_record("dup"), make_record("dup")])
    result = run(data, root)
    assert any("duplicate record id" in e for e in result.errors)


# --------------------------------------------------------------------------- #
# 3. Lifecycle positive + negative for all four states
# --------------------------------------------------------------------------- #
def test_lifecycle_all_states(tmp_path: Path) -> None:
    ok = [
        make_record("adopt-ok", state="adopted", consumer={"kind": "decision", "ref": "dec-001"}),
        make_record("defer-ok", state="deferred", reason="A real reason."),
        make_record(
            "prop-ok", state="proposed", ownership={"issue": 4952, "stream": 4274}
        ),
        make_record("super-ok", state="superseded", replacement="defer-ok"),
    ]
    root, data = build_project(tmp_path, ok)
    assert run(data, root).errors == []

    bad = [
        make_record("adopt-bad", state="adopted", consumer=None),
        make_record("defer-bad", state="deferred", reason=None),
        make_record("prop-bad", state="proposed", ownership=None),
    ]
    root2, data2 = build_project(tmp_path / "b", bad)
    errs = run(data2, root2).errors
    assert any("adopt-bad" in e and "consumer" in e for e in errs)
    assert any("defer-bad" in e and "reason" in e for e in errs)
    assert any("prop-bad" in e and "issue" in e for e in errs)


# --------------------------------------------------------------------------- #
# 4. Replacement: missing / unknown / self / cycle
# --------------------------------------------------------------------------- #
def test_replacement_missing_unknown_self(tmp_path: Path) -> None:
    recs = [
        make_record("s-missing", state="superseded", replacement=None),
        make_record("s-unknown", state="superseded", replacement="ghost"),
        make_record("s-self", state="superseded", replacement="s-self"),
    ]
    root, data = build_project(tmp_path, recs)
    errs = run(data, root).errors
    assert any("s-missing" in e and "replacement" in e for e in errs)
    assert any("s-unknown" in e and "does not exist" in e for e in errs)
    assert any("s-self" in e and "itself" in e for e in errs)


def test_supersession_cycle_detected(tmp_path: Path) -> None:
    recs = [
        make_record("cyc-a", state="superseded", replacement="cyc-b"),
        make_record("cyc-b", state="superseded", replacement="cyc-a"),
    ]
    root, data = build_project(tmp_path, recs)
    errs = run(data, root).errors
    assert any("cycle" in e for e in errs)


# --------------------------------------------------------------------------- #
# 5. Typed consumers: kinds, dangling ref/symbol, escape, wrong decision, seam
# --------------------------------------------------------------------------- #
def test_consumer_kinds_and_boundaries(tmp_path: Path) -> None:
    extra = {"scripts/thing.py": "def my_func():\n    return 1\n"}
    recs = [
        make_record("c-path", state="adopted", consumer={"kind": "path", "ref": "scripts/thing.py"}),
        make_record("c-symbol", state="adopted", consumer={"kind": "path", "ref": "scripts/thing.py::my_func"}),
        make_record("c-decision", state="adopted", consumer={"kind": "decision", "ref": "dec-001"}),
    ]
    root, data = build_project(tmp_path, recs, extra_files=extra)
    assert run(data, root).errors == []

    bad = [
        make_record("c-dangling", state="adopted", consumer={"kind": "path", "ref": "scripts/nope.py"}),
        make_record("c-badsym", state="adopted", consumer={"kind": "path", "ref": "scripts/thing.py::ghost"}),
        make_record("c-escape", state="adopted", consumer={"kind": "path", "ref": "../evil.py"}),
        make_record("c-baddec", state="adopted", consumer={"kind": "decision", "ref": "dec-999"}),
    ]
    root2, data2 = build_project(tmp_path / "b", bad, extra_files=extra)
    errs = run(data2, root2).errors
    assert any("c-dangling" in e and "does not resolve to a file" in e for e in errs)
    assert any("c-badsym" in e and "not found" in e for e in errs)
    assert any("c-escape" in e for e in errs)
    assert any("c-baddec" in e and "decision" in e for e in errs)


def test_issue_and_corpus_consumers_fail_closed_without_resolver(tmp_path: Path) -> None:
    recs = [
        make_record("c-issue", state="adopted", consumer={"kind": "issue", "ref": "4952"}),
        make_record("c-corpus", state="adopted", consumer={"kind": "corpus", "ref": "zno-intake"}),
    ]
    root, data = build_project(tmp_path, recs)
    # Fail-closed: no resolver injected -> both invalid.
    errs = run(data, root).errors
    assert any("c-issue" in e and "resolver" in e for e in errs)
    assert any("c-corpus" in e and "resolver" in e for e in errs)

    # Resolver boundary: inject seams -> both resolve.
    ok = run(data, root, issue_resolver=lambda ref: True, corpus_resolver=lambda ref: True)
    assert ok.errors == []

    # A resolver that rejects still fails closed.
    rej = run(data, root, issue_resolver=lambda ref: False, corpus_resolver=lambda ref: False)
    assert any("c-issue" in e for e in rej.errors)


# --------------------------------------------------------------------------- #
# 6. Canonical hash equivalence
# --------------------------------------------------------------------------- #
def test_canonical_normalization_equivalence() -> None:
    crlf = "line one\r\nline two   \r\n\r\n\r\n"
    lf = "line one\nline two\n"
    bare = "line one\nline two"
    assert crr.normalize_digest_projection(crlf) == "line one\nline two"
    assert (
        crr.compute_content_hash(crr.normalize_digest_projection(crlf))
        == crr.compute_content_hash(crr.normalize_digest_projection(lf))
        == crr.compute_content_hash(crr.normalize_digest_projection(bare))
    )


def test_anchored_section_hashes_equal_dedicated_digest() -> None:
    shared = "<!-- record:foo -->\nBODY line\nsecond\n<!-- /record:foo -->\n"
    projection = crr.extract_digest_projection(shared, "foo", "foo")
    dedicated = "BODY line\nsecond\n"
    assert (
        crr.compute_content_hash(crr.normalize_digest_projection(projection))
        == crr.compute_content_hash(crr.normalize_digest_projection(dedicated))
    )


# --------------------------------------------------------------------------- #
# 7. Drift reports the exact --reconcile --id command
# --------------------------------------------------------------------------- #
def test_drift_reports_reconcile_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = copy_real_project(tmp_path)
    digest = root / "docs/references/research-digests/unlp-2026-cefr-assessment.md"
    digest.write_text(digest.read_text("utf-8") + "\nAn intentional edit.\n", "utf-8")
    before = (root / "docs/references/research-registry.yaml").read_bytes()
    code = crr.main(["--check"], project_root=root)
    err = capsys.readouterr().err
    assert code == 2
    assert "unlp-2026-cefr-assessment" in err
    assert "--reconcile --id unlp-2026-cefr-assessment" in err
    # --check never mutates.
    assert (root / "docs/references/research-registry.yaml").read_bytes() == before


# --------------------------------------------------------------------------- #
# 8. --check is byte-for-byte read-only on the committed registry
# --------------------------------------------------------------------------- #
def test_check_is_byte_for_byte_readonly() -> None:
    reg = REPO_ROOT / "docs/references/research-registry.yaml"
    before = reg.read_bytes()
    code = crr.main(["--check"], project_root=REPO_ROOT)
    assert code == 0
    assert reg.read_bytes() == before


# --------------------------------------------------------------------------- #
# 9. Selective reconcile: only requested hash, preserves comments/order, idempotent
# --------------------------------------------------------------------------- #
def test_selective_reconcile_is_targeted_and_idempotent(tmp_path: Path) -> None:
    root = copy_real_project(tmp_path)
    reg = root / "docs/references/research-registry.yaml"
    digests = root / "docs/references/research-digests"
    target = "unlp-2025-stress-tts"
    other = "unlp-2026-cefr-assessment"
    # Drift BOTH digests.
    for rid in (target, other):
        p = digests / f"{rid}.md"
        p.write_text(p.read_text("utf-8") + f"\nedit {rid}\n", "utf-8")

    original_lines = reg.read_text("utf-8").splitlines()
    # Capture the OTHER record's stored hash before reconcile.
    _, data_before = crr.load_registry(reg)
    other_hash_before = next(r["content_hash"] for r in data_before["records"] if r["id"] == other)
    comment_lines_before = [line for line in original_lines if line.startswith("#")]

    code = crr.main(["--reconcile", "--id", target], project_root=root)
    assert code == 0

    text_after = reg.read_text("utf-8")
    _, data_after = crr.load_registry(reg)
    # Only the targeted record's hash changed; the other's is byte-identical.
    other_hash_after = next(r["content_hash"] for r in data_after["records"] if r["id"] == other)
    assert other_hash_after == other_hash_before
    # Comments and record order preserved.
    assert [line for line in text_after.splitlines() if line.startswith("#")] == comment_lines_before
    assert [r["id"] for r in data_after["records"]] == [r["id"] for r in data_before["records"]]
    # The other record still reports drift (proves selectivity).
    result = crr.validate_registry(data_after, project_root=root)
    assert result.drift == [other]

    # Idempotent: reconciling the same id again is a no-op on bytes.
    bytes_after = reg.read_bytes()
    assert crr.main(["--reconcile", "--id", target], project_root=root) == 0
    assert reg.read_bytes() == bytes_after


# --------------------------------------------------------------------------- #
# 10. Anchor fence errors
# --------------------------------------------------------------------------- #
def test_anchor_fence_errors() -> None:
    with pytest.raises(crr.ProvenanceError, match="missing"):
        crr.extract_digest_projection("no fences here\n", "foo", "foo")
    with pytest.raises(crr.ProvenanceError, match="duplicate"):
        crr.extract_digest_projection(
            "<!-- record:foo -->\nx\n<!-- /record:foo -->\n<!-- record:foo -->\ny\n<!-- /record:foo -->\n",
            "foo",
            "foo",
        )
    with pytest.raises(crr.ProvenanceError, match="nested"):
        crr.extract_digest_projection(
            "<!-- record:foo -->\n<!-- record:bar -->\ny\n<!-- /record:foo -->\n", "foo", "foo"
        )
    with pytest.raises(crr.ProvenanceError, match="mismatched"):
        crr.extract_digest_projection(
            "<!-- /record:foo -->\nx\n<!-- record:foo -->\n", "foo", "foo"
        )
    with pytest.raises(crr.ProvenanceError, match="must equal record id"):
        crr.extract_digest_projection("<!-- record:foo -->\nx\n<!-- /record:foo -->\n", "foo", "bar")
    # Valid.
    assert crr.extract_digest_projection(
        "<!-- record:foo -->\nkeep\n<!-- /record:foo -->\n", "foo", "foo"
    ) == "keep"


def test_wrong_anchor_surfaces_provenance_error(tmp_path: Path) -> None:
    rec = make_record("anchor-rec", state="deferred")
    rec["provenance"]["digest_anchor"] = "anchor-rec"
    # Body has no fence -> missing fence.
    root, data = build_project(tmp_path, [rec], bodies={"anchor-rec": "plain body, no fence\n"}, sync=False)
    rec["content_hash"] = PLACEHOLDER_HASH
    errs = crr.validate_registry(data, project_root=root, streams=DEFAULT_STREAMS, decision_ids=DEFAULT_DECISIONS).errors
    assert any("anchor-rec" in e and "fence" in e for e in errs)


# --------------------------------------------------------------------------- #
# 11. Digest copyright policy
# --------------------------------------------------------------------------- #
def test_digest_policy_oversized_overlong_and_unattributed(tmp_path: Path) -> None:
    big = "filler line number x\n" * 700  # > MAX_DIGEST_BYTES, no quotes
    overlong = 'Source: https://e.org\n\n"' + "q" * (crr.MAX_QUOTE_CHARS + 5) + '"\n'
    unattributed = '"a short quote with no provenance"\n'
    recs = [
        make_record("d-big"),
        make_record("d-quote"),
        make_record(
            "d-noprov",
            provenance={
                "digest": "docs/references/research-digests/d-noprov.md",
                "digest_anchor": None,
                "source_url": None,
            },
        ),
    ]
    root, data = build_project(
        tmp_path,
        recs,
        bodies={"d-big": big, "d-quote": overlong, "d-noprov": unattributed},
    )
    errs = run(data, root).errors
    assert any("d-big" in e and "bytes" in e for e in errs)
    assert any("d-quote" in e and "quoted span" in e for e in errs)
    assert any("d-noprov" in e and "provenance" in e for e in errs)


# --------------------------------------------------------------------------- #
# 12. Ownership: unknown epic + duplicate epic declaration
# --------------------------------------------------------------------------- #
def test_ownership_unknown_and_duplicate_epic(tmp_path: Path) -> None:
    rec_unknown = make_record("own-unknown", state="proposed", ownership={"issue": 1, "stream": 9999})
    root, data = build_project(tmp_path, [rec_unknown])
    errs = run(data, root).errors
    assert any("own-unknown" in e and "not a declared stream epic" in e for e in errs)

    rec_dup = make_record("own-dup", state="proposed", ownership={"issue": 2, "stream": 4274})
    root2, data2 = build_project(tmp_path / "b", [rec_dup])
    dup_streams = {"stream-x": [4274], "stream-y": [4274]}
    errs2 = crr.validate_registry(data2, project_root=root2, streams=dup_streams, decision_ids=DEFAULT_DECISIONS).errors
    assert any("own-dup" in e and "duplicate epic declaration" in e for e in errs2)


def test_ownership_membership_resolver_seam(tmp_path: Path) -> None:
    rec = make_record("own-mem", state="proposed", ownership={"issue": 4952, "stream": 4274})
    root, data = build_project(tmp_path, [rec])
    # Default (offline): no membership claim -> valid.
    assert run(data, root).errors == []
    # Injected resolver that rejects -> membership error.
    errs = run(data, root, membership_resolver=lambda issue, stream: False).errors
    assert any("own-mem" in e and "not a live child" in e for e in errs)


# --------------------------------------------------------------------------- #
# 13. Cold-start per-role cap of five
# --------------------------------------------------------------------------- #
def test_cold_start_role_cap(tmp_path: Path) -> None:
    six = [make_record(f"cs-{i}", cold_start_roles=["quality"]) for i in range(6)]
    root, data = build_project(tmp_path, six)
    assert any("quality" in e and "max 5" in e for e in run(data, root).errors)

    five = [make_record(f"cs5-{i}", cold_start_roles=["quality"]) for i in range(5)]
    root2, data2 = build_project(tmp_path / "b", five)
    assert not any("cold_start" in e for e in run(data2, root2).errors)


# --------------------------------------------------------------------------- #
# 14. Reconcile refuses mutation when non-hash errors exist
# --------------------------------------------------------------------------- #
def test_reconcile_refuses_on_nonhash_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    good = make_record("r-good", state="deferred")
    bad = make_record("r-bad", state="deferred", reason=None)  # non-hash error
    root, _data = build_project(tmp_path, [good, bad])
    reg = root / "docs/references/research-registry.yaml"
    # Introduce hash drift on the good record too.
    dpath = root / "docs/references/research-digests/r-good.md"
    dpath.write_text(dpath.read_text("utf-8") + "\ndrifted\n", "utf-8")
    before = reg.read_bytes()

    code = crr.main(["--reconcile"], project_root=root)
    out = capsys.readouterr()
    assert code == 2
    assert "Refusing to reconcile" in out.err
    assert reg.read_bytes() == before  # no mutation


# --------------------------------------------------------------------------- #
# 15. No dependency on the learner corpus / knowledge API / state / build packets
# --------------------------------------------------------------------------- #
def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text("utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module)
    return roots


def test_no_forbidden_runtime_dependencies() -> None:
    forbidden_prefixes = (
        "sqlite3",
        "requests",
        "urllib",
        "http.client",
        "scripts.api",
        "scripts.build",
        "scripts.ai_agent_bridge",
    )
    module_src = Path(crr.__file__).read_text("utf-8")
    for token in ("sources.db", "sqlite", "state_router", "session_router", "monitor_client", "build_knowledge_packet", "linear_pipeline"):
        assert token not in module_src, f"P1 code must not reference {token!r}"
    for path in (Path(crr.__file__), Path(__file__)):
        for root in _imported_roots(path):
            assert not root.startswith(forbidden_prefixes), f"{path.name} imports forbidden module {root!r}"


# --------------------------------------------------------------------------- #
# 16. Review-fix: YAML alias content_hash is rejected, never silently resolved,
#     never mutated by --reconcile (repro: content_hash: *h aliasing an anchor
#     defined on another field, e.g. summary).
# --------------------------------------------------------------------------- #
def test_yaml_alias_content_hash_rejected_without_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rid = "alias-rec"
    digest_dir = tmp_path / "docs/references/research-digests"
    digest_dir.mkdir(parents=True)
    (digest_dir / f"{rid}.md").write_text(digest_body(rid), "utf-8")

    registry_text = f"""schema_version: 1
records:
  - id: {rid}
    title: Title {rid}
    summary: &h "{PLACEHOLDER_HASH}"
    content_hash: *h
    state: deferred
    provenance:
      digest: docs/references/research-digests/{rid}.md
      digest_anchor: null
      source_url: https://example.org/{rid}
    routing:
      roles: [quality]
    cold_start_roles: []
    ownership: null
    consumer: null
    reason: Deliberately deferred for the test.
    replacement: null
    access_class: tracked-digest
"""
    reg_path = tmp_path / "docs/references/research-registry.yaml"
    reg_path.write_text(registry_text, "utf-8")
    before = reg_path.read_bytes()

    check_code = crr.main(["--check"], project_root=tmp_path)
    check_err = capsys.readouterr().err
    assert check_code == 2
    assert "alias" in check_err
    assert reg_path.read_bytes() == before  # --check never mutates

    reconcile_code = crr.main(["--reconcile"], project_root=tmp_path)
    reconcile_err = capsys.readouterr().err
    assert reconcile_code == 2
    assert "alias" in reconcile_err
    # Byte-for-byte: the anchor was NOT rewritten and no orphaned alias was left.
    assert reg_path.read_bytes() == before


# --------------------------------------------------------------------------- #
# 17. Review-fix: digest copyright policy scoped to the record PROJECTION, not
#     a whole shared file (cross-record false positives / borrowed provenance).
# --------------------------------------------------------------------------- #
def test_digest_policy_scoped_to_record_projection_in_shared_file(tmp_path: Path) -> None:
    small_ok = (
        "<!-- record:shared-a -->\n"
        "Source: https://example.org/shared-a\n\n"
        "Short paraphrase, no issues.\n"
        "<!-- /record:shared-a -->\n"
    )
    unattributed_quote = (
        "<!-- record:shared-b -->\n"
        '"a short quote with no provenance of its own"\n'
        "<!-- /record:shared-b -->\n"
    )
    oversized = (
        "<!-- record:shared-c -->\n"
        + ("filler line to blow past the per-record ceiling\n" * 120)
        + "<!-- /record:shared-c -->\n"
    )
    filler_between = "unrelated filler padding out the shared file\n" * 100
    shared_text = "\n".join([small_ok, filler_between, unattributed_quote, filler_between, oversized])
    assert len(shared_text.encode("utf-8")) > crr.MAX_DIGEST_BYTES  # whole file IS oversized

    def _rec(rid: str) -> dict[str, Any]:
        return make_record(
            rid,
            provenance={
                "digest": "docs/references/shared.md",
                "digest_anchor": rid,
                "source_url": None,
            },
        )

    recs = [_rec("shared-a"), _rec("shared-b"), _rec("shared-c")]
    root, data = build_project(
        tmp_path, recs, extra_files={"docs/references/shared.md": shared_text}
    )
    errs = run(data, root).errors
    # shared-a's own projection is small and clean, despite the file being huge.
    assert not any("shared-a" in e for e in errs)
    # shared-b cannot borrow shared-a's Source: URL from another section.
    assert any("shared-b" in e and "provenance" in e for e in errs)
    # shared-c's own projection (not the whole file) is what trips the ceiling.
    assert any("shared-c" in e and "bytes" in e for e in errs)


# --------------------------------------------------------------------------- #
# 18. Review-fix: quotation guard closes multi-line / curly-quote / combined-
#     blockquote bypasses.
# --------------------------------------------------------------------------- #
def test_quote_guard_multiline_straight_quote(tmp_path: Path) -> None:
    body = (
        "Source: https://example.org/ml-quote\n\n"
        '"' + ("word " * 60) + "\n" + ("more " * 20) + '"\n'
    )
    rec = make_record(
        "ml-quote",
        provenance={
            "digest": "docs/references/research-digests/ml-quote.md",
            "digest_anchor": None,
            "source_url": "https://example.org/ml-quote",
        },
    )
    root, data = build_project(tmp_path, [rec], bodies={"ml-quote": body})
    errs = run(data, root).errors
    assert any("ml-quote" in e and "quoted span" in e for e in errs)


def test_quote_guard_combines_contiguous_blockquote_lines(tmp_path: Path) -> None:
    line_a = "> " + ("alpha " * 20)  # short on its own
    line_b = "> " + ("beta " * 20)  # short on its own
    body = f"Source: https://example.org/bq-combine\n\n{line_a}\n{line_b}\n"
    assert len(line_a.strip()) < crr.MAX_QUOTE_CHARS
    assert len(line_b.strip()) < crr.MAX_QUOTE_CHARS
    rec = make_record(
        "bq-combine",
        provenance={
            "digest": "docs/references/research-digests/bq-combine.md",
            "digest_anchor": None,
            "source_url": "https://example.org/bq-combine",
        },
    )
    root, data = build_project(tmp_path, [rec], bodies={"bq-combine": body})
    errs = run(data, root).errors
    assert any("bq-combine" in e and "quoted span" in e for e in errs)


def test_quote_guard_curly_quotes(tmp_path: Path) -> None:
    body = (
        "Source: https://example.org/curly\n\n"
        "“" + ("x" * (crr.MAX_QUOTE_CHARS + 10)) + "”\n"
    )
    rec = make_record(
        "curly-quote",
        provenance={
            "digest": "docs/references/research-digests/curly-quote.md",
            "digest_anchor": None,
            "source_url": "https://example.org/curly",
        },
    )
    root, data = build_project(tmp_path, [rec], bodies={"curly-quote": body})
    errs = run(data, root).errors
    assert any("curly-quote" in e and "quoted span" in e for e in errs)


# --------------------------------------------------------------------------- #
# 19. Review-fix: digest path policy safe after resolution (symlinks, non-
#     reference files, valid fenced shared references).
# --------------------------------------------------------------------------- #
def test_digest_path_rejects_symlink_to_private(tmp_path: Path) -> None:
    private_dir = tmp_path / "docs/references/private"
    private_dir.mkdir(parents=True)
    secret = private_dir / "secret.md"
    secret.write_text(digest_body("secret"), "utf-8")
    digests_dir = tmp_path / "docs/references/research-digests"
    digests_dir.mkdir(parents=True)
    (digests_dir / "sym-private.md").symlink_to(secret)

    rec = make_record(
        "sym-private",
        provenance={
            "digest": "docs/references/research-digests/sym-private.md",
            "digest_anchor": None,
            "source_url": "https://example.org/sym-private",
        },
    )
    data = {"schema_version": 1, "records": [rec]}
    errs = run(data, tmp_path).errors
    assert any("sym-private" in e and "symlink" in e for e in errs)


def test_digest_path_rejects_symlink_to_nonprivate(tmp_path: Path) -> None:
    digests_dir = tmp_path / "docs/references/research-digests"
    digests_dir.mkdir(parents=True)
    real = digests_dir / "real.md"
    real.write_text(digest_body("real"), "utf-8")
    (digests_dir / "sym-nonprivate.md").symlink_to(real)

    rec = make_record(
        "sym-nonprivate",
        provenance={
            "digest": "docs/references/research-digests/sym-nonprivate.md",
            "digest_anchor": None,
            "source_url": "https://example.org/sym-nonprivate",
        },
    )
    data = {"schema_version": 1, "records": [rec]}
    errs = run(data, tmp_path).errors
    assert any("sym-nonprivate" in e and "symlink" in e for e in errs)


def test_digest_path_rejects_non_reference_file(tmp_path: Path) -> None:
    rec = make_record(
        "nonref",
        provenance={
            "digest": "scripts/audit/not-a-reference.md",
            "digest_anchor": None,
            "source_url": "https://example.org/nonref",
        },
    )
    root, data = build_project(tmp_path, [rec])
    errs = run(data, root).errors
    assert any("nonref" in e and "docs/references/" in e for e in errs)


def test_digest_path_accepts_valid_fenced_shared_reference(tmp_path: Path) -> None:
    shared_text = (
        "# Shared reference doc\n\n"
        "<!-- record:shared-ok -->\n"
        "Source: https://example.org/shared-ok\n\n"
        "Clean paraphrase, nothing borrowed.\n"
        "<!-- /record:shared-ok -->\n"
    )
    rec = make_record(
        "shared-ok",
        provenance={
            "digest": "docs/references/some-shared-notes.md",
            "digest_anchor": "shared-ok",
            "source_url": None,
        },
    )
    root, data = build_project(
        tmp_path, [rec], extra_files={"docs/references/some-shared-notes.md": shared_text}
    )
    assert run(data, root).errors == []


# --------------------------------------------------------------------------- #
# 20. Review-fix: invalid-UTF-8 digest is a record-scoped error, not a traceback.
# --------------------------------------------------------------------------- #
def test_invalid_utf8_digest_is_record_scoped_error(tmp_path: Path) -> None:
    rec = make_record(
        "bad-utf8",
        provenance={
            "digest": "docs/references/research-digests/bad-utf8.md",
            "digest_anchor": None,
            "source_url": "https://example.org/bad-utf8",
        },
    )
    digest_path = tmp_path / "docs/references/research-digests/bad-utf8.md"
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_bytes(b"Source: https://example.org/bad-utf8\n\n\xff\xfe not valid utf-8\n")

    data = {"schema_version": 1, "records": [rec]}
    errs = run(data, tmp_path).errors
    assert any("bad-utf8" in e and "UTF-8" in e for e in errs)


# --------------------------------------------------------------------------- #
# 21. Minor review-fixes: fence whitespace variant + module-level constant symbol.
# --------------------------------------------------------------------------- #
def test_extract_digest_projection_accepts_compact_fence_spacing() -> None:
    text = "<!--record:foo-->\nkeep\n<!--/record:foo-->\n"
    assert crr.extract_digest_projection(text, "foo", "foo") == "keep"


def test_resolve_symbol_finds_module_level_constant(tmp_path: Path) -> None:
    extra = {"scripts/constants.py": "MAX_FOO: int = 5\nOTHER = 1\n"}
    recs = [
        make_record(
            "c-const", state="adopted", consumer={"kind": "path", "ref": "scripts/constants.py::MAX_FOO"}
        ),
        make_record(
            "c-const2", state="adopted", consumer={"kind": "path", "ref": "scripts/constants.py::OTHER"}
        ),
    ]
    root, data = build_project(tmp_path, recs, extra_files=extra)
    assert run(data, root).errors == []
