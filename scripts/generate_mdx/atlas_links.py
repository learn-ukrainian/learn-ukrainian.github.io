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

  * a proper noun in the lesson — a proper-noun ``pos`` label, or a
    capitalised form with a VESUM ``prop`` reading (the headword, or the word
    as its example writes it away from a sentence start) — never links to a
    common-noun article. The capital alone is not enough: formal address
    capitalises titles too («Шановна пані Голово!»);
  * when the lesson's translation has English words, the article must have an
    English sense that shares a normalised content word with them. Only the
    English portion of either side counts: a Ukrainian note such as
    "language register (мовний реєстр)" or "to belong Conjugation: 2nd (-ать)"
    neither skips the check nor hides an article's sense. An article with no
    English sense cannot confirm the meaning, so it gets no link.

English words are compared after folding inflection (plural and third-person
``-s``, ``-ed``, ``-ing``, irregular pronoun and verb forms: "has" ~ "have",
"whom" ~ "who", "these" ~ "this") and British spelling ("centre" ~ "center",
"colouring" ~ "coloring"), because an inflected lesson form links to its
lemma's article. A multiword lesson gloss needs an overlap that survives
without ``-ed``/``-ing`` stemming; otherwise a qualifying phrase such as
"low-register; lowered" could link to the unrelated sense "lower level".

The vocabulary YAML is never modified — slugs are derived here at render time.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
import urllib.parse
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from scripts.lib.readonly_sqlite import SQLiteConnection
    from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
except ModuleNotFoundError as exc:
    # Script execution puts the script directory on sys.path, so the
    # top-level package is absent (exc.name == "scripts"). Any other
    # import failure must propagate.
    if exc.name != "scripts":
        raise
    # lib.readonly_sqlite lives in scripts/, which file execution does not put on sys.path.
    _scripts_dir = next(
        parent for parent in Path(__file__).resolve().parents if parent.name == "scripts"
    )
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from lib.readonly_sqlite import SQLiteConnection  # type: ignore[no-redef]
    from lib.readonly_sqlite import open_readonly as _open_readonly  # type: ignore[no-redef]

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
_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
# Learner-gloss metadata tail: "to belong Conjugation: 2nd (-ать) | ―".
_CONJUGATION_NOTE = re.compile(r"\bConjugation:.*$", re.IGNORECASE | re.DOTALL)
# A bracketed group with no nested brackets; dropped when it holds Cyrillic.
_BRACKETED = re.compile(r"\([^()\[\]]*\)|\[[^()\[\]]*\]")
_EN_WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")
# Only words that carry no meaning of their own. Everything else — "who",
# "here", "noun" — is itself a sense some article must be able to match.
_EN_STOPWORDS = frozenset({"a", "an", "the", "to", "of", "and", "or"})
# Irregular forms folded onto the form a dictionary sense uses: an inflected
# lesson form ("кого" 'whom', "мусить" 'has to') links to its lemma's article
# ("хто" 'who', "мусити" 'to have to').
_EN_IRREGULAR = {
    "me": "i", "him": "he", "his": "he", "her": "she", "hers": "she",
    "us": "we", "them": "they", "their": "they", "theirs": "they",
    "whom": "who", "whose": "who", "these": "this", "those": "that",
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do",
    "people": "person", "men": "man", "women": "woman", "children": "child",
    "grey": "gray",
}
_EN_VOWELS = frozenset("aeiouy")
_UK_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*")
# A capital right after one of these (or at the start) is a sentence start.
_SENTENCE_BREAKS = ".!?…:"
_OPENING_PUNCTUATION = " \t\r\n\"'«»“”„()[]—–-"


@dataclass(frozen=True)
class _ArticleSense:
    """What an Atlas article means, as far as the lesson check needs it."""

    proper: bool
    english: frozenset[str]
    english_unstemmed: frozenset[str]


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


def _american_spelling(token: str) -> str:
    """Fold British spellings: "centre" → "center", "colour" → "color", "-isation" → "-ization"."""
    token = _EN_IRREGULAR.get(token, token)
    if token.endswith("isation"):
        return token[:-7] + "ization"
    if len(token) > 4 and token.endswith("our"):
        return token[:-3] + "or"
    if len(token) > 4 and token.endswith("re") and token[-3] not in _EN_VOWELS:
        return token[:-2] + "er"
    return token


def _english_word_forms(token: str) -> set[str]:
    """Return the forms one English token may stand for.

    Plurals and irregular forms fold to one form ("carpathians" →
    "carpathian", "has" → "have"). ``-ed`` / ``-ing`` cannot tell whether a
    final ``e`` was dropped, so both stems are kept: "lived" → {"lived",
    "liv", "live"} meets "live".
    """
    if token.endswith("'s"):
        token = token[:-2]
    if token in _EN_IRREGULAR:
        return {_EN_IRREGULAR[token]}
    forms = {token}
    if len(token) > 4 and token.endswith("ies"):
        forms = {token[:-3] + "y"}
    elif len(token) > 4 and token.endswith(("sses", "xes", "zes", "ches", "shes")):
        forms = {token[:-2]}
    elif len(token) > 4 and token.endswith("oes"):
        forms = {token[:-1], token[:-2]}
    elif len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        forms = {token[:-1]}
    else:
        for suffix, min_length in (("ing", 6), ("ed", 5)):
            stem = token[: -len(suffix)]
            if len(token) >= min_length and token.endswith(suffix) and set(stem) & _EN_VOWELS:
                forms |= {stem, stem + "e"}
                if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in _EN_VOWELS | {"l", "s", "z"}:
                    forms.add(stem[:-1])
                break
    return {_american_spelling(form) for form in forms}


