"""Vocab → Word Atlas cross-linking (render-time, integrity-gated).

Lesson Tab 2 ``<VocabCard>`` entries gain a "more →" link to the per-lemma
Word Atlas page (``/lexicon/{url_slug}/``) when — and only when — that lemma
actually has an Atlas page. The check is performed at MDX-generation time
against ``site/src/data/lexicon-manifest.json`` (the same file the Astro
``lexicon/[lemma].astro`` route enumerates), so a link is *never* emitted for a
lemma the Atlas does not publish. This makes the lesson→Atlas direction
integrity-safe by construction (design §7/§8 ``cross_link_integrity``; warn at
v1 per §11 Q4 — there is nothing to warn about because broken links cannot be
produced).

Matching is conservative — exact lemma key only, after:
  * stripping stress marks (combining acute U+0301 / grave U+0300) — dmklinger
    and some vocab YAMLs carry stressed headwords (``робо́та``) while Atlas
    lemmas are unstressed (``робота``);
  * normalising apostrophe variants to U+0027;
  * Unicode-aware case folding.

Crucially it does NOT strip *all* combining marks: Ukrainian ``й``/``ї``
decompose (NFD) to base vowel + combining breve/diaeresis, which must survive
so ``їжак`` does not collapse to ``іжак``.

The vocabulary YAML is never modified — slugs are derived here at render time.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

# scripts/generate_mdx/atlas_links.py -> parents[2] == repo root (worktree-aware).
_DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[2] / "site" / "src" / "data" / "lexicon-manifest.json"
)

# Stress accents to strip. Deliberately NOT the full "Mn" category — that would
# also drop the breve/diaeresis that make й/ї, destroying valid lemmas.
_STRESS_MARKS = {"́", "̀"}

# Apostrophe-like characters normalised to a single canonical form so that
# з'їсти / зʼїсти / з`їсти all match the same Atlas key.
_APOSTROPHES = {"’", "ʼ", "ʹ", "`", "´", "‘"}


def normalize_lemma(word: str) -> str:
    """Normalise a surface word to its stress-free, case-folded Atlas key."""
    if not word:
        return ""
    decomposed = unicodedata.normalize("NFD", word)
    out: list[str] = []
    for ch in decomposed:
        if ch in _STRESS_MARKS:
            continue
        if ch in _APOSTROPHES:
            ch = "'"
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out)).strip().casefold()


@lru_cache(maxsize=4)
def _load_index(manifest_path: str) -> dict[str, str]:
    """Build ``{normalized_lemma: url_slug}`` from the lexicon manifest.

    Cached per resolved path — production callers hit a single cached load;
    tests pass a unique tmp path and get isolated indices.
    """
    try:
        data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    index: dict[str, str] = {}
    for entry in data.get("entries", []):
        slug = entry.get("url_slug")
        lemma = entry.get("lemma")
        if not slug or not lemma:
            continue
        # setdefault: first writer wins on stress-only homograph collisions
        # (за́мок / замо́к) — either maps to a valid Atlas page for that spelling.
        index.setdefault(normalize_lemma(lemma), slug)
        index.setdefault(normalize_lemma(slug), slug)
    return index


def atlas_href_for(word: str, manifest_path: str | Path | None = None) -> str | None:
    """Return the Atlas page href for ``word`` iff a page exists, else ``None``.

    Args:
        word: the vocab surface form / lemma (may carry stress marks).
        manifest_path: override the lexicon manifest (tests). Defaults to the
            committed ``site/src/data/lexicon-manifest.json``.
    """
    key = normalize_lemma(word)
    if not key:
        return None
    path = str(manifest_path) if manifest_path is not None else str(_DEFAULT_MANIFEST)
    slug = _load_index(path).get(key)
    return f"/lexicon/{slug}/" if slug else None
