#!/usr/bin/env python3
"""Remove internal authoring cross-references from learner-facing resources.

`resources.yaml` entries whose ``role`` marks them as internal build/design
provenance — any role starting with ``internal`` (internal wiki / internal plan /
internal synthesis) or ``prerequisite`` — are NOT learner resources. They render
in the Resources tab as junk such as ``Wiki: pedagogy/a1/…``, ``Internal module
M43``, ``Plan: A1 finale``, or ``Synthesis of M28-M34 content``, pointing at our
own source files/briefs.

This removes those entries from BOTH the ``resources.yaml`` source and the
committed MDX mirror (matched by title, since ``assemble_mdx`` does not round-trip
legacy core MDX). When a module has no external resources left, its Resources tab
gets an honest empty-state note instead of a dangling empty callout.

Deterministic and reusable across levels. Genuine external references
(``official source`` URLs, ``standard reference`` citations, articles, videos,
podcasts, textbooks, …) are kept untouched.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SITE_DOCS_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"

INTERNAL_ROLE_PREFIXES = ("internal", "prerequisite")
INTERNAL_ROLES = {"checkpoint source"}
# Some internal briefs hide under a VALID role (e.g. role: wiki, title
# "Wiki: pedagogy/a1/... (LOCKED ...)") or an inconsistent checkpoint role, so we
# also detect by the title/source_ref pointing at our own build artifacts.
_INTERNAL_TITLE_RE = re.compile(
    r"^(?:Wiki:\s*pedagogy|Synthesis of M|Internal module|Plan:\s)", re.IGNORECASE
)
# A source_ref pointing back into the repo marks build provenance — EXCEPT
# docs/references/, the reference corpus (school textbooks, style guides) whose
# citations are url-less by nature. A role=textbook citation like source_ref
# "docs/references/private/textbooks-txt/9-klas-…voron-2017.txt" is a real learner resource
# (its source_ref is load-bearing for the plan-reference gate), not junk — without this
# carve-out the tool deleted 26 legitimate B1 textbook citations.
# docs/resources/ (the external-resource catalog, e.g. ULP/DobraForma index) is NOT
# carved out here: its genuine entries always carry an external URL and are kept by the
# url-guard in is_internal_entry, so a url-LESS docs/resources/ entry is still junk.
_INTERNAL_REF_RE = re.compile(
    r"^(?:curriculum/|wiki/|docs/(?!references/)|Wiki:\s*pedagogy|Synthesis of )",
    re.IGNORECASE,
)
_INTERNAL_URL_RE = re.compile(
    r"^(?:wiki/|docs/wiki/|(?:a1|a2|b1|b2|c1|c2|hist|bio|lit|istorio|oes|ruth|folk)/)",
    re.IGNORECASE,
)
_EMPTY_NOTE = "This module introduces no new external resources."
_EMPTY_NOTE_UK = "*Немає зовнішніх ресурсів для цього модуля.*"
_ROLE_RE = re.compile(r"^\s+role:\s*(.+?)\s*$")
_TYPE_RE = re.compile(r"^\s+type:\s*(.+?)\s*$")
_SOURCEREF_RE = re.compile(r"^\s+source_ref:\s*(.+?)\s*$")
_URL_RE = re.compile(r"^\s+url:\s*(.+?)\s*$")
_TITLE_RE = re.compile(r'^\s*-\s*title:\s*(.+?)\s*$')
_ENTRY_START_RE = re.compile(r"^(?P<indent>\s*)-\s")
_EXTERNAL_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_EXT_RES_BLOCK_RE = re.compile(
    r"^:::info\[[^\]]*(?:External Resources|Зовнішні ресурси)[^\]]*\]\n.*?^:::\n",
    re.DOTALL | re.MULTILINE,
)


def _norm(value: str) -> str:
    return value.strip().strip("\"'")


def is_internal_entry(*, role: str, title: str, source_ref: str, url: str = "") -> bool:
    r = _norm(role).lower()
    if r.startswith(INTERNAL_ROLE_PREFIXES) or r in INTERNAL_ROLES:
        return True
    if _INTERNAL_TITLE_RE.match(_norm(title)):
        return True
    if _INTERNAL_URL_RE.match(_norm(url).lstrip("./")):
        return True
    # A `source_ref` pointing back into the repo (docs/, wiki/, curriculum/, "Wiki:
    # pedagogy", "Synthesis of") normally marks a build-provenance pointer. But genuine
    # external resources ALSO record where they were catalogued — e.g.
    # `source_ref: "docs/resources/ulp-articles-index.yaml: /…/"` — while carrying a
    # real off-site URL. An entry the learner can click through to is never internal
    # junk, so the (weaker) source_ref signal is suppressed when an external http(s)
    # URL is present. The role/title signals above stay strict. Without this guard the
    # tool removes 265/265 legitimate A2 external resources (all url-bearing, flagged
    # solely by their `docs/resources/` catalog provenance).
    if _EXTERNAL_URL_RE.match(_norm(url)):
        return False
    return bool(_INTERNAL_REF_RE.match(_norm(source_ref)))


def _split_entry_blocks(text: str) -> tuple[list[str], list[list[str]]]:
    """Split a resources.yaml into top-level ``- `` entry blocks, preserving lines."""
    prefix: list[str] = []
    blocks: list[list[str]] = []
    current: list[str] = []
    entry_indent: str | None = None
    for line in text.splitlines(keepends=True):
        match = _ENTRY_START_RE.match(line)
        is_entry_start = False
        if match:
            indent = match.group("indent")
            if entry_indent is None:
                entry_indent = indent
                is_entry_start = True
            elif indent == entry_indent:
                is_entry_start = True
        if is_entry_start:
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
        else:
            prefix.append(line)
    if current:
        blocks.append(current)
    return prefix, blocks


def _block_field(block: list[str], pattern: re.Pattern[str]) -> str:
    for line in block:
        m = pattern.match(line)
        if m:
            return m.group(1)
    return ""


def _block_title(block: list[str]) -> str:
    m = _TITLE_RE.match(block[0])
    return _norm(m.group(1)) if m else ""


def _block_is_internal(block: list[str]) -> bool:
    return is_internal_entry(
        role=_block_field(block, _ROLE_RE) or _block_field(block, _TYPE_RE),
        title=_block_title(block),
        source_ref=_block_field(block, _SOURCEREF_RE),
        url=_block_field(block, _URL_RE),
    )


def strip_yaml(text: str) -> tuple[str, list[str]]:
    """Return (new_text, removed_titles). Empty result becomes ``[]``."""
    if text.strip() in ("", "[]"):
        return text, []
    prefix, blocks = _split_entry_blocks(text)
    if not blocks:
        return text, []
    kept, removed_titles = [], []
    for block in blocks:
        if _ENTRY_START_RE.match(block[0]) and _block_is_internal(block):
            removed_titles.append(_block_title(block))
        else:
            kept.append(block)
    if not kept:
        return "[]\n", removed_titles
    return "".join(prefix) + "".join("".join(b) for b in kept), removed_titles


def strip_mdx(text: str, removed_titles: list[str]) -> str:
    """Remove the rendered resource bullets for removed titles; fix empty blocks."""
    if not removed_titles:
        return text

    def _removed_title_in_line(line: str) -> bool:
        for title in removed_titles:
            escaped = re.escape(title)
            if f"**{title}**" in line or re.search(rf"\[{escaped}\]\(", line):
                return True
        return False

    keep_lines = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("- ") and _removed_title_in_line(line):
            continue
        keep_lines.append(line)
    text = "".join(keep_lines)

    def _fix_block(m: re.Match) -> str:
        block = m.group(0)
        if re.search(r"^\s*-\s", block, re.MULTILINE):
            return block  # still has bullets
        if "Зовнішні ресурси" in block:
            return f"{_EMPTY_NOTE_UK}\n"
        return f"{_EMPTY_NOTE}\n"

    return _EXT_RES_BLOCK_RE.sub(_fix_block, text)


def module_slugs(level: str) -> list[str]:
    level_dir = CURRICULUM_ROOT / level
    return sorted(
        p.name for p in level_dir.iterdir() if p.is_dir() and (p / "resources.yaml").exists()
    )


def run(level: str, *, apply: bool) -> int:
    total_removed = 0
    emptied: list[str] = []
    for slug in module_slugs(level):
        res = CURRICULUM_ROOT / level / slug / "resources.yaml"
        mdx = SITE_DOCS_ROOT / level / f"{slug}.mdx"
        new_yaml, removed = strip_yaml(res.read_text(encoding="utf-8"))
        if not removed:
            continue
        total_removed += len(removed)
        if new_yaml.strip() == "[]":
            emptied.append(slug)
        if apply:
            res.write_text(new_yaml, encoding="utf-8")
            if mdx.exists():
                mdx.write_text(strip_mdx(mdx.read_text(encoding="utf-8"), removed), encoding="utf-8")
    verb = "Removed" if apply else "Would remove"
    print(f"{verb} {total_removed} internal resource entries (level {level}).")
    if emptied:
        print(f"Modules left with no external resources: {', '.join(emptied)}")
    return total_removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", required=True, help="Level id, e.g. a1")
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    args = parser.parse_args()
    run(args.level, apply=args.apply)


if __name__ == "__main__":
    main()
