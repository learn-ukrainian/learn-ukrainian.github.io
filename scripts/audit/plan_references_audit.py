#!/usr/bin/env python3
"""Audit plan_references in module plans for one or more CEFR tracks.

Walks every plan YAML under curriculum/l2-uk-en/plans/{track}/ for each
requested track, extracts "Author Grade N, p.M" citations from the
`references` field and `content_outline` points, resolves each against
data/sources.db, and emits a deterministic JSON + Markdown report
classifying failure modes:

    GHOST_SOURCE      source_file for (author, grade) not in corpus
    GHOST_PAGE        source_file exists but no chunk for that page
    TOPIC_MISMATCH    chunk exists but text is unrelated to the plan topic
    LEVEL_MISMATCH    grade >= PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS[track] (per-track policy)
    UNKNOWN_AUTHOR    author not present in textbooks.author_uk
    OK                resolves cleanly with on-topic chunk

The resolver queries ``textbooks.author_uk`` directly (Cyrillic-native).
Spelling variants are canonicalized via ``_canonicalize_author_uk``
(Литвінова ≡ Литвінова, Пономарьова ≡ Пономарова). See
``docs/decisions/2026-05-15-cyrillic-native-matcher.md`` for the
decolonization rationale.

Usage:
    .venv/bin/python scripts/audit/plan_references_audit.py
    .venv/bin/python scripts/audit/plan_references_audit.py --tracks a1,a2
    .venv/bin/python scripts/audit/plan_references_audit.py \\
        --tracks b1,b2 --out-dir audit/b1-b2-plan-references-2026-05-15

Issue: #1975
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"
SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUT_DIR = PROJECT_ROOT / "audit" / "a1-a2-plan-references-2026-05-15"
DEFAULT_TRACKS = ("a1", "a2")

# LEVEL_MISMATCH thresholds per track. A citation flags when its
# textbook Grade is >= the track's threshold. Ukrainian school grades
# cap at 11, so B1/B2/C1/C2 set to 11 means "only flag literal Grade 11
# citations" — a low-rate signal kept for completeness rather than a
# common failure mode at higher CEFR levels.
PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS: dict[str, int] = {
    "a1": 7,
    "a2": 10,
    "b1": 11,
    "b2": 11,
    "c1": 11,
    "c2": 11,
}

# Cyrillic spelling-variant canonicalization. Pure Cyrillic-to-Cyrillic
# mapping for plan citations that use a non-canonical spelling
# (Литвінова → Літвінова; Пономарьова → Пономарова). Mirrors
# scripts/build/linear_pipeline.py:_CYRILLIC_AUTHOR_CANONICAL. Edit
# there, not here — this is the audit's reference snapshot.
_CYRILLIC_AUTHOR_CANONICAL: dict[str, str] = {
    "Литвінова": "Літвінова",
    "Пономарьова": "Пономарова",
}


def _canonicalize_author_uk(author: str) -> str:
    """Canonical-form lookup; pass-through on miss."""
    return _CYRILLIC_AUTHOR_CANONICAL.get(author, author)

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
    level: str  # one of PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS keys, e.g. "a1" | "a2" | "b1"
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
    conn: sqlite3.Connection, author_uk: str, grade: int
) -> list[str]:
    """Cyrillic-native matcher: queries textbooks.author_uk + grade directly.

    Applies _canonicalize_author_uk to handle spelling variants
    (Литвінова ≡ Літвінова, Пономарьова ≡ Пономарова).
    """
    if not author_uk:
        return []
    canonical = _canonicalize_author_uk(author_uk)
    rows = conn.execute(
        (
            "SELECT DISTINCT source_file FROM textbooks "
            "WHERE author_uk = ? AND grade = ?"
        ),
        (canonical, str(grade)),
    ).fetchall()
    return sorted(str(r[0]) for r in rows)


def _author_uk_exists(conn: sqlite3.Connection, author_uk: str) -> bool:
    """True iff at least one row exists with this Cyrillic author at any grade."""
    canonical = _canonicalize_author_uk(author_uk)
    row = conn.execute(
        "SELECT 1 FROM textbooks WHERE author_uk = ? LIMIT 1",
        (canonical,),
    ).fetchone()
    return row is not None


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
    """Flag when ``grade`` is at/above the track's threshold.

    Tracks not listed in :data:`PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS` never flag (defensive
    default for unknown tracks); tests assert this behavior.
    """
    threshold = PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS.get(level)
    if threshold is None:
        return False
    return grade >= threshold


def _audit_citation(
    cite: Citation, plan_text: str, conn: sqlite3.Connection
) -> Finding:
    if not _author_uk_exists(conn, cite.author):
        fix = (
            f"unknown author {cite.author!r}; not present in "
            "textbooks.author_uk (verify spelling or add to corpus)"
        )
        return Finding(citation=cite, mode="UNKNOWN_AUTHOR", detail=fix)

    files = _source_files_for(conn, cite.author, cite.grade)
    if not files:
        return Finding(
            citation=cite,
            mode="GHOST_SOURCE",
            detail=(
                f"{cite.author} Grade {cite.grade} not in corpus "
                f"(canonical: {_canonicalize_author_uk(cite.author)!r})"
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
        threshold = PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS.get(cite.level)
        if cite.level in ("a1", "a2"):
            fix_hint = "prefer Grade <=6 source if available"
        else:
            fix_hint = (
                f"verify Grade {cite.grade} content is genuinely "
                f"{cite.level.upper()}-appropriate"
            )
        return Finding(
            citation=cite,
            mode="LEVEL_MISMATCH",
            detail=(
                f"{cite.level.upper()} plan cites Grade {cite.grade} "
                f"textbook (threshold: Grade >= {threshold})"
            ),
            chunk_preview=(chunk.get("text") or "")[:300].replace("\n", " "),
            resolved_source_file=chunk["source_file"],
            chunk_title=str(chunk.get("title") or ""),
            overlap=overlap_count,
            topic_keywords=sorted(overlap),
            suggested_fix=f"verify pedagogical level fit; {fix_hint}",
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


def _render_markdown(
    findings: list[Finding], totals: dict, tracks: list[str]
) -> str:
    lines: list[str] = []
    track_label = " + ".join(t.upper() for t in tracks)
    lines.append(f"# {track_label} plan_references audit")
    lines.append("")
    lines.append(
        f"Generated: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d')}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Plans audited: **{totals['plans']}**")
    for t in tracks:
        lines.append(f"  - {t.upper()}: {totals['plans_by_track'].get(t, 0)}")
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
    lines.append("- LEVEL_MISMATCH thresholds (grade >= threshold flags):")
    for t in tracks:
        lines.append(
            f"  - {t.upper()}: Grade >= {PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS.get(t, '—')}"
        )
    lines.append("")
    lines.append(
        "Failure modes are reported separately: a single citation may be both "
        "TOPIC_MISMATCH and LEVEL_MISMATCH; the audit assigns the strictest "
        "(TOPIC_MISMATCH first), and LEVEL_MISMATCH is listed alongside in the "
        "aggregate findings."
    )
    lines.append("")

    for level in tracks:
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
    lines.append("### Authors absent from `textbooks.author_uk`")
    lines.append("")
    unknown_by_author: dict[str, int] = {}
    for f in findings:
        if f.mode == "UNKNOWN_AUTHOR":
            unknown_by_author[f.citation.author] = (
                unknown_by_author.get(f.citation.author, 0) + 1
            )
    if unknown_by_author:
        lines.append("| author | citations affected |")
        lines.append("| --- | --- |")
        for author in sorted(unknown_by_author):
            lines.append(f"| {author} | {unknown_by_author[author]} |")
    else:
        lines.append(
            "_All cited authors resolve against `textbooks.author_uk`._"
        )
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
        threshold_phrase = "; ".join(
            f"{t.upper()} Grade >= {PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS.get(t, '—')}"
            for t in tracks
        )
        lines.append(f"_No citations crossed thresholds: {threshold_phrase}._")
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
    threshold_summary = ", ".join(
        f"{t.upper()} Grade >= {PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS.get(t, '—')}" for t in tracks
    )
    lines.append(
        f"- LEVEL_MISMATCH is policy: {threshold_summary}. "
        "Not always wrong (school textbooks include simple paradigm tables at "
        "any level), but flagged for orchestrator review."
    )
    lines.append(
        "- GHOST_SOURCE and GHOST_PAGE are deterministic against "
        "`data/sources.db` via direct `textbooks.author_uk = ? AND grade = ?` "
        "queries (Cyrillic-native matcher; see ADR "
        "`docs/decisions/2026-05-15-cyrillic-native-matcher.md`)."
    )
    lines.append("")
    return "\n".join(lines)


def _parse_tracks(raw: str) -> list[str]:
    tracks = [t.strip().lower() for t in raw.split(",") if t.strip()]
    if not tracks:
        raise argparse.ArgumentTypeError("--tracks must list >=1 track")
    unknown = [t for t in tracks if t not in PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown track(s) {unknown}; valid: {sorted(PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS)}"
        )
    return tracks


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
    parser.add_argument(
        "--tracks",
        type=_parse_tracks,
        default=list(DEFAULT_TRACKS),
        help=(
            "Comma-separated track list (default: a1,a2). Valid: "
            f"{sorted(PLAN_AUDIT_LEVEL_MISMATCH_THRESHOLDS)}."
        ),
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        print(f"ERROR: sources.db not found at {args.db}", file=sys.stderr)
        return 2

    tracks: list[str] = args.tracks
    all_cites: list[Citation] = []
    plan_text_by_slug: dict[str, str] = {}
    plans_by_track: dict[str, int] = {}
    for track in tracks:
        cites, text_map = _collect(track)
        all_cites.extend(cites)
        plan_text_by_slug.update(text_map)
        plans_by_track[track] = len(
            list((PLANS_ROOT / track).glob("*.yaml"))
        )

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

    totals = {
        "plans": sum(plans_by_track.values()),
        "plans_by_track": plans_by_track,
        "tracks": tracks,
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
        _render_markdown(findings_sorted, totals, tracks), encoding="utf-8"
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
