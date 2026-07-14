from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.lexicon import content_lexicon_reconciler as reconciler

requires_vesum_db = pytest.mark.skipif(
    not Path("data/vesum.db").exists()
    or Path("data/vesum.db").stat().st_size < 1_000_000,
    reason=(
        "requires the full VESUM data/vesum.db; CI may omit or stub it; "
        "build a verified shadow with scripts/rag/build_vesum_shadow.py and provision the required DB"
    ),
)


def test_mdx_stripping_removes_non_prose_regions_and_keeps_cyrillic() -> None:
    mdx = """---
title: "Не брати"
description: "Компонент теж не брати"
---

import Quiz from '@site/src/components/Quiz';

English rail: this sentence should not contribute Cyrillic tokens.

```uk
привіт код
```

<Quiz client:only='react' questions={JSON.parse(`[{"question": "компонент"}]`)} />

<PrimaryReading>
М'який пʼять п’ять дівка-бранка.
[читати більше](https://example.com/український-шлях)
</PrimaryReading>
"""

    prose = reconciler.strip_mdx_to_prose(mdx)
    tokens = reconciler.extract_ukrainian_tokens(prose)

    assert tokens == [
        "м'який",
        "п'ять",
        "п'ять",
        "дівка-бранка",
        "читати",
        "більше",
    ]


def test_tokenization_preserves_word_internal_apostrophes_and_hyphens() -> None:
    tokens = reconciler.extract_ukrainian_tokens(
        "П'ять пʼять п’ять дівка-бранка 2026 слово—слово край-"
    )

    assert tokens == [
        "п'ять",
        "п'ять",
        "п'ять",
        "дівка-бранка",
        "слово",
        "слово",
        "край",
    ]


def test_reconcile_content_computes_delta_with_fake_lemmatizer_and_manifest(
    tmp_path: Path,
) -> None:
    mdx_path = tmp_path / "module.mdx"
    mdx_path.write_text("Коти замки м'яч хиба.", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, ["кіт"])

    def fake_vesum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        matches = {
            "коти": [{"lemma": "кіт", "pos": "noun", "tags": "anim:p:v_naz"}],
            "замки": [
                {"lemma": "замка", "pos": "noun", "tags": "inanim:p:v_naz"},
                {"lemma": "замок", "pos": "noun", "tags": "inanim:p:v_naz"},
            ],
            "м'яч": [{"lemma": "м'яч", "pos": "noun", "tags": "inanim:m:v_naz"}],
            "хиба": [],
        }
        return {word: matches.get(word, []) for word in words}

    result = reconciler.reconcile_content(
        [mdx_path],
        manifest_path=manifest_path,
        vesum_lookup=fake_vesum,
    )
    payload = reconciler.result_to_json_payload(result, limit=2, project_root=tmp_path)

    assert result.summary == {
        "files_scanned": 1,
        "unique_forms": 4,
        "recognized_lemmas": 4,
        "already_in_lexicon": 1,
        "missing_delta": 3,
        "unrecognized": 1,
    }
    assert [item.lemma for item in result.missing_lemmas] == ["замка", "замок", "м'яч"]
    assert [item.example_form for item in result.missing_lemmas] == ["замки", "замки", "м'яч"]
    assert [item.form for item in result.unrecognized_forms] == ["хиба"]
    assert payload["summary"]["missing_delta"] == 3
    assert payload["missing_lemmas"] == [
        {
            "lemma": "замка",
            "example_form": "замки",
            "example_source": "module.mdx",
        },
        {
            "lemma": "замок",
            "example_form": "замки",
            "example_source": "module.mdx",
        },
    ]
    assert payload["truncated"]["missing_lemmas"] is True


@requires_vesum_db
def test_real_vesum_db_smoke_recognizes_basic_inflected_form(tmp_path: Path) -> None:
    mdx_path = tmp_path / "vesum-smoke.mdx"
    mdx_path.write_text("Мами.", encoding="utf-8")
    manifest_path = _write_manifest(tmp_path, [])

    result = reconciler.reconcile_content([mdx_path], manifest_path=manifest_path)

    assert "мама" in result.recognized_lemmas
    assert "мама" in [item.lemma for item in result.missing_lemmas]


def _write_manifest(tmp_path: Path, lemmas: list[str]) -> Path:
    manifest_path = tmp_path / "lexicon-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"entries": [{"lemma": lemma} for lemma in lemmas]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return manifest_path
