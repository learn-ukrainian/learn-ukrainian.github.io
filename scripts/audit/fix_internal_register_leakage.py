#!/usr/bin/env python3
"""Deterministically rewrite internal build-register jargon off learner surfaces.

Remediation tool for the ``internal_leakage`` findings reported by
``scripts/audit/track_deterministic_audit.py``. It applies a small, fixed set of
text substitutions to BOTH the curriculum source
(``module.md``/``activities.yaml``/``vocabulary.yaml``/``resources.yaml``) and the
committed site MDX mirror (``site/src/content/docs/<level>/<slug>.mdx``).

Why patch the MDX mirror in place instead of regenerating it:
``linear_pipeline.assemble_mdx`` does not faithfully round-trip legacy core MDX —
regenerating churns every ``atlas_href`` slug and injects build frontmatter, an
unrelated and risky diff. The leaked prose is byte-identical in source and mirror,
so an identical in-place substitution keeps the diff surgical.

Transformations (deterministic, word-boundary anchored):

1. ``chunk`` / ``chunks`` / ``Chunk`` (ELT jargon for a lexical chunk) -> ``phrase``
   family. The word boundary means it CANNOT touch ``chunk_id`` / ``source_chunk``
   (those keep an adjacent word character), so load-bearing corpus-provenance keys
   in ``resources.yaml`` — consumed by ``linear_pipeline._plan_reference_match_gate``
   — are left intact by construction.
2. ``learner-facing`` (build/QA register) -> removed. The following word is
   re-capitalised only when the phrase was sentence-initial, so ``"Learner-facing
   support for …"`` becomes ``"Support for …"`` while a mid-sentence ``"Short
   learner-facing overview"`` becomes ``"Short overview"`` (not ``"Short Overview"``).

Residual prose mentions of ``chunk_id`` / ``source_chunk`` (build-meta written into a
``notes`` field, e.g. "no literal chunk_id") are NOT auto-edited — they need human
judgement about the surrounding clause — and are instead reported so a human can
clean them.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SITE_DOCS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"

SOURCE_FILENAMES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")

# Ordered (plural before singular is irrelevant with \b, but kept for readability).
_CHUNK_SUBS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bChunks\b"), "Phrases"),
    (re.compile(r"\bchunks\b"), "phrases"),
    (re.compile(r"\bChunk\b"), "Phrase"),
    (re.compile(r"\bchunk\b"), "phrase"),
)
_LEARNER_FACING_RE = re.compile(r"\b[Ll]earner[ -]facing\s+(\w)")
# When "learner-facing" begins a sentence, dropping it must re-capitalise the next
# word ("Learner-facing overview" -> "Overview"). When it is mid-sentence, the next
# word keeps its running-text case ("Short learner-facing overview" -> "Short
# overview", NOT "Short Overview"). A sentence start is start-of-text or a preceding
# terminator/quote — anything else means a lead-in word precedes the phrase.
_SENTENCE_START_CHARS = ".!?:;\"'“”«»"

# Reported, not auto-fixed: a prose mention (not a bare `chunk_id:` key line).
_RESIDUAL_RE = re.compile(r"\b(?:chunk_ids?|source_chunk(?:_ids?)?)\b", re.IGNORECASE)
_PROVENANCE_KEY_RE = re.compile(r"^\s*(?:-\s*)?(?:packet_)?chunk_id\s*:", re.IGNORECASE)


def _learner_facing_repl(match: re.Match[str]) -> str:
    """Drop the leaked 'learner-facing' register term, capitalising the following
    word only when the term was sentence-initial (else preserve running-text case)."""
    next_char = match.group(1)
    preceding = match.string[: match.start()].rstrip()
    at_sentence_start = (not preceding) or preceding[-1] in _SENTENCE_START_CHARS
    return next_char.upper() if at_sentence_start else next_char


def transform_text(text: str) -> tuple[str, int]:
    """Return (new_text, replacements_made) for the two deterministic rewrites."""
    count = 0
    for pattern, repl in _CHUNK_SUBS:
        text, n = pattern.subn(repl, text)
        count += n
    text, n = _LEARNER_FACING_RE.subn(_learner_facing_repl, text)
    count += n
    return text, count


def residual_prose_hits(text: str) -> list[tuple[int, str]]:
    """Lines mentioning chunk_id/source_chunk in prose (excluding provenance keys)."""
    hits: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _PROVENANCE_KEY_RE.match(line):
            continue
        if _RESIDUAL_RE.search(line):
            hits.append((line_no, line.strip()))
    return hits


def module_slugs(level: str) -> list[str]:
    level_dir = CURRICULUM_ROOT / level
    return sorted(
        p.name
        for p in level_dir.iterdir()
        if p.is_dir() and (p / "module.md").exists()
    )


def target_files(level: str, slug: str) -> list[Path]:
    module_dir = CURRICULUM_ROOT / level / slug
    files = [module_dir / name for name in SOURCE_FILENAMES]
    files.append(SITE_DOCS_ROOT / level / f"{slug}.mdx")
    return [f for f in files if f.exists()]


def run(level: str, *, apply: bool) -> int:
    total_repl = 0
    changed_files = 0
    residuals: list[str] = []
    for slug in module_slugs(level):
        for path in target_files(level, slug):
            original = path.read_text(encoding="utf-8")
            new_text, n = transform_text(original)
            for line_no, line in residual_prose_hits(new_text):
                residuals.append(f"  {path.relative_to(PROJECT_ROOT)}:{line_no}: {line}")
            if n and new_text != original:
                total_repl += n
                changed_files += 1
                if apply:
                    path.write_text(new_text, encoding="utf-8")
    verb = "Applied" if apply else "Would apply"
    print(f"{verb} {total_repl} replacements across {changed_files} files (level {level}).")
    if residuals:
        print(f"\n⚠️  {len(residuals)} residual chunk_id/source_chunk PROSE mention(s) — fix by hand:")
        print("\n".join(residuals))
    return total_repl


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, help="Level id, e.g. a1")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()
    run(args.level, apply=args.apply)


if __name__ == "__main__":
    main()
