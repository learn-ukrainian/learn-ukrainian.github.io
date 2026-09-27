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

Matching is conservative. A surface form links only when normalisation
finds one published article:

  * stripping stress marks (combining acute U+0301 / grave U+0300) — dmklinger
    and some vocab YAMLs carry stressed headwords (``робо́та``) while Atlas
    lemmas are unstressed (``робота``);
  * normalising apostrophe variants to U+0027;
  * Unicode-aware case folding.

Crucially it does NOT strip *all* combining marks: Ukrainian ``й``/``ї``
decompose (NFD) to base vowel + combining breve/diaeresis, which must survive
so ``їжак`` does not collapse to ``іжак``.

The manifest is not the publication oracle. It still supplies the historical
lemma → ``url_slug`` map, but the word-page client shell shows "Word not
found" unless ``slug`` is a ``s`` key in ``lexicon-search-index.json``
(``preflightAtlasSlugInSearchIndex``). Inflected lemmas such as
``студентові`` are manifest entries and are absent from that index; they
exist only as rows in ``lexicon-search-aliases.json``. When the exact
normalised form is not one published entry, a unique alias to one published
entry is rewritten to that entry. An ambiguous alias, or a word with
neither, emits no link — this function does not guess between lemmas.

A spelling match is not a meaning match (#9002: the region «Поділля» linked to
the common noun поділля "lowland"; «реєстр» "register" linked to реєстр
"inventory"). After a target is resolved, a sense check can still drop it:

  * a proper noun in the lesson — a proper-noun ``pos`` label, the word
    capitalised in its example away from a sentence start, or a capitalised
    headword with a VESUM ``prop`` reading — never links to a common-noun
    article;
  * when the lesson gives an English translation, the article must have an
    English sense that shares a normalised content word with it. An article
    with no English sense cannot confirm the meaning, so it gets no link.

The vocabulary YAML is never modified — slugs are derived here at render time.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
import urllib.parse
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from lexicon.manifest_io import load_manifest
except ModuleNotFoundError:  # pragma: no cover - package import path in tests
    from scripts.lexicon.manifest_io import load_manifest

# scripts/generate_mdx/atlas_links.py -> parents[2] == repo root (worktree-aware).
_DATA_DIR = Path(__file__).resolve().parents[2] / "site" / "src" / "data"
_DEFAULT_MANIFEST = _DATA_DIR / "lexicon-manifest.json"
# Client-shell publication oracle: WordAtlasClientShell preflight compares
# the decoded NFC slug to search-index row ``s`` and never opens an alias URL.
_DEFAULT_SEARCH_INDEX = _DATA_DIR / "lexicon-search-index.json"
_DEFAULT_ALIASES = _DATA_DIR / "lexicon-search-aliases.json"
_LEXICON_HREF_RE = re.compile(r"^/lexicon/([^/]+)/?$")
_BAD_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")

# Stress accents to strip. Deliberately NOT the full "Mn" category — that would
# also drop the breve/diaeresis that make й/ї, destroying valid lemmas.
_STRESS_MARKS = {"́", "̀"}

# Apostrophe-like characters normalised to a single canonical form so that
# з'їсти / зʼїсти / з`їсти all match the same Atlas key.
_APOSTROPHES = {"’", "ʼ", "ʹ", "`", "´", "‘"}

_warned_manifest_unavailable = False

# ── Sense check (#9002) ─────────────────────────────────────────────────────

# VocabCard ``pos`` labels that mark a proper noun: "proper noun",
# "proper_noun", "propn", "власна назва", "name in vocative".
_PROPER_POS = re.compile(r"prop|власн|назва|\bname\b", re.IGNORECASE)
# Kaikki-style trailing part-of-speech label on an English sense. It names
# the grammar, not the meaning, so "(proper noun)" must not match "noun".
_SENSE_POS_LABEL = re.compile(
    r"\s*\((?:proper noun|noun|verb|adjective|adverb|pronoun|preposition|"
    r"conjunction|interjection|determiner|particle|numeral|predicative)\)\s*$",
    re.IGNORECASE,
)
_LATIN = re.compile(r"[A-Za-z]")
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_EN_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")
# Only words that carry no meaning of their own. Everything else — "who",
# "here", "noun" — is itself a sense some article must be able to match.
_EN_STOPWORDS = frozenset({"a", "an", "the", "to", "of", "and", "or"})
_UK_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")
# A capital right after one of these (or at the start) is a sentence start.
_SENTENCE_BREAKS = ".!?…:"
_OPENING_PUNCTUATION = " \t\r\n\"'«»“”„()[]—–-"


