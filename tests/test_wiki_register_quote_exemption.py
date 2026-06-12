from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from wiki.register_quote_exemption import find_attributed_verbatim_quote_spans


def _span_texts(article_text: str) -> list[str]:
    return [span.quote_text for span in find_attributed_verbatim_quote_spans(article_text)]


def test_attributed_guillemet_quote_is_register_exempt() -> None:
    article_text = (
        "Енциклопедія українознавства фіксує старіший правопис: "
        "«співці виконували під акомпаньямент ліри» [S2]."
    )

    assert _span_texts(article_text) == ["«співці виконували під акомпаньямент ліри»"]


def test_attributed_blockquote_is_register_exempt() -> None:
    article_text = """
Перед цитатою власна проза.

> У в кругу старших співців текст передавався інакше.

*— Білецький [S3]*

Після цитати власна проза.
"""

    assert _span_texts(article_text) == ["У в кругу старших співців текст передавався інакше."]


def test_exact_chunk_id_counts_as_quote_attribution() -> None:
    article_text = (
        "Досьє цитує фрагмент «дружинний епос не зберігся до наших днів» "
        "(chunk_id: feaa5fa7_c0619)."
    )

    assert _span_texts(article_text) == ["«дружинний епос не зберігся до наших днів»"]


def test_unquoted_russianism_in_article_prose_is_not_exempt() -> None:
    article_text = "Авторська проза каже, що билина виступає доказом і лишається в кругу тем."

    assert _span_texts(article_text) == []


def test_unattributed_quote_is_not_exempt() -> None:
    article_text = "У тексті є цитатні лапки «в кругу співців», але немає джерела."

    assert _span_texts(article_text) == []


def test_generic_reporting_cue_without_source_is_not_exempt() -> None:
    article_text = "Авторська проза стверджує: «в кругу співців»."

    assert _span_texts(article_text) == []


def test_no_verify_quote_is_not_exempt() -> None:
    article_text = """
<!-- NO_VERIFY: quote pending -->
> У в кругу старших співців текст передавався інакше.

*— Білецький [S3]*
"""

    assert _span_texts(article_text) == []


def test_writer_prompt_contains_register_hygiene_rules() -> None:
    prompt = (_REPO_ROOT / "scripts" / "wiki" / "prompts" / "compile_article.md").read_text(
        encoding="utf-8",
    )

    assert "Регістрова гігієна" in prompt
    assert "`вербатимний`" in prompt
    assert "`дослівний`" in prompt
    assert "`приближення`" in prompt
    assert "`наближення`" in prompt
    assert "`виступати` як копулу" in prompt


def test_register_review_prompt_keeps_quote_exemption_teeth() -> None:
    prompt = (_REPO_ROOT / "scripts" / "wiki" / "prompts" / "review_register.md").read_text(
        encoding="utf-8",
    )

    assert "Verbatim Quote Exemption" in prompt
    assert "Do NOT flag russianisms, old spellings, or calques" in prompt
    assert "Unquoted article prose" in prompt
    assert "Unattributed quotations" in prompt
    assert "Fabricated attribution" in prompt


def test_blockquote_preceding_attribution_is_exempt() -> None:
    article_text = """
За свідченням Білецького [S3]:

> У в кругу старших співців текст передавався інакше.
"""
    assert _span_texts(article_text) == ["У в кругу старших співців текст передавався інакше."]


def test_guillemet_preceding_attribution_is_exempt() -> None:
    article_text = """
Енциклопедія українознавства [S2] зазначає:

«співці виконували під акомпаньямент ліри»
"""
    assert _span_texts(article_text) == ["«співці виконували під акомпаньямент ліри»"]


def test_blockquote_internal_dash_attribution_is_exempt() -> None:
    article_text = """
> У в кругу старших співців текст передавався інакше.
> — Білецький
"""
    assert _span_texts(article_text) == [
        "У в кругу старших співців текст передавався інакше.\n— Білецький"
    ]
