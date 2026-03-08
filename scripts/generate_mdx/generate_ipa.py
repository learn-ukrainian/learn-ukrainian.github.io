#!/usr/bin/env python3
"""Deterministic IPA generator for Ukrainian vocabulary.

Uses ipa-uk (Wiktionary algorithm) + ukrainian_word_stress.
Replaces LLM-generated IPA in vocabulary YAML files.

Usage:
  .venv/bin/python scripts/generate_ipa.py VOCAB.yaml          # regenerate IPA
  .venv/bin/python scripts/generate_ipa.py VOCAB.yaml --dry-run # preview
  .venv/bin/python scripts/generate_ipa.py --batch DIR/         # all vocab files
  .venv/bin/python scripts/generate_ipa.py --replace-prose F.md # replace inline IPA with stress marks
"""

import argparse
import logging
import re
import sys
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded singletons
# ---------------------------------------------------------------------------
_stressifier = None
_ipa_overrides: dict | None = None
_stress_overrides: dict | None = None

DATA_DIR = Path(__file__).parent / "data"

STRESS_MARK = "\u0301"  # combining acute accent

# IPA vowel characters (for context detection)
IPA_VOWELS = set("aeiouɛɪɔɑɐəæɒʉʊ")


def _get_stressifier():
    global _stressifier
    if _stressifier is None:
        from ukrainian_word_stress import Stressifier, StressSymbol
        _stressifier = Stressifier(stress_symbol=StressSymbol.CombiningAcuteAccent)
    return _stressifier


