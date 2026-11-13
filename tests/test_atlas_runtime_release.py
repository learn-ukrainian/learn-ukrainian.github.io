"""Specifically granted T1-T3 runtime source and reproducibility defects (#12596)."""

from __future__ import annotations

import copy
import json
import zipfile
from pathlib import Path

import pytest

from scripts.atlas import atlas_db
from scripts.audit import generate_search_index as search
from scripts.deploy import prepare_atlas_runtime_release as release
from scripts.deploy import runtime_source_report as report
from scripts.deploy import vendor_atlas_tree as vendor
from tests.test_vendor_atlas_tree import _archive_for, _build_two_gen_tree


def _source_files(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, dict]:
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "manifest.json"
    manifest.write_bytes(report.canonical_bytes({
        "version": "fixture-v1", "generated_at": "2026-07-17T00:00:00+00:00",
        "manifest_fingerprint": {"schema_version": 1, "fingerprint": "a" * 64},
        "entries": [{"lemma": "дім", "url_slug": "unit", "gloss": "A home.", "primary_source": "built_vocabulary"}],
    }))
    (root / "lexicon-manifest.pointer.json").write_bytes(report.canonical_bytes({
        "json_sha256": report.file_digest(manifest), "json_bytes": manifest.stat().st_size,
        "manifest_version": "fixture-v1", "fingerprint_schema_version": 1, "manifest_fingerprint": "a" * 64,
    }))
    (root / "lexicon-manifest.fingerprint.json").write_text('{"schema_version":1}')
    decks = root / "public/lexicon"
    decks.mkdir(parents=True)
    files = []
    for level in ("A1", "A2", "B1", "B2", "C1"):
        for part in ("index", "lexemes", "cloze"):
            path = decks / f"practice-{part}.{level}.json"
            path.write_text('{"deckVersion":"fixture-v1","items":[]}\n')
            files.append({"path": path.name, "sha256": report.file_digest(path), "bytes": path.stat().st_size})
    (root / "lexicon-practice-deck.pointer.json").write_bytes(report.canonical_bytes({
        "package_schema_version": 1, "files": files, "file_count": len(files),
    }))
    holds = root / "holds.json"
    holds.write_text('{"schema":"atlas-discovery-exclusions","schemaVersion":1,"exclusions":[]}\n')
    monkeypatch.setattr(report, "HOLDS", holds)
    monkeypatch.setattr(vendor, "DISCOVERY_EXCLUSIONS", holds)
    receipt = {
        "schema": "atlas-runtime-release.v1", "source": report.source_binding(manifest, pointer_dir=root, deck_dir=decks),
        "holds_sha256": report.file_digest(holds), "archive_sha256": "b" * 64,
        "runtime": {"dataVersion": "v-fixture", "runtimeManifestSha256": "c" * 64},
        "prior": {"archive_sha256": "d" * 64, "dataVersion": "v-prior", "runtimeManifestSha256": "e" * 64,
                  "manifestUrl": "versions/v-prior/manifest.json"},
        "raw": report.membership(["unit"]), "projected": report.membership(["unit"]),
    }
    receipt_path = root / "atlas-runtime-release.json"
    receipt_path.write_bytes(report.canonical_bytes(receipt))
    return manifest, decks, receipt_path, receipt


