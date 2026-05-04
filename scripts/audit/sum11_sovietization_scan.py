#!/usr/bin/env python3
"""Scan СУМ-11 entries for Sovietization markers and populate the
``sovietization_risk`` and ``sovietization_keywords`` columns added by
``migrations/2026-05-04-1659-sum11-sovietization-flag.sql``.

What this does
--------------
СУМ-11 (1970–1980) was published in the late Soviet era and contains
ideologically framed definitions for many politically loaded headwords —
e.g. ``ленінізм`` is defined as "ідеологія Комуністичної партії
Радянського Союзу", and ``більшовик`` is defined via Soviet-era
citations from 1956.

Without a flag layer, downstream reviewers reading from
``mcp__sources__search_definitions`` cannot tell whether a definition
is neutrally academic or ideologically framed. This script populates a
two-tier flag:

  - ``sovietization_risk = 0`` — no Soviet-era markers
  - ``sovietization_risk = 1`` — at least one keyword match in
    ``definition`` or ``text``
  - ``sovietization_risk = 2`` — three or more matches **or** a
    definition that opens with a Soviet-ideology framing
    (e.g. starts with "Учення В. І. Леніна" or
    "Ідеологія Комуністичної партії Радянського Союзу")

The reviewer / writer prompts can then refuse, override, or escalate
when ``sovietization_risk > 0`` for ideologically loaded headwords.

Usage
-----
``.venv/bin/python scripts/audit/sum11_sovietization_scan.py
    --db data/sources.db
    [--report audit/sum11_sovietization_scan_<DATE>.md]
    [--dry-run]``

Outputs
-------
* Updates ``sovietization_risk`` and ``sovietization_keywords`` on every
  row of ``sum11`` in the target DB (unless ``--dry-run``).
* Writes a markdown audit report to the given path summarising the
  flagged entry count, by-keyword breakdown, top-50 most-Sovietized
  entries, and a reviewer caveat.

Exit codes
----------
* 0 on success.
* 1 on DB errors, missing migration columns, or schema mismatch.
* 2 on user-input errors (bad CLI args, missing files).

Related
-------
* Issue #1659 — adds the flag layer
* Parent EPIC #1657 — verification-layer architecture
* Migration: ``migrations/2026-05-04-1659-sum11-sovietization-flag.sql``
"""

from __future__ import annotations

import argparse
import datetime
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Soviet-era keyword stems. Each entry is a Cyrillic stem that triggers a
# match. We use SQL LIKE / Python regex with explicit suffix wildcards so
# inflected forms (ленінська, більшовицький, радянського, etc.) all match.
#
# These were chosen from:
#   * the parent issue #1659's stated keyword list (ленін*, більшовик*, etc.)
#   * the Explore agent's spot-check report (2026-05-04) which empirically
#     confirmed ленінізм, більшовик, національний, москаль hits.
#
# Stems are matched case-insensitively. We deliberately do NOT include very
# generic terms like "колгосп" or "радгосп" because they appear in many
# neutral agricultural definitions as well — false-positive risk is too high.
SOVIET_KEYWORD_STEMS: tuple[str, ...] = (
    "ленін",          # ленін, ленінський, ленінізм, ленінізму, Леніним
    "більшов",        # більшовик, більшовицький, більшовизм, більшовизму
                      # (к↔ц palatalization breaks "більшовик" prefix match)
    "радянськ",       # радянський, радянського, радянською, Радянськ
    "соціалістичн",   # соціалістичний, соціалістичної
    "комуністичн",    # комуністичний, комуністичної, Комуністичної
    "пролетар",       # пролетарський, пролетар, пролетаріат
    "маркс",          # marксизм, маркс-истський, маркс-ист (covers both)
    "комсомол",       # комсомолець, комсомольський, комсомолу
    "піонер",         # ambiguous — disambiguated below (AMBIGUOUS_STEMS)
    "колективіз",     # колективізація — Soviet-era forced collectivisation
    "СРСР",
    "КПРС",
    "КПУ",
    "ВКП",
    "Жовтнев",        # Жовтневої революції — Capitalised proper noun (1917 ref)
)

# Some stems are ambiguous (e.g. "піонер" can mean an explorer/pioneer in
# neutral contexts as well as a Soviet-era youth organisation member). For
# those, require co-occurrence with a less ambiguous Soviet stem in the
# same definition. Otherwise the flag would over-trigger.
AMBIGUOUS_STEMS: frozenset[str] = frozenset({"піонер"})

