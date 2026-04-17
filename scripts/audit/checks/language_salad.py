"""
Language salad detector — enforce the paragraph language rule.

The rule (issue #1185, agreed with Gemini review on 2026-04-10):

1. Each paragraph is MONOLINGUAL. Ukrainian OR English, no sentence mixing.

2. A Ukrainian paragraph MAY be followed by a full English translation
   wrapped in a blockquote with italics:

       Називний відмінок — це основна форма слова...

       > *The Nominative case is the dictionary form...*

3. English explanation paragraphs stand alone.

4. Isolated Ukrainian example sentences (inline bolded or italicized with
   a tight 1-sentence gloss) are allowed at any level — they're grammar
   illustrations, not prose paragraphs.

5. Inline bolded vocabulary glosses `**кіт** (cat)` are allowed — they're
   dictionary markers, not sentence translations.

6. Dialogs are exempt — they use per-turn formatting.

Phase-driven enforcement:

| Phase | Range              | UK paragraphs      | Translation freq |
|-------|--------------------|--------------------|------------------|
| 0A    | A1 M01-M03 alphabet| Allowed (demo)     | 100%             |
|   0   | A1 M04-M14         | 0 (examples only)  | N/A              |
|   1   | A1 M15-M34         | Short (2-3 sent)   | 100%             |
|   2   | A1 M35-M55         | Medium (4-6 sent)  | 100%             |
|   3   | A2 M01-M03 bridge  | Medium             | 100%             |
|   4   | A2 M04-M20         | Medium-long        | 80%              |
|   5   | A2 M21-M50         | Long               | 60%              |
|   6   | A2 M51-M69 finale  | Long               | 40%              |
|   7   | B1 M01-M30         | Long               | 25%              |
|   8   | B1 M31+            | Long               | 10%              |
|   9   | B2-C2 + seminars   | Long               | 0% (vocab only)  |

**Phase 0A (alphabet) is SPECIAL**: these modules TEACH how to read
Ukrainian letters, so they necessarily contain Ukrainian demonstration
text (example words, greetings, letter→sound mappings). Unlike Phase 0
(decoding practice M04-M14), they may include short Ukrainian prose
blocks — as long as each is followed by an English translation block
and paragraphs stay monolingual. They were being falsely flagged under
Phase 0's "no UK prose" rule before 2026-04-10.

Usage:

    from audit.checks.language_salad import detect_language_salad, get_phase

    phase = get_phase("A2", 1)  # 3
    issues = detect_language_salad(content_str, level="A2", module_num=1)
    # Returns list of dicts:
    # [{"type": "SALAD_MIXED_PARAGRAPH", "paragraph": 3, "message": "..."}]
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# ---------------------------------------------------------------------------
# Phase configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Phase:
    """Rules for a single curriculum phase."""

    number: int
    name: str
    allow_uk_paragraphs: bool
    translation_frequency: float  # 0.0–1.0: fraction of UK paragraphs that should have translations
    min_paragraph_sentences: int  # Lower bound for a paragraph (shorter = treated as example)
    max_paragraph_sentences: int  # Upper bound for paragraph length hint
    require_uk_paragraphs: bool = True  # If False, a module with zero UK paragraphs is fine
    # Max `**term** (gloss)` markers per paragraph before SALAD_EXCESSIVE_INLINE_GLOSSES
    # fires. Default 3 matches the "3 per paragraph" rule in the writer prompt.
    # Alphabet modules (M01-M03) override this to a very high value because
    # phonetics teaching inherently requires dense term-gloss content (every
    # word is a new vocab item being introduced).
    max_inline_glosses_per_paragraph: int = 3


# Special sub-phase for A1 M01-M03 (alphabet/phonetics intro). These modules
# TEACH how to read Ukrainian — they MUST contain Ukrainian demonstration
# text. Keyed off the main PHASES map so the normal int-keyed lookup keeps
# working; resolved by get_phase() via a name check on level+module_num.
_ALPHABET_PHASE = Phase(
    number=0,  # same numeric slot as Decoding — both precede real UK prose
    name="Alphabet (A1 M01-M03)",
    allow_uk_paragraphs=True,      # UK demonstration is the point of these modules
    translation_frequency=1.0,     # when a UK block IS present, it needs an EN translation
    min_paragraph_sentences=2,
    max_paragraph_sentences=6,
    require_uk_paragraphs=False,   # but dialog-based + inline-gloss teaching is also fine
    # Alphabet modules teach reading. Every word is a new vocab item
    # introduced with its gloss. 20 markers per paragraph is effectively
    # "no upper bound" for these three modules — the pedagogy demands it.
    max_inline_glosses_per_paragraph=20,
)

PHASES: dict[int, Phase] = {
    0: Phase(0, "Decoding (A1 M04-M14)", allow_uk_paragraphs=False, translation_frequency=0.0, min_paragraph_sentences=2, max_paragraph_sentences=3),
    1: Phase(1, "First UK prose (A1 M15-M34)", allow_uk_paragraphs=True, translation_frequency=1.0, min_paragraph_sentences=2, max_paragraph_sentences=3),
    2: Phase(2, "Growing (A1 M35-M55)", allow_uk_paragraphs=True, translation_frequency=1.0, min_paragraph_sentences=3, max_paragraph_sentences=6),
    3: Phase(3, "A2 bridge (A2 M01-M03)", allow_uk_paragraphs=True, translation_frequency=1.0, min_paragraph_sentences=3, max_paragraph_sentences=6),
    4: Phase(4, "Mid A2 (A2 M04-M20)", allow_uk_paragraphs=True, translation_frequency=0.80, min_paragraph_sentences=3, max_paragraph_sentences=8),
    5: Phase(5, "Late A2 (A2 M21-M50)", allow_uk_paragraphs=True, translation_frequency=0.60, min_paragraph_sentences=3, max_paragraph_sentences=10),
    6: Phase(6, "A2 finale (A2 M51-M69)", allow_uk_paragraphs=True, translation_frequency=0.40, min_paragraph_sentences=4, max_paragraph_sentences=10),
    7: Phase(7, "Early B1 (B1 M01-M30)", allow_uk_paragraphs=True, translation_frequency=0.25, min_paragraph_sentences=4, max_paragraph_sentences=12),
    8: Phase(8, "Late B1 (B1 M31+)", allow_uk_paragraphs=True, translation_frequency=0.10, min_paragraph_sentences=4, max_paragraph_sentences=15),
    9: Phase(9, "B2+ / seminars", allow_uk_paragraphs=True, translation_frequency=0.0, min_paragraph_sentences=4, max_paragraph_sentences=20),
}


def get_phase(level: str, module_num: int) -> Phase:
    """Resolve the curriculum phase for a level + module number.

    Special-case: A1 M01-M03 are alphabet/phonetics modules and return
    the dedicated _ALPHABET_PHASE (same numeric slot as Decoding, but
    with allow_uk_paragraphs=True because these modules TEACH Ukrainian
    letters and necessarily contain demonstration text).
    """
    lvl = level.lower()
    n = int(module_num)

    if lvl == "a1":
        if n <= 3:
            return _ALPHABET_PHASE
        if n <= 14:
            return PHASES[0]
        if n <= 34:
            return PHASES[1]
        return PHASES[2]
    if lvl == "a2":
        if n <= 3:
            return PHASES[3]
        if n <= 20:
            return PHASES[4]
        if n <= 50:
            return PHASES[5]
        return PHASES[6]
    if lvl == "b1":
        if n <= 30:
            return PHASES[7]
        return PHASES[8]
    # B2, C1, C2, seminars — all fully immersive
    return PHASES[9]


# ---------------------------------------------------------------------------
# Sentence / paragraph classification
# ---------------------------------------------------------------------------

LangClass = Literal["UK", "EN", "mixed", "empty"]

_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
_LATIN_RE = re.compile(r"[A-Za-z]")

# Bolded vocab glosses: **word** (translation) where word is ≤3 words.
# These are dictionary markers and don't count as language content.
_VOCAB_GLOSS_RE = re.compile(
    r"\*\*([^\*]{1,40})\*\*\s*\(([^)]{1,80})\)",
)


def _strip_vocab_glosses(text: str) -> str:
    """Remove `**term** (gloss)` markers so they don't skew classification."""
    return _VOCAB_GLOSS_RE.sub(" ", text)