@dataclass(frozen=True)
class _ArticleSense:
    """What an Atlas article means, as far as the lesson check needs it."""

    proper: bool
    english: frozenset[str]


def _strip_stress(text: str) -> str:
    """Drop stress marks and unify apostrophes; keep case and й/ї."""
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", text):
        if ch in _STRESS_MARKS:
            continue
        out.append("'" if ch in _APOSTROPHES else ch)
    return unicodedata.normalize("NFC", "".join(out))


def normalize_lemma(word: str) -> str:
    """Normalise a surface word to its stress-free, case-folded Atlas key."""
    if not word:
        return ""
    return _strip_stress(word).strip().casefold()


def _english_word(token: str) -> str:
    """Fold possessive and regular plural endings: "carpathians" → "carpathian"."""
    if token.endswith("'s"):
        token = token[:-2]
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith(("sses", "xes", "zes", "ches", "shes")):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def english_content_words(text: str) -> frozenset[str]:
    """Return the normalised content words of one English gloss or sense.

    A gloss made only of stopwords ("to", "a") keeps them, so a function-word
    card can still match a function-word sense.
    """
    text = _SENSE_POS_LABEL.sub("", text)
    folded = unicodedata.normalize("NFKD", text.casefold())
    words = {_english_word(token) for token in _EN_WORD.findall(folded)}
    words.discard("")
    return frozenset(words - _EN_STOPWORDS or words)


def _is_english(text: str | None) -> bool:
    return bool(text) and bool(_LATIN.search(text)) and not _CYRILLIC.search(text)


def _entry_english_senses(entry: dict) -> list[str]:
    """English senses an Atlas article shows: its gloss and translations."""
    senses: list[str] = []
    gloss = entry.get("gloss")
    if isinstance(gloss, str) and _is_english(gloss):
        senses.append(gloss)
    translation = (entry.get("enrichment") or {}).get("translation")
    if isinstance(translation, dict):
        for key in ("en", "terms"):
            values = translation.get(key)
            if isinstance(values, list):
                senses.extend(value for value in values if isinstance(value, str))
        if isinstance(translation.get("gloss"), str):
            senses.append(translation["gloss"])
    return [sense for sense in senses if _is_english(sense)]


def _entry_is_proper(entry: dict, senses: list[str]) -> bool:
    lemma = _strip_stress(str(entry.get("lemma") or "")).strip()
    if lemma and " " not in lemma and lemma[:1].isupper():
        return True
    if "prop" in str(entry.get("pos") or "").casefold():
        return True
    return any("(proper noun)" in sense.casefold() for sense in senses)


@lru_cache(maxsize=4)
def _load_manifest_tables(manifest_path: str) -> tuple[dict[str, str], dict[str, _ArticleSense]]:
    """Build ``{normalized_lemma: url_slug}`` and ``{url_slug: sense}`` from the manifest.

    Cached per resolved path — production callers hit a single cached load;
    tests pass a unique tmp path and get isolated indices.
    """
    global _warned_manifest_unavailable
    try:
        data = load_manifest(Path(manifest_path))
    except (FileNotFoundError, OSError, ValueError) as exc:
        if not _warned_manifest_unavailable:
            import sys
            print(f"WARNING: atlas manifest unavailable ({exc!r}) — generating MDX without atlas links", file=sys.stderr)
            _warned_manifest_unavailable = True
        return {}, {}

    index: dict[str, str] = {}
    proper: dict[str, bool] = {}
    english: dict[str, set[str]] = {}
    for entry in data.get("entries", []):
        slug = entry.get("url_slug")
        lemma = entry.get("lemma")
        if not slug or not lemma:
            continue
        # setdefault: first writer wins on stress-only homograph collisions
        # (за́мок / замо́к) — either maps to a valid Atlas page for that spelling.
        index.setdefault(normalize_lemma(lemma), slug)
        index.setdefault(normalize_lemma(slug), slug)
        senses = _entry_english_senses(entry)
        proper[slug] = proper.get(slug, False) or _entry_is_proper(entry, senses)
        words = english.setdefault(slug, set())
        for sense in senses:
            words.update(english_content_words(sense))
    senses_by_slug = {
        slug: _ArticleSense(proper=proper[slug], english=frozenset(english[slug]))
        for slug in proper
    }
    return index, senses_by_slug


def _load_index(manifest_path: str) -> dict[str, str]:
    return _load_manifest_tables(manifest_path)[0]