@pytest.mark.parametrize("scenario, expected", [
    ("unchanged", {"status": "current", "reasons": []}),
    ("manifest_deck", {"status": "stale", "reasons": ["manifest_changed"]}),
    ("membership", {"status": "stale", "reasons": ["membership_diverged"]}),
    ("count", {"status": "stale", "reasons": ["count_diverged"]}),
    ("holds", {"status": "stale", "reasons": ["holds_changed"]}),
    ("missing", {"status": "unknown", "reasons": ["receipt_missing"]}),
    ("invalid", {"status": "unknown", "reasons": ["receipt_invalid"]}),
    ("report_error", {"status": "unknown", "reasons": ["report_error"]}),
])
def test_report_classifies_data_drift_and_missing_or_invalid_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], scenario: str, expected: dict,
) -> None:
    """T1: stale or unknown source evidence must never be falsely reported current."""
    manifest, _, receipt_path, receipt = _source_files(tmp_path, monkeypatch)
    db = tmp_path / "atlas.db"
    atlas_db.migrate_manifest(manifest, db)
    if scenario == "manifest_deck":
        receipt["source"]["manifest_json_sha256"] = "f" * 64
        receipt["source"]["deck_sha256"]["practice-index.A1.json"] = "f" * 64
    elif scenario == "membership":
        receipt["raw"] = receipt["projected"] = report.membership(["different"])
    elif scenario == "count":
        receipt["raw"]["count"] = receipt["projected"]["count"] = 2
    elif scenario == "holds":
        receipt["holds_sha256"] = "f" * 64
    elif scenario == "invalid":
        receipt["raw"]["count"] = 2  # Identical membership digests cannot have unequal cardinality.
    receipt_path.write_bytes(report.canonical_bytes(receipt))
    if scenario == "missing":
        receipt_path.unlink()
    if scenario == "report_error":
        def fail(*args, **kwargs):
            raise RuntimeError("report-only failure")
        monkeypatch.setattr(report, "source_binding", fail)
    real_report = report.report_source_freshness
    monkeypatch.setattr(report, "report_source_freshness", lambda rows, parity, **kwargs: real_report(
        rows, parity, receipt_path=receipt_path, pointer_dir=tmp_path, **kwargs,
    ))
    monkeypatch.chdir(tmp_path)
    assert search.main(["--db", str(db), "--manifest", str(manifest)]) == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith('{"')]
    assert len(lines) == 1
    actual = lines[0]
    assert {key: actual[key] for key in ("status", "reasons")} == expected
    if scenario not in ("missing", "invalid", "report_error"):
        assert (actual["raw_count"], actual["projected_count"], actual["source_raw_count"], actual["source_projected_count"]) == (1, 1, 1, 1)


def test_prepare_refuses_nondeterministic_archive_without_weakening_vendor_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T2: byte-different archives must not pass a reproducible prepare replay."""
    from scripts.lexicon.runner import finalize

    manifest, decks, _, _ = _source_files(tmp_path / "source", monkeypatch)
    tree = _build_two_gen_tree(tmp_path / "prior")
    archive, digest = _archive_for(tree, tmp_path / "prior")
    common = {"manifest_path": manifest, "deck_dir": decks, "pointer_dir": manifest.parent,
              "prior_archive": archive, "prior_sha256": digest}
    first = release.prepare_release(work=tmp_path / "work1", out=tmp_path / "out1", **common)
    reference = tmp_path / "out1/atlas-runtime-release.json"
    second = release.verify_release(work=tmp_path / "work2", out=tmp_path / "out2", receipt_path=reference, **common)
    assert first == second
    assert (tmp_path / "out1/atlas-tree.zip").read_bytes() == (tmp_path / "out2/atlas-tree.zip").read_bytes()
    assert reference.read_bytes() == (tmp_path / "out2/atlas-runtime-release.json").read_bytes()
    real_build = finalize.build_publication_archive

    def changed_archive(tree_root: Path, archive_path: Path) -> str:
        real_build(tree_root, archive_path)
        with zipfile.ZipFile(archive_path, "a") as stream:
            stream.comment = b"deliberate nondeterministic transport bytes"
        return report.file_digest(archive_path)

    monkeypatch.setattr(finalize, "build_publication_archive", changed_archive)
    with pytest.raises(release.ReleaseError, match=r"^nondeterministic_export$"):
        release.verify_release(work=tmp_path / "work3", out=tmp_path / "out3", receipt_path=reference, **common)
    assert report.file_digest(archive) == digest


def test_report_rejects_workflow_command_injection_from_slug_or_reason(capsys: pytest.CaptureFixture[str]) -> None:
    """T3: source slug/reason text must never inject a second workflow command."""
    injected = "%\r\n::error::injected"
    slugs = report.membership([injected])
    binding = {"manifest_json_sha256": "a" * 64, "deck_sha256": {}}
    receipt = {"source": binding, "holds_sha256": "b" * 64, "runtime": None, "raw": slugs, "projected": slugs}
    result = report.compare_evidence(receipt, source=binding, holds_sha256="b" * 64, source_raw=slugs,
                                     source_projected=slugs, observed_raw=slugs, observed_projected=slugs, runtime=None)
    result["slug"] = injected
    result["reason"] = injected
    report.emit_report(result)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["slug"] == injected
    assert lines[1] == "::notice title=Atlas runtime source::current raw_count=1 projected_count=1 source_raw_count=1 source_projected_count=1"
    invalid = copy.deepcopy(result)
    invalid["reasons"] = [injected]
    with pytest.raises(ValueError, match="invalid source report"):
        report.emit_report(invalid)
    assert capsys.readouterr().out == ""
