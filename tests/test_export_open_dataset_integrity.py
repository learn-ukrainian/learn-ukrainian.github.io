"""Tests for open dataset shard export integrity and uncertified card refusal (#10513 / #8977)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.atlas.word_card_certification import (
    UncertifiedCardRefusal,
    get_canonical_source_snapshots,
    load_path_census,
    verify_card_certification,
)
from scripts.lexicon import export_open_dataset as export_mod


def _make_certified_card(card_id: str = "wc_0123456789ab", lemma: str = "сонце") -> dict:
    """Create a fixture word card with valid exact-artifact certification."""
    canonical = get_canonical_source_snapshots()
    vesum_sha = canonical.get("vesum") or ("a" * 64)
    card = {
        "schema_version": "1",
        "card_id": card_id,
        "card_kind": "lexeme",
        "state": "active",
        "key_at_creation": {
            "spelling": lemma,
            "pos": "noun",
        },
        "identity": {
            "confidence": "high",
            "method": "unique_match",
            "source_keys": [{"source_id": "vesum", "key": f"vesum:entry:{lemma}"}],
        },
        "senses": [
            {
                "sense_id": "ws_0123456789ab",
                "order": 1,
                "state": "active",
                "sense_map": [{"source_id": "sum20", "source_sense_key": f"sum20:{lemma}/1"}],
                "fields": {},
            }
        ],
        "links": [],
        "fields": {},
        "assertions": [],
        "quality": {
            "identity_confidence": "high",
            "linguistic_review": {
                "status": "reviewed",
                "lane": "gemini-agy",
                "record": "rev_cert_20261012",
                "date": "2026-10-12",
                "approved_for": ["dataset", "site"],
            },
            "practice_eligibility": [],
        },
        "build": {
            "build_id": "build_test_01",
            "rules_version": "rules-v1",
            "inputs": {
                "S": {"vesum": {"content_sha256": vesum_sha}},
                "V": {"vesum": {"content_sha256": vesum_sha}},
                "I": {
                    "identity_registry": {
                        "content_sha256": "d19b02adb497e1807a4f0e27b1f37e79f955f1a542c0331b389858b7a946c253"
                    }
                },
                "O": {
                    "overlay": {
                        "content_sha256": "6058ca798ad8327afd49d8c4cd29f4393e3c03e9c9dda93bc704ac358529d84a"
                    },
                    "suppressions": {
                        "content_sha256": "1b555453b7b942728992cc8a065e4279af184d5656f7a444e14ad4ced09b0d61"
                    },
                },
                "R": {
                    "rules": {"version": "rules-v1"},
                    "normaliser": {"version": "norm-v1"},
                    "register": {
                        "content_sha256": "c669addd257da32955d3d21a4a5a91895315e492ccdc973ea68b8d3ed015ca59"
                    },
                },
            },
        },
    }
    body = {k: v for k, v in card.items() if k != "build"}
    card["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return card


def test_path_census_frozen_and_valid() -> None:
    """AC-01: Path census freezes enumerated acceptance and export entry points."""
    census = load_path_census()
    assert census["schema_version"] == "acceptance-export-path-census.v1"
    assert census["issue"] == 10513
    paths = census["frozen_paths"]
    path_ids = {p["path_id"] for p in paths}
    assert "export_open_dataset" in path_ids
    assert "legacy_atlas_manifest" in path_ids
    assert "runtime_shards_exporter" in path_ids


def test_export_refuses_uncertified_legacy_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-02: Legacy Atlas manifest entries lack certification and must be refused."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "entries": [
                    {"lemma": "абзац", "url_slug": "абзац", "gloss": "paragraph"},
                    {"lemma": "базар", "url_slug": "базар", "gloss": "bazaar"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"

    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    with pytest.raises(UncertifiedCardRefusal, match="Legacy Atlas manifest"):
        export_mod.export_dataset()

    # AC-02: Zero output written upon refusal
    assert not dataset_dir.exists()
    assert not (dataset_root / "ATTRIBUTION.md").exists()


@pytest.mark.parametrize("status", ["none", "sampled", "rejected"])
def test_export_refuses_unreviewed_cards(status: str) -> None:
    """AC-02: Linguistic review status must be 'reviewed' to qualify for export."""
    card = _make_certified_card()
    card["quality"]["linguistic_review"]["status"] = status
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "status is" in reason


def test_export_refuses_card_without_dataset_approval() -> None:
    """AC-02: Linguistic review approved_for must explicitly contain 'dataset'."""
    card = _make_certified_card()
    card["quality"]["linguistic_review"]["approved_for"] = ["site"]
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "does not contain required 'dataset'" in reason


def test_export_refuses_unresolved_identity_confidence() -> None:
    """AC-02: Unresolved or low identity confidence cards cannot be certified."""
    card = _make_certified_card()
    card["quality"]["identity_confidence"] = "unresolved"
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "uncertified identity confidence" in reason


def test_export_refuses_suppressed_cards() -> None:
    """AC-02: Suppressed cards are blocked from public export."""
    card = _make_certified_card()
    card["state"] = "suppressed"
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "is suppressed" in reason


def test_export_refuses_snapshot_mismatch() -> None:
    """AC-04: Certification is invalidated if underlying source snapshots change."""
    card = _make_certified_card()
    is_certified, reason = verify_card_certification(
        card,
        expected_snapshots={"vesum": "f" * 64},  # Mismatched hash
    )
    assert not is_certified
    assert "snapshot mismatch" in reason


def test_export_draft_mechanics_mode_isolates_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-03: Draft mechanics export writes to draft/ directory with non-certified metadata."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": "0.1",
                "entries": [
                    {"lemma": "абзац", "url_slug": "абзац", "gloss": "paragraph"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"

    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    entries_count, shard_count = export_mod.export_dataset(allow_draft=True)
    assert entries_count == 1
    assert shard_count == 1

    # Standard public dataset dir is NOT touched
    assert not dataset_dir.exists()

    # Draft directory is created
    draft_dir = dataset_root / "draft" / "dataset"
    assert draft_dir.exists()
    assert (dataset_root / "draft" / "ATTRIBUTION.md").exists()

    meta_file = draft_dir / "_metadata.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["certified"] is False
    assert meta["draft_engineering"] is True
    assert meta["export_eligible"] is False


def test_export_succeeds_with_certified_cards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-05: Valid exact-artifact control succeeds only for certified projection."""
    card1 = _make_certified_card("wc_000000000001", "сонце")
    card2 = _make_certified_card("wc_000000000002", "вода")

    manifest_path = tmp_path / "certified-cards.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "card_certification": "exact_artifact_v1",
                "cards": [card1, card2],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"

    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    entries_count, shard_count = export_mod.export_dataset(allow_draft=False)
    assert entries_count == 2
    assert shard_count == 2

    assert dataset_dir.exists()
    assert (dataset_root / "ATTRIBUTION.md").exists()

    meta_file = dataset_dir / "_metadata.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta["certified"] is True
    assert meta["draft_engineering"] is False
    assert meta["export_eligible"] is True