@lru_cache(maxsize=1)
def _vesum_connection() -> sqlite3.Connection | None:
    """Open VESUM read-only, or return None where it is not installed (CI)."""
    try:
        from rag.config import VESUM_DB_PATH
    except ModuleNotFoundError:  # pragma: no cover - package import path
        from scripts.rag.config import VESUM_DB_PATH
    if not Path(VESUM_DB_PATH).is_file():
        return None
    try:
        return sqlite3.connect(f"file:{VESUM_DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    except sqlite3.Error:
        return None


@lru_cache(maxsize=4096)
def _vesum_has_proper_reading(form: str) -> bool:
    """True when VESUM tags this exact (capitalised) form as a proper name."""
    connection = _vesum_connection()
    if connection is None:
        return False
    row = connection.execute(
        "SELECT 1 FROM forms WHERE word_form = ? AND tags LIKE '%:prop%' LIMIT 1",
        (form,),
    ).fetchone()
    return row is not None


def _capitalised_mid_sentence(word: str, example: str) -> bool:
    """True when ``word`` appears capitalised in ``example`` away from a sentence start."""
    target = normalize_lemma(word)
    if not target or " " in target:
        return False
    text = _strip_stress(example)
    for match in _UK_WORD.finditer(text):
        token = match.group(0)
        if not token[:1].isupper() or token.casefold() != target:
            continue
        before = text[: match.start()].rstrip(_OPENING_PUNCTUATION)
        if before and before[-1] not in _SENTENCE_BREAKS:
            return True
    return False


def lesson_word_is_proper(word: str, pos: str | None = None, example: str | None = None) -> bool:
    """Decide whether the lesson uses ``word`` as a proper noun."""
    if pos and _PROPER_POS.search(pos):
        return True
    if example and _capitalised_mid_sentence(word, example):
        return True
    surface = _strip_stress(word or "").strip()
    return bool(surface) and " " not in surface and surface[:1].isupper() and _vesum_has_proper_reading(surface)


def _sense_allows(
    slug: str,
    manifest_path: str,
    *,
    lesson_word: str,
    translation: str | None,
    pos: str | None,
    example: str | None,
) -> bool:
    """Apply the #9002 sense check to one resolved target slug."""
    article = _load_manifest_tables(manifest_path)[1].get(slug)
    if lesson_word_is_proper(lesson_word, pos, example) and not (article and article.proper):
        return False
    if not _is_english(translation):
        return True
    return article is not None and bool(english_content_words(translation or "") & article.english)


def _href(slug: str) -> str:
    return f"/lexicon/{slug}/"


def _unique_target(targets: frozenset[str], allowed: set[str]) -> str | None:
    """Return the only target that is a published entry; refuse to guess."""
    published = targets & allowed
    if len(published) != 1:
        return None
    return next(iter(published))


@lru_cache(maxsize=4)
def _load_alias_index(path: str) -> dict[str, frozenset[str]]:
    """Map ``normalize_lemma(alias)`` to the set of alias target slugs."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(data, list):
        return {}
    grouped: dict[str, set[str]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        alias = row.get("a")
        target = row.get("s")
        if not isinstance(alias, str) or not isinstance(target, str):
            continue
        key = normalize_lemma(alias)
        if not key or not target:
            continue
        grouped.setdefault(key, set()).add(target)
    return {key: frozenset(values) for key, values in grouped.items()}


@lru_cache(maxsize=2)
def _load_search_publication(path: str) -> tuple[frozenset[str], dict[str, frozenset[str]]]:
    """Load ``(exact published slugs, normalized surface → slugs)``.

    Surfaces are the search-index article slug ``s`` and display head ``l`` —
    the same rows ``preflightAtlasSlugInSearchIndex`` treats as real pages.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return frozenset(), {}
    if not isinstance(data, list):
        return frozenset(), {}
    exact: set[str] = set()
    by_norm: dict[str, set[str]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        slug = row.get("s")
        if not isinstance(slug, str) or not slug:
            continue
        exact.add(slug)
        surfaces = [slug]
        lemma = row.get("l")
        if isinstance(lemma, str) and lemma:
            surfaces.append(lemma)
        for surface in surfaces:
            key = normalize_lemma(surface)
            if key:
                by_norm.setdefault(key, set()).add(slug)
    return frozenset(exact), {key: frozenset(values) for key, values in by_norm.items()}


def _resolve_fixture(
    key: str,
    manifest_path: str,
    aliases_path: str | None,
    published_slugs: frozenset[str] | set[str] | None,
) -> str | None:
    """Resolve against an explicit manifest fixture (unit tests).

    ``published_slugs`` narrows which fixture slugs count as real pages.
    Aliases are consulted only when ``aliases_path`` is passed, so existing
    manifest-only tests stay isolated from the committed alias file.
    """
    index = _load_index(manifest_path)
    allowed = set(index.values()) if published_slugs is None else set(published_slugs)
    slug = index.get(key)
    if slug and slug in allowed:
        return _href(slug)
    if aliases_path is None:
        return None
    chosen = _unique_target(_load_alias_index(aliases_path).get(key, frozenset()), allowed)
    return _href(chosen) if chosen else None


def _resolve_published(key: str) -> str | None:
    """Resolve against the committed manifest, search index, and alias file."""
    manifest_slug = _load_index(str(_DEFAULT_MANIFEST)).get(key)
    exact, by_norm = _load_search_publication(str(_DEFAULT_SEARCH_INDEX))
    if manifest_slug and manifest_slug in exact:
        return _href(manifest_slug)
    direct = by_norm.get(key, frozenset())
    if len(direct) == 1:
        return _href(next(iter(direct)))
    if len(direct) > 1:
        return None
    chosen = _unique_target(_load_alias_index(str(_DEFAULT_ALIASES)).get(key, frozenset()), set(exact))
    return _href(chosen) if chosen else None


def atlas_href_for(
    word: str,
    manifest_path: str | Path | None = None,
    *,
    aliases_path: str | Path | None = None,
    published_slugs: frozenset[str] | set[str] | None = None,
    translation: str | None = None,
    pos: str | None = None,
    example: str | None = None,
    lesson_word: str | None = None,
) -> str | None:
    """Return the Atlas page href for ``word`` iff one published page matches its sense.

    Args:
        word: the vocab surface form / lemma (may carry stress marks).
        manifest_path: override the lexicon manifest (tests). Defaults to the
            committed ``site/src/data/lexicon-manifest.json``. Passing this,
            ``aliases_path``, or ``published_slugs`` selects fixture mode and
            does not read the live search index.
        aliases_path: alias rows (``a`` → ``s``) used in fixture mode.
        published_slugs: fixture-mode page set. When omitted, every fixture
            manifest slug counts as published.
        translation: the lesson card's translation. When it is English, the
            article must share a content word with one of its English senses.
        pos: the lesson card's part-of-speech label.
        example: the lesson card's example sentence.
        lesson_word: the word as the lesson writes it, when ``word`` is a
            pre-set slug. Defaults to ``word``.
    """
    key = normalize_lemma(word)
    if not key:
        return None
    if manifest_path is None and aliases_path is None and published_slugs is None:
        path = str(_DEFAULT_MANIFEST)
        href = _resolve_published(key)
    else:
        path = str(manifest_path) if manifest_path is not None else str(_DEFAULT_MANIFEST)
        alias_path = str(aliases_path) if aliases_path is not None else None
        href = _resolve_fixture(key, path, alias_path, published_slugs)
    if href is None:
        return None
    slug = slug_from_atlas_href(href)
    if slug is None or not _sense_allows(
        slug,
        path,
        lesson_word=lesson_word if lesson_word is not None else word,
        translation=translation,
        pos=pos,
        example=example,
    ):
        return None
    return href


def slug_from_atlas_href(value: str) -> str | None:
    """Return the decoded NFC slug of a ``/lexicon/<slug>/`` href, else None.

    Percent-decoding matches ``parseLexiconArticleSlug``: a dangling ``%``
    is rejected rather than kept as literal text.
    """
    match = _LEXICON_HREF_RE.match(value.strip())
    if not match:
        return None
    raw = match.group(1)
    if _BAD_PERCENT_ESCAPE.search(raw):
        return None
    try:
        decoded = urllib.parse.unquote(raw, errors="strict")
    except UnicodeDecodeError:
        return None
    slug = unicodedata.normalize("NFC", decoded)
    if not slug or slug != slug.strip() or "\\" in slug or "\0" in slug:
        return None
    return slug


def validated_atlas_href(
    value: object,
    manifest_path: str | Path | None = None,
    *,
    aliases_path: str | Path | None = None,
    published_slugs: frozenset[str] | set[str] | None = None,
    translation: str | None = None,
    pos: str | None = None,
    example: str | None = None,
    lesson_word: str | None = None,
) -> str | None:
    """Resolve a pre-set ``atlas_href`` the same way as :func:`atlas_href_for`.

    A unique alias is rewritten to its canonical entry. Anything that is not
    one published entry — including an ambiguous alias — becomes ``None``
    instead of being copied into the lesson. The sense check applies too.
    """
    if not isinstance(value, str):
        return None
    slug = slug_from_atlas_href(value)
    if slug is None:
        return None
    return atlas_href_for(
        slug,
        manifest_path,
        aliases_path=aliases_path,
        published_slugs=published_slugs,
        translation=translation,
        pos=pos,
        example=example,
        lesson_word=lesson_word,
    )