# Patterns that identify a Soviet-ideology FRAMING in the definition opener
# — escalate from risk=1 to risk=2. These are exact substrings (case-insens)
# anchored near the start of the definition.
SOVIET_FRAMING_OPENERS: tuple[str, ...] = (
    "учення в. і. леніна",
    "учення в.і. леніна",
    "ідеологія комуністичної партії",
    "ідеологія комуністичної партіi",
    "ідеологія кпрс",
    "ленінська національна політика",
    "соціалістична батьківщина",
    "великий жовтень",
    "велика жовтнева",
)

# Compiled once at module load.
_KEYWORD_REGEX = re.compile(
    r"(?<![A-Za-zА-Яа-яЁёІіЇїЄєҐґ])(" + "|".join(SOVIET_KEYWORD_STEMS) + r")",
    re.IGNORECASE,
)


@dataclass
class ScanStats:
    total_rows: int = 0
    flagged_low: int = 0   # risk == 1
    flagged_high: int = 0  # risk == 2
    by_keyword: dict[str, int] = field(default_factory=dict)
    top_examples: list[tuple[str, int, str]] = field(default_factory=list)
    # ^ list of (word, match_count, top_keywords_csv)

    @property
    def flagged_total(self) -> int:
        return self.flagged_low + self.flagged_high

    @property
    def flagged_pct(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return 100.0 * self.flagged_total / self.total_rows


def classify_entry(definition: str, text: str) -> tuple[int, list[str]]:
    """Return (risk_level, sorted_unique_keywords) for one row."""
    haystack = f"{definition or ''}\n{text or ''}"
    haystack_lower = haystack.lower()

    raw_matches = _KEYWORD_REGEX.findall(haystack)
    if not raw_matches:
        return 0, []

    # Disambiguate: if the only matches are ambiguous stems (e.g. just
    # "піонер" without any other Soviet stem), drop the flag.
    matched_stems = {m.lower() for m in raw_matches}
    non_ambiguous = matched_stems - AMBIGUOUS_STEMS
    if not non_ambiguous and AMBIGUOUS_STEMS & matched_stems:
        return 0, []

    sorted_keywords = sorted(matched_stems)

    # Escalation rule 1: framing opener present → risk = 2
    head = haystack_lower[:200]
    if any(opener in head for opener in SOVIET_FRAMING_OPENERS):
        return 2, sorted_keywords

    # Escalation rule 2: ≥ 3 distinct keyword stems → risk = 2
    if len(sorted_keywords) >= 3:
        return 2, sorted_keywords

    return 1, sorted_keywords


def verify_migration_columns(conn: sqlite3.Connection) -> None:
    """Fail fast if the migration hasn't been applied."""
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(sum11);").fetchall()
    }
    missing = {"sovietization_risk", "sovietization_keywords"} - cols
    if missing:
        print(
            f"ERROR: sum11 is missing columns {missing}. Apply migration "
            "migrations/2026-05-04-1659-sum11-sovietization-flag.sql first.",
            file=sys.stderr,
        )
        sys.exit(1)


def scan_and_update(
    conn: sqlite3.Connection,
    *,
    dry_run: bool,
) -> ScanStats:
    stats = ScanStats()

    rows = conn.execute(
        "SELECT id, word, definition, text FROM sum11"
    ).fetchall()
    stats.total_rows = len(rows)

    # Buffer updates and apply in one transaction at the end for speed.
    update_buffer: list[tuple[int, str, int]] = []
    flagged_for_top: list[tuple[str, int, list[str]]] = []

    for row_id, word, definition, text in rows:
        risk, keywords = classify_entry(definition or "", text or "")
        if risk == 0:
            continue
        if risk == 1:
            stats.flagged_low += 1
        else:
            stats.flagged_high += 1
        for k in keywords:
            stats.by_keyword[k] = stats.by_keyword.get(k, 0) + 1
        update_buffer.append((risk, ",".join(keywords), row_id))
        flagged_for_top.append((word, len(keywords), keywords))

    # Top-50 most-Sovietized: sort by keyword-match count desc.
    flagged_for_top.sort(key=lambda x: (-x[1], x[0]))
    stats.top_examples = [
        (word, count, ",".join(kws))
        for word, count, kws in flagged_for_top[:50]
    ]

    if dry_run:
        print(f"[dry-run] would update {len(update_buffer)} rows")
        return stats

    print(f"Updating {len(update_buffer)} flagged rows...")
    with conn:
        conn.executemany(
            "UPDATE sum11 SET sovietization_risk = ?, "
            "sovietization_keywords = ? WHERE id = ?",
            update_buffer,
        )

    return stats


