from __future__ import annotations

from pathlib import Path

import yaml

from scripts.audit.wiki_completeness_gate import check_wiki_completeness


def _write_sources(wiki_path: Path, count: int = 5) -> None:
    wiki_path.with_suffix(".sources.yaml").write_text(
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


def test_b2_legacy_wiki_uses_source_readiness_not_compile_schema(tmp_path: Path) -> None:
    wiki = tmp_path / "legacy-b2.md"
    wiki.write_text(
        """
# Граматика B2: Legacy
<!-- wiki-meta slug: legacy-b2 domain: grammar/b2 tracks: [b2] -->

## Як це пояснюють у школі

Шкільний підхід подає тему через функцію в тексті й поступове редагування [S1].

## Типові помилки L2 (англомовні учні)

| Помилково | Правильно | Чому |
| --- | --- | --- |
| Хиба 1. | Норма 1. | Пояснення [S2]. |
| Хиба 2. | Норма 2. | Пояснення [S3]. |
| Хиба 3. | Норма 3. | Пояснення [S4]. |

## Деколонізаційні застереження

Не переносити російську модель керування на українські конструкції [S3].

Не подавати суржикові варіанти як нейтральну норму [S4].

## Природні приклади

Перший приклад показує норму [S5].

## Рекомендації для вправ

**Фаза 1: Розпізнавання.** Учень знаходить форму в тексті [S1].

**Фаза 2: Керована трансформація.** Учень перебудовує речення [S2].

**Фаза 3: Продукція.** Учень пише власний короткий текст [S5].
""".strip(),
        encoding="utf-8",
    )
    _write_sources(wiki)

    report = check_wiki_completeness(wiki, level="b2", slug="legacy-b2")

    assert report["verdict"] == "PASS"
    assert "vocabulary_minimum" not in report["checks"]
    assert "textbook_exercises" not in report["checks"]
    assert "decolonization_pairs" not in report["checks"]
    assert report["checks"]["exercise_progression"]["actual"] == 3
    assert report["checks"]["decolonization_guidance"]["actual"] == 2
