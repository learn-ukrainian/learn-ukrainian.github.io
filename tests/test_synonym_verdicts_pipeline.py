from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.generate_practice_deck import (
    BuildConfig,
    JsonVesumVerifier,
    ReviewedSourceAllowlist,
    build_practice_shards,
    format_a2_synonym_nomination_report,
    nominate_a2_synonym_pairs,
    validate_synonym_verdict_record,
)
from scripts.lexicon.build_synonym_verdicts_yaml import main as run_converter
from scripts.lexicon.verify_synonym_pairs import main as run_verify_script

FIXTURES = Path("tests/fixtures")
MANIFEST = FIXTURES / "lexicon-practice-manifest.json"
ALLOWLIST = FIXTURES / "lexicon-practice-reviewed-allowlist.json"
VESUM = FIXTURES / "lexicon-practice-vesum.json"


def make_mock_manifest_entry(lemma: str, url_slug: str, gloss: str, synonyms: list[str] | None = None) -> dict[str, Any]:
    entry = {
        "lemma": lemma,
        "url_slug": url_slug,
        "gloss": gloss,
        "pos": "noun",
        "primary_source": "course_vocab",
        "course_usage": [
            {
                "track": "b1",
                "slug": "some-slug"
            }
        ],
        "enrichment": {
            "cefr": {
                "level": "B1"
            }
        }
    }
    if synonyms:
        entry["sections"] = {
            "synonyms": {
                "items": synonyms
            }
        }
    return entry


def make_a2_mock_manifest_entry(
    lemma: str,
    url_slug: str,
    gloss: str,
    synonyms: list[str] | None = None,
) -> dict[str, Any]:
    entry = make_mock_manifest_entry(lemma, url_slug, gloss, synonyms)
    entry["course_usage"] = [{"track": "a2", "slug": "a2-synonyms"}]
    entry["enrichment"]["cefr"]["level"] = "A2"
    return entry


def _a2_synonym_fixture_verifier() -> JsonVesumVerifier:
    return JsonVesumVerifier(
        {
            "друг": [{"lemma": "друг", "pos": "noun"}],
            "товариш": [{"lemma": "товариш", "pos": "noun"}],
            "книга": [{"lemma": "книга", "pos": "noun"}],
            "том": [{"lemma": "том", "pos": "noun"}],
            "зошит": [{"lemma": "зошит", "pos": "noun"}],
            "папір": [{"lemma": "папір", "pos": "noun"}],
            "ручка": [{"lemma": "ручка", "pos": "noun"}],
        }
    )


def _a2_synonym_fixture_manifest() -> list[dict[str, Any]]:
    return [
        make_a2_mock_manifest_entry("друг", "druh", "friend", ["товариш"]),
        make_a2_mock_manifest_entry("товариш", "tovarysh", "comrade", ["друг"]),
        make_a2_mock_manifest_entry("книга", "knyha", "book"),
        make_a2_mock_manifest_entry("том", "tom", "volume"),
        make_a2_mock_manifest_entry("зошит", "zoshyt", "notebook"),
        make_a2_mock_manifest_entry("папір", "papir", "paper"),
        make_a2_mock_manifest_entry("ручка", "ruchka", "pen"),
    ]


def test_converter_round_trip(tmp_path: Path) -> None:
    # 1. Create a dummy JSON file representing raw verdicts from adjudication
    json_path = tmp_path / "raw_verdicts.json"
    yaml_path = tmp_path / "verdicts.yaml"

    raw_data = {
        "pairs": [
            {
                "a": "Привітання́",
                "b": "приві́т",
                "polarity": "synonym",
                "attest_sources": ["synonyms", "wiktionary"],
                "llm_verdict": "approve",
                "llm_reason": "Very close meanings.",
                "emit": True
            },
            {
                "a": "абстрактний",
                "b": "загальний",
                "polarity": "synonym",
                "attest_sources": [],
                "llm_verdict": "reject",
                "llm_reason": "Not synonyms. Abstract vs general.",
                "emit": False
            },
            # Duplicate rejected pair
            {
                "a": "абстрактний",
                "b": "загальний",
                "polarity": "synonym",
                "attest_sources": [],
                "llm_verdict": "reject",
                "llm_reason": "Different words.",
                "emit": False
            }
        ]
    }

    json_path.write_text(json.dumps(raw_data, ensure_ascii=False), encoding="utf-8")

    # Run the converter script
    sys.argv = ["", "--source", str(json_path), "--out", str(yaml_path)]
    exit_code = run_converter()
    assert exit_code == 0

    # Load generated YAML and check structure/contents
    yaml_content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert yaml_content["schema_version"] == 1
    assert yaml_content["policy"] == "emit = deterministically-attested AND llm-approved"
    assert yaml_content["judged_at"] == "2026-07-06"
    assert yaml_content["issue"] == 4504

    # Approved: normalized, sorted (a <= b), sources sorted
    assert len(yaml_content["approved"]) == 1
    approved_item = yaml_content["approved"][0]
    assert approved_item["a"] == "привіт"
    assert approved_item["b"] == "привітання"
    assert approved_item["polarity"] == "synonym"
    assert approved_item["sources"] == ["synonyms", "wiktionary"]

    # Rejected: normalized, sorted, first reason kept
    assert len(yaml_content["rejected"]) == 1
    rejected_item = yaml_content["rejected"][0]
    assert rejected_item["a"] == "абстрактний"
    assert rejected_item["b"] == "загальний"
    assert rejected_item["reason"] == "Not synonyms. Abstract vs general."