def _count_inline_glosses(text: str) -> int:
    """Count inline `**bold** (gloss)` or `**bold** *(gloss)*` markers."""
    count = len(_VOCAB_GLOSS_RE.findall(text))
    # Also catch italic-wrapped parenthetical: **term** *(gloss)*
    italic_paren = re.compile(r"\*\*([^\*]{1,40})\*\*\s*\*\(([^)]{1,80})\)\*")
    count += len(italic_paren.findall(text))
    return count


def _strip_markdown_noise(text: str) -> str:
    """Remove markdown punctuation that shouldn't count for classification."""
    text = re.sub(r"[*_`#>\-|]", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)  # links
    return text


def classify_text(text: str) -> LangClass:
    """Classify a text blob as UK, EN, mixed, or empty.

    Uses character-count ratio. ≥60% Cyrillic → UK, ≥60% Latin → EN.
    Anything else is mixed. Very short text (<5 alpha chars) → empty.
    """
    cleaned = _strip_vocab_glosses(text)
    cleaned = _strip_markdown_noise(cleaned)
    cyr = len(_CYRILLIC_RE.findall(cleaned))
    lat = len(_LATIN_RE.findall(cleaned))
    total = cyr + lat
    if total < 5:
        return "empty"
    cyr_ratio = cyr / total
    if cyr_ratio >= 0.60:
        return "UK"
    if cyr_ratio <= 0.40:
        return "EN"
    return "mixed"


