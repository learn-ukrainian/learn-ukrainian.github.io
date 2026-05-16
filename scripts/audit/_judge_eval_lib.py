"""Shared Russianism-judge calibration helpers.

The Grok single-model harness and the multi-model matrix use the same
Antonenko-grounded prompt, PR #2006 gold loader, and sev2-tolerant scoring.
Keep this module free of provider-specific subprocess logic.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT_ROOT / "data" / "sources.db"
VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"

PR_2006_REF = "origin/pr-2006"
CALIBRATION_BLOB = "eval/russianism/calibration-cases.jsonl"

CYRILLIC_TOKEN_RE = re.compile(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+")


def utc_timestamp() -> str:
    """Return a stable UTC timestamp for artifact metadata."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pull_calibration_cases(
    *,
    ref: str = PR_2006_REF,
    blob: str = CALIBRATION_BLOB,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, Any]]:
    """Pull the calibration cases from PR #2006's branch without copying them.

    The branch may not be checked out locally; callers should fetch
    ``refs/pull/2006/head`` into ``refs/remotes/origin/pr-2006`` if this
    read fails.
    """
    proc = subprocess.run(
        ["git", "show", f"{ref}:{blob}"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.exit(
            f"ERROR: could not read {blob} from {ref}.\n"
            f"git stderr: {proc.stderr.strip()}\n"
            "If origin/pr-2006 has been pruned, refetch with:\n"
            "  git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'"
        )

    cases: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def retrieve_antonenko(text: str, k: int = 8, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Find Antonenko entries whose headwords appear in ``text``.

    Ported from ``scripts/audit/russianism_judge.py`` on ``origin/pr-2006``.
    It grounds the judge prompt in canonical evidence from the local sources DB.
    """
    conn = sqlite3.connect(db_path)
    try:
        words = set(re.findall(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+", text.lower()))
        if not words:
            return []
        placeholders = ",".join("?" * len(words))
        rows = conn.execute(
            f"""
            SELECT word, section, page, text
            FROM style_guide
            WHERE word_lower IN ({placeholders})
               OR EXISTS (
                   SELECT 1 FROM (
                       SELECT value FROM json_each(?)
                   ) t WHERE word_lower = t.value
               )
            LIMIT ?
            """,
            (*words, json.dumps(list(words), ensure_ascii=False), k),
        ).fetchall()
    finally:
        conn.close()

    return [
        {"headword": r[0], "section": r[1], "page": r[2], "text": (r[3] or "")[:600]}
        for r in rows
    ]


def _text_tokens(text: str, *, min_len: int = 3) -> list[str]:
    """Lowercased Cyrillic tokens of length >= ``min_len``, deduplicated, sorted."""
    return sorted({m for m in (t.lower() for t in CYRILLIC_TOKEN_RE.findall(text)) if len(m) >= min_len})


def _proper_noun_tokens(text: str) -> set[str]:
    """Lowercased tokens that appear capitalized in non-sentence-initial position.

    Used to exclude proper nouns from VESUM-unknown / Russian-shadow checks.
    ``Львова`` (Lviv-gen) is morphologically valid Ukrainian but absent from
    VESUM's common-form table, so a naive check creates fake Russianism
    candidates on clean travel prose.
    """
    proper_nouns: set[str] = set()
    sentence_boundary = True
    for match in re.finditer(r"\S+", text):
        token = match.group(0)
        cyrillic_match = CYRILLIC_TOKEN_RE.match(token)
        if cyrillic_match and cyrillic_match.group(0)[0].isupper() and not sentence_boundary:
            proper_nouns.add(cyrillic_match.group(0).lower())
        sentence_boundary = token[-1] in ".!?…"
    return proper_nouns


def _heritage_check(text: str, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Tokens with attestation in Grinchenko (1907) or ESUM etymology.

    Single-word attestation in pre-Soviet / etymological dictionaries is strong
    evidence that the form is canonical Ukrainian, NOT a Russianism.
    """
    tokens = _text_tokens(text)
    if not tokens:
        return []
    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(tokens))
        grinchenko = {
            r[0].lower()
            for r in conn.execute(
                f"SELECT word FROM grinchenko WHERE lower(word) IN ({placeholders})",
                tokens,
            ).fetchall()
        }
        esum = {
            r[0].lower()
            for r in conn.execute(
                f"SELECT lemma FROM esum_etymology WHERE lower(lemma) IN ({placeholders})",
                tokens,
            ).fetchall()
        }
    finally:
        conn.close()
    attested = []
    for token in tokens:
        sources = []
        if token in grinchenko:
            sources.append("Grinchenko 1907")
        if token in esum:
            sources.append("ESUM etymology")
        if sources:
            attested.append({"token": token, "sources": sources})
    return attested


def _russian_shadow_check(text: str) -> dict[str, Any]:
    """Run pymorphy3-based Russian-shadow heuristic over Cyrillic tokens.

    Returns ``{"available": bool, "triggered_tokens": [{token, ru_lemma, confidence}]}``.
    ``check_ru_morph.is_russian_pattern`` short-circuits on VESUM hits, so this
    only fires on tokens that are NOT valid Ukrainian forms AND look Russian.
    Proper nouns are excluded to avoid flagging place/person names.
    """
    try:
        from scripts.verification.check_ru_morph import is_russian_pattern
    except ImportError:
        return {"available": False, "triggered_tokens": []}
    proper_nouns = _proper_noun_tokens(text)
    triggered = []
    for token in _text_tokens(text):
        if token in proper_nouns:
            continue
        try:
            result = is_russian_pattern(token)
        except Exception:
            continue
        if result.get("matches_russian"):
            triggered.append(
                {
                    "token": token,
                    "ru_lemma": result.get("russian_lemma"),
                    "confidence": round(float(result.get("confidence", 0.0)), 2),
                }
            )
    return {"available": True, "triggered_tokens": triggered}


def _vesum_unknown(text: str, *, db_path: Path = VESUM_DB) -> list[str]:
    """Cyrillic tokens NOT present in VESUM as a known word_form.

    Proper nouns are excluded — place and person names are typically absent
    from VESUM's common-form table even when morphologically valid Ukrainian.
    """
    tokens = _text_tokens(text)
    if not tokens:
        return []
    if not db_path.exists():
        return []
    proper_nouns = _proper_noun_tokens(text)
    candidate_tokens = [t for t in tokens if t not in proper_nouns]
    if not candidate_tokens:
        return []
    conn = sqlite3.connect(db_path)
    try:
        placeholders = ",".join("?" * len(candidate_tokens))
        known = {
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT word_form FROM forms WHERE word_form IN ({placeholders})",
                candidate_tokens,
            ).fetchall()
        }
    finally:
        conn.close()
    return sorted(set(candidate_tokens) - known)


def retrieve_evidence(text: str) -> dict[str, Any]:
    """Aggregate all evidence signals for one judge prompt.

    Combines Antonenko-Davydovych entries (style guide), Grinchenko/ESUM
    token attestation (heritage defense), pymorphy3 Russian-shadow morphology
    detection, and VESUM-unknown token enumeration.
    """
    return {
        "antonenko": retrieve_antonenko(text),
        "heritage_attested": _heritage_check(text),
        "russian_shadow": _russian_shadow_check(text),
        "vesum_unknown_tokens": _vesum_unknown(text),
    }


def retrieve_ua_gec(text: str, k: int = 8, *, db_path: Path = DB) -> list[dict[str, Any]]:
    """Find UA-GEC error pairs matching words in ``text``.

    Searches the ``ua_gec_errors`` FTS5 table for error→correction triples
    whose ``error`` substring overlaps any word in the input. UA-GEC is
    Grammarly UA's MIT-licensed human-annotated learner-error corpus
    (8,937 rows filtered to russianism-relevant tags: F/Calque, F/Collocation,
    G/Case, G/Gender). Densest evidence source for phraseological and
    register calques that don't have Antonenko-Davydovych headword entries.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        words = set(re.findall(r"[А-Яа-яҐґЄєІіЇї'’ʼ\-]+", text.lower()))
        if not words:
            return []

        query_parts = []
        for word in words:
            if len(word) >= 3:
                # Escape double quotes for FTS5
                safe_word = word.replace('"', '""')
                query_parts.append(f'"{safe_word}"')

        if not query_parts:
            return []

        fts_query = " OR ".join(query_parts)
        rows = conn.execute(
            """
            SELECT m.error, m.correct, m.error_type, m.doc_id
            FROM ua_gec_errors_fts f
            JOIN ua_gec_errors m ON f.rowid = m.id
            WHERE f.error MATCH ?
            ORDER BY f.rank
            LIMIT ?
            """,
            (fts_query, k),
        ).fetchall()
    except sqlite3.OperationalError:
        # ua_gec_errors table may not yet exist on every checkout (e.g.
        # before this PR's ingest landed); fail soft.
        return []
    finally:
        conn.close()

    return [
        {"error": r["error"], "correct": r["correct"], "type": r["error_type"], "doc_id": r["doc_id"]}
        for r in rows
    ]


def build_judge_prompt(
    target_text: str,
    antonenko_entries: list[dict[str, Any]],
    ua_gec_entries: list[dict[str, Any]] | None = None,
) -> str:
    """Universal Russianism-judge prompt, identical across model families.

    Preserved at main as the production baseline. The H1 evidence-rich variant
    documented in ``audit/2026-05-17-judge-calibration-h1/COMPARISON.md`` was
    falsified on the current 12-case calibration set (recall collapsed because
    the evidence catalog couldn't anchor 14 of 16 sev>=2 flags). The
    ``retrieve_evidence`` helper below is preserved for H2c use (typed
    calibration set authoring + per-channel coverage metrics).

    The optional ``ua_gec_entries`` parameter renders human-annotated UA-GEC
    error→correction pairs as additional evidence. Backward-compatible: when
    omitted or None, the prompt body is byte-identical to the 2-argument form.
    """
    evidence = ""
    if antonenko_entries:
        evidence += (
            "## Relevant Antonenko-Davydovych entries "
            "(potentially applicable rules):\n\n"
        )
        for i, entry in enumerate(antonenko_entries[:8], 1):
            evidence += f"### Antonenko Rule {i}: {entry['headword']}\n{entry['text']}\n\n"

    if ua_gec_entries:
        evidence += "## UA-GEC human-annotated error pairs matching text:\n\n"
        for entry in ua_gec_entries[:8]:
            evidence += (
                f"- Error: \"{entry['error']}\" → Correction: "
                f"\"{entry['correct']}\" (Type: {entry['type']})\n"
            )
        evidence += "\n"

    if not evidence:
        evidence = (
            "(No directly-keyed Antonenko entries or UA-GEC pairs found for words in this text. "
            "Apply general knowledge of Ukrainian register and Russianism patterns.)\n"
        )

    return f"""You are an expert Ukrainian-language proofreader specializing in identifying Russianisms (русизми), calques (кальки), Surzhyk (суржик), and unnatural Ukrainian phrasing.
Your primary authorities are Антоненко-Давидович «Як ми говоримо» and UA-GEC (Ukrainian Grammatical Error Corpus, Grammarly UA, MIT-licensed).

## Text to evaluate

```
{target_text}
```

{evidence}

## Your task

Identify EVERY Russianism, calque, Surzhyk, or unnatural Ukrainian construction in the text above. For each issue:

- Quote the exact problematic phrase
- Cite the relevant authority (Antonenko rule by headword or UA-GEC pattern) or general principle
- Provide the correct Ukrainian alternative
- Severity: 1=minor (debatable), 2=clear Russianism, 3=blatant calque or borrowing

If the text is genuinely clean Ukrainian with NO Russianisms, output `{{"verdict": "clean", "issues": []}}`.

Otherwise output JSON with this exact shape:

```json
{{
  "verdict": "issues_found",
  "issues": [
    {{"phrase": "...", "rule": "...", "correct": "...", "severity": 1-3}}
  ]
}}
```

Output ONLY the JSON object — no commentary, no markdown fences, no preamble."""


def parse_json_verdict(raw_content: str, *, duration_s: float = 0.0) -> dict[str, Any]:
    """Parse a judge response into the verdict shape used by scoring."""
    match = re.search(r"\{.*\}", raw_content or "", re.DOTALL)
    if not match:
        return {
            "verdict": "judge_error",
            "raw": (raw_content or "")[:500],
            "duration_s": duration_s,
            "note": "no JSON object in response",
        }
    try:
        verdict = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        return {
            "verdict": "json_parse_error",
            "raw": match.group(0)[:500],
            "error": str(exc),
            "duration_s": duration_s,
        }
    if isinstance(verdict, dict):
        verdict["_duration_s"] = duration_s
        return verdict
    return {
        "verdict": "json_parse_error",
        "raw": match.group(0)[:500],
        "error": "parsed JSON was not an object",
        "duration_s": duration_s,
    }


def score_case(verdict: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    """Score one case with PR #2006's sev2-tolerant approximation.

    Case-level accuracy is clean-vs-issues. Precision/recall/F1 count only
    severity >= 2 flags, so debatable severity-1 flags do not dominate routing.
    """
    expected_clean = bool(gold.get("expected_clean"))
    judged_clean = verdict.get("verdict") == "clean"
    case_acc = expected_clean == judged_clean

    issues = verdict.get("issues") or []
    sev2_plus_judge = sum(
        1
        for item in issues
        if isinstance(item, dict)
        and isinstance(item.get("severity"), int)
        and item["severity"] >= 2
    )
    expected_flags_n = len(gold.get("expected_flags") or [])

    if expected_clean:
        tp = 0
        fp = sev2_plus_judge
        fn = 0
    else:
        tp = min(sev2_plus_judge, expected_flags_n)
        fn = max(0, expected_flags_n - sev2_plus_judge)
        fp = max(0, sev2_plus_judge - expected_flags_n)

    return {
        "case_acc": case_acc,
        "judged_clean": judged_clean,
        "expected_clean": expected_clean,
        "judge_sev2_plus_count": sev2_plus_judge,
        "expected_flags_count": expected_flags_n,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-case scores into precision, recall, F1, and case accuracy."""
    tp = sum(int(s["tp"]) for s in scores)
    fp = sum(int(s["fp"]) for s in scores)
    fn = sum(int(s["fn"]) for s in scores)
    n = len(scores)
    case_acc = sum(1 for s in scores if s["case_acc"]) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    rounded_case_acc = round(case_acc, 4)
    return {
        "n": n,
        "case_accuracy": rounded_case_acc,
        "case_acc": rounded_case_acc,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def judgment_row_from_case(
    *,
    case: dict[str, Any],
    model: str,
    verdict: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    """Build the legacy judgment row written by ``grok_judge_calibration.py``."""
    return {
        "prompt_id": case["prompt_id"],
        "model": model,
        "verdict": verdict.get("verdict"),
        "judge_sev2_plus_count": score["judge_sev2_plus_count"],
        "expected_flags_count": score["expected_flags_count"],
        "case_acc": score["case_acc"],
        "duration_s": round(float(verdict.get("_duration_s", verdict.get("duration_s", 0.0))), 2),
        "raw": verdict,
    }


def render_grok_report(
    *,
    model: str,
    agg: dict[str, Any],
    judgments_path: Path,
    calibration_blob: str = CALIBRATION_BLOB,
    ref: str = PR_2006_REF,
) -> str:
    """Render the legacy single-model Grok report body."""
    report_lines = [
        f"# Grok 4.3 Russianism judge calibration — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
        "",
        f"Model: `{model}` via Hermes OAuth (`api.x.ai/v1`)",
        f"Cases: {agg['n']} (from `{calibration_blob}` on `{ref}`)",
        "",
        "## Aggregate",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Case accuracy | **{agg['case_accuracy']*100:.1f}%** |",
        f"| Precision (sev≥2) | {agg['precision']*100:.1f}% |",
        f"| Recall (sev≥2) | {agg['recall']*100:.1f}% |",
        f"| **F1 (sev≥2)** | **{agg['f1']*100:.1f}%** |",
        f"| tp / fp / fn | {agg['tp']} / {agg['fp']} / {agg['fn']} |",
        "",
        "## Reference leaderboard (2026-05-15, n=12)",
        "",
        "| Judge | F1 | Precision | Recall | Case acc |",
        "|---|---:|---:|---:|---:|",
        "| claude-opus-4-7 | 86% | 79% | 94% | 100% |",
        "| gemini-3.1-pro-preview | 84% | 81% | 87% | 92% |",
        "| gpt-5.5 | 78% | 90% | 69% | 83% |",
        f"| **{model}** | **{agg['f1']*100:.0f}%** | **{agg['precision']*100:.0f}%** | **{agg['recall']*100:.0f}%** | **{agg['case_accuracy']*100:.0f}%** |",
        "",
        f"Source: `audit/2026-05-15-russianism-judge-calibration/REPORT.md` on `{ref}` for the prior 3 judges.",
        "",
        "## Per-case breakdown",
        "",
        "| Case | Expected | Judged | Match | sev≥2 flags | Dur (s) |",
        "|---|---|---|:---:|---:|---:|",
    ]
    with judgments_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            expected = "clean" if row["expected_flags_count"] == 0 else "issues"
            mark = "✓" if row["case_acc"] else "✗"
            report_lines.append(
                f"| `{row['prompt_id']}` | {expected} | {row['verdict']} | {mark} | "
                f"{row['judge_sev2_plus_count']} | {row['duration_s']:.1f} |"
            )
    return "\n".join(report_lines) + "\n"
