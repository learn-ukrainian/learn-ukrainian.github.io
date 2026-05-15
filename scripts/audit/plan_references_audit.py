#!/usr/bin/env python3
"""Audit plan_references in A1 + A2 module plans.

Walks every plan YAML under curriculum/l2-uk-en/plans/{a1,a2}/, extracts
"Author Grade N, p.M" citations from the `references` field and
`content_outline` points, resolves each against data/sources.db, and
emits a deterministic JSON + Markdown report classifying failure modes:

    GHOST_SOURCE      source_file for (author, grade) not in corpus
    GHOST_PAGE        source_file exists but no chunk for that page
    TOPIC_MISMATCH    chunk exists but text is unrelated to the plan topic
    LEVEL_MISMATCH    A1 cites Grade >=7 OR A2 cites Grade >=10
    UNKNOWN_AUTHOR    author not in _TEXTBOOK_AUTHOR_TRANSLITS (canonical 10)
    OK                resolves cleanly with on-topic chunk

The resolver uses the FIXED LIKE pattern (both `%-{translit}-%` AND
`%-{translit}`) so the matcher bug for source_files without a year
suffix (e.g. `4-klas-ukrmova-zaharijchuk`) does not produce spurious
GHOST_SOURCE flags.

Usage:
    .venv/bin/python scripts/audit/plan_references_audit.py
    .venv/bin/python scripts/audit/plan_references_audit.py --out-dir audit/foo

Issue: #1975
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUT_DIR = PROJECT_ROOT / "audit" / "a1-a2-plan-references-2026-05-15"

# Mirror of scripts/build/linear_pipeline.py:_TEXTBOOK_AUTHOR_TRANSLITS.
# Edit there, not here — this is the audit's reference snapshot.
CANONICAL_TRANSLITS: dict[str, list[str]] = {
    "Караман": ["karaman"],
    "Захарійчук": ["zakhariychuk", "zaharijchuk", "zahariichuk"],
    "Кравцова": ["kravcova", "kravtsova"],
    "Авраменко": ["avramenko"],
    "Глазова": ["glazova", "hlazova"],
    "Заболотний": ["zabolotnyi", "zabolotnij"],
    "Захарчук": ["zakharchuk"],
    "Вашуленко": ["vashulenko"],
    "Большакова": ["bolshakova"],
    "Міщенко": ["mishhenko", "mishchenko"],
    "Літвінова": ["litvinova"],
    "Литвінова": ["litvinova"],
    "Голуб": ["golub"],
    "Варзацька": ["varzatska"],
    "Пономарова": ["ponomarova"],
    "Пономарьова": ["ponomarova"],
}

# Authors observed in plans but not in CANONICAL_TRANSLITS. Used to
# suggest extensions to _TEXTBOOK_AUTHOR_TRANSLITS in the aggregate
# findings section — never to silently resolve UNKNOWN_AUTHOR citations.
SUGGESTED_TRANSLITS: dict[str, list[str]] = {}

# "Author Grade N, p.M" / "с. M" / "стор. M". Cyrillic author block,
# Grade integer, then a page-style marker followed by digits.
PAGED_CITATION_RE = re.compile(
    r"([Ѐ-ӿʼ’'-]{3,})\s+Grade\s+(\d+)\s*,\s*(?:p\.|с\.|стор\.)\s*(\d+)",
    re.IGNORECASE,
)

# Ukrainian content stopwords — short closed-class set so topic
# overlap doesn't get inflated by particles/auxiliaries.
UK_STOPWORDS = frozenset(
    [
        "що", "як", "це", "цей", "ця", "ці", "той", "та", "те", "ті",
        "або", "але", "тому", "тому що", "ще", "вже", "коли", "де",
        "куди", "звідки", "чому", "хто", "який", "яка", "яке", "які",
        "для", "про", "над", "під", "при", "без", "після", "перед",
        "між", "через", "проти", "крім", "окрім", "разом", "поряд",
        "сам", "сама", "сами", "інший", "інша", "інше", "інші",
        "може", "можна", "треба", "потрібно", "потрібен", "є", "був",
        "була", "було", "були", "буде", "буду", "будемо", "будуть",
        "так", "ні", "не", "ані", "лише", "тільки", "навіть", "хоча",
        "якщо", "коли", "поки", "доки", "поки що", "досі", "вже",
        "теж", "також", "багато", "мало", "трохи", "дуже", "зовсім",
        "грамат", "урок", "розділ", "тема", "підручник", "клас",
        "вправ", "завдан", "ілюстр", "приклад", "сторінк",
    ]
)


@dataclass(frozen=True)
class Citation:
    plan_slug: str
    level: str  # "a1" | "a2"
    raw: str
    author: str
    grade: int
    page: int
    field_source: str  # "references" | "content_outline"
    ref_index: int


@dataclass
class Finding:
    citation: Citation
    mode: str
    detail: str = ""
    chunk_preview: str = ""
    resolved_source_file: str = ""
    chunk_title: str = ""
    overlap: int = 0
    topic_keywords: list[str] = field(default_factory=list)
    suggested_fix: str = ""


def _stem(word: str) -> str:
    return word[:5].casefold()


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[Ѐ-ӿ’ʼ'-]{4,}", text)
    stems = set()
    for w in words:
        lw = w.casefold()
        if lw in UK_STOPWORDS:
            continue
        stems.add(_stem(lw))
    return stems


def _topic_keywords(plan: dict) -> list[str]:
    """Topic text for overlap scoring: title + subtitle + grammar +
    objectives + content_outline section titles (not points, which
    inflate noise)."""
    parts: list[str] = []
    for key in ("title", "subtitle"):
        v = plan.get(key)
        if v:
            parts.append(str(v))
    for key in ("objectives", "grammar"):
        v = plan.get(key) or []
        for item in v:
            parts.append(str(item))
    for sec in plan.get("content_outline") or []:
        title = sec.get("section") if isinstance(sec, dict) else None
        if title:
            parts.append(str(title))
    return parts


def _extract_citations(
    plan_path: Path, level: str
) -> list[Citation]:
    with plan_path.open(encoding="utf-8") as f:
        plan = yaml.safe_load(f) or {}
    slug = plan_path.stem
    cites: list[Citation] = []

    refs = plan.get("references") or []
    for idx, ref in enumerate(refs):
        text = (
            " || ".join(str(ref.get(k) or "") for k in ("title", "notes"))
            if isinstance(ref, dict)
            else str(ref)
        )
        for m in PAGED_CITATION_RE.finditer(text):
            cites.append(
                Citation(
                    plan_slug=slug,
                    level=level,
                    raw=m.group(0),
                    author=m.group(1),
                    grade=int(m.group(2)),
                    page=int(m.group(3)),
                    field_source="references",
                    ref_index=idx,
                )
            )

    for sec_idx, sec in enumerate(plan.get("content_outline") or []):
        for pt_idx, point in enumerate(sec.get("points") or []):
            for m in PAGED_CITATION_RE.finditer(str(point)):
                cites.append(
                    Citation(
                        plan_slug=slug,
                        level=level,
                        raw=m.group(0),
                        author=m.group(1),
                        grade=int(m.group(2)),
                        page=int(m.group(3)),
                        field_source="content_outline",
                        ref_index=sec_idx * 1000 + pt_idx,
                    )
                )

    return cites


def _source_files_for(
    conn: sqlite3.Connection, translits: Iterable[str], grade: int
) -> list[str]:
    """FIXED matcher: matches `%-translit-%` (year suffix present) OR
    `%-translit` (no year suffix, e.g. 4-klas-ukrmova-zaharijchuk)."""
    translits = list(translits)
    if not translits:
        return []
    clauses = []
    params: list[str] = [f"{grade}-klas-%"]
    for t in translits:
        clauses.append("source_file LIKE ?")
        params.append(f"%-{t}-%")
        clauses.append("source_file LIKE ?")
        params.append(f"%-{t}")
    sql = (
        "SELECT DISTINCT source_file FROM textbooks "
        f"WHERE source_file LIKE ? AND ({' OR '.join(clauses)})"
    )
    rows = conn.execute(sql, params).fetchall()
    return sorted(str(r[0]) for r in rows)


def _fetch_chunk(
    conn: sqlite3.Connection, source_files: list[str], page: int
) -> dict | None:
    if not source_files:
        return None
    quoted = ",".join("?" for _ in source_files)
    for width in (4, 3):
        suffix = f"\\_s{page:0{width}d}"
        row = conn.execute(
            (
                "SELECT chunk_id, title, text, source_file "
                f"FROM textbooks WHERE source_file IN ({quoted}) "
                "AND chunk_id LIKE ? ESCAPE '\\' "
                "ORDER BY source_file DESC, chunk_id LIMIT 1"
            ),
            (*source_files, f"%{suffix}"),
        ).fetchone()
        if row:
            return {
                "chunk_id": row[0],
                "title": row[1],
                "text": row[2],
                "source_file": row[3],
            }
    return None


def _nearby_pages(
    conn: sqlite3.Connection, source_files: list[str], page: int, radius: int = 3
) -> list[tuple[int, str]]:
    """Return up to `radius`-distance pages that DO exist, with chunk
    titles, for the GHOST_PAGE 'suggested fix' column."""
    if not source_files:
        return []
    out: list[tuple[int, str]] = []
    quoted = ",".join("?" for _ in source_files)
    for d in range(1, radius + 1):
        for candidate in (page - d, page + d):
            if candidate <= 0:
                continue
            for width in (4, 3):
                suffix = f"\\_s{candidate:0{width}d}"
                row = conn.execute(
                    (
                        "SELECT chunk_id, title FROM textbooks "
                        f"WHERE source_file IN ({quoted}) "
                        "AND chunk_id LIKE ? ESCAPE '\\' LIMIT 1"
                    ),
                    (*source_files, f"%{suffix}"),
                ).fetchone()
                if row:
                    out.append((candidate, str(row[1] or "")))
                    break
    return out


def _classify_level_mismatch(level: str, grade: int) -> bool:
    if level == "a1" and grade >= 7:
        return True
    return level == "a2" and grade >= 10


def _audit_citation(
    cite: Citation, plan_text: str, conn: sqlite3.Connection
) -> Finding:
    canonical = CANONICAL_TRANSLITS.get(cite.author)

    if canonical is None:
        # UNKNOWN_AUTHOR — note if SUGGESTED_TRANSLITS would resolve it.
        suggested = SUGGESTED_TRANSLITS.get(cite.author)
        if suggested:
            files = _source_files_for(conn, suggested, cite.grade)
            if files:
                fix = (
                    f"add {cite.author!r}: {suggested!r} to "
                    f"_TEXTBOOK_AUTHOR_TRANSLITS (corpus has {files[0]})"
                )
            else:
                fix = (
                    f"add {cite.author!r}: {suggested!r} to "
                    f"_TEXTBOOK_AUTHOR_TRANSLITS — but Grade "
                    f"{cite.grade} not in corpus"
                )
        else:
            fix = (
                f"unknown author {cite.author!r}; verify against "
                "data/sources.db"
            )
        return Finding(citation=cite, mode="UNKNOWN_AUTHOR", detail=fix)

    files = _source_files_for(conn, canonical, cite.grade)
    if not files:
        return Finding(
            citation=cite,
            mode="GHOST_SOURCE",
            detail=(
                f"{cite.author} Grade {cite.grade} not in corpus "
                f"(translits tried: {canonical})"
            ),
            suggested_fix="drop citation or replace with a grade in corpus",
        )

    chunk = _fetch_chunk(conn, files, cite.page)
    if chunk is None:
        nearby = _nearby_pages(conn, files, cite.page)
        if nearby:
            near_str = "; ".join(f"p.{p} ({t})" for p, t in nearby[:3])
            fix = f"nearest pages with content: {near_str}"
        else:
            fix = f"no chunk near p.{cite.page} in {files[0]}"
        return Finding(
            citation=cite,
            mode="GHOST_PAGE",
            detail=(
                f"page {cite.page} not in corpus for "
                f"{', '.join(files)}"
            ),
            resolved_source_file=files[0],
            suggested_fix=fix,
        )

    # Chunk exists. Topic-mismatch + level-mismatch evaluation.
    plan_stems = _content_words(plan_text)
    chunk_text = f"{chunk.get('title') or ''} {chunk.get('text') or ''}"
    chunk_stems = _content_words(chunk_text)
    overlap = plan_stems & chunk_stems
    overlap_count = len(overlap)

    level_warn = _classify_level_mismatch(cite.level, cite.grade)

    if overlap_count < 3:
        return Finding(
            citation=cite,
            mode="TOPIC_MISMATCH",
            detail=(
                f"chunk title {chunk['title']!r}; only {overlap_count} "
                "shared content stems with plan topic"
            ),
            chunk_preview=(chunk.get("text") or "")[:300].replace("\n", " "),
            resolved_source_file=chunk["source_file"],
            chunk_title=str(chunk.get("title") or ""),
            overlap=overlap_count,
            topic_keywords=sorted(overlap),
            suggested_fix=(
                "verify topic relevance; drop or replace with on-topic page"
            ),
        )

    if level_warn:
        return Finding(
            citation=cite,
            mode="LEVEL_MISMATCH",
            detail=(
                f"{cite.level.upper()} plan cites Grade {cite.grade} "
                "textbook (above level)"
            ),
            chunk_preview=(chunk.get("text") or "")[:300].replace("\n", " "),
            resolved_source_file=chunk["source_file"],
            chunk_title=str(chunk.get("title") or ""),
            overlap=overlap_count,
            topic_keywords=sorted(overlap),
            suggested_fix=(
                "verify pedagogical level fit; prefer Grade <=6 source if available"
            ),
        )

    return Finding(
        citation=cite,
        mode="OK",
        chunk_preview=(chunk.get("text") or "")[:300].replace("\n", " "),
        resolved_source_file=chunk["source_file"],
        chunk_title=str(chunk.get("title") or ""),
        overlap=overlap_count,
        topic_keywords=sorted(overlap),
    )


def _collect(level: str) -> tuple[list[Citation], dict[str, str]]:
    cites: list[Citation] = []
    plan_text_by_slug: dict[str, str] = {}
    for plan_path in sorted((PLANS_ROOT / level).glob("*.yaml")):
        slug = plan_path.stem
        with plan_path.open(encoding="utf-8") as f:
            plan = yaml.safe_load(f) or {}
        plan_text_by_slug[slug] = " ".join(_topic_keywords(plan))
        cites.extend(_extract_citations(plan_path, level))
    return cites, plan_text_by_slug


def _render_markdown(findings: list[Finding], totals: dict) -> str:
    lines: list[str] = []
    lines.append("# A1 + A2 plan_references audit")
    lines.append("")
    lines.append(
        f"Generated: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d')}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Plans audited: **{totals['plans']}**")
    lines.append(f"  - A1: {totals['plans_a1']}")
    lines.append(f"  - A2: {totals['plans_a2']}")
    lines.append(
        f"- Paged citations extracted: **{totals['citations']}**"
    )
    lines.append("- By failure mode:")
    for mode in (
        "OK",
        "GHOST_SOURCE",
        "GHOST_PAGE",
        "TOPIC_MISMATCH",
        "LEVEL_MISMATCH",
        "UNKNOWN_AUTHOR",
    ):
        lines.append(f"  - {mode}: {totals['by_mode'].get(mode, 0)}")
    lines.append("")
    lines.append(
        "Failure modes are reported separately: a single citation may be both "
        "TOPIC_MISMATCH and LEVEL_MISMATCH; the audit assigns the strictest "
        "(TOPIC_MISMATCH first), and LEVEL_MISMATCH is listed alongside in the "
        "aggregate findings."
    )
    lines.append("")

    for level in ("a1", "a2"):
        level_findings = [
            f
            for f in findings
            if f.citation.level == level and f.mode != "OK"
        ]
        lines.append(f"## {level.upper()} — broken citations")
        lines.append("")
        if not level_findings:
            lines.append(f"_No broken citations in {level.upper()}._")
            lines.append("")
            continue
        # Group by plan slug, sorted alphabetically.
        by_plan: dict[str, list[Finding]] = {}
        for f in level_findings:
            by_plan.setdefault(f.citation.plan_slug, []).append(f)
        for slug in sorted(by_plan):
            lines.append(f"### {slug}")
            lines.append("")
            lines.append(
                "| citation | mode | corpus reality | suggested fix |"
            )
            lines.append("| --- | --- | --- | --- |")
            for f in sorted(
                by_plan[slug],
                key=lambda f: (f.citation.ref_index, f.citation.raw),
            ):
                detail = f.detail.replace("|", "\\|")
                fix = (f.suggested_fix or "").replace("|", "\\|")
                if f.mode == "TOPIC_MISMATCH" and f.chunk_preview:
                    detail += (
                        f"<br>chunk text (first 300 chars): "
                        f'_"{f.chunk_preview.replace("|", "\\|")[:300]}"_'
                    )
                if f.mode == "LEVEL_MISMATCH" and f.chunk_title:
                    detail += f"<br>chunk title: _{f.chunk_title}_"
                lines.append(
                    f"| `{f.citation.raw}` | {f.mode} | {detail} | {fix} |"
                )
            lines.append("")

    lines.append("## Aggregate findings")
    lines.append("")
    lines.append("### Authors to add to `_TEXTBOOK_AUTHOR_TRANSLITS`")
    lines.append("")
    unknown_by_author: dict[str, int] = {}
    for f in findings:
        if f.mode == "UNKNOWN_AUTHOR":
            unknown_by_author[f.citation.author] = (
                unknown_by_author.get(f.citation.author, 0) + 1
            )
    if unknown_by_author:
        lines.append(
            "| author | citations affected | suggested translits | corpus has it? |"
        )
        lines.append("| --- | --- | --- | --- |")
        for author in sorted(unknown_by_author):
            translits = SUGGESTED_TRANSLITS.get(author, [])
            in_corpus = "yes" if translits else "unknown"
            lines.append(
                f"| {author} | {unknown_by_author[author]} | "
                f"{translits or '—'} | {in_corpus} |"
            )
    else:
        lines.append("_All cited authors are in `_TEXTBOOK_AUTHOR_TRANSLITS`._")
    lines.append("")

    lines.append("### Level-mismatch summary")
    lines.append("")
    lvl_rows: dict[tuple[str, str, int], int] = {}
    for f in findings:
        if _classify_level_mismatch(f.citation.level, f.citation.grade):
            key = (f.citation.level, f.citation.author, f.citation.grade)
            lvl_rows[key] = lvl_rows.get(key, 0) + 1
    if lvl_rows:
        lines.append("| level | author | grade | citations |")
        lines.append("| --- | --- | --- | --- |")
        for (lvl, author, grade), cnt in sorted(lvl_rows.items()):
            lines.append(
                f"| {lvl.upper()} | {author} | Grade {grade} | {cnt} |"
            )
    else:
        lines.append("_No A1 plan cites Grade >=7; no A2 plan cites Grade >=10._")
    lines.append("")

    lines.append("### Ghost sources by author + grade")
    lines.append("")
    ghost_rows: dict[tuple[str, int], int] = {}
    for f in findings:
        if f.mode == "GHOST_SOURCE":
            ghost_rows[(f.citation.author, f.citation.grade)] = (
                ghost_rows.get((f.citation.author, f.citation.grade), 0) + 1
            )
    if ghost_rows:
        lines.append("| author | grade | citations |")
        lines.append("| --- | --- | --- |")
        for (author, grade), cnt in sorted(ghost_rows.items()):
            lines.append(f"| {author} | Grade {grade} | {cnt} |")
    else:
        lines.append("_No ghost sources._")
    lines.append("")

    lines.append("### Notes")
    lines.append("")
    lines.append(
        "- TOPIC_MISMATCH is heuristic: a citation is flagged when fewer than "
        "3 content-word stems overlap between the plan's topic block "
        "(title + subtitle + objectives + grammar + content_outline sections) "
        "and the resolved chunk's title + body. False positives are expected; "
        "verify each row before editing the plan."
    )
    lines.append(
        "- LEVEL_MISMATCH is policy: A1 cites Grade >= 7, A2 cites Grade >= 10. "
        "Not always wrong (school textbooks include simple paradigm tables at "
        "any level), but flagged for orchestrator review."
    )
    lines.append(
        "- GHOST_SOURCE and GHOST_PAGE are deterministic against "
        "`data/sources.db` using the FIXED LIKE pattern "
        "(`%-translit-%` OR `%-translit`)."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory for findings.json and REPORT.md.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=SOURCES_DB,
        help="Path to data/sources.db.",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        print(f"ERROR: sources.db not found at {args.db}", file=sys.stderr)
        return 2

    a1_cites, a1_text = _collect("a1")
    a2_cites, a2_text = _collect("a2")
    all_cites = a1_cites + a2_cites
    plan_text_by_slug = {**a1_text, **a2_text}

    findings: list[Finding] = []
    with sqlite3.connect(str(args.db)) as conn:
        conn.row_factory = sqlite3.Row
        for cite in all_cites:
            f = _audit_citation(
                cite, plan_text_by_slug.get(cite.plan_slug, ""), conn
            )
            findings.append(f)

    by_mode: dict[str, int] = {}
    for f in findings:
        by_mode[f.mode] = by_mode.get(f.mode, 0) + 1

    a1_plan_count = len(list((PLANS_ROOT / "a1").glob("*.yaml")))
    a2_plan_count = len(list((PLANS_ROOT / "a2").glob("*.yaml")))
    totals = {
        "plans": a1_plan_count + a2_plan_count,
        "plans_a1": a1_plan_count,
        "plans_a2": a2_plan_count,
        "citations": len(all_cites),
        "by_mode": by_mode,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)

    findings_sorted = sorted(
        findings,
        key=lambda f: (
            f.citation.level,
            f.citation.plan_slug,
            f.citation.ref_index,
            f.citation.raw,
        ),
    )
    payload = {
        "totals": totals,
        "findings": [
            {
                "level": f.citation.level,
                "plan_slug": f.citation.plan_slug,
                "citation": f.citation.raw,
                "author": f.citation.author,
                "grade": f.citation.grade,
                "page": f.citation.page,
                "field": f.citation.field_source,
                "mode": f.mode,
                "detail": f.detail,
                "resolved_source_file": f.resolved_source_file,
                "chunk_title": f.chunk_title,
                "overlap_stems": f.overlap,
                "topic_keywords": f.topic_keywords,
                "suggested_fix": f.suggested_fix,
            }
            for f in findings_sorted
        ],
    }
    (args.out_dir / "findings.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    (args.out_dir / "REPORT.md").write_text(
        _render_markdown(findings_sorted, totals), encoding="utf-8"
    )

    summary = (
        f"plans={totals['plans']} citations={totals['citations']} "
        f"OK={by_mode.get('OK', 0)} "
        f"GHOST_SOURCE={by_mode.get('GHOST_SOURCE', 0)} "
        f"GHOST_PAGE={by_mode.get('GHOST_PAGE', 0)} "
        f"TOPIC_MISMATCH={by_mode.get('TOPIC_MISMATCH', 0)} "
        f"LEVEL_MISMATCH={by_mode.get('LEVEL_MISMATCH', 0)} "
        f"UNKNOWN_AUTHOR={by_mode.get('UNKNOWN_AUTHOR', 0)}"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