def split_sentences(paragraph: str) -> list[str]:
    """Split a paragraph into sentences using ``tokenize_uk`` (#1318).

    Handles Ukrainian abbreviations (м., вул., проф.) correctly,
    unlike the previous regex ``(?<=[.!?])\\s+(?=[A-ZА-ЯІЇЄҐ])``.
    """
    from ..cleaners import split_sentences as _split_sents

    # Strip vocab glosses so the parens don't confuse sentence splitting
    cleaned = _strip_vocab_glosses(paragraph)
    return _split_sents(cleaned)


# ---------------------------------------------------------------------------
# Paragraph-level detection
# ---------------------------------------------------------------------------


def split_paragraphs(content: str) -> list[tuple[int, str]]:
    """Split content into (line_number, text) paragraph tuples.

    Skips:
      - Frontmatter (--- ... ---)
      - Code blocks (``` ... ```)
      - Section headings (## ...)
      - Activity YAML blocks
      - INJECT_ACTIVITY markers
      - Tables (lines starting with |)
      - Dialog blocks (lines starting with > — or > ** or quoted dialogue)
    """
    in_frontmatter = False
    in_codeblock = False
    in_dialog = False
    paragraphs: list[tuple[int, str]] = []
    buf: list[str] = []
    buf_start_line = 0

    def flush():
        nonlocal buf, buf_start_line
        if buf:
            text = "\n".join(buf).strip()
            if text:
                paragraphs.append((buf_start_line, text))
        buf = []

    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Frontmatter fences
        if stripped == "---" and i == 1:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        # Code fences
        if stripped.startswith("```"):
            in_codeblock = not in_codeblock
            flush()
            continue
        if in_codeblock:
            continue

        # Dialog block detection: blockquotes containing a dash + speaker
        # pattern (> — **Name:** ...) or italic translation blocks
        # (> *English translation*). Skip dialog blocks entirely.
        if stripped.startswith("> "):
            # Check if this looks like a dialog turn. Writers use BOTH
            # conventions for speaker markers:
            #   **Name:** text    (colon inside the bold — Gemini default)
            #   **Name**: text    (colon after the closing asterisks)
            # We accept either. (Bug fixed 2026-04-10: the second-form-only
            # regex let entire dialog blocks leak into salad detection as
            # "UK paragraphs" — spurious PHASE_TRANSLATIONS_MISSING on A1 M01.)
            inside = stripped[2:].lstrip()
            _speaker_colon_inside  = re.match(r"\*\*[^*]+:\s*\*\*", inside)
            _speaker_colon_outside = re.match(r"\*\*[^*]+\*\*\s*[:：]", inside)
            if inside.startswith("—") or _speaker_colon_inside or _speaker_colon_outside:
                in_dialog = True
                flush()
                continue
            # A blockquote with italic content is a TRANSLATION block —
            # it's part of the preceding paragraph's structure, not a
            # separate paragraph. Don't emit as its own.
            if re.match(r"\*[^*]", inside):
                flush()
                continue
        elif in_dialog and not stripped:
            in_dialog = False
            continue

        if in_dialog:
            continue

        # Blank line: flush current paragraph
        if not stripped:
            flush()
            continue

        # Skip non-prose lines
        if stripped.startswith("#"):
            flush()
            continue
        if stripped.startswith("<!--"):
            continue
        if stripped.startswith("|") and ("|" in stripped[1:]):
            flush()
            continue
        if re.match(r"^\s*[-*]\s", line):
            # List item — treat as paragraph break
            flush()
            continue

        if not buf:
            buf_start_line = i
        buf.append(line)

    flush()
    return paragraphs


