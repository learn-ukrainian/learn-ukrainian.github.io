#!/usr/bin/env python3
"""Verify Ukrainian word forms in a module against VESUM + RAG.

Extracts all Ukrainian words from a module's prose (.md), vocabulary (.yaml),
and activities (.yaml), then checks each against VESUM (local SQLite) and
RAG textbook/literary collections (Qdrant). Produces a machine-readable
audit report.

VESUM-first, RAG-fallback: VESUM lookup is local (fast). RAG requires
network calls to Qdrant (slow). Only VESUM misses go to RAG.

Usage:
    .venv/bin/python scripts/rag_batch_verify.py curriculum/l2-uk-en/a1/this-is-i-am.md
    .venv/bin/python scripts/rag_batch_verify.py curriculum/l2-uk-en/a1/this-is-i-am.md --json
    .venv/bin/python scripts/rag_batch_verify.py curriculum/l2-uk-en/a1/this-is-i-am.md --no-rag
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Add scripts/ to sys.path for imports
sys.path.insert(0, str(SCRIPT_DIR))


# ---------------------------------------------------------------------------
# Stress-mark stripping
# ---------------------------------------------------------------------------
# Combining diacritical marks used for stress in Ukrainian text
_COMBINING_MARKS = {
    "\u0301",  # combining acute accent (most common stress mark)
    "\u0300",  # combining grave accent
    "\u030B",  # combining double acute
}


def strip_stress(text: str) -> str:
    """Remove combining accent marks from Ukrainian text.

    Normalizes to NFD, strips combining marks used for stress,
    then re-normalizes to NFC.
    """
    nfd = unicodedata.normalize("NFD", text)
    cleaned = "".join(ch for ch in nfd if ch not in _COMBINING_MARKS)
    return unicodedata.normalize("NFC", cleaned)


# ---------------------------------------------------------------------------
# Tokenizer (custom — NOT reusing tokenize_ukrainian from auto_vocab_extract)
# ---------------------------------------------------------------------------
# Require at least 2 characters to avoid single-letter noise (abbreviations, etc.)
_UKRAINIAN_WORD_RE = re.compile(r"[а-яіїєґА-ЯІЇЄҐ][а-яіїєґА-ЯІЇЄҐ'ʼ\u0027\u02BC-]+")


def tokenize_all_ukrainian(text: str) -> list[tuple[str, str]]:
    """Extract ALL Ukrainian words, preserving original form.

    Returns: [(original_form, clean_form), ...]
    where clean_form has stress marks stripped and is lowercased.

    Strips combining diacritics BEFORE regex matching so that stress-marked
    words like зва́ти are captured as single tokens (not split into зва + ти).

    Does NOT filter stop words.
    Preserves original casing for proper noun detection in report.
    """
    # Strip stress marks before tokenization to avoid word-splitting
    stripped_text = strip_stress(text)

    tokens = []
    for match in _UKRAINIAN_WORD_RE.finditer(stripped_text):
        original = match.group()
        clean = original.lower()
        # Strip trailing hyphens/apostrophes that regex may capture
        clean = clean.rstrip("-'ʼ\u0027\u02BC")  # noqa: B005 — stripping individual chars
        original = original.rstrip("-'ʼ\u0027\u02BC")  # noqa: B005
        if clean:
            tokens.append((original, clean))
    return tokens


# ---------------------------------------------------------------------------
# Text extraction (reuses logic from auto_vocab_extract.py)
# ---------------------------------------------------------------------------

def extract_ukrainian_text(md_path: Path) -> str:
    """Extract Ukrainian text from markdown content.

    Skips frontmatter (--- markers), code blocks (```), tables (| markers).
    Preserves header text (strips # prefix).
    """
    content = md_path.read_text(encoding="utf-8")

    lines = []
    in_frontmatter = False
    in_code_block = False

    for line in content.split("\n"):
        stripped = line.strip()

        if stripped == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("|"):
            continue

        # Strip markdown header symbols
        if stripped.startswith("#"):
            stripped = re.sub(r"^#+\s*", "", stripped)

        # Only include lines with Cyrillic characters
        if re.search(r"[\u0400-\u04FF]", stripped):
            lines.append(stripped)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Word extraction from different sources
# ---------------------------------------------------------------------------

def extract_words_from_md(md_path: Path) -> dict[str, str]:
    """Extract Ukrainian words from module prose.

    Returns: {clean_form: original_form} (deduped, keeps first occurrence casing).
    """
    text = extract_ukrainian_text(md_path)
    tokens = tokenize_all_ukrainian(text)
    words: dict[str, str] = {}
    for original, clean in tokens:
        if clean not in words:
            words[clean] = original
    return words


def _walk_yaml_strings(data) -> list[str]:
    """Recursively collect all string values from a YAML structure."""
    strings = []
    if isinstance(data, str):
        strings.append(data)
    elif isinstance(data, list):
        for item in data:
            strings.extend(_walk_yaml_strings(item))
    elif isinstance(data, dict):
        for value in data.values():
            strings.extend(_walk_yaml_strings(value))
    return strings


def extract_words_from_yaml(yaml_path: Path, is_vocab: bool = False) -> dict[str, str]:
    """Extract Ukrainian words from YAML fields.

    For vocab files: extracts from 'lemma' field values only.
    For activity files: recursively walks all string values, extracts Cyrillic tokens.

    Returns: {clean_form: original_form}
    """
    if not yaml_path.exists():
        return {}

    try:
        raw = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except Exception:
        return {}

    if data is None:
        return {}

    words: dict[str, str] = {}

    if is_vocab:
        # Vocab: extract only lemma fields
        entries = data if isinstance(data, list) else []
        for entry in entries:
            if isinstance(entry, dict) and "lemma" in entry:
                lemma = str(entry["lemma"])
                tokens = tokenize_all_ukrainian(lemma)
                for original, clean in tokens:
                    if clean not in words:
                        words[clean] = original
    else:
        # Activities: walk all strings and extract Ukrainian tokens
        all_strings = _walk_yaml_strings(data)
        # Skip blending formula strings (e.g. "М + А + М + А → ___")
        # — they contain pedagogical syllables (ЛО, КІ, МА) that aren't words.
        # Filter: "→" catches result arrows, " + " catches letter addition notation.
        filtered = [s for s in all_strings if "→" not in s and " + " not in s]
        combined = "\n".join(filtered)
        tokens = tokenize_all_ukrainian(combined)
        for original, clean in tokens:
            if clean not in words:
                words[clean] = original

    return words


# ---------------------------------------------------------------------------
# VESUM verification
# ---------------------------------------------------------------------------

from rag.query import get_vesum_conn


def vesum_batch_lookup(words: list[str], batch_size: int = 500) -> dict[str, list[dict]]:
    """Batch VESUM lookup for multiple words. Much faster than individual queries.

    Returns: {word: [matches]} where matches can be empty.
    """
    conn = get_vesum_conn()
    results: dict[str, list[dict]] = {}

    for i in range(0, len(words), batch_size):
        batch = words[i : i + batch_size]
        placeholders = ",".join("?" * len(batch))
        query = f"SELECT word_form, lemma, pos, tags FROM forms WHERE word_form IN ({placeholders})"
        rows = conn.execute(query, batch).fetchall()

        # Initialize all words as empty
        for w in batch:
            if w not in results:
                results[w] = []

        # Fill in matches (lowercase key to match input)
        for r in rows:
            wf = r["word_form"].lower()
            results.setdefault(wf, []).append({
                "lemma": r["lemma"],
                "pos": r["pos"],
                "tags": r["tags"],
            })

    return results


# ---------------------------------------------------------------------------
# RAG verification (Qdrant fallback)
# ---------------------------------------------------------------------------

def _word_boundary_match(word: str, text: str) -> bool:
    """Check if word appears in text as a whole word (not a substring of another).

    Uses word-boundary-aware matching: checks that characters before/after
    the match are not Ukrainian letters (Cyrillic + apostrophe).
    """
    word_lower = word.lower()
    text_lower = text.lower()
    start = 0
    cyrillic_chars = set("абвгґдеєжзиіїйклмнопрстуфхцчшщьюяʼ'\u0027\u02BC")

    while True:
        idx = text_lower.find(word_lower, start)
        if idx == -1:
            return False

        # Check left boundary
        if idx > 0 and text_lower[idx - 1] in cyrillic_chars:
            start = idx + 1
            continue

        # Check right boundary
        end = idx + len(word_lower)
        if end < len(text_lower) and text_lower[end] in cyrillic_chars:
            start = idx + 1
            continue

        return True


def rag_verify_words(words: list[str], use_literary: bool = True) -> dict[str, dict]:
    """Check VESUM-missed words against RAG textbook + literary collections.

    For each word, queries RAG and checks if the exact word form appears
    as a whole word in the returned chunk text (word-boundary matching).

    Returns: {word: {"textbook": bool, "literary": bool, "error": bool}}
    """
    try:
        from rag.query import search_literary, search_text
    except ImportError:
        print("WARNING: rag.query not importable, skipping RAG verification", file=sys.stderr)
        return {w: {"textbook": False, "literary": False, "error": True} for w in words}

    results: dict[str, dict] = {}
    qdrant_error = False

    for word in words:
        textbook_found = False
        literary_found = False
        error = False

        # Textbook search
        try:
            hits = search_text(word, limit=3)
            for hit in hits:
                chunk_text = hit.get("text", "")
                if _word_boundary_match(word, chunk_text):
                    textbook_found = True
                    break
        except Exception as e:
            if not qdrant_error:
                print(f"  WARNING: RAG query failed: {e}", file=sys.stderr)
                qdrant_error = True
            error = True

        # Literary search (only if textbook miss and requested)
        if not textbook_found and use_literary:
            try:
                hits = search_literary(word, limit=3)
                for hit in hits:
                    chunk_text = hit.get("text", "")
                    if _word_boundary_match(word, chunk_text):
                        literary_found = True
                        break
            except Exception:
                error = True

        results[word] = {"textbook": textbook_found, "literary": literary_found, "error": error}

    return results


# ---------------------------------------------------------------------------
# Main verification pipeline
# ---------------------------------------------------------------------------

def verify_module(md_path: Path, use_rag: bool = True,
                  skip_activities: bool = False) -> tuple[list[dict], dict]:
    """Verify all Ukrainian words in a module against VESUM + RAG.

    Returns: (results_list, stats_dict)

    results_list: [{original, clean, source, vesum, textbook, literary, vesum_info, status}, ...]
    stats_dict: {total, vesum_hits, rag_hits, not_found, by_source: {...}}
    """
    stem = md_path.stem
    level_dir = md_path.parent
    vocab_path = level_dir / "vocabulary" / f"{stem}.yaml"
    act_path = level_dir / "activities" / f"{stem}.yaml"

    # 1. Extract words from all three sources
    md_words = extract_words_from_md(md_path)
    vocab_words = extract_words_from_yaml(vocab_path, is_vocab=True)
    act_words = {} if skip_activities else extract_words_from_yaml(act_path, is_vocab=False)

    # Build combined word list with source tracking
    # {clean_form: (original_form, source_label)}
    all_words: dict[str, tuple[str, str]] = {}
    for clean, original in md_words.items():
        all_words[clean] = (original, "prose")
    for clean, original in vocab_words.items():
        if clean not in all_words:
            all_words[clean] = (original, "vocabulary")
    for clean, original in act_words.items():
        if clean not in all_words:
            all_words[clean] = (original, "activities")

    if not all_words:
        return [], {"total": 0, "vesum_hits": 0, "rag_hits": 0, "not_found": 0, "by_source": {}}

    # 2. Batch VESUM lookup
    clean_words = list(all_words.keys())
    vesum_results = vesum_batch_lookup(clean_words)

    # 2.5. Retry hyphenated words with hyphens stripped (syllable breakdowns)
    # Words like "мо-ло-ко", "ав-то-бус" are pedagogically correct syllable
    # divisions but fail VESUM. Dehyphenate and re-lookup.
    hyphenated_misses = [w for w in clean_words if "-" in w and not vesum_results.get(w)]
    if hyphenated_misses:
        dehyphenated = [w.replace("-", "") for w in hyphenated_misses]
        dehyph_results = vesum_batch_lookup(dehyphenated)
        for orig_w, dehyph_w in zip(hyphenated_misses, dehyphenated, strict=False):
            if dehyph_results.get(dehyph_w):
                # Mark the hyphenated form as found via its dehyphenated form
                vesum_results[orig_w] = dehyph_results[dehyph_w]

    # 3. Identify VESUM misses
    vesum_misses = [w for w in clean_words if not vesum_results.get(w)]

    # 4. RAG fallback for misses only
    rag_results: dict[str, dict] = {}
    if use_rag and vesum_misses:
        print(f"  VESUM misses: {len(vesum_misses)} — querying RAG...", file=sys.stderr)
        rag_results = rag_verify_words(vesum_misses)
    elif vesum_misses:
        rag_results = {w: {"textbook": False, "literary": False, "error": False} for w in vesum_misses}

    # 5. Build results
    from audit.config import PROPER_NAME_WHITELIST
    results = []
    stats = {
        "total": len(all_words),
        "vesum_hits": 0,
        "rag_hits": 0,
        "not_found": 0,
        "rag_errors": 0,
        "proper_names": 0,
        "by_source": {},
    }

    for clean, (original, source) in sorted(all_words.items()):
        vesum_info = vesum_results.get(clean, [])
        vesum_hit = bool(vesum_info)
        textbook_hit = False
        literary_hit = False
        rag_error = False

        if not vesum_hit:
            rag = rag_results.get(clean, {})
            textbook_hit = rag.get("textbook", False)
            literary_hit = rag.get("literary", False)
            rag_error = rag.get("error", False)

        # Check proper name whitelist before marking as not-found.
        # Only explicit whitelist — no capitalization heuristic (sentence-initial
        # words are capitalized too, which would suppress real VESUM failures).
        is_proper_name = (
            not vesum_hit and not textbook_hit and not literary_hit
            and (original in PROPER_NAME_WHITELIST
                 or clean in PROPER_NAME_WHITELIST)
        )

        # Determine status
        if vesum_hit:
            status = "✅"
            stats["vesum_hits"] += 1
        elif textbook_hit or literary_hit:
            status = "⚠️"
            stats["rag_hits"] += 1
        elif is_proper_name:
            status = "ℹ️"
            stats["proper_names"] += 1
        elif rag_error and not use_rag:
            # RAG was skipped, not an error
            status = "❌"
            stats["not_found"] += 1
        elif rag_error:
            status = "❓"
            stats["rag_errors"] += 1
        else:
            status = "❌"
            stats["not_found"] += 1

        # Per-source stats
        src_stats = stats["by_source"].setdefault(source, {
            "total": 0, "vesum_hits": 0, "not_found": 0,
        })
        src_stats["total"] += 1
        if vesum_hit:
            src_stats["vesum_hits"] += 1
        elif is_proper_name:
            pass  # Proper names don't count as not_found
        elif not (textbook_hit or literary_hit):
            src_stats["not_found"] += 1

        results.append({
            "original": original,
            "clean": clean,
            "source": source,
            "vesum": vesum_hit,
            "textbook": textbook_hit,
            "literary": literary_hit,
            "vesum_info": vesum_info,
            "status": status,
        })

    return results, stats


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(slug: str, results: list[dict], stats: dict, output_path: Path) -> None:
    """Write markdown audit report to output_path."""
    total = stats["total"]
    vesum_hits = stats["vesum_hits"]
    coverage = (vesum_hits / total * 100) if total else 0

    lines = [
        f"# RAG Verification: {slug}",
        "",
        f"**Date:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} "
        f"| **Words checked:** {total} "
        f"| **VESUM coverage:** {vesum_hits}/{total} ({coverage:.1f}%)",
        "",
        "## Summary",
        f"- ✅ Verified (VESUM): {stats['vesum_hits']}",
        f"- ⚠️ Partial (RAG only): {stats['rag_hits']}",
        f"- ❌ Not found: {stats['not_found']}",
    ]
    if stats.get("rag_errors"):
        lines.append(f"- ❓ RAG error (Qdrant unreachable): {stats['rag_errors']}")
    lines.append("")

    # ❌ Not Found section
    not_found = [r for r in results if r["status"] == "❌"]
    if not_found:
        lines.append("## ❌ Not Found (action required)")
        lines.append("")
        lines.append("| Word | Source | VESUM | Textbook | Literary |")
        lines.append("|------|--------|-------|----------|----------|")
        for r in sorted(not_found, key=lambda x: x["clean"]):
            lines.append(
                f"| {r['original']} | {r['source']} "
                f"| {'✓' if r['vesum'] else '✗'} "
                f"| {'✓' if r['textbook'] else '✗'} "
                f"| {'✓' if r['literary'] else '✗'} |"
            )
        lines.append("")

    # ⚠️ Partial section
    partial = [r for r in results if r["status"] == "⚠️"]
    if partial:
        lines.append("## ⚠️ Partial Match (human review)")
        lines.append("")
        lines.append("| Word | Source | VESUM | Textbook | Literary |")
        lines.append("|------|--------|-------|----------|----------|")
        for r in sorted(partial, key=lambda x: x["clean"]):
            lines.append(
                f"| {r['original']} | {r['source']} "
                f"| {'✓' if r['vesum'] else '✗'} "
                f"| {'✓' if r['textbook'] else '✗'} "
                f"| {'✓' if r['literary'] else '✗'} |"
            )
        lines.append("")

    # Statistics by source
    lines.append("## ✅ Statistics by Source")
    lines.append("")
    lines.append("| Source | Words | VESUM ✓ | Not Found |")
    lines.append("|--------|-------|---------|-----------|")
    for src in ["prose", "vocabulary", "activities"]:
        s = stats["by_source"].get(src)
        if s:
            lines.append(f"| {src.capitalize()} (.{'md' if src == 'prose' else 'yaml'}) "
                          f"| {s['total']} | {s['vesum_hits']} | {s['not_found']} |")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Ukrainian word forms in a module against VESUM + RAG.",
        epilog="Example: .venv/bin/python scripts/rag_batch_verify.py curriculum/l2-uk-en/a1/this-is-i-am.md",
    )
    parser.add_argument("md_file", type=Path, help="Path to module .md file")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown report")
    parser.add_argument("--no-rag", action="store_true", help="Skip RAG verification (VESUM only)")
    parser.add_argument("--skip-activities", action="store_true", help="Skip activity YAML extraction")
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Override output directory for report (default: {level}/audit/)",
    )
    args = parser.parse_args()

    md_path = args.md_file.resolve()
    if not md_path.exists():
        print(f"Error: File not found: {md_path}", file=sys.stderr)
        return 1

    stem = md_path.stem
    # Strip leading number prefix (e.g. "09-aspect-future" → "aspect-future")
    slug = re.sub(r"^\d+-", "", stem)

    print(f"Verifying: {md_path.name}", file=sys.stderr)

    results, stats = verify_module(
        md_path, use_rag=not args.no_rag, skip_activities=args.skip_activities,
    )

    if not results:
        print("  No Ukrainian words found in module.", file=sys.stderr)
        return 0

    total = stats["total"]
    vesum_hits = stats["vesum_hits"]
    coverage = (vesum_hits / total * 100) if total else 0
    print(
        f"  Words: {total} | VESUM: {vesum_hits} ({coverage:.1f}%) "
        f"| RAG: {stats['rag_hits']} | Not found: {stats['not_found']}",
        file=sys.stderr,
    )

    if args.json:
        output = {
            "slug": slug,
            "date": datetime.now(UTC).isoformat(),
            "stats": stats,
            "not_found": [r for r in results if r["status"] == "❌"],
            "partial": [r for r in results if r["status"] == "⚠️"],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        out_dir = args.output_dir or md_path.parent / "audit"
        report_path = out_dir / f"{slug}-rag-audit.md"
        generate_report(slug, results, stats, report_path)
        print(f"  Report: {report_path}", file=sys.stderr)

    return 1 if stats["not_found"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
