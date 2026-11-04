"""Citation-provenance check for agent-bridge messages.

Detects verbatim quotes attributed to authoritative Ukrainian-language
sources inside a message body and verifies the cited headword exists
in the corresponding source corpus. Sources fall into two tiers:

  - **DB-verified** (flag on absent headword): Антоненко-Давидович,
    Грінченко 1907, ЕСУМ. These have a deterministic local
    lookup in ``data/sources.db``.
  - **Detection-only / soft-skip** (citation counted, never flagged):
    Правопис 2019, VESUM, Шевельов, Вихованець, Пономарів. These have
    no deterministic local headword verifier yet — Правопис's existing
    helper is topic→section + does live HTTP, so it would either false-
    flag or stall posts; VESUM has its own DB but no exposed string-
    presence query in ``wiki.sources_db``; the rest are author
    references with no machine-readable corpus indexed.
  - **Disallowed verification evidence**: СУМ-11 citations are detected and
    annotated even when a headword is present in its Soviet-era corpus.

If verification fails, the body is annotated with a
``<!-- CITATION-UNVERIFIED ... -->`` marker — annotate-mode by design,
not block-mode.

Issue: #1683.

Empirical incident driving this module (2026-05-05): in two separate
``ab discuss`` runs hours apart, Gemini fabricated the same verbatim
Антоненко-Давидович citation about ``собака`` ("В українській мові
іменник собака — чоловічого роду..."). АД has no entry on собака per
``mcp__sources__search_style_guide``; the model's prior was the bug,
not the source. The deliberation-protocol fix (commit 872d8376b0)
caught the live channel-post case by blocking round-1 short-circuit;
this check catches the citation before it propagates to downstream
consumers (reviewers, content modules, students).

Scope (v1):
  - Detection: regex-based source-name + verbatim-quote pairing.
  - Verification: dispatch headword to the source's lookup function;
    empty result set → flag.
  - Annotation: append ``<!-- CITATION-UNVERIFIED ... -->`` markers
    BEFORE any trailing ``[AGREE]``/``[DISAGREE]`` token so the
    deliberation tail check (`_channels_cli.py:1306-1308`) is preserved.

Out of scope (v1, deferred to follow-ups if needed):
  - Fuzzy-match of quoted text against the source's body content
    (would require search-then-content-similarity; current first-cut
    catches outright fabrication where the headword does not exist
    at all in the source corpus).
  - LLM-based attribution detection (regex misses paraphrases; the
    canonical fabrication pattern is "explicitly emphasized by
    <author> who categorizes <X> as <Y>" — that is regex-tractable).
  - Block-mode rejection. Annotate first, tighten later.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

try:
    from scripts.lib.readonly_sqlite import open_readonly
except ModuleNotFoundError as exc:
    if exc.name != "scripts":
        raise
    from lib.readonly_sqlite import open_readonly  # type: ignore[no-redef]


logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────


@dataclass
class Citation:
    """A single source-attribution event detected in a message body."""

    source: str  # canonical key, e.g. "antonenko_davydovych"
    source_label: str  # human-readable label for annotations
    headword: str | None  # extracted lemma being cited about, if any
    span_start: int  # body offset where the source attribution begins
    span_end: int  # body offset where the local context ends
    quoted_text: str | None  # verbatim quote string within the span, if any


@dataclass
class VerificationResult:
    """Outcome of verifying a single citation against its source."""

    citation: Citation
    verified: bool  # True = headword exists in the source corpus
    detail: str = ""  # short human-readable reason

    @property
    def is_skipped(self) -> bool:
        """Verifier soft-skipped (DB missing, no headword, lookup error)."""
        return self.verified and self.detail.startswith("skipped:")


@dataclass
class CitationCheckResult:
    """Aggregate result of running citation check on a message body."""

    citations: list[Citation] = field(default_factory=list)
    verifications: list[VerificationResult] = field(default_factory=list)
    annotated_body: str = ""

    @property
    def unverified(self) -> list[VerificationResult]:
        return [
            v
            for v in self.verifications
            if not v.verified and not v.is_skipped
        ]

    @property
    def has_unverified(self) -> bool:
        return bool(self.unverified)


# ──────────────────────────────────────────────────────────────────────
# Source registry
# ──────────────────────────────────────────────────────────────────────

# Permissive hyphen class — Antonenko-Davydovych appears with ASCII hyphen,
# non-breaking hyphen, soft hyphen, en/em dashes depending on copy source.
_HYPHEN = "[-‐‑‒–—­]?"

# Cyrillic letter range used for headword extraction. Includes stress
# combining mark U+0301, soft sign, apostrophe variants, Ukrainian
# specifics (ї, є, ґ, і).
_CYR_WORD = r"[Ѐ-ӿ́'’ʼ\-]+"


def _has_cyrillic(text: str) -> bool:
    return any("Ѐ" <= ch <= "ӿ" for ch in text)


def _normalize_word(word: str) -> str:
    """Lower-case + strip stress marks + normalize apostrophe variants."""
    return (
        word.replace("́", "")
        .replace("’", "'")
        .replace("‘", "'")
        .replace("ʼ", "'")
        .strip("-'")
        .lower()
    )


# ──────────────────────────────────────────────────────────────────────
# Headword lookup. The bridge does not import wiki. A product caller that
# wants the product module passes it to ``check_and_annotate``. With no
# caller, a read-only probe of ``data/sources.db`` answers the same
# existence questions. A missing database returns None, the soft-skip
# ``ImportError`` used to produce: an empty lookup result would otherwise
# look like "headword not found" and flag every citation.
# ──────────────────────────────────────────────────────────────────────

_SOURCES_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sources.db"
_caller_sources: ContextVar[object | None] = ContextVar("citation_sources_db", default=None)
_LIKE_PATTERN_LIMIT = 50_000
# Same high-confidence markers the product cleaner uses to drop a row.
_ESUM_MOJIBAKE_MARKERS = (
    "Зпоц",
    "Эндзелин",
    "Зндзелин",
    "Веліа[",
    "Вегіа[",
    "Вехіа]",
    "Е55)",
    "Е55Л",
    "Е5)С",
    "Зспиз",
    "51ййсііа",
    "\\У",
)


def _fold_key(value: str) -> str:
    cleaned = str(value or "").replace("\u0301", "").strip()
    return cleaned.strip("«»\"'“”„`").strip().lower()


def _like_is_safe(query: str) -> bool:
    return len(query.encode("utf-8")) + 1 <= _LIKE_PATTERN_LIMIT


class _SourcesProbe:
    """Read-only stand-in for the product sources lookups the verifiers call."""

    def __init__(self, path: Path) -> None:
        self.SOURCES_DB_PATH = path

    def search_style_guide(self, word: str, limit: int = 5, **_kwargs: object) -> list[dict]:
        query_key = _fold_key(word)
        if not query_key:
            return []
        conn = _open_sources(self.SOURCES_DB_PATH)
        if conn is None:
            return []
        try:
            rows = conn.execute("SELECT word, text FROM style_guide ORDER BY rowid").fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()
        exact: list[dict] = []
        partial: list[dict] = []
        body: list[dict] = []
        for row in rows:
            item = {"word": row["word"], "text": row["text"]}
            headword_key = _fold_key(str(item.get("word", "")))
            if headword_key:
                if headword_key == query_key:
                    exact.append(item)
                    continue
                if query_key in headword_key or headword_key in query_key:
                    partial.append(item)
                    continue
            text_key = _fold_key(str(item.get("text", "")))
            if text_key and query_key in text_key:
                body.append(item)
        return (exact + partial + body)[:limit]

    def search_grinchenko_1907(self, word: str, limit: int = 10, **_kwargs: object) -> list[dict]:
        return _headword_rows(self.SOURCES_DB_PATH, "grinchenko", word, limit)

    def search_esum(self, query: str, limit: int = 5, **_kwargs: object) -> list[dict]:
        return _esum_rows(self.SOURCES_DB_PATH, query, limit)


def _open_sources(path: Path) -> sqlite3.Connection | None:
    if not path.exists():
        return None
    try:
        conn = open_readonly(path)
    except sqlite3.OperationalError as exc:
        logger.debug("citation-check: read-only connect to %s failed: %s", path, exc)
        return None
    conn.row_factory = sqlite3.Row
    return conn


def _headword_rows(path: Path, table: str, word: str, limit: int) -> list[dict]:
    cleaned = _fold_key(word)
    variants = [
        v
        for v in dict.fromkeys(
            [word.strip(), cleaned, cleaned.capitalize(), cleaned.upper(), word.replace("\u0301", "").strip()]
        )
        if v
    ]
    if not variants:
        return []
    conn = _open_sources(path)
    if conn is None:
        return []
    try:
        placeholders = ",".join("?" for _ in variants)
        rows = conn.execute(
            f"SELECT word FROM {table} WHERE word IN ({placeholders}) OR word = ? COLLATE NOCASE "
            "ORDER BY word COLLATE NOCASE, rowid LIMIT ?",
            (*variants, word, limit),
        ).fetchall()
        if not rows and cleaned:
            rows = conn.execute(
                f"SELECT word FROM {table} WHERE word LIKE ? OR word LIKE ? COLLATE NOCASE "
                "ORDER BY word COLLATE NOCASE, rowid LIMIT ?",
                (f"{cleaned}%", f"{word}%", limit),
            ).fetchall()
    except sqlite3.OperationalError as exc:
        logger.debug("citation-check: headword lookup on %s failed: %s", table, exc)
        return []
    finally:
        conn.close()
    return [{"word": row["word"]} for row in rows]


def _esum_text_kept(text: object) -> bool:
    body = str(text or "")
    return not any(marker in body for marker in _ESUM_MOJIBAKE_MARKERS)


def _esum_rows(path: Path, query: str, limit: int) -> list[dict]:
    clean = _fold_key(query)
    if not clean:
        return []
    limit = max(1, min(limit, 20))
    variants = [
        v
        for v in dict.fromkeys(
            [query.strip(), clean, clean.capitalize(), clean.upper(), query.replace("\u0301", "").strip()]
        )
        if v
    ]
    conn = _open_sources(path)
    if conn is None:
        return []
    try:
        meta_cols = {row["name"] for row in conn.execute("PRAGMA table_info(esum_etymology_meta)").fetchall()}
        body_cols = {row["name"] for row in conn.execute("PRAGMA table_info(esum_etymology)").fetchall()}
        if not meta_cols or not body_cols:
            return []
        volumes = conn.execute("SELECT DISTINCT vol FROM esum_etymology_meta ORDER BY vol LIMIT 2").fetchall()
        loaded = int(volumes[0]["vol"]) if len(volumes) == 1 else None
        if loaded == 1:
            normalized = query.strip().lower()
            letters = normalized.replace("'", "").replace("’", "")
            if normalized and letters.isalpha() and not normalized.startswith(("а", "б", "в", "г", "ґ")):
                return []
        placeholders = ",".join("?" for _ in variants)
        meta_where = f"(lemma IN ({placeholders}) OR replace(lemma, char(0x301), '') = ? COLLATE NOCASE"
        params: list[object] = [*variants, clean]
        if _like_is_safe(clean):
            meta_where += " OR lemma LIKE ? COLLATE NOCASE OR replace(lemma, char(0x301), '') LIKE ? COLLATE NOCASE"
            params.extend((f"{clean}%", f"{clean}%"))
        meta_where += ")"
        params.append(limit * 3)
        meta_rows = conn.execute(
            f"SELECT lemma, etymology_text FROM esum_etymology_meta WHERE {meta_where} "
            "ORDER BY vol, page, lemma LIMIT ?",
            tuple(params),
        ).fetchall()
        kept = [row for row in meta_rows if _esum_text_kept(row["etymology_text"])]
        if kept:
            return [{"lemma": row["lemma"]} for row in kept[:limit]]
        if not _like_is_safe(clean):
            return []
        phrase = clean.replace("\x00", " ").replace('"', " ").strip()
        if not phrase:
            return []
        fts_rows = conn.execute(
            "SELECT lemma, etymology_text FROM esum_etymology WHERE esum_etymology MATCH ? "
            "ORDER BY rank, rowid LIMIT ?",
            (f'"{phrase}"', max(limit * 4, 30)),
        ).fetchall()
        fts_rows = [row for row in fts_rows if _esum_text_kept(row["etymology_text"])]
    except sqlite3.OperationalError as exc:
        logger.debug("citation-check: ESUM lookup failed: %s", exc)
        return []
    finally:
        conn.close()
    return [{"lemma": row["lemma"]} for row in fts_rows[:limit]]


def _sources_if_db_present(sources_db: object) -> object | None:
    path = getattr(sources_db, "SOURCES_DB_PATH", None)
    if path is None or not Path(path).exists():
        logger.debug("citation-check: %s missing — verifier will soft-skip", path)
        return None
    return sources_db


def _try_load_sources_db():
    """Return the caller's sources lookup, or the local probe, or None.

    None means soft-skip. That is the missing-database result, and it is
    what an absent caller used to get from ``ImportError``.
    """
    supplied = _caller_sources.get()
    if supplied is not None:
        return _sources_if_db_present(supplied)
    return _sources_if_db_present(_SourcesProbe(_SOURCES_DB_PATH))


# Правопис verifier is intentionally NOT plumbed into the v1 lookup
# path — see ``_verify_pravopys`` below for the rationale. This stub
# remains for forward compatibility; do NOT switch it on without first
# wiring a deterministic, network-free headword verifier.
def _try_load_pravopys():  # pragma: no cover - deliberate stub
    return None


def _verify_via_lookup(
    citation: Citation,
    *,
    lookup: Callable[[str], object] | None,
    source_label: str,
) -> VerificationResult:
    """Generic dispatch — call ``lookup(headword)`` and inspect result.

    Resolution rules (the contract this function actually implements):
      - ``lookup is None`` (verifier itself unavailable) → soft-skip.
      - ``citation.headword`` empty / unextractable → soft-skip.
      - ``lookup(headword)`` raises → soft-skip with the exception
        text in ``detail`` (defensive — verifier crashes must not
        manufacture a flag).
      - ``lookup(headword)`` returns a falsy value (empty list, dict,
        ``None``) → **flag as unverified**. Any caller that wants
        falsy-=-soft-skip semantics MUST wrap their own lookup.

    Codex review of #1683 (PR #1694) flagged the previous wording
    ("None => soft-skip") as ambiguous: the wrapper used to send a
    callable returning None for an unmapped Правопис topic, and the
    previous prose suggested that should soft-skip when in fact the
    code flags it. The Правопис case is now handled at
    ``_verify_pravopys`` (which delegates to ``_verify_unknown``);
    this docstring is tightened so the same trap can't be re-laid
    by future callers.
    """
    if lookup is None:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: verifier unavailable (sources DB or module missing)",
        )
    if not citation.headword:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: no extractable headword from quote",
        )
    word = _normalize_word(citation.headword)
    if not word:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: headword empty after normalization",
        )
    try:
        result = lookup(word)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "citation-check: %s lookup raised for %r: %s",
            source_label,
            word,
            exc,
        )
        return VerificationResult(
            citation,
            verified=True,
            detail=f"skipped: {source_label} lookup error: {exc}",
        )
    is_present = bool(result)
    if is_present:
        return VerificationResult(citation, verified=True)
    return VerificationResult(
        citation,
        verified=False,
        detail=(
            f"no entry for «{citation.headword}» in {source_label} "
            f"(verified via direct lookup)"
        ),
    )


# ── Per-source verifier wrappers ─────────────────────────────────────


def _body_text_has(db_path: Path, table: str, column: str, term: str) -> bool:
    """Direct LIKE-scan fallback for tables whose ``word`` column is a
    section title rather than a lemma.

    Used by ``_verify_antonenko``: the ``style_guide`` table indexes
    Антоненко-Давидович by section title (e.g. "Називний відмінок у
    складеному присудку"), not by individual lemma. Lemmas appear only
    inside ``text``. AD has 279 entries, so a `LIKE %term%` scan is
    cheap.

    Opens its own short-lived sqlite connection (read-only via URI)
    so the call doesn't depend on or pollute ``wiki.sources_db``'s
    cached connection.
    """
    if not db_path.exists():
        return False
    try:
        conn = open_readonly(db_path)
    except sqlite3.OperationalError as exc:
        logger.debug("citation-check: read-only connect to %s failed: %s", db_path, exc)
        return False
    try:
        rows = conn.execute(
            f"SELECT 1 FROM {table} WHERE {column} LIKE ? COLLATE NOCASE LIMIT 1",
            (f"%{term}%",),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        logger.debug(
            "citation-check: body scan on %s.%s failed: %s", table, column, exc
        )
        return False
    finally:
        conn.close()
    return bool(rows)


def _verify_antonenko(citation: Citation) -> VerificationResult:
    """Verify АД citation. AD's `word` column holds SECTION TITLES, not
    lemmas, so we fall back to a `LIKE` body scan when the word-column
    lookup misses.
    """
    db = _try_load_sources_db()
    if db is None:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: verifier unavailable (sources DB missing)",
        )
    if not citation.headword:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: no extractable headword from quote",
        )
    word = _normalize_word(citation.headword)
    if not word:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: headword empty after normalization",
        )
    # Word-column hit (section titles like "паронім X" might match)
    try:
        if db.search_style_guide(word):
            return VerificationResult(citation, verified=True)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("citation-check: AD word lookup raised: %s", exc)
    # Body-text scan — AD has 279 entries, fast.
    if _body_text_has(
        db.SOURCES_DB_PATH, "style_guide", "text", word
    ):
        return VerificationResult(citation, verified=True)
    return VerificationResult(
        citation,
        verified=False,
        detail=(
            f"no entry for «{citation.headword}» in Антоненко-Давидович "
            f"(verified via search_style_guide + body LIKE scan)"
        ),
    )


def _verify_hrinchenko(citation: Citation) -> VerificationResult:
    db = _try_load_sources_db()
    lookup = db.search_grinchenko_1907 if db is not None else None
    return _verify_via_lookup(
        citation, lookup=lookup, source_label="Грінченко 1907"
    )


def _verify_sum11(citation: Citation) -> VerificationResult:
    return VerificationResult(
        citation,
        verified=False,
        detail="sovietized_source_not_authority",
    )


def _verify_esum(citation: Citation) -> VerificationResult:
    db = _try_load_sources_db()
    if db is None:
        return VerificationResult(
            citation,
            verified=True,
            detail="skipped: verifier unavailable (sources DB missing)",
        )
    # search_esum has a different signature — wrap.
    return _verify_via_lookup(
        citation,
        lookup=lambda w: db.search_esum(w),
        source_label="ЕСУМ",
    )


def _verify_pravopys(citation: Citation) -> VerificationResult:
    """Правопис 2019 — INTENTIONAL SOFT-SKIP in v1.

    The natural candidate API is ``rag.source_query.pravopys_lookup``,
    but it has two properties that disqualify it for the bridge's
    synchronous post-time check:

    1. **Topic→section, not headword→presence.** ``pravopys_lookup``
       maps a small dict of topical keywords (e.g. "Апостроф") to
       Правопис section numbers. An unmapped headword (`кав'ярня`,
       `мітинг`, `собака`) returns ``None``. Treating ``None`` as
       "headword absent" would false-flag every Правопис mention
       whose claim isn't one of the indexed topics.

    2. **Live HTTP under the hood.** A mapped topic calls
       ``pravopys_section`` (`scripts/rag/source_query.py:812`) which
       does ``requests.get`` against izbornyk.org.ua. ``_channels.post()``
       runs the verifier synchronously before BEGIN IMMEDIATE — a
       slow / failing network would stall posts.

    Until a deterministic local Правопис index exists with proper
    headword lookup, soft-skip every Правопис citation. This matches
    the behaviour for sources without an automated verifier (VESUM,
    Шевельов, Вихованець, Пономарів) — citation is detected and
    counted but never flagged.

    Codex review of #1683 caught this on the first round; see PR
    #1694's review thread for the full rationale.
    """
    return _verify_unknown(citation)


def _verify_unknown(citation: Citation) -> VerificationResult:
    """No verifier available for this source — soft-skip.

    Used for sources we name-detect but cannot programmatically
    lookup yet (e.g. Шевельов, Вихованець, Пономарів). A future
    follow-up can plug in HTTP / corpus lookups.
    """
    return VerificationResult(
        citation,
        verified=True,
        detail=f"skipped: no automated verifier for {citation.source_label}",
    )


class _SourceEntry(NamedTuple):
    key: str
    label: str
    pattern: re.Pattern[str]
    verifier: Callable[[Citation], VerificationResult]


# Source registry: each entry = name pattern + verifier. Order matters:
# earlier patterns take precedence on overlapping spans.
_SOURCES: tuple[_SourceEntry, ...] = (
    _SourceEntry(
        "antonenko_davydovych",
        "Антоненко-Давидович",
        # Match any inflected form: nom Антоненко, gen Антоненка,
        # ins Антоненком, dat Антоненкові, etc. + same for Давидович.
        # The publication name «Як ми говоримо» is also a synonym.
        re.compile(
            rf"Антоненк[Ѐ-ӿ]*{_HYPHEN}\s*"
            rf"[-‐‑‒–—]?\s*Давидович[Ѐ-ӿ]*"
            rf"|«Як ми говоримо»",
            re.IGNORECASE,
        ),
        _verify_antonenko,
    ),
    _SourceEntry(
        "hrinchenko_1907",
        "Грінченко 1907",
        re.compile(r"Грі́?нченк[Ѐ-ӿ]*\b", re.IGNORECASE),
        _verify_hrinchenko,
    ),
    _SourceEntry(
        "pravopys_2019",
        "Правопис 2019",
        re.compile(
            r"Правопис(?:\s+2019|\s*\(2019\))?\b|Український\s+правопис\b",
            re.IGNORECASE,
        ),
        _verify_pravopys,
    ),
    _SourceEntry(
        "sum_11",
        "СУМ-11",
        re.compile(r"СУМ[-‐–]?11\b", re.IGNORECASE),
        _verify_sum11,
    ),
    _SourceEntry(
        "esum",
        "ЕСУМ",
        re.compile(r"\bЕСУМ\b|\bетимологічний\s+словник\b", re.IGNORECASE),
        _verify_esum,
    ),
    _SourceEntry(
        "shevelov",
        "Шевельов",
        re.compile(r"Шевельов\b", re.IGNORECASE),
        _verify_unknown,
    ),
    _SourceEntry(
        "vykhovanets",
        "Вихованець",
        re.compile(r"Вихованець\b", re.IGNORECASE),
        _verify_unknown,
    ),
    _SourceEntry(
        "ponomariv",
        "Пономарів",
        re.compile(r"Пономарів\b", re.IGNORECASE),
        _verify_unknown,
    ),
    _SourceEntry(
        "vesum",
        "VESUM",
        re.compile(r"\bVESUM\b"),
        _verify_unknown,
    ),
)


# ──────────────────────────────────────────────────────────────────────
# Detection
# ──────────────────────────────────────────────────────────────────────

# Verbatim quotes — match either ASCII paired " " or Ukrainian « »
# brackets with at least 4 chars of content (avoid catching inline
# single-letter " in code blocks). Lookahead/behind exclude obvious
# code fences / URLs.
_QUOTE_RE = re.compile(
    r'(?:"((?:[^"\n]){4,500})")|(?:«((?:[^»\n]){4,500})»)',
)

# Headword extraction patterns inside or near a quote. Order matters —
# more specific (italicized + code-fenced) before fall-through.
_HEADWORD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(rf"\*({_CYR_WORD})\*"),  # *foo* (markdown italic)
    re.compile(rf"_({_CYR_WORD})_"),  # _foo_ (alt italic)
    re.compile(rf"`({_CYR_WORD})`"),  # `foo` (code-fenced)
    re.compile(rf"['‘’]({_CYR_WORD})['‘’]"),  # 'foo'
    re.compile(rf"«({_CYR_WORD})»"),  # «foo»
    re.compile(rf"іменник\s+({_CYR_WORD})", re.IGNORECASE),  # "іменник X"
    re.compile(rf"слово\s+({_CYR_WORD})", re.IGNORECASE),  # "слово X"
    re.compile(rf"лексем[аиу]\s+({_CYR_WORD})", re.IGNORECASE),  # "лексема X"
    re.compile(
        rf"(?:дієслов[оаіу]|прикметник|числівник)\s+({_CYR_WORD})",
        re.IGNORECASE,
    ),
)

# Window in chars around a source-name match in which to look for
# the cited headword. Tuned to capture sentence-local references
# without catching unrelated quotes elsewhere in the message.
_HEADWORD_WINDOW = 400


def _extract_headword(body: str, span_start: int, span_end: int) -> str | None:
    """Best-effort headword extraction from a window around a citation.

    Looks at ``[max(0, span_start - WINDOW), min(len, span_end + WINDOW)]``
    for italicized/code-fenced/quoted Cyrillic tokens, plus common
    "іменник X" / "слово X" / "лексема X" patterns.

    Prefers matches AFTER the citation end ("Source X says about Y")
    over matches before, because attribution typically introduces the
    headword on the right. Within each side, picks the match closest
    to the citation. Returns None if no Cyrillic candidate exists.
    """
    window_start = max(0, span_start - _HEADWORD_WINDOW)
    window_end = min(len(body), span_end + _HEADWORD_WINDOW)
    window = body[window_start:window_end]
    citation_start_in_window = span_start - window_start
    citation_end_in_window = span_end - window_start

    after_best: tuple[int, str] | None = None  # (distance after end, hw)
    before_best: tuple[int, str] | None = None
    for pattern in _HEADWORD_PATTERNS:
        for match in pattern.finditer(window):
            word = match.group(1)
            if not word or not _has_cyrillic(word):
                continue
            mstart = match.start()
            if mstart >= citation_end_in_window:
                distance = mstart - citation_end_in_window
                if after_best is None or distance < after_best[0]:
                    after_best = (distance, word)
            elif mstart < citation_start_in_window:
                distance = citation_start_in_window - mstart
                if before_best is None or distance < before_best[0]:
                    before_best = (distance, word)
            # else: match overlaps the citation span itself — skip
    chosen = after_best or before_best
    return chosen[1] if chosen is not None else None


def _extract_quote(body: str, span_start: int, span_end: int) -> str | None:
    """Find the nearest verbatim Cyrillic quote near a citation."""
    window_start = max(0, span_start - _HEADWORD_WINDOW)
    window_end = min(len(body), span_end + _HEADWORD_WINDOW)
    window = body[window_start:window_end]
    for match in _QUOTE_RE.finditer(window):
        text = match.group(1) or match.group(2) or ""
        if _has_cyrillic(text):
            return text.strip()
    return None


# Two same-source citations within this many chars of each other are
# de-duplicated to one citation. The fabrication pattern routinely says
# "Антоненко-Давидович у посібнику «Як ми говоримо»" — both regex
# alternations fire on adjacent spans referring to the SAME claim.
# Tuned to ~one paragraph; cross-paragraph mentions remain separate
# because they may cite different headwords.
_DEDUP_WINDOW = 200


def detect_citations(body: str) -> list[Citation]:
    """Find all source-attribution events in a body.

    Returns one Citation per source-name match, except that two
    mentions of the SAME source within ``_DEDUP_WINDOW`` chars are
    collapsed to one (an attribution like "Антоненко-Давидович у
    посібнику «Як ми говоримо»" matches twice but is one claim).

    Cross-source mentions are kept separate. Multi-paragraph mentions
    of the same source remain separate because they may cite different
    headwords.
    """
    if not body:
        return []
    candidates: list[Citation] = []
    for entry in _SOURCES:
        for match in entry.pattern.finditer(body):
            span_start, span_end = match.start(), match.end()
            headword = _extract_headword(body, span_start, span_end)
            quoted = _extract_quote(body, span_start, span_end)
            candidates.append(
                Citation(
                    source=entry.key,
                    source_label=entry.label,
                    headword=headword,
                    span_start=span_start,
                    span_end=span_end,
                    quoted_text=quoted,
                )
            )
    # Sort by appearance for stable annotation order + dedup pass.
    candidates.sort(key=lambda c: c.span_start)

    citations: list[Citation] = []
    last_by_source: dict[str, Citation] = {}
    for cand in candidates:
        prev = last_by_source.get(cand.source)
        if prev is not None and cand.span_start - prev.span_end <= _DEDUP_WINDOW:
            # Same source, close together — keep the earlier one but
            # widen its span and inherit a non-None headword/quote
            # if the earlier one lacked one.
            prev_idx = citations.index(prev)
            citations[prev_idx] = Citation(
                source=prev.source,
                source_label=prev.source_label,
                headword=prev.headword or cand.headword,
                span_start=prev.span_start,
                span_end=cand.span_end,
                quoted_text=prev.quoted_text or cand.quoted_text,
            )
            last_by_source[cand.source] = citations[prev_idx]
            continue
        citations.append(cand)
        last_by_source[cand.source] = cand
    return citations


def verify_citation(citation: Citation) -> VerificationResult:
    """Dispatch a single Citation to its verifier."""
    for entry in _SOURCES:
        if entry.key == citation.source:
            return entry.verifier(citation)
    # Should never happen — detect_citations only emits known sources.
    return VerificationResult(
        citation,
        verified=True,
        detail="skipped: unknown source key (registry mismatch)",
    )


# ──────────────────────────────────────────────────────────────────────
# Annotation
# ──────────────────────────────────────────────────────────────────────

# Markers preserved on the deliberation tail; we must place
# annotations BEFORE these. Match `[AGREE]`/`[DISAGREE]` (case-
# insensitive) to be robust to variants, but the deliberation
# convergence check uses strict `[AGREE]` so production agents
# already type that exact form.
_TAIL_MARKER_RE = re.compile(r"\s*\[(?:AGREE|DISAGREE)\]\s*$", re.IGNORECASE)


def _format_annotation(verification: VerificationResult) -> str:
    """One-line ``<!-- CITATION-UNVERIFIED ... -->`` HTML comment."""
    citation = verification.citation
    headword = citation.headword or "(no headword extracted)"
    return (
        f"<!-- CITATION-UNVERIFIED: source={citation.source} "
        f'headword="{headword}" '
        f'reason="{verification.detail}" -->'
    )


def annotate_body(
    body: str, verifications: list[VerificationResult]
) -> str:
    """Insert annotations for each unverified citation.

    Annotations go on their own lines, BEFORE any trailing
    ``[AGREE]``/``[DISAGREE]`` token so that downstream tail-checks
    (`_channels_cli.py:1306-1308`) keep matching. Preserves the original
    body verbatim — only appends.
    """
    unverified = [v for v in verifications if not v.verified and not v.is_skipped]
    if not unverified:
        return body

    annotations = "\n\n".join(_format_annotation(v) for v in unverified)

    tail_match = _TAIL_MARKER_RE.search(body)
    if tail_match:
        head = body[: tail_match.start()].rstrip()
        tail = body[tail_match.start():].strip()
        return f"{head}\n\n{annotations}\n\n{tail}"
    return f"{body.rstrip()}\n\n{annotations}\n"


# ──────────────────────────────────────────────────────────────────────
# Public top-level entry
# ──────────────────────────────────────────────────────────────────────


def check_and_annotate(body: str, sources_db: object | None = None) -> CitationCheckResult:
    """Run detection + verification + annotation on a single body.

    ``sources_db`` is the product lookup (``wiki.sources_db``). Omit it
    and the bridge uses its own read-only probe. Either way a missing
    database soft-skips. Each call opens and closes its own connection.

    Returns ``CitationCheckResult`` with:
      - ``annotated_body``: body with markers appended for unverified
        citations (verbatim if all verified or no citations found).
      - ``citations``: every detected attribution event.
      - ``verifications``: 1:1 with citations, in order.
    """
    token = _caller_sources.set(sources_db) if sources_db is not None else None
    try:
        citations = detect_citations(body or "")
        verifications = [verify_citation(c) for c in citations]
        annotated = annotate_body(body or "", verifications)
        return CitationCheckResult(
            citations=citations,
            verifications=verifications,
            annotated_body=annotated,
        )
    finally:
        if token is not None:
            _caller_sources.reset(token)