@dataclass
class SaladIssue:
    """A detected language-salad problem."""

    type: str
    line: int
    message: str
    severity: str  # "error" | "warning"

    def __str__(self) -> str:
        icon = "❌" if self.severity == "error" else "⚠️"
        return f"{icon} L{self.line}: [{self.type}] {self.message}"


def check_paragraph(text: str, line: int) -> list[SaladIssue]:
    """Run all rules on a single paragraph. Returns list of issues."""
    issues: list[SaladIssue] = []
    sentences = split_sentences(text)
    if len(sentences) < 2:
        # Single sentence — can't be salad, but check for sentence-level
        # mixing (which the writer sometimes produces as one run-on).
        cls = classify_text(text)
        if cls == "mixed":
            issues.append(SaladIssue(
                "SALAD_MIXED_SENTENCE", line,
                f"single-sentence paragraph mixes languages: \"{text[:80]}...\"",
                "error",
            ))
        return issues

    # Classify each sentence
    classes: list[LangClass] = [classify_text(s) for s in sentences]
    uk_count = classes.count("UK")
    en_count = classes.count("EN")
    total = uk_count + en_count

    if total == 0:
        return issues  # all empty/vocab-only

    # Rule 1: paragraph dominance ≥70%
    dominant = max(uk_count, en_count) / total
    if dominant < 0.70:
        issues.append(SaladIssue(
            "SALAD_MIXED_PARAGRAPH", line,
            f"paragraph has {uk_count} UK and {en_count} EN sentences — "
            f"must be ≥70% one language (currently {dominant*100:.0f}%)",
            "error",
        ))
        return issues

    # Rule 2: at most 1 non-dominant sentence
    non_dominant = min(uk_count, en_count)
    if non_dominant > 1:
        issues.append(SaladIssue(
            "SALAD_TOO_MANY_TRANSLATIONS", line,
            f"paragraph has {non_dominant} non-dominant sentences — "
            "max 1 allowed (dominant language should fill the paragraph)",
            "error",
        ))
        return issues

    # Rule 3: no paired translation pattern UK→EN→UK→EN
    for i in range(len(classes) - 3):
        window = classes[i:i + 4]
        if window == ["UK", "EN", "UK", "EN"] or window == ["EN", "UK", "EN", "UK"]:
            issues.append(SaladIssue(
                "SALAD_PAIRED_TRANSLATION", line,
                "sentence-by-sentence translation pattern detected — "
                "put all UK sentences first, then ONE English translation "
                "block after",
                "error",
            ))
            return issues

    return issues


