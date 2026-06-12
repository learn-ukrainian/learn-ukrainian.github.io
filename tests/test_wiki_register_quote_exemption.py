from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from wiki.register_quote_exemption import find_attributed_verbatim_quote_spans
from wiki.review import (
    Finding,
    _parse_dim_result,
    _register_score_from_findings,
)


def _register_response(findings: list[dict], score: int, verdict: str) -> str:
    return json.dumps(
        {
            "dimension": "register",
            "findings": findings,
            "fixes": [],
            "score": score,
            "verdict": verdict,
            "notes": "",
        },
        ensure_ascii=False,
    )


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


# ── Deterministic wiring through the register gate (_parse_dim_result) ──


def test_parse_dim_result_drops_attributed_quote_finding_keeps_prose() -> None:
    """The deterministic filter must fire through the gate: an attributed-quote
    russianism is dropped + the score recomputed, while a prose russianism in
    the same article survives (teeth)."""
    article_text = (
        "Билина виступає доказом єдності землі.\n\n"
        "Енциклопедія українознавства [S2] зазначає: "
        "«співці виконували під акомпаньямент ліри»."
    )
    response = _register_response(
        findings=[
            {
                "location": "Поетика",
                "quote": "виступає",
                "issue_type": "CALQUE",
                "severity": "major",
                "issue_description": "copula calque",
            },
            {
                "location": "Виконавство",
                "quote": "акомпаньямент",
                "issue_type": "RUSSIANISM",
                "severity": "major",
                "issue_description": "russian spelling inside quote",
            },
        ],
        score=7,
        verdict="REVISE",
    )
    result = _parse_dim_result(
        dim="register",
        agent="gemini",
        model="g",
        response=response,
        duration_s=1.0,
        article_text=article_text,
    )
    quotes = [f.quote for f in result.findings]
    assert "акомпаньямент" not in quotes  # exempt: only inside an attributed quote
    assert "виступає" in quotes  # prose russianism survives — teeth preserved
    assert result.score == 8  # recomputed from 1 surviving major
    assert result.verdict == "PASS"


def test_parse_dim_result_register_unchanged_without_article_text() -> None:
    response = _register_response(
        findings=[
            {
                "location": "X",
                "quote": "акомпаньямент",
                "issue_type": "RUSSIANISM",
                "severity": "major",
                "issue_description": "y",
            }
        ],
        score=8,
        verdict="PASS",
    )
    result = _parse_dim_result(
        dim="register", agent="gemini", model="g", response=response, duration_s=1.0
    )
    assert [f.quote for f in result.findings] == ["акомпаньямент"]
    assert result.score == 8


def test_parse_dim_result_non_register_dim_never_exempts() -> None:
    article_text = "Енциклопедія [S2] зазначає: «акомпаньямент»."
    response = _register_response(
        findings=[
            {
                "location": "X",
                "quote": "акомпаньямент",
                "issue_type": "RUSSIANISM",
                "severity": "major",
                "issue_description": "y",
            }
        ],
        score=6,
        verdict="REVISE",
    )
    result = _parse_dim_result(
        dim="source_grounding",
        agent="codex",
        model="c",
        response=response,
        duration_s=1.0,
        article_text=article_text,
    )
    # source_grounding must NOT get the register quote-exemption.
    assert [f.quote for f in result.findings] == ["акомпаньямент"]
    assert result.score == 6


def test_parse_dim_result_recomputes_unreliable_gemini_score() -> None:
    """gemini's holistic register score is unreliable (observed literal 0 for a
    multi-finding REVISE). With article_text present, the gate must derive the
    score deterministically from the surviving findings, never trusting the
    erratic number — and never lowering it."""
    article_text = "Авторська проза містить один зворот, що виступає доказом."
    response = _register_response(
        findings=[
            {
                "location": "Поетика",
                "quote": "виступає",
                "issue_type": "CALQUE",
                "severity": "major",
                "issue_description": "copula calque in prose",
            }
        ],
        score=0,  # erratic gemini output
        verdict="REVISE",
    )
    result = _parse_dim_result(
        dim="register",
        agent="gemini",
        model="g",
        response=response,
        duration_s=1.0,
        article_text=article_text,
    )
    # 1 prose major → table score 8 (PASS), not the erratic 0.
    assert [f.quote for f in result.findings] == ["виступає"]
    assert result.score == 8
    assert result.verdict == "PASS"


def test_register_score_from_findings_table() -> None:
    def mk(sev: str) -> Finding:
        return Finding(
            location="", quote="", issue_type="", severity=sev, description="", raw={}
        )

    assert _register_score_from_findings([]) == 10
    assert _register_score_from_findings([mk("minor")]) == 9
    assert _register_score_from_findings([mk("major")]) == 8
    assert _register_score_from_findings([mk("major"), mk("major")]) == 7
    assert _register_score_from_findings([mk("critical")]) == 7
    assert (
        _register_score_from_findings([mk("critical"), mk("major"), mk("major")]) == 6
    )
    assert _register_score_from_findings([mk("critical"), mk("critical")]) == 5
