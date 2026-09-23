#!/usr/bin/env python3
"""Benchmark check_text against legacy per-tool MCP handler path (#8398 part C).

Performs the real per-tool path through the library functions:
  - verify_words once
  - check_russian_shadow (is_russian_pattern) once per unique form
  - verify_stresses in chunks of 500
  - search_ua_gec_errors once per candidate sentence span

Counts calls, times execution, and sums serialized response characters (mirroring MCP handlers).
Compares with a single call to check_text.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root and scripts/ are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for p in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from wiki.sources_db import search_ua_gec_errors

from scripts.curriculum.evidence.sources import _sources_path
from scripts.curriculum.resolver.codes import SKIPPED_KINDS
from scripts.curriculum.resolver.tokenize import tokenize
from scripts.verification.check_ru_morph import is_russian_pattern
from scripts.verification.check_text import check_text
from scripts.verification.stress import STRESS_BATCH_CAP, verify_stresses
from scripts.verification.vesum import verify_words

DEFAULT_CHUNK_ID = "private-teacher-lessons-a_43833086dcbaea83555d"
REDUCED_SAMPLE_TEXT = (
    "Це гарний день для вивчення української мови. Тут стоїть замок на високій горі. Ми раді вітати всіх охочих учнів."
)


def _serialize_verify_words(words: list[str], results: dict[str, list[dict]]) -> str:
    found = 0
    lines = [f"Batch verification: {len(words)} words\n"]
    for word in words:
        matches = results.get(word, [])
        if matches:
            found += 1
            tags_str = ", ".join(f"{m['lemma']}({m['pos']})" for m in matches[:3])
            lines.append(f"- **{word}** — FOUND ({len(matches)}): {tags_str}")
        else:
            lines.append(f"- **{word}** — NOT FOUND")
    lines.insert(1, f"Found: {found}/{len(words)}\n")
    return "\n".join(lines)


def _serialize_ua_gec(query: str, hits: list[dict]) -> str:
    if not hits:
        return f'No UA-GEC results found for: "{query}"'
    lines = [f'Found {len(hits)} human-annotated error pairs for: "{query}"\n']
    for i, hit in enumerate(hits, 1):
        native_flag = " (native author)" if hit.get("is_native") else ""
        lines.append(f"### Result {i}{native_flag}")
        lines.append(f"- **Error**: {hit.get('error')}")
        lines.append(f"- **Correction**: {hit.get('correct')}")
        lines.append(f"- **Type**: {hit.get('error_type')}")
        lines.append(f"- **Source**: `{hit.get('doc_id')}` ({hit.get('source_lang', 'uk')})")
        lines.append("")
    return "\n".join(lines)


def run_benchmark(
    *,
    text: str | None = None,
    chunk_id: str = DEFAULT_CHUNK_ID,
    reduced: bool = False,
) -> dict[str, Any]:
    """Run real per-tool vs check_text benchmark."""
    if text is None:
        if reduced:
            text = REDUCED_SAMPLE_TEXT
        else:
            sources_path = _sources_path()
            if not sources_path.is_file():
                raise FileNotFoundError(f"Sources database not found at {sources_path}")
            conn = sqlite3.connect(f"file:{sources_path}?mode=ro", uri=True)
            try:
                cur = conn.execute(
                    "SELECT text FROM textbooks WHERE chunk_id = ?",
                    (chunk_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    text = row[0]
                else:
                    # Fallback to first chunk with >= 600 tokens
                    cur = conn.execute("SELECT text FROM textbooks WHERE char_count > 4000 ORDER BY id LIMIT 10")
                    for (t_candidate,) in cur.fetchall():
                        toks = [t for t in tokenize(t_candidate) if t.kind not in SKIPPED_KINDS]
                        if len(toks) >= 600:
                            text = t_candidate
                            break
                    if text is None:
                        raise ValueError("No textbook chunk with >= 600 tokens found")
            finally:
                conn.close()

    tokens = [t for t in tokenize(text) if t.kind not in SKIPPED_KINDS]
    unique_forms = list(dict.fromkeys(t.lookup for t in tokens))

    # Candidate sentence spans
    sentence_spans: list[str] = []
    current_sentence = []
    for t in tokens:
        if t.sentence_initial and current_sentence:
            s_start = current_sentence[0].start
            s_end = current_sentence[-1].end
            sentence_spans.append(text[s_start:s_end].strip())
            current_sentence = []
        current_sentence.append(t)
    if current_sentence:
        s_start = current_sentence[0].start
        s_end = current_sentence[-1].end
        sentence_spans.append(text[s_start:s_end].strip())

    # ── 1. Legacy Per-Tool Path ──────────────────────────────────────────────
    # A. verify_words (1 call)
    t0 = time.perf_counter()
    vw_res = verify_words(unique_forms)
    t_vw = time.perf_counter() - t0
    vw_text = _serialize_verify_words(unique_forms, vw_res)
    vw_chars = len(vw_text)

    # B. check_russian_shadow (is_russian_pattern: 1 call per unique form)
    t0 = time.perf_counter()
    ru_chars = 0
    for w in unique_forms:
        res = is_russian_pattern(w)
        ru_chars += len(json.dumps(res, indent=2, ensure_ascii=False))
    t_ru = time.perf_counter() - t0

    # C. verify_stresses (in chunks of STRESS_BATCH_CAP)
    t0 = time.perf_counter()
    stress_chars = 0
    stress_calls = 0
    for i in range(0, len(unique_forms), STRESS_BATCH_CAP):
        chunk = unique_forms[i : i + STRESS_BATCH_CAP]
        st_res = verify_stresses(chunk)
        stress_calls += 1
        stress_chars += len(json.dumps(st_res, ensure_ascii=False))
    t_st = time.perf_counter() - t0

    # D. search_ua_gec_errors (1 call per candidate sentence span)
    t0 = time.perf_counter()
    gec_chars = 0
    gec_calls = len(sentence_spans)
    for span in sentence_spans:
        hits = search_ua_gec_errors(
            span,
            tag_filter=["F/Calque", "F/Collocation"],
            limit=10,
        )
        gec_chars += len(_serialize_ua_gec(span, hits))
    t_gec = time.perf_counter() - t0

    total_legacy_calls = 1 + len(unique_forms) + stress_calls + gec_calls
    total_legacy_time = t_vw + t_ru + t_st + t_gec
    total_legacy_chars = vw_chars + ru_chars + stress_chars + gec_chars

    # ── 2. check_text (Single Call) ──────────────────────────────────────────
    # Warm-up call
    check_text(text=text)

    t0 = time.perf_counter()
    ct_res = check_text(text=text)
    t_ct = time.perf_counter() - t0
    ct_chars = len(json.dumps(ct_res, ensure_ascii=False))
    ct_calls = 1

    return {
        "text_chars": len(text),
        "tokens": len(tokens),
        "unique_forms": len(unique_forms),
        "sentence_spans": len(sentence_spans),
        "steps": {
            "verify_words": {"calls": 1, "time_s": t_vw, "chars": vw_chars},
            "check_russian_shadow": {"calls": len(unique_forms), "time_s": t_ru, "chars": ru_chars},
            "verify_stresses": {"calls": stress_calls, "time_s": t_st, "chars": stress_chars},
            "search_ua_gec_errors": {"calls": gec_calls, "time_s": t_gec, "chars": gec_chars},
        },
        "legacy": {
            "calls": total_legacy_calls,
            "time_s": total_legacy_time,
            "chars": total_legacy_chars,
        },
        "check_text": {
            "calls": ct_calls,
            "time_s": t_ct,
            "chars": ct_chars,
        },
    }


def format_table(results: dict[str, Any]) -> str:
    """Format benchmark results as a clean table."""
    steps = results["steps"]
    legacy = results["legacy"]
    ct = results["check_text"]

    speedup = legacy["time_s"] / ct["time_s"] if ct["time_s"] > 0 else float("inf")
    char_reduction = legacy["chars"] / ct["chars"] if ct["chars"] > 0 else float("inf")
    call_reduction = legacy["calls"] / ct["calls"]

    rows = [
        (
            "verify_words",
            steps["verify_words"]["calls"],
            f"{steps['verify_words']['time_s']:.4f}s",
            f"{steps['verify_words']['chars']:,}",
        ),
        (
            "check_russian_shadow",
            steps["check_russian_shadow"]["calls"],
            f"{steps['check_russian_shadow']['time_s']:.4f}s",
            f"{steps['check_russian_shadow']['chars']:,}",
        ),
        (
            "verify_stresses",
            steps["verify_stresses"]["calls"],
            f"{steps['verify_stresses']['time_s']:.4f}s",
            f"{steps['verify_stresses']['chars']:,}",
        ),
        (
            "search_ua_gec_errors",
            steps["search_ua_gec_errors"]["calls"],
            f"{steps['search_ua_gec_errors']['time_s']:.4f}s",
            f"{steps['search_ua_gec_errors']['chars']:,}",
        ),
        ("---", "---", "---", "---"),
        ("Legacy per-tool total", legacy["calls"], f"{legacy['time_s']:.4f}s", f"{legacy['chars']:,}"),
        ("check_text (single call)", ct["calls"], f"{ct['time_s']:.4f}s", f"{ct['chars']:,}"),
        ("---", "---", "---", "---"),
        ("Improvement", f"{call_reduction:.1f}x calls", f"{speedup:.1f}x faster", f"{char_reduction:.1f}x fewer chars"),
    ]

    col_widths = [26, 14, 16, 18]
    header = ("Operation / Approach", "Calls", "Wall Time", "Response Chars")

    def _fmt_row(vals):
        return "| " + " | ".join(f"{v!s:<{w}}" for v, w in zip(vals, col_widths, strict=False)) + " |"

    sep = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"

    lines = [
        f"Benchmark on text ({results['tokens']} tokens, {results['unique_forms']} unique forms, {results['sentence_spans']} sentences):",
        _fmt_row(header),
        sep,
    ]
    for row in rows:
        if row[0] == "---":
            lines.append(sep)
        else:
            lines.append(_fmt_row(row))

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark check_text against legacy per-tool MCP handler path.")
    parser.add_argument(
        "--chunk-id",
        default=DEFAULT_CHUNK_ID,
        help=f"Textbook chunk ID to use as fixture (default: {DEFAULT_CHUNK_ID})",
    )
    parser.add_argument(
        "--reduced",
        action="store_true",
        help="Run benchmark on reduced sample text for quick testing",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Custom text string to benchmark",
    )

    args = parser.parse_args()
    results = run_benchmark(
        text=args.text,
        chunk_id=args.chunk_id,
        reduced=args.reduced,
    )
    print(format_table(results))


if __name__ == "__main__":
    main()