def write_audit_report(stats: ScanStats, report_path: Path, db_path: Path) -> None:
    today = datetime.date.today().isoformat()
    by_kw_lines = [
        f"| `{kw}` | {count} |"
        for kw, count in sorted(stats.by_keyword.items(), key=lambda x: -x[1])
    ]
    top_lines = [
        f"| `{word}` | {count} | `{keywords}` |"
        for word, count, keywords in stats.top_examples
    ]
    body = f"""# СУМ-11 Sovietization scan — {today}

**Issue:** #1659  (parent EPIC: #1657)
**DB scanned:** `{db_path}`
**Total СУМ-11 rows:** {stats.total_rows:,}

## Headline numbers

| Metric | Value |
|---|---|
| Flagged (any risk > 0) | **{stats.flagged_total:,}** ({stats.flagged_pct:.2f}% of corpus) |
| Risk = 1 (single-keyword match) | {stats.flagged_low:,} |
| Risk = 2 (high — framing opener OR ≥3 distinct keywords) | {stats.flagged_high:,} |

## Match counts by keyword stem

| Keyword stem | Flagged entries containing it |
|---|---|
{chr(10).join(by_kw_lines) or '| — | — |'}

## Top-50 most-Sovietized entries (ranked by distinct-keyword count)

| Headword | Distinct keywords matched | Keywords |
|---|---|---|
{chr(10).join(top_lines) or '| — | — | — |'}

## Reviewer caveat (use this verbatim in V7 review prompts)

> When pulling a definition from `mcp__sources__search_definitions` for a
> politically/ideologically loaded term, check `sovietization_risk` in the
> result row. If `sovietization_risk > 0`, treat the definition as
> potentially Soviet-framed: do not reproduce verbatim, prefer СУМ-20 or
> Грінченко 1907 for the same headword, or omit the definition and route
> to a neutral phrasing.

## How to reproduce this report

```
.venv/bin/python scripts/audit/sum11_sovietization_scan.py \\
    --db data/sources.db \\
    --report audit/sum11_sovietization_scan_{today}.md
```

The scan is idempotent — re-running it overwrites the flag columns based
on the current keyword stems. To extend the keyword list, edit
`SOVIET_KEYWORD_STEMS` in the script, then re-run.

## Anti-scope (recorded for future readers)

This scan **does not delete or rewrite Sovietized entries**. The 1970–1980
framing is historically real and must remain visible — the flag exists so
downstream reviewers can override at decision time, not so the project
silently rewrites the source.
"""
    report_path.write_text(body, encoding="utf-8")
    print(f"Audit report written to {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="sum11_sovietization_scan",
        description=(
            "Scan СУМ-11 entries for Soviet-era ideological framing and "
            "populate sovietization_risk / sovietization_keywords columns "
            "in data/sources.db. Use after applying migration "
            "2026-05-04-1659-sum11-sovietization-flag.sql.\n\n"
            "When to use: once after the migration; rerun whenever the "
            "keyword stem list is extended."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/sum11_sovietization_scan.py \\\n"
            "      --db data/sources.db \\\n"
            "      --report audit/sum11_sovietization_scan_2026-05-04.md\n"
            "\n"
            "  .venv/bin/python scripts/audit/sum11_sovietization_scan.py \\\n"
            "      --db /tmp/sources_test.db --dry-run\n"
            "\n"
            "Outputs:\n"
            "  - Mutates sovietization_risk and sovietization_keywords columns\n"
            "    in the target DB (unless --dry-run).\n"
            "  - Writes an audit report markdown file at --report path.\n"
            "\n"
            "Exit codes:\n"
            "  0 = success\n"
            "  1 = schema or DB error (e.g. migration not applied)\n"
            "  2 = bad CLI args / missing input file\n"
            "\n"
            "Related:\n"
            "  Issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1659\n"
            "  EPIC : #1657\n"
            "  Migration: migrations/2026-05-04-1659-sum11-sovietization-flag.sql\n"
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to data/sources.db SQLite file (e.g. data/sources.db).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help=(
            "Optional path for the audit report markdown. Defaults to "
            "audit/sum11_sovietization_scan_<TODAY>.md."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute stats and report but do not modify the DB.",
    )
    args = parser.parse_args()

    if not args.db.exists():
        print(f"ERROR: DB file not found: {args.db}", file=sys.stderr)
        return 2

    today = datetime.date.today().isoformat()
    report_path = (
        args.report
        if args.report is not None
        else Path("audit") / f"sum11_sovietization_scan_{today}.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    try:
        verify_migration_columns(conn)
        stats = scan_and_update(conn, dry_run=args.dry_run)
    finally:
        conn.close()

    write_audit_report(stats, report_path, args.db)

    print(
        f"Scanned {stats.total_rows:,} rows. "
        f"Flagged {stats.flagged_total:,} "
        f"({stats.flagged_pct:.2f}% — {stats.flagged_high:,} high, "
        f"{stats.flagged_low:,} low)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