def test_builder_gating_and_fail_closed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Mock manifest entries with B1 CEFR levels and synonym relation to trigger B1+ synonym item logic
    # (Since synonyms are B1+ only and distractors must be >= 3)
    mock_manifest = [
        make_mock_manifest_entry("слово", "slovo", "word", ["термін"]),
        make_mock_manifest_entry("термін", "termin", "term", ["слово"]),
        make_mock_manifest_entry("мова", "mova", "language"),
        make_mock_manifest_entry("книга", "knyha", "book"),
        make_mock_manifest_entry("звук", "zvuk", "sound")
    ]

    allowlist = ReviewedSourceAllowlist.from_payload([])
    # Mock Vesum to verify all mock words
    vesum_mock_payload = {
        "слово": [{"lemma": "слово", "pos": "noun"}],
        "термін": [{"lemma": "термін", "pos": "noun"}],
        "мова": [{"lemma": "мова", "pos": "noun"}],
        "книга": [{"lemma": "книга", "pos": "noun"}],
        "звук": [{"lemma": "звук", "pos": "noun"}]
    }
    verifier = JsonVesumVerifier(vesum_mock_payload)

    # CASE 1: Missing verdicts file (fail-closed)
    shards_missing = build_practice_shards(
        mock_manifest,
        allowlist,
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=10),
        synonym_verdicts=None
    )
    captured = capsys.readouterr()
    # Check that a WARN was printed and no synonym items were emitted
    assert "WARN: synonym verdicts file not found; emitting no synonym items" in captured.err
    assert shards_missing["B1"]["synonym"]["synonym"] == []

    # CASE 2: Empty/unverdicted synonym_verdicts dict
    empty_verdicts = {
        "approved": [],
        "rejected": []
    }
    shards_unverdicted = build_practice_shards(
        mock_manifest,
        allowlist,
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=10),
        synonym_verdicts=empty_verdicts
    )
    assert shards_unverdicted["B1"]["synonym"]["synonym"] == []
    captured = capsys.readouterr()
    assert "1 synonym pairs awaiting verification — excluded" in captured.out

    # CASE 3: Approved verdict
    approved_verdicts = {
        "approved": [
            {
                "a": "слово",
                "b": "термін",
                "polarity": "synonym",
                "sources": ["synonyms"]
            }
        ],
        "rejected": []
    }
    shards_approved = build_practice_shards(
        mock_manifest,
        allowlist,
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=10),
        synonym_verdicts=approved_verdicts
    )
    # The synonym item should be emitted!
    b1_synonyms = shards_approved["B1"]["synonym"]["synonym"]
    assert len(b1_synonyms) > 0
    assert b1_synonyms[0]["prompt"] == "слово"
    assert b1_synonyms[0]["answer"] == "термін"

    # CASE 4: Rejected verdict
    rejected_verdicts = {
        "approved": [],
        "rejected": [
            {
                "a": "слово",
                "b": "термін",
                "polarity": "synonym",
                "reason": "Not true synonyms."
            }
        ]
    }
    shards_rejected = build_practice_shards(
        mock_manifest,
        allowlist,
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=10),
        synonym_verdicts=rejected_verdicts
    )
    assert shards_rejected["B1"]["synonym"]["synonym"] == []


def test_verify_script_new_pair_detection(tmp_path: Path) -> None:
    # 1. Write a small manifest containing a synonym pair
    manifest_path = tmp_path / "mock-manifest.json"
    verdicts_path = tmp_path / "mock-verdicts.yaml"
    out_path = tmp_path / "new_pairs.jsonl"

    mock_manifest = {
        "entries": [
            make_mock_manifest_entry("слово", "slovo", "word", ["термін"]),
            make_mock_manifest_entry("термін", "termin", "term", ["слово"]),
            make_mock_manifest_entry("мова", "mova", "language"),
            make_mock_manifest_entry("книга", "knyha", "book"),
            make_mock_manifest_entry("звук", "zvuk", "sound")
        ]
    }
    manifest_path.write_text(json.dumps(mock_manifest, ensure_ascii=False), encoding="utf-8")

    # 2. Write empty verdicts file
    yaml.dump({"approved": [], "rejected": []}, verdicts_path.open("w", encoding="utf-8"))

    # 3. Run the verify_synonym_pairs.py script
    sys.argv = ["", "--manifest", str(manifest_path), "--verdicts", str(verdicts_path), "--out", str(out_path)]

    # We run it and check if it runs successfully and writes the new pair
    exit_code = run_verify_script()
    assert exit_code == 0
    assert out_path.exists()

    # Read the output JSONL
    lines = out_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    new_pair = json.loads(lines[0])
    assert new_pair["a"] in ("слово", "термін")
    assert new_pair["b"] in ("слово", "термін")
    assert new_pair["polarity"] == "synonym"


