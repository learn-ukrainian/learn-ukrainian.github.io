from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness.build_heldout_manifest import (
    DEFAULT_OUTPUT,
    ManifestError,
    build_manifest,
    validate_manifest,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_upstream(root: Path) -> str:
    m2_path = root / "data/gec-fluency/test/gec-fluency.test.m2"
    m2_path.parent.mkdir(parents=True)
    (root / "LICENSE").write_text("Attribution 4.0 International\n", encoding="utf-8")
    (root / "README.md").write_text("Version 2.0 released\n", encoding="utf-8")
    (root / "data/metadata.csv").write_text(
        "\n".join(
            [
                "id,author_id,is_native,region,gender,occupation,submission_type,"
                "source_language,annotator_id,partition,is_sensitive",
                "0001,train-author,1,,,,,,,train,0",
                "0002,test-author,0,,,,,ru,1 2,test,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    m2_path.write_text(
        "\n".join(
            [
                "S # 0002",
                "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0",
                "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||1",
                "",
                "S Він приймає участь у місто .",
                "A 1 3|||F/Calque|||бере участь|||REQUIRED|||-NONE-|||0",
                "A 4 5|||G/Case|||місті|||REQUIRED|||-NONE-|||0",
                "A 1 3|||F/Calque|||бере участь|||REQUIRED|||-NONE-|||1",
                "",
                "S Тут одрук .",
                "A 1 2|||Spelling|||друкарська помилка|||REQUIRED|||-NONE-|||0",
                "",
                "S # Логічно ?",
                "A -1 -1|||noop|||-NONE-|||REQUIRED|||-NONE-|||0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _config(root: Path, commit: str) -> dict:
    return {
        "schema_version": "ua_gec_heldout_config.v1",
        "manifest_id": "test-manifest",
        "upstream": {
            "repository": "https://example.com/ua-gec",
            "commit": commit,
            "version": "2.0",
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "citation": "Test citation",
            "files": {
                "LICENSE": _sha256(root / "LICENSE"),
                "README.md": _sha256(root / "README.md"),
                "data/metadata.csv": _sha256(root / "data/metadata.csv"),
                "data/gec-fluency/test/gec-fluency.test.m2": _sha256(
                    root / "data/gec-fluency/test/gec-fluency.test.m2"
                ),
            },
        },
        "predicate": {
            "partition": "test",
            "annotation_layer": "gec-fluency",
            "record_unit": "m2_tokenized_sentence",
            "included_exact_tags": ["F/Calque"],
            "included_tag_prefixes": ["G/"],
            "reference_policy": "apply_only_in_scope_edits_per_annotator",
            "selection_policy": "include_every_sentence_with_at_least_one_in_scope_edit",
            "exclusion_reason": "no_calque_or_grammar_edit",
            "arbitrary_item_quota": None,
        },
    }


def test_build_manifest_applies_quota_free_heldout_predicate(tmp_path: Path) -> None:
    upstream = tmp_path / "ua-gec"
    commit = _write_upstream(upstream)
    manifest = build_manifest(upstream, _config(upstream, commit))

    assert manifest["counts"]["upstream_test_sentences"] == 3
    assert manifest["counts"]["included_sentences"] == 1
    assert manifest["counts"]["excluded_sentences"] == 2
    assert manifest["counts"]["references"] == 2
    assert manifest["counts"]["eligible_edits"] == 3
    assert manifest["integrity"]["train_test_author_overlap"] == 0
    assert manifest["integrity"]["train_test_document_overlap"] == 0
    item = dict(zip(manifest["record_layouts"]["item"], manifest["items"][0], strict=True))
    reference = dict(zip(manifest["record_layouts"]["reference"], item["references"][0], strict=True))
    assert item["id"] == "ua-gec-test-0002-s0001"
    assert item["author_id"] == "test-author"
    assert item["eligible_tags"] == ["F/Calque", "G/Case"]
    assert reference["target"] == "Він бере участь у місті ."
    assert manifest["record_semantics"]["exclusion_reason"] == "no_calque_or_grammar_edit"
    assert "not an index into item.annotator_ids" in manifest["record_semantics"]["reference_annotator_index"]
    validate_manifest(manifest)


def test_build_manifest_fails_closed_on_provenance_drift(tmp_path: Path) -> None:
    upstream = tmp_path / "ua-gec"
    commit = _write_upstream(upstream)
    config = _config(upstream, commit)
    (upstream / "LICENSE").write_text("changed\n", encoding="utf-8")

    with pytest.raises(ManifestError, match="hash mismatch"):
        build_manifest(upstream, config)


def test_validate_manifest_detects_payload_tampering(tmp_path: Path) -> None:
    upstream = tmp_path / "ua-gec"
    commit = _write_upstream(upstream)
    manifest = build_manifest(upstream, _config(upstream, commit))
    source_index = manifest["record_layouts"]["item"].index("source")
    manifest["items"][0][source_index] = "tampered"

    with pytest.raises(ManifestError, match="source hash mismatch"):
        validate_manifest(manifest)


def test_committed_manifest_is_internally_valid_and_held_out() -> None:
    manifest = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
    validate_manifest(manifest)

    assert manifest["attribution"]["source_commit"] == "4757f72f192c4a41e4c8fb1d9690a948f87cf6d6"
    assert manifest["counts"]["upstream_test_documents"] == 166
    assert manifest["counts"]["upstream_test_authors"] == 76
    assert manifest["counts"]["upstream_test_sentences"] == 2690
    assert manifest["counts"]["included_sentences"] == 677
    assert manifest["counts"]["excluded_sentences"] == 2013
    assert manifest["predicate"]["partition"] == "test"
    assert manifest["integrity"]["train_test_author_overlap"] == 0
    assert manifest["integrity"]["train_test_document_overlap"] == 0