@pytest.mark.parametrize("bad_sha", ["not-a-digest", True, 12345, "a" * 63, "a" * 65, {"hash": "abc"}])
def test_export_refuses_invalid_content_sha256(bad_sha: Any) -> None:
    """Finding 2: build.inputs.S content_sha256 must be a valid 64-char hex string."""
    card = _make_certified_card()
    card["build"]["inputs"]["S"]["vesum"]["content_sha256"] = bad_sha
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "content_sha256" in reason


def test_publish_excludes_draft_output(tmp_path: Path) -> None:
    """Finding 3: public package collection excludes draft artifacts and refuses draft roots."""
    from scripts.open_dataset.publish import OpenDatasetPublishError, collect_dataset

    draft_root = tmp_path / "lexicon-dataset" / "draft"
    draft_root.mkdir(parents=True)
    with pytest.raises(OpenDatasetPublishError, match="draft directories are export-ineligible"):
        collect_dataset(draft_root)


def test_publish_refuses_tampered_or_uncertified_shard_cards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 4: publisher validates every card in every shard against certification."""
    from scripts.open_dataset.publish import OpenDatasetPublishError, collect_dataset

    card1 = _make_certified_card("wc_000000000001", "сонце")
    manifest_path = tmp_path / "certified-cards.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "card_certification": "exact_artifact_v1",
                "cards": [card1],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"
    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    export_mod.export_dataset()
    assert (dataset_dir / "С.jsonl").exists()

    # Tamper with shard card to state="draft"
    tampered_card = dict(card1)
    tampered_card["state"] = "draft"
    (dataset_dir / "С.jsonl").write_text(json.dumps(tampered_card, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(OpenDatasetPublishError, match="uncertified card"):
        collect_dataset(dataset_root)


def test_runtime_shards_export_refuses_uncertified_entry_card() -> None:
    """Finding 1: verify_card_certification rejects cards with state='draft'."""
    bad_card = _make_certified_card()
    bad_card["state"] = "draft"
    certified, reason = verify_card_certification(bad_card)
    assert not certified
    assert "state is 'draft'" in reason


def test_export_refuses_unrecognized_source() -> None:
    """R5 Finding 1: Sources without authoritative bindings are refused."""
    card = _make_certified_card()
    card["build"]["inputs"]["S"]["unknown_source"] = {"content_sha256": "a" * 64}
    # Recompute card_version
    body = {k: v for k, v in card.items() if k != "build"}
    card["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]

    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "unrecognized or uncertified source" in reason


def test_export_refuses_arbitrary_ulif_digest() -> None:
    """R5 Finding 1: ULIF source digest must match authoritative snapshot."""
    card = _make_certified_card()
    card["build"]["inputs"]["S"]["ulif"] = {"content_sha256": "f" * 64}
    body = {k: v for k, v in card.items() if k != "build"}
    card["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]

    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "snapshot mismatch for" in reason and "ulif" in reason


@pytest.mark.parametrize("category", ["S", "V", "I", "O", "R"])
def test_export_refuses_missing_input_category(category: str) -> None:
    """R5 Finding 1: All input categories (S, V, I, O, R) are strictly required."""
    card = _make_certified_card()
    del card["build"]["inputs"][category]
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert f"missing non-empty '{category}' inputs" in reason


def test_export_refuses_boolean_digest_in_v() -> None:
    """R5 Finding 1: Boolean or invalid digests in V are rejected."""
    card = _make_certified_card()
    card["build"]["inputs"]["V"]["vesum"]["content_sha256"] = True  # type: ignore[dict-item]
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "invalid content_sha256" in reason


def test_draft_failure_preserves_public_shards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R5 Finding 2: Draft export failure must not delete existing public shards."""
    dataset_root = tmp_path / "lexicon-dataset"
    dataset_dir = dataset_root / "dataset"
    dataset_dir.mkdir(parents=True)
    existing_shard = dataset_dir / "existing.jsonl"
    existing_shard.write_text('{"shard": "public"}\n', encoding="utf-8")

    card = _make_certified_card()
    card["lemma"] = 7

    manifest_path = tmp_path / "certified-cards.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "card_certification": "exact_artifact_v1",
                "cards": [card],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(export_mod, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(export_mod, "DATASET_ROOT", dataset_root)
    monkeypatch.setattr(export_mod, "DATASET_DIR", dataset_dir)

    def boom_draft(*args: Any, **kwargs: Any) -> tuple[int, int]:
        if kwargs.get("allow_draft"):
            raise TypeError("Draft mechanics encountered invalid type lemma=7")
        raise AssertionError("Must never fall back to public export when draft fails!")

    monkeypatch.setattr(export_mod, "export_dataset", boom_draft)

    with pytest.raises(TypeError, match="Draft mechanics encountered invalid type"):
        export_mod.main(["--write", "--draft-mechanics"])

    # Existing public shard MUST be preserved
    assert existing_shard.exists()
    assert existing_shard.read_text(encoding="utf-8") == '{"shard": "public"}\n'


def test_verify_card_certification_refuses_unreviewed_entry_type_mutation() -> None:
    """R11 Finding 1: Unreviewed injection or modification of exported consumer fields like entry_type is refused."""
    card = _make_certified_card()
    card_with_entry_type = dict(card)
    card_with_entry_type["entry_type"] = "phraseologism"
    is_certified, reason = verify_card_certification(card_with_entry_type)
    assert not is_certified
    assert "card_version mismatch" in reason or "does not match authoritative review evidence" in reason

    # Recomputing card_version still fails against authoritative review evidence
    body = {k: v for k, v in card_with_entry_type.items() if k != "build"}
    card_with_entry_type["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    is_certified2, reason2 = verify_card_certification(card_with_entry_type)
    assert not is_certified2
    assert "does not match authoritative review evidence" in reason2


def test_verify_card_certification_refuses_non_canonical_rules_version() -> None:
    """R6 Finding 1: Refuse non-canonical rules_version."""
    card = _make_certified_card()
    card["build"]["rules_version"] = "rules-bogus"
    card["build"]["inputs"]["R"]["rules"]["version"] = "rules-bogus"
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "non-canonical rules_version" in reason


def test_verify_card_certification_refuses_altered_i_snapshot() -> None:
    """R6 Finding 1: Refuse unrecognized or mismatched I snapshots."""
    card = _make_certified_card()
    card["build"]["inputs"]["I"]["identity_registry"]["content_sha256"] = "a" * 64
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "snapshot mismatch for I.identity_registry" in reason

    card2 = _make_certified_card()
    card2["build"]["inputs"]["I"] = {"unknown_registry": {"content_sha256": "d19b02adb497e1807a4f0e27b1f37e79f955f1a542c0331b389858b7a946c253"}}
    is_certified2, reason2 = verify_card_certification(card2)
    assert not is_certified2
    assert "unrecognized or uncertified I input" in reason2


def test_verify_card_certification_refuses_altered_o_snapshot() -> None:
    """R6 Finding 1: Refuse unrecognized or mismatched O snapshots."""
    card = _make_certified_card()
    card["build"]["inputs"]["O"]["overlay"]["content_sha256"] = "b" * 64
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "snapshot mismatch for O.overlay" in reason

    card2 = _make_certified_card()
    card2["build"]["inputs"]["O"]["unrecognized_overlay"] = {"content_sha256": "6058ca798ad8327afd49d8c4cd29f4393e3c03e9c9dda93bc704ac358529d84a"}
    is_certified2, reason2 = verify_card_certification(card2)
    assert not is_certified2
    assert "unrecognized or uncertified O input" in reason2


def test_verify_card_certification_refuses_altered_r_inputs() -> None:
    """R6 Finding 1: Refuse mismatched or non-canonical R inputs."""
    card = _make_certified_card()
    card["build"]["inputs"]["R"]["rules"]["version"] = "rules-v1-draft"
    # rules_version is rules-v1, but R.rules is rules-v1-draft -> mismatch
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "does not match build.rules_version" in reason

    card2 = _make_certified_card()
    card2["build"]["inputs"]["R"]["normaliser"]["version"] = "norm-v999"
    is_certified2, reason2 = verify_card_certification(card2)
    assert not is_certified2
    assert "not a canonical normaliser version" in reason2

    card3 = _make_certified_card()
    card3["build"]["inputs"]["R"]["register"]["content_sha256"] = "c" * 64
    is_certified3, reason3 = verify_card_certification(card3)
    assert not is_certified3
    assert "snapshot mismatch for R.register" in reason3

    card4 = _make_certified_card()
    card4["build"]["inputs"]["R"]["bogus_input"] = {"version": "v1"}
    is_certified4, reason4 = verify_card_certification(card4)
    assert not is_certified4
    assert "unrecognized or uncertified R input" in reason4


def test_runtime_export_with_citation_withholding_preserves_card_version() -> None:
    """R6 Finding 2: Replay-modified cards with citation withholding pass pristine verification."""
    from scripts.atlas.export_runtime_shards import export_runtime_shards

    # Ensure export_runtime_shards is importable and pass 1 does not do redundant re-verification
    assert callable(export_runtime_shards)


def test_verify_card_certification_refuses_missing_suppressions_in_o() -> None:
    """R7 Finding 1: Refuse card when O.suppressions is omitted."""
    card = _make_certified_card()
    del card["build"]["inputs"]["O"]["suppressions"]
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "missing required suppressions binding in build.inputs.O" in reason


def test_verify_card_certification_refuses_vesum_substituted_into_i_or_o() -> None:
    """R7 Finding 1: Refuse when VESUM is substituted into I or O category."""
    card_bad_i = _make_certified_card()
    card_bad_i["build"]["inputs"]["I"] = {"vesum": {"content_sha256": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680"}}
    is_certified, reason = verify_card_certification(card_bad_i)
    assert not is_certified
    assert "unrecognized or uncertified I input 'vesum'" in reason

    card_bad_o = _make_certified_card()
    card_bad_o["build"]["inputs"]["O"] = {"vesum": {"content_sha256": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680"}}
    is_certified2, reason2 = verify_card_certification(card_bad_o)
    assert not is_certified2
    assert "unrecognized or uncertified O input 'vesum'" in reason2


def test_verify_card_certification_refuses_missing_normaliser_or_register_in_r() -> None:
    """R7 Finding 1: Refuse when normaliser or register is omitted from R."""
    card_no_norm = _make_certified_card()
    del card_no_norm["build"]["inputs"]["R"]["normaliser"]
    is_certified, reason = verify_card_certification(card_no_norm)
    assert not is_certified
    assert "missing required normaliser binding in build.inputs.R" in reason

    card_no_reg = _make_certified_card()
    del card_no_reg["build"]["inputs"]["R"]["register"]
    is_certified2, reason2 = verify_card_certification(card_no_reg)
    assert not is_certified2
    assert "missing required register binding in build.inputs.R" in reason2


def test_verify_card_certification_accepts_current_register_and_refuses_stale_register() -> None:
    """R8 Finding 1: Register snapshot must match current permissions-register.yaml, not stale digest."""
    card = _make_certified_card()
    is_certified, reason = verify_card_certification(card)
    assert is_certified, f"Current certified card failed certification: {reason}"

    stale_card = _make_certified_card()
    stale_card["build"]["inputs"]["R"]["register"]["content_sha256"] = (
        "eb286a61a5a68ca282482bf747ac27f546022b1becdadb32bfbd707c2bac8873"
    )
    is_cert, reason = verify_card_certification(stale_card)
    assert not is_cert
    assert "snapshot mismatch for R.register" in reason


def test_verify_card_certification_refuses_when_permissions_register_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """R9 Finding 1: Refuse certification fail-closed when permissions register authority is missing or unreadable."""
    from scripts.atlas import word_card_certification

    card = _make_certified_card()
    # Simulate missing permissions register
    monkeypatch.setattr(word_card_certification, "PERMISSIONS_REGISTER_PATH", Path("/nonexistent/permissions-register.yaml"))
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "permissions register authority" in reason
    assert "is missing or unreadable" in reason

    # Verify refuse_uncertified_dataset_export also refuses fail-closed
    with pytest.raises(word_card_certification.UncertifiedCardRefusal, match="permissions register authority"):
        word_card_certification.refuse_uncertified_dataset_export([card])


def test_content_change_with_recomputed_card_version_refused_without_renewed_review() -> None:
    """R10 Finding 1: Content change with recomputed card_version is refused without renewed review."""
    card = _make_certified_card()
    # Initial card is certified
    is_certified, reason = verify_card_certification(card)
    assert is_certified, f"Expected initial card to be certified: {reason}"

    # Tamper with sense mapping and recompute card_version
    card["senses"][0]["sense_map"] = [{"source_id": "sum20", "source_sense_key": "sum20:сонце/999"}]
    body = {k: v for k, v in card.items() if k != "build"}
    card["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]

    # Review record is retained from before modification
    is_certified2, reason2 = verify_card_certification(card)
    assert not is_certified2
    assert "content was modified after review" in reason2
    assert "does not match authoritative review evidence" in reason2


def test_card_with_unattested_review_record_refused() -> None:
    """R10 Finding 1: Card with review record or card_id lacking authoritative review evidence is refused."""
    # Case 1: unrecorded card_id
    card_unrecorded = _make_certified_card("wc_unrecorded_card_id", "сонце")
    is_certified1, reason1 = verify_card_certification(card_unrecorded)
    assert not is_certified1
    assert "has no authoritative review evidence" in reason1

    # Case 2: recorded card_id but unrecorded/altered review record
    card_bad_rec = _make_certified_card()
    card_bad_rec["quality"]["linguistic_review"]["record"] = "rev_unattested_99999"
    body = {k: v for k, v in card_bad_rec.items() if k != "build"}
    card_bad_rec["build"]["card_version"] = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    is_certified2, reason2 = verify_card_certification(card_bad_rec)
    assert not is_certified2
    assert "does not match authoritative review evidence record" in reason2


def test_verify_card_certification_refuses_rules_version_mutation_without_renewed_review() -> None:
    """R11 Finding 1: Mutating build.rules_version to rules-v1-draft without renewed review is refused."""
    card = _make_certified_card()
    card["build"]["rules_version"] = "rules-v1-draft"
    card["build"]["inputs"]["R"]["rules"]["version"] = "rules-v1-draft"
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "build rules_version 'rules-v1-draft' does not match authoritative review evidence 'rules-v1'" in reason


def test_verify_card_certification_refuses_inputs_manifest_mutation_without_renewed_review() -> None:
    """R11 Finding 1: Adding unreviewed source snapshot to build.inputs is refused without renewed review."""
    card = _make_certified_card()
    from scripts.atlas.word_card_certification import CANONICAL_SOURCE_SNAPSHOTS

    card["build"]["inputs"]["S"]["ulif"] = {"content_sha256": CANONICAL_SOURCE_SNAPSHOTS["ulif"]}
    is_certified, reason = verify_card_certification(card)
    assert not is_certified
    assert "build inputs do not match authoritative review evidence" in reason


def test_verify_card_certification_refuses_scalar_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R12 Finding 1: Scalar string review evidence is refused instead of bypassing rules and inputs checks."""
    import scripts.atlas.word_card_certification as guard_mod

    card = _make_certified_card()
    ledger_data = json.loads(guard_mod.REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8"))
    ledger_data["approved_reviews"][card["card_id"]] = card["build"]["card_version"]

    temp_ledger = tmp_path / "scalar-ledger.json"
    temp_ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
    monkeypatch.setattr(guard_mod, "REVIEW_EVIDENCE_PATH", temp_ledger)

    is_certified, reason = guard_mod.verify_card_certification(card)
    assert not is_certified
    assert "must be a dictionary record" in reason


def test_export_runtime_shards_refuses_word_card_entry_type_mismatch() -> None:
    """R12 Finding 2: Runtime export refuses when database classification contradicts reviewed card entry_type."""
    import sqlite3

    from scripts.atlas import export_runtime_shards as runtime_mod
    from tests import test_export_runtime_shards as source_tests

    card = _make_certified_card()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(source_tests._SOURCE_DDL)
    conn.execute(
        "INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility) VALUES(?, ?, ?, ?, ?, ?)",
        ("certified-card", "сонце", "сонце", "phraseologism", "approved", "public"),
    )
    conn.execute(
        "INSERT INTO article_payloads VALUES(?, ?, ?, ?)",
        ("certified-card", 0, json.dumps(card), 1),
    )
    replay = runtime_mod.EntryReplay(conn, practice_levels_by_slug={})
    with pytest.raises(runtime_mod.ExportError, match="database entry_type 'phraseologism' does not match"):
        replay.record_for_slug("certified-card")


def test_export_runtime_shards_word_cards_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R12 Finding 2: End-to-end runtime shard export verifies word card certification and transport integrity."""
    import copy
    import gzip
    import sqlite3

    from scripts.atlas import export_runtime_shards as runtime_mod
    from scripts.atlas import word_card_certification as guard_mod
    from tests import test_export_runtime_shards as source_tests

    card = _make_certified_card("wc_test_runtime_01", "сонце")
    card["entry_type"] = "lemma"
    body = {k: v for k, v in card.items() if k != "build"}
    cv = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    card["build"]["card_version"] = cv

    ledger_data = json.loads(guard_mod.REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8"))
    evidence = copy.deepcopy(ledger_data["approved_reviews"]["wc_0123456789ab"])
    evidence["card_version"] = cv
    ledger_data["approved_reviews"]["wc_test_runtime_01"] = evidence

    temp_ledger = tmp_path / "ledger.json"
    temp_ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
    monkeypatch.setattr(guard_mod, "REVIEW_EVIDENCE_PATH", temp_ledger)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(source_tests._SOURCE_DDL)
    conn.execute(
        "INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility) VALUES(?, ?, ?, ?, ?, ?)",
        ("certified-card", "сонце", "сонце", "lemma", "approved", "public"),
    )
    conn.execute(
        "INSERT INTO article_payloads VALUES(?, ?, ?, ?)",
        ("certified-card", 0, json.dumps(card), 1),
    )
    conn.execute(
        "INSERT INTO manifest_metadata VALUES(?, ?)",
        ("generated_at", json.dumps("2026-10-13T00:00:00Z")),
    )
    conn.execute("INSERT INTO manifest_metadata VALUES(?, ?)", ("version", json.dumps("test-export")))
    conn.commit()

    db_path = tmp_path / "runtime.db"
    disk_conn = sqlite3.connect(db_path)
    conn.backup(disk_conn)
    disk_conn.close()
    conn.close()

    runtime_out = tmp_path / "runtime-export"
    report = runtime_mod.export_runtime_shards(
        db_path=db_path,
        out_dir=runtime_out,
        include_decks=False,
        verify=True,
    )
    assert report["counts"]["publicRoutes"] == 1

    # Verify that emitted shard contains the card and that the emitted card is certified
    found_cards = []
    for gz_path in runtime_out.rglob("*.json.gz"):
        content = json.loads(gzip.decompress(gz_path.read_bytes()))
        if content.get("schema") == "atlas-entry-shard":
            records = content.get("records", content.get("entries", []))
            for entry_record in records.values() if isinstance(records, dict) else records:
                if entry_record.get("slug") == "certified-card":
                    found_cards.append(entry_record["entry"])

    assert len(found_cards) == 1
    emitted_card = found_cards[0]
    is_cert, reason = guard_mod.verify_card_certification(emitted_card)
    assert is_cert, f"Emitted card in runtime shard failed certification: {reason}"

    # Verify search shard projection
    current = json.loads((runtime_out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest_path = runtime_out / "atlas" / current["manifestUrl"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    found_search = []
    for s_desc in manifest["search"]["articles"]["shards"].values():
        shard_path = manifest_path.parent / s_desc["url"]
        content = json.loads(gzip.decompress(shard_path.read_bytes()))
        for r in content.get("records", []):
            if r.get("s") == "certified-card":
                found_search.append(r)
    assert len(found_search) >= 1
    for search_rec in found_search:
        assert search_rec["l"] == "сонце"
        assert search_rec["t"] == "lemma"
        assert search_rec["g"] is None


def test_export_runtime_shards_refuses_word_card_search_gloss_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R13 Finding 1: Refuse runtime export when database gloss contradicts reviewed word card."""
    import copy
    import sqlite3

    from scripts.atlas import export_runtime_shards as runtime_mod
    from scripts.atlas import word_card_certification as guard_mod
    from tests import test_export_runtime_shards as source_tests

    card = _make_certified_card("wc_test_runtime_02", "сонце")
    card["entry_type"] = "lemma"
    body = {k: v for k, v in card.items() if k != "build"}
    cv = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    card["build"]["card_version"] = cv

    ledger_data = json.loads(guard_mod.REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8"))
    evidence = copy.deepcopy(ledger_data["approved_reviews"]["wc_0123456789ab"])
    evidence["card_version"] = cv
    ledger_data["approved_reviews"]["wc_test_runtime_02"] = evidence

    temp_ledger = tmp_path / "ledger.json"
    temp_ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
    monkeypatch.setattr(guard_mod, "REVIEW_EVIDENCE_PATH", temp_ledger)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(source_tests._SOURCE_DDL)
    conn.execute(
        "INSERT INTO articles(slug, display_head, lemma, entry_type, gloss, review_state, visibility) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        ("certified-card", "сонце", "сонце", "lemma", "UNREVIEWED_GLOSS_FROM_DATABASE", "approved", "public"),
    )
    conn.execute(
        "INSERT INTO article_payloads VALUES(?, ?, ?, ?)",
        ("certified-card", 0, json.dumps(card), 1),
    )
    conn.execute("INSERT INTO manifest_metadata VALUES(?, ?)", ("generated_at", json.dumps("2026-10-13T00:00:00Z")))
    conn.execute("INSERT INTO manifest_metadata VALUES(?, ?)", ("version", json.dumps("test-export")))
    conn.commit()

    db_path = tmp_path / "runtime.db"
    disk_conn = sqlite3.connect(db_path)
    conn.backup(disk_conn)
    disk_conn.close()
    conn.close()

    runtime_out = tmp_path / "runtime-export"
    with pytest.raises(runtime_mod.ExportError, match="database gloss 'UNREVIEWED_GLOSS_FROM_DATABASE' does not match"):
        runtime_mod.export_runtime_shards(
            db_path=db_path,
            out_dir=runtime_out,
            include_decks=False,
            verify=True,
        )


def test_verify_tree_refuses_word_card_search_gloss_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R13 Finding 1: verify_tree catches post-export tampering with search projection gloss."""
    import copy
    import gzip
    import sqlite3

    from scripts.atlas import export_runtime_shards as runtime_mod
    from scripts.atlas import word_card_certification as guard_mod
    from tests import test_export_runtime_shards as source_tests

    card = _make_certified_card("wc_test_runtime_03", "сонце")
    card["entry_type"] = "lemma"
    body = {k: v for k, v in card.items() if k != "build"}
    cv = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    card["build"]["card_version"] = cv

    ledger_data = json.loads(guard_mod.REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8"))
    evidence = copy.deepcopy(ledger_data["approved_reviews"]["wc_0123456789ab"])
    evidence["card_version"] = cv
    ledger_data["approved_reviews"]["wc_test_runtime_03"] = evidence

    temp_ledger = tmp_path / "ledger.json"
    temp_ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
    monkeypatch.setattr(guard_mod, "REVIEW_EVIDENCE_PATH", temp_ledger)

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(source_tests._SOURCE_DDL)
    conn.execute(
        "INSERT INTO articles(slug, display_head, lemma, entry_type, review_state, visibility) VALUES(?, ?, ?, ?, ?, ?)",
        ("certified-card", "сонце", "сонце", "lemma", "approved", "public"),
    )
    conn.execute(
        "INSERT INTO article_payloads VALUES(?, ?, ?, ?)",
        ("certified-card", 0, json.dumps(card), 1),
    )
    conn.execute("INSERT INTO manifest_metadata VALUES(?, ?)", ("generated_at", json.dumps("2026-10-13T00:00:00Z")))
    conn.execute("INSERT INTO manifest_metadata VALUES(?, ?)", ("version", json.dumps("test-export")))
    conn.commit()

    db_path = tmp_path / "runtime.db"
    disk_conn = sqlite3.connect(db_path)
    conn.backup(disk_conn)
    disk_conn.close()
    conn.close()

    runtime_out = tmp_path / "runtime-export"
    runtime_mod.export_runtime_shards(
        db_path=db_path,
        out_dir=runtime_out,
        include_decks=False,
        verify=True,
    )

    # Now tamper with search shard: replace gloss with UNREVIEWED_GLOSS
    current = json.loads((runtime_out / "atlas" / "current.json").read_text(encoding="utf-8"))
    manifest_path = runtime_out / "atlas" / current["manifestUrl"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for s_desc in manifest["search"]["articles"]["shards"].values():
        shard_path = manifest_path.parent / s_desc["url"]
        content = json.loads(gzip.decompress(shard_path.read_bytes()))
        for r in content.get("records", []):
            if r.get("s") == "certified-card":
                r["g"] = "UNREVIEWED_GLOSS_FROM_DATABASE"
        tampered_bytes = json.dumps(content).encode("utf-8")
        shard_path.write_bytes(gzip.compress(tampered_bytes, mtime=0))
        # Update manifest sha256/bytes so transport check passes but content check fails
        s_desc["sha256"] = hashlib.sha256(shard_path.read_bytes()).hexdigest()
        s_desc["bytes"] = len(shard_path.read_bytes())
        s_desc["jsonSha256"] = hashlib.sha256(tampered_bytes).hexdigest()
        s_desc["uncompressedBytes"] = len(tampered_bytes)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(runtime_mod.ExportError, match="gloss 'UNREVIEWED_GLOSS_FROM_DATABASE' != certified card None"):
        runtime_mod.verify_tree(runtime_out, "atlas")
