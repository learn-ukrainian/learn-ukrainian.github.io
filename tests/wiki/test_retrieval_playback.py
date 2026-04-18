import sys
from pathlib import Path

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
        "milozvuchnist": {
            "present_in_full_corpus": True,
            "corpus_match_count": 2,
            "sample_chunk_ids": ["milozvuchnist-1"],
            "sample_grades": ["5"],
        },
        "g_ge_history": {
            "present_in_full_corpus": False,
            "corpus_match_count": 0,
            "sample_chunk_ids": [],
            "sample_grades": [],
        },
    }

    def fake_query(_conn, variants):
        normalized = {retrieval_playback.normalize_text(v) for v in variants}
        if retrieval_playback.normalize_text("букви — це умовні знаки, які позначають звуки мови") in normalized:
            return corpus_hits["sound_before_letter"]
        if retrieval_playback.normalize_text("голосні звуки утворюються за допомогою голосу") in normalized:
            return corpus_hits["vowel_consonant_definition"]
        if retrieval_playback.normalize_text("милозвучність") in normalized:
            return corpus_hits["milozvuchnist"]
        return corpus_hits["g_ge_history"]

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
    assert result["concepts"]["milozvuchnist"]["present_in_full_corpus"] is True
    assert result["concepts"]["g_ge_history"]["present_in_full_corpus"] is False
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
    scenarios = [
        (7, 9, "writer_bottleneck"),
        (6, 7, "retrieval_bottleneck"),
        (2, 6, "corpus_bottleneck"),
        (6, 6, "corpus_bottleneck"),
        (10, 10, "writer_bottleneck"),
    ]

    for returned_present, full_present, expected in scenarios:
        concepts = {}
        for index, concept in enumerate(retrieval_playback.TARGET_CONCEPTS):
            concepts[concept] = {
                "present_in_returned_41": index < returned_present,
                "present_in_full_corpus": index < full_present,
            }
        assert retrieval_playback.diagnose_verdict(concepts) == expected