def detect_language_salad(
    content: str,
    level: str,
    module_num: int,
) -> list[SaladIssue]:
    """Run the full salad detection on a module's content.

    Returns a list of SaladIssue objects. Empty list = clean.
    """
    phase = get_phase(level, module_num)
    issues: list[SaladIssue] = []

    paragraphs = split_paragraphs(content)
    uk_paragraphs: list[tuple[int, str]] = []
    en_paragraphs: list[tuple[int, str]] = []

    for line, text in paragraphs:
        para_issues = check_paragraph(text, line)
        issues.extend(para_issues)

        cls = classify_text(text)
        if cls == "UK":
            uk_paragraphs.append((line, text))
        elif cls == "EN":
            en_paragraphs.append((line, text))

        # Count inline vocab glosses: `**term** (gloss)` or `**term** *(gloss)*`
        # More than N per paragraph = inline-gloss salad regardless of
        # which language dominates the outer sentence.
        #
        # The threshold comes from the Phase (default 3 = max_inline_glosses
        # + 1; the +1 is the "fires at >=N+1" semantic kept from the
        # original hard-coded `>= 4`). The Alphabet phase raises this to
        # 20 because phonetics modules inherently introduce every word
        # with a gloss.
        gloss_count = _count_inline_glosses(text)
        sent_count = max(len(split_sentences(text)), 1)
        gloss_ceiling = phase.max_inline_glosses_per_paragraph + 1
        if gloss_count >= gloss_ceiling and gloss_count >= sent_count:
            issues.append(SaladIssue(
                "SALAD_EXCESSIVE_INLINE_GLOSSES", line,
                f"paragraph has {gloss_count} inline **term** (gloss) "
                f"markers across {sent_count} sentence(s) — too dense "
                f"for {phase.name} (max {phase.max_inline_glosses_per_paragraph}); "
                "move to vocabulary section or convert to UK paragraph + "
                "translation block",
                "error",
            ))

    # Phase-level enforcement
    if not phase.allow_uk_paragraphs and uk_paragraphs:
        # Phase 0: no Ukrainian prose paragraphs allowed (examples only)
        for line, text in uk_paragraphs:
            sent_count = len(split_sentences(text))
            if sent_count >= 2:  # multi-sentence = prose paragraph
                issues.append(SaladIssue(
                    "PHASE_UK_PARAGRAPH_TOO_EARLY", line,
                    f"{phase.name} forbids multi-sentence Ukrainian prose "
                    f"paragraphs (found {sent_count}-sentence paragraph); "
                    "use isolated UK example sentences only",
                    "error",
                ))

    # Phase 1+: the module MUST contain Ukrainian paragraphs. If the
    # writer produced all-English prose at a phase that requires UK content,
    # fail hard — the module is salad-by-omission.
    #
    # Exempt when phase.require_uk_paragraphs is False (e.g. the A1 M01-M03
    # Alphabet phase, where dialog + inline-gloss teaching is an acceptable
    # substitute for UK prose paragraphs).
    if (
        phase.allow_uk_paragraphs
        and phase.require_uk_paragraphs
        and phase.translation_frequency > 0
        and not uk_paragraphs
    ):
        issues.append(SaladIssue(
            "PHASE_NO_UK_PARAGRAPHS", 0,
            f"{phase.name} requires Ukrainian prose paragraphs but none were "
            f"found (module has {len(en_paragraphs)} English paragraphs, "
            "0 Ukrainian paragraphs). The writer is producing English-only "
            "prose with inline glosses — must convert major concepts to "
            "Ukrainian paragraphs with translation blocks.",
            "error",
        ))

    # Translation frequency check: count how many UK paragraphs have an
    # adjacent translation block (either a `> *English*` blockquote OR a
    # parenthetical translation block directly following)
    if phase.allow_uk_paragraphs and uk_paragraphs:
        translated = _count_translated_uk_paragraphs(content, uk_paragraphs)
        total_uk = len(uk_paragraphs)
        actual_freq = translated / total_uk if total_uk else 0.0

        # Allow ±20% tolerance from the target frequency
        target = phase.translation_frequency
        if target == 1.0 and actual_freq < 0.90:
            issues.append(SaladIssue(
                "PHASE_TRANSLATIONS_MISSING", 0,
                f"{phase.name} requires ~100% of Ukrainian paragraphs "
                f"to have a (translation) block — currently "
                f"{actual_freq*100:.0f}% ({translated}/{total_uk})",
                "error",
            ))
        elif target > 0 and actual_freq < max(target - 0.20, 0.0):
            issues.append(SaladIssue(
                "PHASE_TRANSLATIONS_LOW", 0,
                f"{phase.name} targets ~{target*100:.0f}% translated UK "
                f"paragraphs — currently {actual_freq*100:.0f}% "
                f"({translated}/{total_uk})",
                "warning",
            ))
        elif target == 0 and actual_freq > 0.10:
            issues.append(SaladIssue(
                "PHASE_TRANSLATIONS_EXCESS", 0,
                f"{phase.name} should have 0% paragraph translations "
                f"(bolded vocab glosses only) — currently "
                f"{actual_freq*100:.0f}%",
                "warning",
            ))

    return issues