def _load_overrides(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _get_ipa_overrides() -> dict:
    global _ipa_overrides
    if _ipa_overrides is None:
        _ipa_overrides = _load_overrides("ipa_overrides.yaml")
    return _ipa_overrides


def _get_stress_overrides() -> dict:
    global _stress_overrides
    if _stress_overrides is None:
        _stress_overrides = _load_overrides("stress_overrides.yaml")
    return _stress_overrides


# ---------------------------------------------------------------------------
# Post-processing rules (align ipa-uk output with our conventions)
# ---------------------------------------------------------------------------

def _postprocess(raw: str) -> str:
    """Apply normalization rules to ipa-uk output.

    Rules:
    1. ɐ -> ɑ  (our convention: open back vowel)
    2. i̯ -> j  (non-syllabic i -> standard palatal approximant, IPA-011)
    3. ʊ -> u  (no lax vowel in Ukrainian, IPA-001)
    3b. o -> ɔ  (our convention: all Ukrainian о = open-mid [ɔ], IPA-009)
    3c. e -> ɛ  (our convention: all Ukrainian е = open-mid [ɛ], IPA-010)
    4. w -> ʋ  (В is labiodental approximant, IPA-005)
    5. u̯ʲ -> ʋʲ  (u̯ before palatalization = consonant onset)
    6. u̯ˈ -> ˈʋ  (u̯ before primary stress = onset of next syllable)
    7. u̯ˌ -> ˌʋ  (u̯ before secondary stress = onset of next syllable)
    8. u̯ + vowel -> ʋ + vowel  (В before vowel = onset position)
    """
    s = raw
    # Rule 1: ɐ -> ɑ
    s = s.replace("ɐ", "ɑ")
    # Rule 2: i̯ (i + U+032F) -> j
    s = s.replace("i\u032F", "j")
    # Rule 3: ʊ -> u
    s = s.replace("ʊ", "u")
    # Rule 3b: o -> ɔ (ipa-uk distinguishes stressed/unstressed, we normalize)
    s = s.replace("o", "ɔ")
    # Rule 3c: e -> ɛ (same normalization for е)
    s = s.replace("e", "ɛ")
    # Rule 4: w -> ʋ
    s = s.replace("w", "ʋ")
    # Rule 5: u̯ʲ -> ʋʲ (onset before palatalized consonant)
    s = s.replace("u\u032Fʲ", "ʋʲ")
    # Rule 6: u̯ˈ -> ˈʋ (onset before primary stress)
    s = s.replace("u\u032Fˈ", "ˈʋ")
    # Rule 7: u̯ˌ -> ˌʋ (onset before secondary stress)
    s = s.replace("u\u032Fˌ", "ˌʋ")
    # Rule 8: u̯ + vowel -> ʋ + vowel (В before vowel is always onset)
    _U_NONSYL = "u\u032F"
    for v in IPA_VOWELS:
        s = s.replace(f"{_U_NONSYL}{v}", f"ʋ{v}")
    return s


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def generate_ipa(word: str) -> str | None:
    """Generate IPA for a Ukrainian word.

    Returns bracketed IPA string like '[ˈmʲistɔ]', or None on failure.

    Pipeline (with hierarchical fallback):
    1. Check ipa_overrides.yaml for full IPA override
    2. Check stress_overrides.yaml for stress override; else use Stressifier
    3. Pass stressed form to ipa_uk.ipa()
    4. Post-process output
    5. Wrap in brackets
    """
    if not word or not word.strip():
        return None

    clean = word.strip()

    # 1. Full IPA override (highest priority)
    ipa_ovr = _get_ipa_overrides().get(clean)
    if ipa_ovr:
        return ipa_ovr

    # 2. Stress: override or auto
    stress_ovr = _get_stress_overrides().get(clean)
    if stress_ovr:
        stressed = stress_ovr
    else:
        try:
            stressed = _get_stressifier()(clean)
        except Exception:
            logger.warning("Stressifier failed for %r", clean, exc_info=True)
            return None

    # 3. Generate IPA via ipa-uk
    try:
        import ipa_uk
        raw = ipa_uk.ipa(stressed)
    except Exception:
        logger.warning("ipa_uk.ipa() failed for %r", clean, exc_info=True)
        return None

    if not raw or not raw.strip():
        logger.warning("ipa_uk.ipa() returned empty for %r", clean)
        return None

    # 4. Post-process
    result = _postprocess(raw)

    # 5. Wrap in brackets
    return f"[{result}]"


# ---------------------------------------------------------------------------
# Vocabulary YAML processing (targeted regex, preserves comments/ordering)
# ---------------------------------------------------------------------------

# Matches:  ipa: '[anything]'  or  ipa: "[anything]"
_IPA_LINE_RE = re.compile(
    r"""^(?P<indent>\s*)ipa:\s*(?P<q>['"])(?P<val>[^'"]*?)(?P=q)\s*$""",
    re.MULTILINE,
)

# Matches a YAML list entry start:  - lemma: word
_LEMMA_RE = re.compile(
    r"""^(?P<indent>\s*)-\s+lemma:\s*(?P<q>['"]?)(?P<word>.+?)(?P=q)\s*$""",
    re.MULTILINE,
)


def regenerate_vocab_ipa(path: Path, dry_run: bool = False) -> int:
    """Regenerate IPA fields in a vocabulary YAML file.

    Uses targeted regex replacement (not yaml.dump) to preserve comments
    and key ordering. Handles any key order (ipa: before or after lemma:).
    Returns the number of fields updated.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    changes = 0

    # Pass 1: parse entries — find each list item and its lemma + ipa line index
    # An entry starts with "- key:" and continues with indented "  key:" lines
    entries: list[dict] = []  # {lemma, ipa_line_idx, ipa_old, entry_start, entry_end, indent}
    i = 0
    while i < len(lines):
        # Detect list entry start: "- key: value" or "  - key: value"
        entry_m = re.match(r"^(\s*)-\s+\w+:", lines[i])
        if entry_m:
            indent = entry_m.group(1)
            entry = {"start": i, "indent": indent, "lemma": None,
                     "ipa_line": None, "ipa_old": None}
            # Check if this first line has lemma or ipa
            _check_entry_line(lines[i], entry, i, is_first=True)
            j = i + 1
            # Scan continuation lines (indented, not a new list item)
            while j < len(lines):
                ln = lines[j]
                # New list entry or unindented content = end of this entry
                if ln.strip() and re.match(r"^\s*-\s+\w+:", ln):
                    break
                if ln.strip() and not ln.startswith(indent + " ") and not ln.startswith(indent + "\t"):
                    break
                _check_entry_line(ln, entry, j, is_first=False)
                j += 1
            entry["end"] = j - 1
            entries.append(entry)
            i = j
        else:
            i += 1

    # Pass 2: generate IPA and build line replacements
    replacements: dict[int, str] = {}  # line_idx -> new line content
    inserts: dict[int, str] = {}  # insert AFTER line_idx -> new line
    for entry in entries:
        lemma = entry.get("lemma")
        if not lemma:
            continue
        new_ipa = generate_ipa(lemma)
        if not new_ipa:
            continue

        if entry["ipa_line"] is not None:
            # Entry has an existing ipa: line — replace if different
            if entry["ipa_old"] != new_ipa:
                old_line = lines[entry["ipa_line"]]
                # Match quoted: "- ipa: '...'" or "  ipa: '...'"
                ipa_m = re.match(
                    r"""^(?P<prefix>\s*(?:-\s+)?)ipa:\s*(?P<q>['"])(?P<val>[^'"]*?)(?P=q)(?P<trail>.*)$""",
                    old_line,
                )
                if ipa_m:
                    replacements[entry["ipa_line"]] = (
                        f"{ipa_m.group('prefix')}ipa: {ipa_m.group('q')}{new_ipa}{ipa_m.group('q')}"
                        f"{ipa_m.group('trail')}"
                    )
                    changes += 1
                else:
                    # Match bare brackets: "  ipa: [value]"
                    bare_m = re.match(
                        r"""^(?P<prefix>\s*(?:-\s+)?)ipa:\s*\[.+?\](?P<trail>.*)$""",
                        old_line,
                    )
                    if bare_m:
                        replacements[entry["ipa_line"]] = (
                            f"{bare_m.group('prefix')}ipa: '{new_ipa}'{bare_m.group('trail')}"
                        )
                        changes += 1
        else:
            # No ipa: line — insert one after the entry start line
            indent = entry["indent"]
            inserts[entry["start"]] = f"{indent}  ipa: '{new_ipa}'"
            changes += 1

    if changes == 0:
        return 0

    # Pass 3: rebuild file
    new_lines = []
    for idx, line in enumerate(lines):
        if idx in replacements:
            new_lines.append(replacements[idx])
        else:
            new_lines.append(line)
        if idx in inserts:
            new_lines.append(inserts[idx])

    if not dry_run:
        path.write_text("\n".join(new_lines), encoding="utf-8")

    return changes


def _check_entry_line(line: str, entry: dict, idx: int, is_first: bool):
    """Check a YAML line for lemma:/term:/uk: or ipa: fields and update entry dict."""
    # Match word key: lemma, term, or uk (all provide the Ukrainian word)
    prefix = r"^\s*-\s+" if is_first else r"^\s+"
    word_m = re.match(prefix + r"""(?:lemma|term|uk):\s*(['"]?)(.+?)\1\s*$""", line)
    if word_m:
        entry["lemma"] = word_m.group(2)
        return
    # Match ipa: with quotes ('...' or "...") or bare brackets ([...])
    ipa_m = re.match(prefix + r"""ipa:\s*(['"])([^'"]*?)\1\s*$""", line)
    if ipa_m:
        entry["ipa_line"] = idx
        entry["ipa_old"] = ipa_m.group(2)
        return
    ipa_bare_m = re.match(prefix + r"""ipa:\s*(\[.+?\])\s*$""", line)
    if ipa_bare_m:
        entry["ipa_line"] = idx
        entry["ipa_old"] = ipa_bare_m.group(1)
        return


# ---------------------------------------------------------------------------
# Prose IPA replacement (A1/A2 .md files: [IPA] -> stress marks)
# ---------------------------------------------------------------------------

# IPA-specific chars that distinguish [IPA] from markdown [links]
_IPA_CHARS = set("ˈˌɔɛɪʃʒʋŋθðæɑɐɜəɒɦɹɾʲʰ\u0361\u032F")

# Cyrillic + apostrophe + stress mark character class
_CYR = r"А-ЯІЇЄҐа-яіїєґ'\u0027\u2019\u0301"

# Pattern 1: **bold word** [IPA] or **bold word** — [IPA]
_BOLD_IPA_RE = re.compile(
    rf"\*\*(?P<word>[{_CYR} ]+?)\*\*\s*(?:(?:—|–|-)\s*)?\[(?P<ipa>[^\[\]]{{2,80}})\]"
)

# Pattern 2: plain word [IPA] or word — [IPA] (no bold)
_PLAIN_IPA_RE = re.compile(
    rf"(?<!\*\*)(?<![{_CYR}])(?P<word>[{_CYR}]+(?:\s+[{_CYR}]+)*)\s*(?:(?:—|–|-)\s*)?\[(?P<ipa>[^\[\]]{{2,80}})\]"
)


def _is_ipa_content(s: str) -> bool:
    """Check if bracket content looks like IPA (not a markdown link)."""
    return any(c in _IPA_CHARS for c in s)


def _stressify_word(word: str) -> str:
    """Apply stress marks to a single Ukrainian word."""
    # Strip existing stress marks first
    clean = word.replace(STRESS_MARK, "")
    if len(clean) <= 1:
        return clean  # Single letter — no stress needed
    try:
        return _get_stressifier()(clean)
    except Exception:
        return clean


def _stressify_phrase(phrase: str) -> str:
    """Apply stress marks to a multi-word phrase."""
    words = phrase.split()
    return " ".join(_stressify_word(w) for w in words)


def replace_prose_ipa(path: Path, dry_run: bool = False) -> int:
    """Replace inline IPA annotations with stress-marked Ukrainian in a .md file.

    Transforms:  **місто** — [ˈmʲistɔ]  ->  **мі́сто**
                 місто [ˈmʲistɔ]         ->  мі́сто
                 **Х** — [x], like «ch»   ->  **Х**, like «ch»

    Returns the number of replacements made.
    """
    text = path.read_text(encoding="utf-8")
    changes = 0

    # Pass 1: bold words — **word** [IPA] or **word** — [IPA]
    def _replace_bold(m: re.Match) -> str:
        nonlocal changes
        if not _is_ipa_content(m.group("ipa")):
            return m.group(0)
        word = m.group("word").strip()
        stressed = _stressify_phrase(word)
        changes += 1
        return f"**{stressed}**"

    new_text = _BOLD_IPA_RE.sub(_replace_bold, text)

    # Pass 2: plain words — word [IPA] or word — [IPA]
    def _replace_plain(m: re.Match) -> str:
        nonlocal changes
        if not _is_ipa_content(m.group("ipa")):
            return m.group(0)
        word = m.group("word").strip()
        stressed = _stressify_phrase(word)
        changes += 1
        return stressed

    new_text = _PLAIN_IPA_RE.sub(_replace_plain, new_text)

    if changes > 0 and not dry_run:
        path.write_text(new_text, encoding="utf-8")

    return changes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic IPA generator for Ukrainian vocabulary",
    )
    parser.add_argument("files", nargs="*", type=Path, help="YAML or MD files to process")
    parser.add_argument("--batch", type=Path, help="Process all vocab YAML in directory")
    parser.add_argument("--replace-prose", action="store_true",
                        help="Replace inline [IPA] with stress marks in .md files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    total = 0

    if args.batch:
        files = sorted(args.batch.glob("*.yaml"))
        if not files:
            print(f"No .yaml files found in {args.batch}", file=sys.stderr)
            return 1
        for f in files:
            n = regenerate_vocab_ipa(f, dry_run=args.dry_run)
            if n > 0:
                action = "would update" if args.dry_run else "updated"
                print(f"  {action} {n} IPA field(s) in {f.name}")
                total += n
    elif args.replace_prose:
        files = args.files or []
        for f in files:
            if not f.exists():
                print(f"  SKIP {f}: not found", file=sys.stderr)
                continue
            n = replace_prose_ipa(f, dry_run=args.dry_run)
            if n > 0:
                action = "would replace" if args.dry_run else "replaced"
                print(f"  {action} {n} inline IPA in {f.name}")
                total += n
    else:
        files = args.files or []
        for f in files:
            if not f.exists():
                print(f"  SKIP {f}: not found", file=sys.stderr)
                continue
            n = regenerate_vocab_ipa(f, dry_run=args.dry_run)
            if n > 0:
                action = "would update" if args.dry_run else "updated"
                print(f"  {action} {n} IPA field(s) in {f.name}")
                total += n

    print(f"\n  Total: {total} change(s)" + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