def test_synonym_verdict_a2_exception_requires_curator() -> None:
    assert "curator" in " ".join(
        validate_synonym_verdict_record(
            {"a": "друг", "b": "товариш", "polarity": "synonym", "a2Exception": True}
        )
    )


def test_flagged_a2_synonym_pair_emits_at_a2() -> None:
    manifest = _a2_synonym_fixture_manifest()
    verifier = _a2_synonym_fixture_verifier()
    verdicts = {
        "approved": [
            {
                "a": "друг",
                "b": "товариш",
                "polarity": "synonym",
                "sources": ["synonyms"],
                "a2Exception": True,
                "curator": "fixture-2026-07-07",
            }
        ],
        "rejected": [],
    }
    shards = build_practice_shards(
        manifest,
        ReviewedSourceAllowlist.from_payload([]),
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=20),
        synonym_verdicts=verdicts,
    )
    a2_synonyms = shards["A2"]["synonym"]["synonym"]
    assert len(a2_synonyms) >= 1
    prompts = {item["prompt"] for item in a2_synonyms}
    assert "друг" in prompts or "товариш" in prompts
    assert all(item["answer"] in {"друг", "товариш"} for item in a2_synonyms)
    assert shards.get("B1", {}).get("synonym", {}).get("synonym", []) == []


def test_unflagged_both_leg_a2_synonym_pair_does_not_emit_at_a2() -> None:
    manifest = _a2_synonym_fixture_manifest()
    verifier = _a2_synonym_fixture_verifier()
    verdicts = {
        "approved": [
            {
                "a": "друг",
                "b": "товариш",
                "polarity": "synonym",
                "sources": ["synonyms"],
            }
        ],
        "rejected": [],
    }
    shards = build_practice_shards(
        manifest,
        ReviewedSourceAllowlist.from_payload([]),
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=20),
        synonym_verdicts=verdicts,
    )
    assert shards["A2"]["synonym"]["synonym"] == []
    assert shards.get("B1", {}).get("synonym", {}).get("synonym", []) == []


def test_b1_synonym_behavior_unchanged_with_a2_exception_mechanism() -> None:
    mock_manifest = [
        make_mock_manifest_entry("слово", "slovo", "word", ["термін"]),
        make_mock_manifest_entry("термін", "termin", "term", ["слово"]),
        make_mock_manifest_entry("мова", "mova", "language"),
        make_mock_manifest_entry("книга", "knyha", "book"),
        make_mock_manifest_entry("звук", "zvuk", "sound"),
    ]
    verifier = JsonVesumVerifier(
        {
            "слово": [{"lemma": "слово", "pos": "noun"}],
            "термін": [{"lemma": "термін", "pos": "noun"}],
            "мова": [{"lemma": "мова", "pos": "noun"}],
            "книга": [{"lemma": "книга", "pos": "noun"}],
            "звук": [{"lemma": "звук", "pos": "noun"}],
        }
    )
    verdicts = {
        "approved": [
            {
                "a": "слово",
                "b": "термін",
                "polarity": "synonym",
                "sources": ["synonyms"],
            }
        ],
        "rejected": [],
    }
    shards = build_practice_shards(
        mock_manifest,
        ReviewedSourceAllowlist.from_payload([]),
        verifier,
        cloze_sources=None,
        config=BuildConfig(target=10),
        synonym_verdicts=verdicts,
    )
    b1_synonyms = shards["B1"]["synonym"]["synonym"]
    assert len(b1_synonyms) >= 1
    assert any(item["prompt"] == "слово" and item["answer"] == "термін" for item in b1_synonyms)
    assert shards.get("A2", {}).get("synonym", {}).get("synonym", []) == []


def test_nominate_a2_synonym_report_lists_fixture_candidates() -> None:
    from scripts.audit.generate_practice_deck import _select_practice_lexemes

    manifest = _a2_synonym_fixture_manifest()
    verifier = _a2_synonym_fixture_verifier()
    verdicts = {
        "approved": [
            {
                "a": "друг",
                "b": "товариш",
                "polarity": "synonym",
                "sources": ["synonyms", "wiktionary"],
            }
        ],
        "rejected": [],
    }
    _lexemes_by_entry, all_lexemes, by_plain_lemma, _lexemes_by_id = _select_practice_lexemes(
        manifest,
        verifier,
        BuildConfig(target=20),
    )
    nominations = nominate_a2_synonym_pairs(manifest, verdicts, all_lexemes, by_plain_lemma)
    report = format_a2_synonym_nomination_report(nominations)
    assert "друг\tтовариш\tsynonym\tsynonyms,wiktionary\tA2\tA2" in report
    assert nominations[0]["a"] == "друг"
    assert nominations[0]["b"] == "товариш"
    assert "total\t1" in report