def _count_translated_uk_paragraphs(content: str, uk_paragraphs: list[tuple[int, str]]) -> int:
    """Count how many Ukrainian paragraphs are followed by a translation block.

    A translation block is:
      - A blockquote with italicized English: `> *English text*`
      - OR a parenthetical English paragraph: `(English text)` as its own block
    """
    lines = content.split("\n")
    translated = 0

    for uk_line, uk_text in uk_paragraphs:
        # Look at the next non-blank line(s) after the UK paragraph ends
        uk_end = uk_line + uk_text.count("\n")
        cursor = uk_end + 1
        # Skip blank lines
        while cursor <= len(lines) and cursor - 1 < len(lines):
            nxt = lines[cursor - 1].strip() if cursor - 1 < len(lines) else ""
            if not nxt:
                cursor += 1
                continue
            break

        if cursor - 1 >= len(lines):
            continue

        next_line = lines[cursor - 1].strip()
        # Blockquote italic format: > *English*
        if next_line.startswith("> *") or next_line.startswith(">*"):
            translated += 1
            continue
        # Parenthetical paragraph format: (English
        if next_line.startswith("(") and classify_text(next_line) == "EN":
            translated += 1
            continue

    return translated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _main():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Detect language salad in module prose.")
    parser.add_argument("path", help="Path to module .md file OR level code (a1/a2/b1) to scan")
    parser.add_argument("--level", help="Level code (required if path is .md file without level in path)")
    parser.add_argument("--module", type=int, help="Module number (required if path is .md file)")
    parser.add_argument("--summary-only", action="store_true", help="Only print per-module pass/fail summary")
    args = parser.parse_args()

    target = Path(args.path)

    # Level-scan mode
    if not target.suffix and target.name in ("a1", "a2", "b1", "b2", "c1", "c2"):
        level = target.name
        level_dir = Path("curriculum/l2-uk-en") / level
        if not level_dir.exists():
            print(f"❌ Not found: {level_dir}")
            return 1

        md_files = sorted(p for p in level_dir.glob("*.md") if not p.name.startswith("_"))
        total = len(md_files)
        salad_count = 0
        issue_counts: dict[str, int] = {}

        for md in md_files:
            slug = md.stem
            try:
                from batch_gemini_config import num_for_slug
                module_num = num_for_slug(level, slug)
            except Exception:
                module_num = 1

            content = md.read_text("utf-8")
            issues = detect_language_salad(content, level, module_num)
            errors = [i for i in issues if i.severity == "error"]

            if errors:
                salad_count += 1
                for i in errors:
                    issue_counts[i.type] = issue_counts.get(i.type, 0) + 1
                if not args.summary_only:
                    print(f"\n=== M{module_num:02d} {slug} ===")
                    phase = get_phase(level, module_num)
                    print(f"  Phase {phase.number}: {phase.name}")
                    for issue in errors[:5]:
                        print(f"  {issue}")
                    if len(errors) > 5:
                        print(f"  ... and {len(errors) - 5} more")

        print(f"\n{'='*60}")
        print(f"{level.upper()} Language Salad Report")
        print(f"{'='*60}")
        print(f"  Total modules scanned: {total}")
        print(f"  Modules with salad issues: {salad_count} ({salad_count*100//max(total,1)}%)")
        if issue_counts:
            print("\nBy issue type:")
            for itype, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
                print(f"  {count:4d}  {itype}")
        return 0 if salad_count == 0 else 1

    # Single-file mode
    if not target.exists():
        print(f"❌ Not found: {target}")
        return 1

    # Infer level + module from path if not supplied
    level = args.level
    module_num = args.module
    if not level:
        parts = target.parts
        for p in parts:
            if p.lower() in ("a1", "a2", "b1", "b2", "c1", "c2"):
                level = p.lower()
                break
    if not module_num:
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
            from batch_gemini_config import num_for_slug
            module_num = num_for_slug(level or "a1", target.stem)
        except Exception:
            module_num = 1

    if not level:
        print("❌ Could not infer level. Use --level.")
        return 1

    content = target.read_text("utf-8")
    issues = detect_language_salad(content, level, module_num)

    phase = get_phase(level, module_num)
    print(f"📋 {target.name}  [Phase {phase.number}: {phase.name}]")

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    if not issues:
        print("  ✅ No salad detected")
        return 0

    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for issue in errors:
            print(f"  {issue}")
    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for issue in warnings:
            print(f"  {issue}")

    return 1 if errors else 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_main())
