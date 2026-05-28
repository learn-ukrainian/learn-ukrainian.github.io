from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.audit.wiki_completeness_gate import (
    check_wiki_completeness,
    thresholds_for_level,
)

ROOT = Path(__file__).resolve().parents[2]


def _pass_verify_quote(source_id: str, quote: str, source: dict[str, Any]) -> dict[str, Any]:
    return {"verdict": "PASS", "source_id": source_id, "quote": quote, "source": dict(source)}


def _write_sources(path: Path, count: int) -> None:
    path.with_suffix(".sources.yaml").write_text(
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "id": f"S{index}",
                        "file": f"chunk-{index}",
                        "type": "textbook",
                        "title": f"Source {index}",
                    }
                    for index in range(1, count + 1)
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _full_wiki(
    tmp_path: Path,
    *,
    vocab_count: int = 20,
    step_count: int = 5,
    l2_rows: int = 3,
    decolonization_pairs: int = 1,
    exercise_count: int = 3,
    citation_count: int = 5,
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    vocab = "\n".join(f"- слово{index} (★★★) — word {index}." for index in range(vocab_count))
    steps = "\n\n".join(f"Крок {index}: Послідовність {index} [S1]." for index in range(1, step_count + 1))
    l2 = "\n".join(
        f"| Хиба{index}а. / Хиба{index}б. | Правильно{index}. | Пояснення [S2]. |"
        for index in range(1, l2_rows + 1)
    )
    pairs = ", ".join(f"«правильно{index}» (не «помилка{index}»)" for index in range(1, decolonization_pairs + 1))
    exercises = "\n\n".join(
        f"**Вправа {index}: Формат**\n- *Chunk ID:* chunk-{index} [S{index}]\n- *Формат:* Вправа."
        for index in range(1, exercise_count + 1)
    )
    citations = " ".join(f"Речення з джерелом [S{index}]." for index in range(1, citation_count + 1))
    wiki = tmp_path / "fixture.md"
    wiki.write_text(
        f"""# Fixture

<!-- wiki-meta
slug: fixture
-->

## Методичний підхід

Методика повна. {citations}

## Послідовність введення

{steps}

## Типові помилки L2 (англомовні учні)

| ❌ Помилково | ✅ Правильно | Чому |
|---|---|---|
{l2}

## Деколонізаційні застереження

Використовуємо {pairs}.

## Словниковий мінімум

{vocab}

## Приклади з підручників

{exercises}
""",
        encoding="utf-8",
    )
    _write_sources(wiki, citation_count)
    return wiki


def test_m20_my_morning_wiki_passes_completeness_gate() -> None:
    report = check_wiki_completeness(
        ROOT / "wiki/pedagogy/a1/my-morning.md",
        level="a1",
        slug="my-morning",
        verify_quote_fn=_pass_verify_quote,
    )

    assert report["verdict"] == "PASS"
    assert report["checks"]["vocabulary_minimum"]["actual"] == 21
    assert report["checks"]["l2_errors"]["actual"] == 6
    assert report["checks"]["decolonization_pairs"]["actual"] == 3
    assert report["checks"]["textbook_exercises"]["actual"] == 5
    assert report["checks"]["chunk_citations_spot_check"]["detail"] == "3/3 verify_quote returned PASS"


def test_synthetic_thin_wiki_fails_with_specific_check_name(tmp_path: Path) -> None:
    wiki = _full_wiki(tmp_path, vocab_count=18, step_count=3, l2_rows=3)

    report = check_wiki_completeness(
        wiki,
        level="a1",
        slug="fixture",
        verify_quote_fn=_pass_verify_quote,
    )

    assert report["verdict"] == "FAIL"
    assert report["checks"]["sequence_steps"]["verdict"] == "FAIL"
    assert report["checks"]["sequence_steps"]["actual"] == 3
    assert report["checks"]["vocabulary_minimum"]["verdict"] == "FAIL"
    assert "Послідовність введення" in report["diagnostic"]


def test_per_level_threshold_application_and_seminar_deferred(tmp_path: Path) -> None:
    assert thresholds_for_level("a1")["vocabulary_minimum"] == 20
    assert thresholds_for_level("b1")["vocabulary_minimum"] == 50
    with pytest.raises(NotImplementedError, match="Seminar wiki completeness checks are deferred"):
        thresholds_for_level("hist")

    wiki = _full_wiki(tmp_path, vocab_count=49, decolonization_pairs=2, citation_count=5)
    report = check_wiki_completeness(
        wiki,
        level="b1",
        slug="fixture",
        verify_quote_fn=_pass_verify_quote,
    )
    assert report["checks"]["vocabulary_minimum"] == {
        "verdict": "FAIL",
        "actual": 49,
        "minimum": 50,
        "detail": "wiki vocabulary-minimum lemma(s) found.",
    }
    assert report["checks"]["chunk_citations_spot_check"]["detail"] == "5/5 verify_quote returned PASS"


def test_distractor_inventory_counts_l2_and_decolonization_together(tmp_path: Path) -> None:
    wiki = _full_wiki(
        tmp_path,
        l2_rows=2,
        decolonization_pairs=2,
        vocab_count=20,
        exercise_count=3,
        citation_count=3,
    )

    report = check_wiki_completeness(
        wiki,
        level="a1",
        slug="fixture",
        verify_quote_fn=_pass_verify_quote,
    )

    assert report["checks"]["distractor_inventory"]["actual"] == 6
    assert report["checks"]["distractor_inventory"]["verdict"] == "PASS"


def test_spot_check_sample_size_is_three_for_a1_and_five_for_b1(tmp_path: Path) -> None:
    calls: list[str] = []

    def recorder(source_id: str, quote: str, source: dict[str, Any]) -> dict[str, Any]:
        calls.append(source_id)
        return {"verdict": "PASS"}

    a1_wiki = _full_wiki(tmp_path / "a1", citation_count=5)
    a1_report = check_wiki_completeness(a1_wiki, level="a1", slug="fixture", verify_quote_fn=recorder)
    assert a1_report["checks"]["chunk_citations_spot_check"]["detail"] == "3/3 verify_quote returned PASS"
    assert calls == ["S1", "S2", "S3"]

    calls.clear()
    b1_wiki = _full_wiki(tmp_path / "b1", vocab_count=50, decolonization_pairs=2, l2_rows=4, citation_count=5)
    b1_report = check_wiki_completeness(b1_wiki, level="b1", slug="fixture", verify_quote_fn=recorder)
    assert b1_report["checks"]["chunk_citations_spot_check"]["detail"] == "5/5 verify_quote returned PASS"
    assert calls == ["S1", "S2", "S3", "S4", "S5"]


def test_missing_sections_fail_with_named_checks(tmp_path: Path) -> None:
    wiki = tmp_path / "missing.md"
    wiki.write_text("# Missing sections\n\nNo required sections.\n", encoding="utf-8")

    report = check_wiki_completeness(
        wiki,
        level="a1",
        slug="missing",
        verify_quote_fn=_pass_verify_quote,
    )

    assert report["verdict"] == "FAIL"
    assert {
        "methodology",
        "sequence_steps",
        "l2_errors",
        "decolonization_pairs",
        "vocabulary_minimum",
        "textbook_exercises",
        "distractor_inventory",
        "chunk_citations_spot_check",
    } == {name for name, check in report["checks"].items() if check["verdict"] == "FAIL"}