def _english_portion(text: str) -> str:
    """Drop the Ukrainian notes from a gloss, keeping its English words.

    "language register (мовний реєстр)" → "language register";
    "to belong Conjugation: 2nd (-ать) | ―" → "to belong";
    "to belong (+ до, + genitive)" → "to belong".
    """
    text = _CONJUGATION_NOTE.sub("", text)
    previous = None
    while previous != text:
        previous = text
        text = _BRACKETED.sub(lambda match: " " if _CYRILLIC.search(match.group(0)) else match.group(0), text)
    return _CYRILLIC.sub(" ", text)


def english_content_words(text: str) -> frozenset[str]:
    """Return the normalised content words of the English in one gloss or sense.

    A gloss made only of stopwords ("to", "a") keeps them, so a function-word
    card can still match a function-word sense. Cyrillic text contributes
    nothing (see :func:`_english_portion`).
    """
    text = _SENSE_POS_LABEL.sub("", _english_portion(text))
    folded = unicodedata.normalize("NFKD", text.casefold())
    words: set[str] = set()
    for token in _EN_WORD.findall(folded):
        words |= _english_word_forms(token)
    words.discard("")
    return frozenset(words - _EN_STOPWORDS or words)


def _english_unstemmed_words(text: str) -> frozenset[str]:
    """Fold spelling and irregular forms, but keep -ed/-ing words distinct.

    A qualified lesson gloss cannot be confirmed just because a common word
    such as "lowered" stems to an article's "lower" in another sense.
    """
    text = _SENSE_POS_LABEL.sub("", _english_portion(text))
    folded = unicodedata.normalize("NFKD", text.casefold())
    words: set[str] = set()
    for token in _EN_WORD.findall(folded):
        # Plurals and third-person -s are grammatical forms of the same word;
        # -ed/-ing can also change an adjective's sense, as in "lowered".
        if token.endswith("s") or token.endswith("'s"):
            words.update(_english_word_forms(token))
        else:
            words.add(_american_spelling(token))
    return frozenset(words - _EN_STOPWORDS or words)


def _entry_english_senses(entry: dict) -> list[str]:
    """Senses an Atlas article shows that carry English: its gloss and translations."""
    senses: list[str] = []
    gloss = entry.get("gloss")
    if isinstance(gloss, str):
        senses.append(gloss)
    translation = (entry.get("enrichment") or {}).get("translation")
    if isinstance(translation, dict):
        for key in ("en", "terms"):
            values = translation.get(key)
            if isinstance(values, list):
                senses.extend(value for value in values if isinstance(value, str))
        if isinstance(translation.get("gloss"), str):
            senses.append(translation["gloss"])
    return [sense for sense in senses if english_content_words(sense)]


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
    english_unstemmed: dict[str, set[str]] = {}
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
        unstemmed = english_unstemmed.setdefault(slug, set())
        for sense in senses:
            words.update(english_content_words(sense))
            unstemmed.update(_english_unstemmed_words(sense))
    senses_by_slug = {
        slug: _ArticleSense(
            proper=proper[slug],
            english=frozenset(english[slug]),
            english_unstemmed=frozenset(english_unstemmed[slug]),
        )
        for slug in proper
    }
    return index, senses_by_slug


def _load_index(manifest_path: str) -> dict[str, str]:
    return _load_manifest_tables(manifest_path)[0]


@lru_cache(maxsize=1)
def _vesum_connection() -> SQLiteConnection | None:
    """Open VESUM read-only, or return None where it is not installed (CI)."""
    try:
        from rag.config import VESUM_DB_PATH
    except ModuleNotFoundError:  # pragma: no cover - package import path
        from scripts.rag.config import VESUM_DB_PATH
    if not Path(VESUM_DB_PATH).is_file():
        return None
    try:
        return _open_readonly(VESUM_DB_PATH, check_same_thread=False)
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


def _capitalised_mid_sentence(word: str, example: str) -> list[str]:
    """Return the forms of ``word`` that ``example`` capitalises away from a sentence start."""
    target = normalize_lemma(word)
    if not target or " " in target:
        return []
    text = _strip_stress(example)
    forms: list[str] = []
    for match in _UK_WORD.finditer(text):
        token = match.group(0)
        if not token[:1].isupper() or token.casefold() != target:
            continue
        before = text[: match.start()].rstrip(_OPENING_PUNCTUATION)
        if before and before[-1] not in _SENTENCE_BREAKS:
            forms.append(token)
    return forms


def lesson_word_is_proper(word: str, pos: str | None = None, example: str | None = None) -> bool:
    """Decide whether the lesson uses ``word`` as a proper noun.

    A capital is evidence only when VESUM confirms a proper-name reading for
    that capitalised form: «Поділля» has one, the title in «пані Голово» has not.
    """
    if pos and _PROPER_POS.search(pos):
        return True
    surface = _strip_stress(word or "").strip()
    candidates = [surface] if surface and " " not in surface and surface[:1].isupper() else []
    if example:
        candidates.extend(_capitalised_mid_sentence(word, example))
    return any(_vesum_has_proper_reading(form) for form in dict.fromkeys(candidates))


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
    lesson_english = english_content_words(translation or "")
    if not lesson_english:
        return True
    if article is None or not (lesson_english & article.english):
        return False
    # A multiword gloss carries a qualifier. A match based solely on a
    # -ed/-ing stem does not establish that the article covers that sense.
    lesson_unstemmed = _english_unstemmed_words(translation or "")
    return len(lesson_unstemmed) <= 1 or bool(lesson_unstemmed & article.english_unstemmed)


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
        translation: the lesson card's translation. When it has English
            words, the article must share a content word with one of its
            English senses.
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
