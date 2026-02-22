#!/usr/bin/env python3
"""
Backfill Key Facts Ledger (KFL) into seminar research files.

Converts old-format research files (## Хронологія + ## Ключові факти та цитати)
into the structured KFL YAML block expected by Phase D reviews.

Deterministic extraction for ~80% of fields; Gemini CLI for the rest
(forbidden_claims, ambiguous date normalization).

Usage:
    .venv/bin/python scripts/backfill_kfl.py --track b2-hist
    .venv/bin/python scripts/backfill_kfl.py --track c1-bio --dry-run
    .venv/bin/python scripts/backfill_kfl.py --all
    .venv/bin/python scripts/backfill_kfl.py --all --skip-llm

Issue: #626
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
GEMINI_BIN = shutil.which("gemini") or "/opt/homebrew/bin/gemini"

# Tracks that contain seminar research files
SEMINAR_TRACKS = ["b2-hist", "c1-bio", "c1-hist"]
# Tracks where subjects are people (have birth/death dates)
BIOGRAPHICAL_TRACKS = {"c1-bio"}

# Death keywords in Ukrainian chronology
_DEATH_KEYWORDS = re.compile(
    r"(помер|загинув|вбит|смерть|†|похован|розстрілян|страчен|убит)",
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def extract_subject(content: str) -> str:
    """Extract subject from H1 heading: # Дослідження: {title}"""
    m = re.search(r"^# Дослідження:\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_section(content: str, header: str) -> str:
    """Extract content of a ## section (up to next ## or EOF)."""
    pattern = rf"^## {re.escape(header)}\s*\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_chronology(section: str) -> list[dict[str, Any]]:
    """Parse ## Хронологія bullets into structured events.

    Format: - **{date}** — {event}
    Returns list of {raw_date, event, year (int or None)}
    """
    events = []
    for m in re.finditer(
        r"^- \*\*([^*]+)\*\*\s*[—–-]\s*(.+)$", section, re.MULTILINE
    ):
        raw_date = m.group(1).strip()
        event_text = m.group(2).strip()
        year = _extract_year(raw_date)
        events.append({
            "raw_date": raw_date,
            "event": event_text,
            "year": year,
        })
    return events


def _extract_year(date_str: str) -> int | None:
    """Extract a single year from a date string.

    Handles: "1896 р.", "~890–920 рр.", "5500–5400 рр. до н.е.",
             "11 липня 969 р.", "9 вересня / 18 жовтня 957 р."

    Returns the primary year as int, or None for unparseable dates.
    BCE dates return negative values.
    """
    s = date_str.strip().replace("~", "")

    # Check for BCE marker
    is_bce = bool(re.search(r"до\s+н\.?\s*е\.?", s, re.IGNORECASE))

    # Century format: "VII ст." → approximate year
    century_m = re.match(r"^([IVXLCDM]+)\s+ст", s, re.IGNORECASE)
    if century_m:
        century = _roman_to_int(century_m.group(1))
        if century:
            year = (century - 1) * 100 + 50  # midpoint of century
            return -year if is_bce else year

    # Find all 4-digit years
    years = [int(y) for y in re.findall(r"\b(\d{4})\b", s)]
    if not years:
        # Try 3-digit years (e.g., "882 рік")
        years = [int(y) for y in re.findall(r"\b(\d{3})\b", s)]
    if not years:
        return None

    year = years[0]  # Take first year in ranges
    return -year if is_bce else year


def _roman_to_int(s: str) -> int | None:
    """Convert Roman numeral to integer."""
    roman_vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    s = s.upper()
    result = 0
    prev = 0
    for ch in reversed(s):
        val = roman_vals.get(ch)
        if val is None:
            return None
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result if result > 0 else None


def parse_quotes(section: str) -> list[dict[str, str]]:
    """Parse ## Ключові факти та цитати for quoted text.

    Extracts guillemet-quoted text «...» and surrounding context for
    source/attribution.
    """
    quotes = []
    for line in section.split("\n"):
        line = line.strip()
        if not line.startswith("-"):
            continue

        # Extract guillemet-quoted text
        quote_matches = re.findall(r"[«\u201c]([^»\u201d]+)[»\u201d]", line)
        if not quote_matches:
            continue

        # Extract label for attribution: **Label:** or **Label (source):**
        label_m = re.match(r"^-\s*\*\*([^*]+)\*\*:?\s*", line)
        label = label_m.group(1).strip().rstrip(":") if label_m else ""

        # Parse attribution from label
        source = ""
        attribution = ""
        if label:
            # "Цитата Хвойки (1896)" → attribution="Хвойка", source="1896"
            attr_m = re.match(r"Цитата\s+([^(]+?)(?:\s*\(([^)]+)\))?$", label)
            if attr_m:
                attribution = attr_m.group(1).strip()
                source = attr_m.group(2).strip() if attr_m.group(2) else ""
            # "Цитата (ПМЛ про 3-тю помсту)" → source="ПМЛ"
            elif "Цитата" in label:
                src_m = re.search(r"\(([^)]+)\)", label)
                if src_m:
                    source = src_m.group(1).strip()

        for qt in quote_matches:
            quotes.append({
                "text": qt.strip(),
                "source": source,
                "attribution": attribution,
            })

    return quotes


def parse_decolonization(section: str) -> list[str]:
    """Extract imperial/Soviet myths from ## Деколонізаційний контекст.

    These become the basis for forbidden_claims.
    Handles multiple label formats: English, Ukrainian, with/without colon.
    """
    # All known myth label variants (case-insensitive match)
    # Labels may include parenthetical qualifiers: "Імперський міф (польський)"
    _MYTH_LABELS = (
        r"Imperial/Soviet [Mm]yth(?:\s*\([^)]*\))?"
        r"|Imperial\s*(?:\([^)]*\)\s*)?[Mm]yth"
        r"|Soviet [Mm]yth"
        r"|Імперський/Радянський міф"
        r"|Радянський/Імперський міф"
        r"|Імперський/Польський міф"
        r"|Імперський/радянський міф"
        r"|Російський/Радянський міф"
        r"|Імперський міф(?:\s*\([^)]*\))?"
        r"|Радянський міф"
        r"|Імперський наратив"
        r"|Міф(?:\s+про\s+[^*]+)?"
    )
    myths = []
    for m in re.finditer(
        rf"\*\*(?:{_MYTH_LABELS}):?\*\*:?\s*(.+?)(?=\n-|\Z)",
        section, re.DOTALL
    ):
        myth = m.group(1).strip()
        # Clean up multi-line myths
        myth = re.sub(r"\s+", " ", myth)
        if myth:
            myths.append(myth)
    return myths


def detect_vital_status(events: list[dict], content: str) -> str:
    """Determine if the subject is deceased based on chronology."""
    # Check last few events for death keywords
    for event in reversed(events[-3:]):
        if _DEATH_KEYWORDS.search(event["event"]):
            return "deceased"
    # Check full content for death references
    if _DEATH_KEYWORDS.search(content):
        return "deceased"
    return "unknown"


def detect_birth_death(events: list[dict]) -> tuple[str, str]:
    """Extract birth and death dates from chronology (biographical tracks only).

    Returns (birth_str, death_str) in "YYYY" or "~YYYY" format.
    """
    birth = ""
    death = ""

    if not events:
        return birth, death

    # First event often contains birth
    first = events[0]
    if first["year"] and any(kw in first["event"].lower()
                             for kw in ("народж", "народив", "народил", "час народження")):
        year = abs(first["year"])
        birth = f"~{year}" if "~" in first["raw_date"] else str(year)

    # Last few events may contain death
    for event in reversed(events[-3:]):
        if event["year"] and _DEATH_KEYWORDS.search(event["event"]):
            year = abs(event["year"])
            death = str(year)
            break

    return birth, death


# ---------------------------------------------------------------------------
# KFL YAML generation
# ---------------------------------------------------------------------------

def build_kfl_yaml(
    subject: str,
    events: list[dict],
    quotes: list[dict[str, str]],
    forbidden_claims: list[str],
    track: str,
) -> str:
    """Build the KFL YAML block string."""
    lines = [
        "## Key Facts Ledger",
        "<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->",
        "```yaml",
        f'subject: "{_yaml_escape(subject)}"',
    ]

    # Biographical fields (c1-bio only)
    is_bio = track in BIOGRAPHICAL_TRACKS
    if is_bio:
        vital = detect_vital_status(events, "")
        birth, death = detect_birth_death(events)
        lines.append(f'vital_status: "{vital}"')
        lines.append("dates:")
        if birth:
            lines.append(f'  birth: "{birth}"')
        if death:
            lines.append(f'  death: "{death}"')
    else:
        lines.append("dates:")

    # Key events
    lines.append("  key_events:")
    for ev in events:
        if ev["year"] is not None:
            lines.append(f"    - year: {ev['year']}")
            lines.append(f'      event: "{_yaml_escape(ev["event"][:200])}"')

    # Primary quotes
    if quotes:
        lines.append("primary_quotes:")
        for q in quotes[:5]:  # Cap at 5 quotes
            lines.append(f'  - text: "{_yaml_escape(q["text"][:300])}"')
            lines.append(f'    source: "{_yaml_escape(q["source"])}"')
            lines.append(f'    attribution: "{_yaml_escape(q["attribution"])}"')

    # Forbidden claims
    if forbidden_claims:
        lines.append("forbidden_claims:")
        for claim in forbidden_claims:
            lines.append(f'  - "{_yaml_escape(claim[:300])}"')

    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def _yaml_escape(s: str) -> str:
    """Escape characters that would break YAML double-quoted strings."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


# ---------------------------------------------------------------------------
# LLM-assisted enrichment
# ---------------------------------------------------------------------------

def enrich_with_llm(
    subject: str,
    myths: list[str],
    events: list[dict],
    track: str,
) -> list[str]:
    """Call Gemini to generate forbidden_claims from decolonization context.

    Falls back to deterministic myth extraction if Gemini is unavailable.
    """
    if not myths and not events:
        return []

    myth_text = "\n".join(f"- {m}" for m in myths) if myths else "(none found)"
    events_text = "\n".join(
        f"- {ev['raw_date']}: {ev['event'][:100]}" for ev in events[:10]
    )

    prompt = (
        f"Given the Ukrainian educational module about: {subject}\n\n"
        f"Track: {track}\n\n"
        f"Imperial/Soviet myths identified in research:\n{myth_text}\n\n"
        f"Key chronological events:\n{events_text}\n\n"
        "Task: Generate 2-4 concise forbidden_claims for the Key Facts Ledger. "
        "These are common myths, propaganda claims, or historical distortions "
        "that the module content should NOT repeat. Each claim should be a single "
        "sentence in English.\n\n"
        "Output ONLY a JSON array of strings, nothing else. Example:\n"
        '[\"Myth about X\", \"False claim that Y\"]\n'
    )

    try:
        res = subprocess.run(
            [GEMINI_BIN, "-p", prompt, "-o", "json"],
            capture_output=True, timeout=60,
            cwd=str(PROJECT_ROOT),
        )
        if res.returncode != 0:
            return _fallback_claims(myths)

        # Parse Gemini JSON output
        output = res.stdout.decode("utf-8", errors="replace")
        data = json.loads(output)
        # gemini-cli JSON output has response text in data
        text = data.get("response", "") if isinstance(data, dict) else str(data)

        # Extract JSON array from response
        arr_m = re.search(r"\[.*\]", text, re.DOTALL)
        if arr_m:
            claims = json.loads(arr_m.group(0))
            if isinstance(claims, list):
                return [str(c) for c in claims[:4]]

    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, KeyError):
        pass

    return _fallback_claims(myths)


def _fallback_claims(myths: list[str]) -> list[str]:
    """Deterministic fallback: reframe imperial myths as forbidden claims."""
    return [m[:300] for m in myths[:3]]


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def has_kfl(content: str) -> bool:
    """Check if a research file already contains a KFL block."""
    return "## Key Facts Ledger" in content


def insert_kfl(content: str, kfl_yaml: str) -> str:
    """Insert KFL block after H1 heading, before ## Використані джерела."""
    # Find insertion point: after H1, before first ## section
    m = re.search(r"^(# Дослідження:.+\n)", content, re.MULTILINE)
    if not m:
        return content

    insert_pos = m.end()
    # Add a blank line before KFL if needed
    prefix = content[:insert_pos]
    if not prefix.endswith("\n\n"):
        prefix = prefix.rstrip("\n") + "\n\n"

    return prefix + kfl_yaml + "\n" + content[insert_pos:].lstrip("\n")


def process_file(
    path: Path,
    track: str,
    dry_run: bool = False,
    skip_llm: bool = False,
) -> dict[str, Any]:
    """Process a single research file. Returns stats dict."""
    stats = {
        "path": str(path),
        "skipped": False,
        "fields_extracted": 0,
        "llm_called": False,
        "error": None,
    }

    try:
        content = path.read_text("utf-8")
    except OSError as e:
        stats["error"] = str(e)
        return stats

    if has_kfl(content):
        stats["skipped"] = True
        return stats

    # Deterministic extraction
    subject = extract_subject(content)
    chrono_section = extract_section(content, "Хронологія")
    facts_section = extract_section(content, "Ключові факти та цитати")
    decol_section = extract_section(content, "Деколонізаційний контекст")

    events = parse_chronology(chrono_section)
    quotes = parse_quotes(facts_section)
    myths = parse_decolonization(decol_section)

    fields = 0
    if subject:
        fields += 1
    if events:
        fields += 1
    if quotes:
        fields += 1
    stats["fields_extracted"] = fields

    # LLM enrichment for forbidden_claims
    if skip_llm:
        forbidden_claims = _fallback_claims(myths)
    else:
        forbidden_claims = enrich_with_llm(subject, myths, events, track)
        stats["llm_called"] = True

    # Build KFL YAML
    kfl = build_kfl_yaml(subject, events, quotes, forbidden_claims, track)

    if dry_run:
        print(f"  [DRY-RUN] Would insert KFL ({len(events)} events, "
              f"{len(quotes)} quotes, {len(forbidden_claims)} claims)")
        return stats

    # Insert into file
    new_content = insert_kfl(content, kfl)
    path.write_text(new_content, "utf-8")
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill Key Facts Ledger (KFL) into seminar research files.",
    )
    parser.add_argument("--track", type=str, default=None,
                        help="Process a single track (b2-hist, c1-bio, c1-hist)")
    parser.add_argument("--all", action="store_true", dest="process_all",
                        help="Process all seminar tracks")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without modifying files")
    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip Gemini calls; use deterministic fallback for forbidden_claims")
    parser.add_argument("--file", type=Path, default=None,
                        help="Process a single file (for testing)")
    args = parser.parse_args()

    if not args.track and not args.process_all and not args.file:
        parser.error("Specify --track, --all, or --file")

    if args.file:
        track = "unknown"
        for t in SEMINAR_TRACKS:
            if f"/{t}/" in str(args.file):
                track = t
                break
        stats = process_file(args.file, track, args.dry_run, args.skip_llm)
        print(json.dumps(stats, indent=2))
        return

    tracks = SEMINAR_TRACKS if args.process_all else [args.track]

    total_processed = 0
    total_skipped = 0
    total_llm_calls = 0
    total_errors = 0
    t0 = time.time()

    for track in tracks:
        research_dir = CURRICULUM_DIR / track / "research"
        if not research_dir.is_dir():
            print(f"  {track}: no research/ directory — skipping")
            continue

        files = sorted(research_dir.glob("*-research.md"))
        print(f"\n{'='*60}")
        print(f"  {track}: {len(files)} research file(s)")
        print(f"{'='*60}")

        for path in files:
            slug = path.stem.replace("-research", "")
            print(f"  [{slug}] ", end="", flush=True)

            stats = process_file(path, track, args.dry_run, args.skip_llm)

            if stats["skipped"]:
                print("SKIP (already has KFL)")
                total_skipped += 1
            elif stats["error"]:
                print(f"ERROR: {stats['error']}")
                total_errors += 1
            else:
                print(f"OK ({stats['fields_extracted']} fields"
                      f"{', +LLM' if stats['llm_called'] else ''})")
                total_processed += 1
                if stats["llm_called"]:
                    total_llm_calls += 1

    elapsed = time.time() - t0
    print(f"\n{'─'*60}")
    print(f"  Done in {elapsed:.1f}s")
    print(f"  Processed: {total_processed}")
    print(f"  Skipped:   {total_skipped}")
    print(f"  LLM calls: {total_llm_calls}")
    print(f"  Errors:    {total_errors}")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()
