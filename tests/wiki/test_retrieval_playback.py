import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.diagnostics import retrieval_playback


def _chunk(chunk_id: str, text: str, grade: str = "2") -> dict[str, str]:
    return {
        "chunk_id": chunk_id,
        "text": text,
        "grade": grade,
        "title": f"Chunk {chunk_id}",
        "author": "test",
    }


def test_run_diagnostic_matches_concepts_with_mocked_search(tmp_path, monkeypatch):
    discovery_path = tmp_path / "discovery.yaml"
    discovery_path.write_text(
        yaml.safe_dump(
            {
                "query_keywords": [
                    "Sounds, Letters, and Hello",
                    "Звуки і літери",
                    "Пояснюємо, що букви — це умовні знаки",
                    "пом'якшує",
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("sources: []\n", encoding="utf-8")

    chunks = [
        _chunk("syll", "У слові стільки складів, скільки голосних звуків."),
        _chunk("larynx", "Покладіть пальці на гортань і відчуйте напруження голосових зв'язок."),
        _chunk("voice", "Дзвінкі приголосні звуки в кінці слова і складу вимовляються дзвінко."),
        _chunk("semiw", "Звук [в] треба вимовляти ніби короткий голосний [ў]; у кінці слова: лев [леў]."),
        _chunk("yi", "Буква ї завжди позначає два звуки — [йі]."),
        _chunk("iotated", "Після приголосних букви я, ю, є позначають один звук і пом’якшують попередній приголосний."),
    ]

    monkeypatch.setattr(retrieval_playback, "DISCOVERY_PATH", discovery_path)
    monkeypatch.setattr(retrieval_playback, "SOURCE_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(retrieval_playback, "search_textbooks", lambda *args, **kwargs: chunks)

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    corpus_hits = {
        "sound_before_letter": {
            "present_in_full_corpus": True,
            "corpus_match_count": 3,
            "sample_chunk_ids": ["sound-before-letter-1"],
            "sample_grades": ["1"],
        },
        "vowel_consonant_definition": {
            "present_in_full_corpus": True,
            "corpus_match_count": 4,
            "sample_chunk_ids": ["vowel-definition-1"],
            "sample_grades": ["2"],
        },
        "milozvuchnist_v_to_w_gloss": {
            "present_in_full_corpus": True,
            "corpus_match_count": 2,
            "sample_chunk_ids": ["milozvuchnist-1"],
            "sample_grades": ["5"],
        },
        # Default: not found in corpus. Used for any concept not explicitly
        # mapped above. After #1340 dropped g_ge_history this is just a
        # safety net; no real concept is expected to hit it under this
        # fixture. Kept as the default branch so future concept additions
        # don't silently inherit "found in corpus".
        "default_not_in_corpus": {
            "present_in_full_corpus": False,
            "corpus_match_count": 0,
            "sample_chunk_ids": [],
            "sample_grades": [],
        },
    }

    def fake_query(_conn, variants):
        normalized = {
            retrieval_playback.normalize_text(token)
            for variant in variants
            for token in retrieval_playback._flatten_variant_tokens(variant)
        }
        if retrieval_playback.normalize_text("букви — це умовні знаки, які позначають звуки мови") in normalized:
            return corpus_hits["sound_before_letter"]
        if retrieval_playback.normalize_text("голосні звуки утворюються за допомогою голосу") in normalized:
            return corpus_hits["vowel_consonant_definition"]
        # Variants for milozvuchnist_v_to_w_gloss now emit the root token
        # `милозвучн` (not the full noun) so a Grade 10 generic milozvuchnist
        # chapter no longer satisfies the concept on its own — the all_of
        # logic also requires в→[ў]/лев/був co-occurrence.
        if retrieval_playback.normalize_text("милозвучн") in normalized:
            return corpus_hits["milozvuchnist_v_to_w_gloss"]
        return corpus_hits["default_not_in_corpus"]

    monkeypatch.setattr(retrieval_playback.sqlite3, "connect", lambda *args, **kwargs: FakeConnection())
    monkeypatch.setattr(retrieval_playback, "query_full_corpus_for_concept", fake_query)

    result = retrieval_playback.run_diagnostic("a1", "sounds-letters-and-hello")

    assert result["returned_chunk_count"] == 6
    assert set(result["retrieval_query_keywords"]) == {
        "букви",
        "звуки",
        "знаки",
        "літери",
        "пояснюємо",
        "пом'якшує",
        "умовні",
    }
    assert result["concepts"]["syllable_count_rule"]["chunks_containing"] == ["syll"]
    assert result["concepts"]["larynx_touch_exercise"]["chunks_containing"] == ["larynx"]
    assert result["concepts"]["ya_yu_ye_dual"]["chunks_containing"] == ["iotated"]
    assert result["concepts"]["sound_before_letter"]["present_in_full_corpus"] is True
    assert result["concepts"]["vowel_consonant_definition"]["present_in_full_corpus"] is True
    assert result["concepts"]["milozvuchnist_v_to_w_gloss"]["present_in_full_corpus"] is True
    # #1340: g_ge_history removed from A1 scope (Grade 10/11 material).
    # Guard against accidental re-introduction.
    assert "g_ge_history" not in result["concepts"]
    assert result["verdict"] == "retrieval_bottleneck"


def test_match_returned_concepts_normalizes_apostrophes():
    chunks = [
        _chunk(
            "apostrophe",
            "Після приголосних букви я, ю, є позначають один звук і пом’якшують попередній приголосний.",
        )
    ]

    results = retrieval_playback.match_returned_concepts(chunks)

    assert results["ya_yu_ye_dual"]["present_in_returned_41"] is True
    assert results["ya_yu_ye_dual"]["chunks_containing"] == ["apostrophe"]


def test_diagnose_verdict_fixture_scenarios():
    # Verdict thresholds are absolute counts in diagnose_verdict (>= 7),
    # which aligns with ~70% coverage at the current 9-concept scope.
    # Scenarios use counts that stay valid as the scope shrinks/grows;
    # the final case uses TOTAL_CONCEPTS to test the "everything covered"
    # extreme without hardcoding.
    total = retrieval_playback.TOTAL_CONCEPTS
    scenarios = [
        (7, total, "writer_bottleneck"),
        (6, 7, "retrieval_bottleneck"),
        (2, 6, "corpus_bottleneck"),
        (6, 6, "corpus_bottleneck"),
        (total, total, "writer_bottleneck"),
    ]

    for returned_present, full_present, expected in scenarios:
        concepts = {}
        for index, concept in enumerate(retrieval_playback.TARGET_CONCEPTS):
            concepts[concept] = {
                "present_in_returned_41": index < returned_present,
                "present_in_full_corpus": index < full_present,
            }
        assert retrieval_playback.diagnose_verdict(concepts) == expected, (
            f"failed for (returned={returned_present}, full={full_present}, total={total})"
        )


def test_run_diagnostic_modern_dense_uses_search_sources(tmp_path, monkeypatch):
    discovery_path = tmp_path / "discovery.yaml"
    discovery_path.write_text(
        yaml.safe_dump(
            {
                "query_keywords": [
                    "Звуки і літери",
                    "Пояснюємо, що букви — це умовні знаки",
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("sources: []\n", encoding="utf-8")

    calls: list[dict[str, object]] = []

    def fake_search_sources(query, *, track, strategy, limit):
        calls.append(
            {
                "query": query,
                "track": track,
                "strategy": strategy,
                "limit": limit,
            }
        )
        return [
            {
                "unit_key": "textbook_sections:77",
                "chunk_id": "S77",
                "text": "Букви — це умовні знаки, які позначають звуки мови.",
                "grade": "2",
                "source_file": "source-77",
                "author": "author-77",
                "title": "Section 77",
                "final_score": 0.91,
                "corpus": "textbook_sections",
                "source_type": "textbook",
            }
        ]

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_query(_conn, variants):
        normalized = {
            retrieval_playback.normalize_text(token)
            for variant in variants
            for token in retrieval_playback._flatten_variant_tokens(variant)
        }
        if retrieval_playback.normalize_text("букви — це умовні знаки, які позначають звуки мови") in normalized:
            return {
                "present_in_full_corpus": True,
                "corpus_match_count": 1,
                "sample_chunk_ids": ["sound-before-letter-1"],
                "sample_grades": ["2"],
            }
        return {
            "present_in_full_corpus": False,
            "corpus_match_count": 0,
            "sample_chunk_ids": [],
            "sample_grades": [],
        }

    monkeypatch.setattr(retrieval_playback, "DISCOVERY_PATH", discovery_path)
    monkeypatch.setattr(retrieval_playback, "SOURCE_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(retrieval_playback, "search_sources", fake_search_sources)
    monkeypatch.setattr(retrieval_playback.sqlite3, "connect", lambda *args, **kwargs: FakeConnection())
    monkeypatch.setattr(retrieval_playback, "query_full_corpus_for_concept", fake_query)

    result = retrieval_playback.run_diagnostic(
        "a1",
        "sounds-letters-and-hello",
        strategy=retrieval_playback.STRATEGY_MODERN,
    )

    assert calls == [
        {
            "query": discovery_path,
            "track": "a1",
            "strategy": "unified_dense",
            "limit": 40,
        }
    ]
    assert result["strategy"] == retrieval_playback.STRATEGY_MODERN
    assert result["returned_chunk_count"] == 1
    assert result["returned_chunks"][0]["chunk_id"] == "S77"
    assert result["returned_chunks"][0]["source_file"] == "source-77"
    assert result["returned_chunks"][0]["score"] == 0.91
    assert result["concepts"]["sound_before_letter"]["present_in_returned_41"] is True


def test_write_comparison_report_reads_both_outputs(tmp_path, monkeypatch):
    diagnostics_dir = tmp_path / "diagnostics"
    playback_json = diagnostics_dir / "a1-sounds-letters-playback.json"
    playback_modern_json = diagnostics_dir / "a1-sounds-letters-playback.modern.json"
    playback_md = diagnostics_dir / "a1-sounds-letters-playback.md"
    comparison_md = diagnostics_dir / "a1-sounds-letters-comparison.md"

    monkeypatch.setattr(retrieval_playback, "PLAYBACK_OUTPUT_PATH", playback_json)
    monkeypatch.setattr(retrieval_playback, "PLAYBACK_MARKDOWN_OUTPUT_PATH", playback_md)
    monkeypatch.setattr(retrieval_playback, "COMPARISON_OUTPUT_PATH", comparison_md)
    monkeypatch.setattr(retrieval_playback, "PROJECT_ROOT", tmp_path)

    def make_result(strategy: str, hit_count: int) -> dict[str, object]:
        concepts = {}
        for index, concept in enumerate(retrieval_playback.TARGET_CONCEPTS):
            hit = index < hit_count
            concepts[concept] = {
                "present_in_returned_41": hit,
                "present_in_full_corpus": hit,
            }
        return {
            "track": "a1",
            "slug": "sounds-letters-and-hello",
            "strategy": strategy,
            "concepts": concepts,
        }

    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    playback_json.write_text(
        json.dumps(make_result(retrieval_playback.STRATEGY_LEGACY, 6), ensure_ascii=False),
        encoding="utf-8",
    )
    playback_modern_json.write_text(
        json.dumps(make_result(retrieval_playback.STRATEGY_MODERN, 8), ensure_ascii=False),
        encoding="utf-8",
    )

    comparison_path, verdict, legacy_present, modern_present = retrieval_playback.write_comparison_report()

    report = comparison_md.read_text(encoding="utf-8")
    total = retrieval_playback.TOTAL_CONCEPTS
    assert comparison_path == comparison_md
    assert verdict == "PASS"
    assert legacy_present == 6
    assert modern_present == 8
    assert f"legacy_concepts_present: 6/{total}" in report
    assert f"modern_concepts_present: 8/{total}" in report
    assert "Verdict: PASS" in report
    assert "| syllable_count_rule | yes | yes |" in report


def test_write_comparison_report_requires_both_outputs(tmp_path, monkeypatch):
    diagnostics_dir = tmp_path / "diagnostics"
    playback_json = diagnostics_dir / "a1-sounds-letters-playback.json"
    playback_md = diagnostics_dir / "a1-sounds-letters-playback.md"
    comparison_md = diagnostics_dir / "a1-sounds-letters-comparison.md"

    monkeypatch.setattr(retrieval_playback, "PLAYBACK_OUTPUT_PATH", playback_json)
    monkeypatch.setattr(retrieval_playback, "PLAYBACK_MARKDOWN_OUTPUT_PATH", playback_md)
    monkeypatch.setattr(retrieval_playback, "COMPARISON_OUTPUT_PATH", comparison_md)
    monkeypatch.setattr(retrieval_playback, "PROJECT_ROOT", tmp_path)

    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    playback_json.write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit, match="run --strategy legacy_chunk and --strategy modern_dense first"):
        retrieval_playback.write_comparison_report()
