"""Heritage practice densification wave — GEC calque → sentence corruption (#6623).

Grows the thin heritage-practice mode by turning UA-GEC ``F/Calque``
error→correction pairs into fill-the-blank MC frames, gated by a real
corpus carrier sentence:

    1. Load ``data/sources.db`` ``ua_gec_errors`` rows tagged ``F/Calque``.
    2. Normalize/dedupe (error, correct) pairs; drop empty or annotation-span
       artifacts (stray quote marks).
    3. Prefer (a) pairs whose ``correct`` form is already covered by an
       existing ``data/lexicon/heritage_pairs.yaml`` pair — these extend that
       pair's ``frames``; (b) multiword calques next; (c) the rest, when
       ``correct`` resolves *exactly* (case/diacritic-insensitive) to a
       public practice-eligible Atlas lemma — these become new pairs.
    4. For each admitted pair, search the local textbook/literary corpus
       (``data/sources.db`` FTS5) for a clean sentence that contains
       ``correct`` as a whole token (single occurrence, 40–220 chars,
       Ukrainian script, no pre-existing blank/OCR artifacts).
    5. Corrupt it: substitute ``correct`` → ``error`` for the wrong-answer
       option; blank ``correct`` → ``___`` for ``sentence_with_slot``.
    6. Emit an *additive* overlay (``data/lexicon/heritage_pairs.wave1-calque.yaml``)
       that ``generate_practice_deck.read_heritage_pairs`` merges into the
       curated set at build time — the hand-curated 90-pair file is never
       edited. A pair or frame that cannot find a carrier is never invented;
       it is counted in the residual report instead.

Fails closed throughout: no sentence is ever authored or altered beyond the
single documented substitution, and every candidate that cannot clear a gate
is dropped with a stated reason rather than silently guessed at.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.generate_practice_deck import _plain, read_atlas_db
from scripts.audit.lexeme_filter import is_practice_eligible
from scripts.verification.vesum import verify_words as _vesum_verify_words

DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_ATLAS_DB = PROJECT_ROOT / "data" / "atlas.db"
DEFAULT_VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"
DEFAULT_HERITAGE_PAIRS = PROJECT_ROOT / "data" / "lexicon" / "heritage_pairs.yaml"
DEFAULT_OVERLAY_OUT = PROJECT_ROOT / "data" / "lexicon" / "heritage_pairs.wave1-calque.yaml"
DEFAULT_RESIDUAL_JSON = PROJECT_ROOT / "data" / "lexicon" / "heritage_pairs.wave1-calque.residual.json"
DEFAULT_RESIDUAL_REPORT = PROJECT_ROOT / "docs" / "practice" / "heritage-calque-wave1-residual.md"

WAVE_ORIGIN_TAG = "ua-gec-calque-wave1"
WAVE_CURATOR_TAG = "script:heritage_calque_wave-2026-08-11"

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_EDGE_PUNCT = "\"'«»„”“,.:;!?…"
_QUOTE_CHARS = '"«»„”“'


def normalize_gec_text(value: str | None) -> str | None:
    """NFC-normalize, strip whitespace, and strip GEC annotation-span punctuation.

    UA-GEC error spans occasionally carry a leading/trailing comma or a
    dangling quote from the sentence they were extracted from (e.g.
    ``"Таким чином,"``). Stripping *edge* punctuation only (never internal)
    consolidates those into the same key as the clean form without altering
    genuine multiword phrases.
    """
    if not value:
        return None
    text = unicodedata.normalize("NFC", value).strip()
    text = text.strip(_EDGE_PUNCT).strip()
    return text or None


def has_stray_quote(value: str) -> bool:
    """True if a quote character survives inside the (already edge-stripped) text.

    A few UA-GEC spans include a neighboring word plus a stray quote from a
    dialogue line (e.g. ``доктор"``); those are annotation-boundary noise,
    not a calque, so callers drop the row rather than guess at trimming it.
    """
    return any(ch in value for ch in _QUOTE_CHARS)


# ---------------------------------------------------------------------------
# UA-GEC F/Calque loading
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GecPair:
    error: str
    correct: str
    count: int
    doc_ids: tuple[str, ...]

    @property
    def is_multiword(self) -> bool:
        return " " in self.error or " " in self.correct


def load_gec_calque_pairs(sources_db: Path) -> list[GecPair]:
    """Load, normalize, and dedupe UA-GEC ``F/Calque`` (error, correct) pairs."""
    con = sqlite3.connect(sources_db)
    try:
        rows = con.execute(
            "SELECT error, correct, doc_id FROM ua_gec_errors WHERE error_type = 'F/Calque'"
        ).fetchall()
    finally:
        con.close()

    counts: dict[tuple[str, str], int] = {}
    doc_ids: dict[tuple[str, str], list[str]] = {}
    for raw_error, raw_correct, doc_id in rows:
        error = normalize_gec_text(raw_error)
        correct = normalize_gec_text(raw_correct)
        if not error or not correct or error == correct:
            continue
        if has_stray_quote(error) or has_stray_quote(correct):
            continue
        key = (error, correct)
        counts[key] = counts.get(key, 0) + 1
        bucket = doc_ids.setdefault(key, [])
        if doc_id and doc_id not in bucket:
            bucket.append(doc_id)

    pairs = [
        GecPair(error=error, correct=correct, count=n, doc_ids=tuple(doc_ids[(error, correct)]))
        for (error, correct), n in counts.items()
    ]
    # Deterministic priority: higher-frequency, then multiword, then alpha —
    # actual existing-pair/multiword preference is applied by the caller,
    # this is just a stable base ordering.
    pairs.sort(key=lambda p: (-p.count, p.error, p.correct))
    return pairs


# ---------------------------------------------------------------------------
# Atlas practice-lexeme resolution
# ---------------------------------------------------------------------------


def load_atlas_lexeme_index(atlas_db: Path) -> dict[str, dict[str, Any]]:
    """Map plain(lemma) -> first practice-eligible, non-proper-noun Atlas entry.

    Exact-plain match only (case/diacritic-insensitive, no lemmatization):
    a GEC ``correct`` value resolves only when it is already the Atlas
    entry's own citation-form lemma. This deliberately avoids inventing a
    lemma via inflection guessing.
    """
    entries = read_atlas_db(atlas_db)
    eligible = [e for e in entries if is_practice_eligible(e)]
    index: dict[str, dict[str, Any]] = {}
    for entry in eligible:
        lemma = entry.get("lemma")
        if not isinstance(lemma, str) or not lemma.strip():
            continue
        if entry.get("pos") == "proper noun":
            continue
        slug = entry.get("url_slug") or entry.get("slug")
        if not isinstance(slug, str) or not slug.strip():
            continue
        index.setdefault(_plain(lemma), entry)
    return index


def load_existing_pairs_by_native_slug(heritage_pairs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map nativeSlug -> owning curated pair, across every kind (first-wins).

    Used to catch the case a GEC row's ``correct`` isn't listed in any
    pair's ``corrections``/``nativeLemma`` (so :func:`load_existing_pair_good_forms`
    misses it) but the row's Atlas-resolved lemma *is* an existing pair's
    ``nativeSlug`` — e.g. a bare ``лікар`` GEC row resolving to the same
    Atlas lexeme as the curated sense-restricted ``доктор`` -> ``лікар``
    pair. Both routes must agree, because
    ``generate_practice_deck._merge_heritage_pair_overlay`` folds ANY
    overlay pair sharing a nativeSlug into the curated one at merge time
    regardless of which route produced it.
    """
    index: dict[str, dict[str, Any]] = {}
    for pair in heritage_pairs:
        slug = pair.get("nativeSlug")
        if isinstance(slug, str) and slug.strip():
            index.setdefault(slug, pair)
    return index


def load_existing_pair_good_forms(heritage_pairs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map plain(correction form) -> owning curated pair, for extend-in-place routing.

    ``sense_restricted`` pairs are excluded: every one of their frames MUST
    carry ``disambiguated: true`` (validate_heritage_pair), which requires a
    human to confirm the carrier sentence actually uses the *calque* sense
    rather than the pair's authentic sense (calque_corrections.py rule 3 —
    never a blanket auto-replace). A mechanical carrier match cannot make
    that call, so a GEC row whose correct-form only matches a
    sense_restricted pair falls through to plain new-pair resolution instead.
    """
    index: dict[str, dict[str, Any]] = {}
    for pair in heritage_pairs:
        if pair.get("kind") == "sense_restricted":
            continue
        forms: set[str] = set()
        for correction in pair.get("corrections") or []:
            if isinstance(correction, str) and correction.strip():
                forms.add(_plain(correction))
        native_lemma = pair.get("nativeLemma")
        if isinstance(native_lemma, str) and native_lemma.strip():
            forms.add(_plain(native_lemma))
        for form in forms:
            index.setdefault(form, pair)
    return index


# ---------------------------------------------------------------------------
# Corpus carrier-sentence search
# ---------------------------------------------------------------------------

_DASH = r"\-‐‑‒–—―"
_LATIN_RE = re.compile(r"[A-Za-z]")
_WS_RE = re.compile(r"\s+")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+(?=[А-ЯЄІЇҐA-Z«„\"'(])")
_BLANK_RUN_RE = re.compile(r"_{2,}")
_BROKEN_HYPHEN_RE = re.compile(r"-\s+[а-яіїєґ]")
_OCR_NOISE_RE = re.compile(r"[|~^_]|\.{4,}|,{2,}|\d{1,2}\)")
_TERMINAL_RE = re.compile(r"[.!?…][\"»”]?$")
_LEADING_RE = re.compile(r"^[«„\"'(]?[А-ЯЄІЇҐ0-9]")
MIN_SENTENCE_LEN = 40
MAX_SENTENCE_LEN = 220
MIN_SENTENCE_WORDS = 5


def word_boundary_pattern(token: str) -> re.Pattern[str]:
    """Whole-token match, dash/apostrophe-aware (mirrors read_sentence_inventory)."""
    return re.compile(rf"(?<![\wʼ’{_DASH}]){re.escape(token)}(?![\wʼ’{_DASH}])")


def candidate_sentences(text: str) -> list[str]:
    collapsed = _WS_RE.sub(" ", text).strip()
    return [piece.strip() for piece in _SENT_SPLIT_RE.split(collapsed) if piece.strip()]


def is_clean_sentence(sentence: str) -> bool:
    if not (MIN_SENTENCE_LEN <= len(sentence) <= MAX_SENTENCE_LEN):
        return False
    if len(sentence.split()) < MIN_SENTENCE_WORDS:
        return False
    if _LATIN_RE.search(sentence):
        return False
    if _BLANK_RUN_RE.search(sentence):
        return False
    if _BROKEN_HYPHEN_RE.search(sentence):
        return False
    if _OCR_NOISE_RE.search(sentence):
        return False
    if not _TERMINAL_RE.search(sentence):
        return False
    return bool(_LEADING_RE.match(sentence))


@dataclass(frozen=True)
class Carrier:
    sentence: str
    sentence_with_slot: str
    bad_sentence: str
    chunk_id: str
    source_file: str
    table: str


def substitute_single(pattern: re.Pattern[str], sentence: str, replacement: str) -> str | None:
    result, count = pattern.subn(replacement, sentence)
    return result if count == 1 else None


def find_carrier_sentence(
    con: sqlite3.Connection,
    target: str,
    replacement: str,
    *,
    limit: int = 40,
    exclude_sentences: set[str] | None = None,
) -> Carrier | None:
    """Find a clean corpus sentence with exactly one whole-token ``target``.

    Literary corpus is tried first (born-digital prose reads cleaner than
    OCR'd textbook scans); textbooks are the fallback. Never invents text —
    returns None when no sentence clears every gate. ``exclude_sentences``
    skips carrier sentences already used elsewhere for the same pair, so a
    pair's multiple frames read as distinct sentences rather than the same
    sentence repeated with a different wrong-answer label.
    """
    pattern = word_boundary_pattern(target)
    # Always FTS5-quote: an unquoted bareword containing "-" (e.g. будь-який)
    # is parsed as a NOT-operator boundary, not a literal token.
    fts_query = '"' + target.replace('"', '""') + '"'
    for table, fts in (("literary_texts", "literary_fts"), ("textbooks", "textbooks_fts")):
        cur = con.execute(
            f"SELECT t.chunk_id, t.source_file, t.text FROM {fts} f "
            f"JOIN {table} t ON t.rowid = f.rowid WHERE f.text MATCH ? LIMIT ?",
            (fts_query, limit),
        )
        for chunk_id, source_file, text in cur.fetchall():
            for sentence in candidate_sentences(text):
                if not is_clean_sentence(sentence):
                    continue
                if target not in sentence or replacement in sentence:
                    continue
                blanked = substitute_single(pattern, sentence, "___")
                bad = substitute_single(pattern, sentence, replacement)
                if blanked is None or bad is None:
                    continue
                if exclude_sentences and blanked in exclude_sentences:
                    continue
                return Carrier(
                    sentence=sentence,
                    sentence_with_slot=blanked,
                    bad_sentence=bad,
                    chunk_id=str(chunk_id),
                    source_file=str(source_file),
                    table=table,
                )
    return None


# ---------------------------------------------------------------------------
# Frame / pair assembly
# ---------------------------------------------------------------------------


@dataclass
class WaveStats:
    total_raw_rows: int = 0
    unique_clean_pairs: int = 0
    routed_extend_existing: int = 0
    routed_new_candidate: int = 0
    routed_unresolved: int = 0
    routed_sense_restricted_conflict: int = 0
    frames_emitted_extend: int = 0
    frames_emitted_new: int = 0
    new_pairs_emitted: int = 0
    residual_no_carrier: list[dict[str, Any]] = field(default_factory=list)
    capped_skipped: list[dict[str, Any]] = field(default_factory=list)
    per_pair_capped: list[dict[str, Any]] = field(default_factory=list)
    homonym_ambiguous: list[dict[str, Any]] = field(default_factory=list)


def build_frame(pair_key: tuple[str, str], carrier: Carrier, count: int, doc_ids: tuple[str, ...]) -> dict[str, Any]:
    error, correct = pair_key
    origin = f"{WAVE_ORIGIN_TAG}:{carrier.table}/{carrier.chunk_id}"
    frame: dict[str, Any] = {
        "sentence_with_slot": carrier.sentence_with_slot,
        "answer_form": correct,
        "calque_form": error,
        "origin": origin,
    }
    return frame


def rationale_for(calque_label: str, native_lemma: str, count: int, doc_count: int) -> str:
    return (
        f"UA-GEC F/Calque corpus evidence (native + fluency annotator correction, "
        f"n={count} occurrence(s) across {doc_count} document(s)): "
        f"«{calque_label}» flagged non-standard; reviewed correction «{native_lemma}»."
    )


def build_new_pair(
    native_entry: dict[str, Any],
    rows: list[GecPair],
) -> dict[str, Any]:
    slug = native_entry.get("url_slug") or native_entry.get("slug")
    native_lemma = native_entry.get("lemma")
    total_count = sum(row.count for row in rows)
    doc_ids: set[str] = set()
    for row in rows:
        doc_ids.update(row.doc_ids)
    calque_surfaces = sorted({row.error for row in rows})
    corrections = sorted({row.correct for row in rows})
    # Citation form: highest-frequency observed error surface, alpha tiebreak.
    calque_label = sorted(rows, key=lambda r: (-r.count, r.error))[0].error
    return {
        "calqueLabel": calque_label,
        "calqueSurfaces": calque_surfaces,
        "nativeSlug": slug,
        "nativeLemma": native_lemma,
        "kind": "lexical",
        "corrections": corrections,
        "rationale": rationale_for(calque_label, native_lemma, total_count, len(doc_ids)),
        "citations": [f"ua-gec:F/Calque n={total_count}"],
        "sourceFamily": "ua-gec",
        "sourceFamilies": ["ua-gec"],
        "severity": "enrichment",
        "curator": WAVE_CURATOR_TAG,
        "notes": (
            "Wave-1 mechanical GEC-calque densification (#6623): nativeSlug resolved via exact "
            "Atlas lemma match; frame sentences are corpus-attested carriers with the sole "
            "`correct` occurrence substituted by the UA-GEC `error` surface. No curator linguistic "
            "review beyond mechanical POS-admission and carrier-sentence gates; severity defaults "
            "to enrichment pending curator upgrade to russianism where warranted."
        ),
        "frames": [],
    }


def is_ambiguous_single_token(word: str, vesum_db: Path, cache: dict[str, bool]) -> bool:
    """True if the word-form maps to more than one distinct VESUM lemma.

    Ukrainian is rich in cross-POS homonyms (e.g. ``збіг`` the noun
    "coincidence" vs ``збіг`` the masculine past tense of ``збігти`` "ran
    off"). A carrier sentence is matched by literal string only — no
    parsing — so a token with more than one *distinct* lemma spelling risks
    landing the fill-slot on the wrong sense of the word entirely.
    Conservative: skip these rather than guess. Multiword phrases are exempt
    (VESUM is word-form level; unrelated-meaning phrase collision is rare).
    """
    if " " in word:
        return False
    if word not in cache:
        matches = _vesum_verify_words([word], db_path=vesum_db).get(word, [])
        lemmas = {m["lemma"] for m in matches if isinstance(m, dict) and m.get("lemma")}
        cache[word] = len(lemmas) > 1
    return cache[word]


def run_wave(
    *,
    sources_db: Path,
    atlas_db: Path,
    vesum_db: Path,
    heritage_pairs_path: Path,
    max_frames_per_existing_pair: int,
    max_frames_per_new_pair: int,
    max_total_frames: int,
) -> tuple[list[dict[str, Any]], WaveStats]:
    import yaml

    gec_pairs = load_gec_calque_pairs(sources_db)
    heritage_payload = yaml.safe_load(heritage_pairs_path.read_text(encoding="utf-8")) or {}
    heritage_pairs = [row for row in (heritage_payload.get("pairs") or []) if isinstance(row, dict)]
    good_form_index = load_existing_pair_good_forms(heritage_pairs)
    existing_by_slug = load_existing_pairs_by_native_slug(heritage_pairs)
    atlas_index = load_atlas_lexeme_index(atlas_db)
    ambiguity_cache: dict[str, bool] = {}

    stats = WaveStats(total_raw_rows=len(gec_pairs), unique_clean_pairs=len(gec_pairs))

    # (row, owning curated pair) — owning is None until a new-pair group is
    # built for it below (new pairs are grouped, so they carry no single
    # "owning pair" up front).
    extend_rows: list[tuple[GecPair, dict[str, Any]]] = []
    new_rows: dict[str, list[GecPair]] = {}
    for row in gec_pairs:
        plain_correct = _plain(row.correct)
        owning = good_form_index.get(plain_correct)
        atlas_entry = atlas_index.get(plain_correct)
        if owning is None and atlas_entry is not None:
            slug = atlas_entry.get("url_slug") or atlas_entry.get("slug")
            collision = existing_by_slug.get(slug)
            if collision is not None:
                if collision.get("kind") == "sense_restricted":
                    # Never fold a mechanical frame into a sense-restricted
                    # pair — same reasoning as load_existing_pair_good_forms.
                    stats.routed_sense_restricted_conflict += 1
                    continue
                owning = collision
        if owning is not None:
            extend_rows.append((row, owning))
            stats.routed_extend_existing += 1
        elif atlas_entry is not None:
            new_rows.setdefault(plain_correct, []).append(row)
            stats.routed_new_candidate += 1
        else:
            stats.routed_unresolved += 1

    # Priority: existing-pair extensions first (pre-vetted quality anchor),
    # then multiword new-pair groups, then the remaining new-pair groups —
    # each ordered by descending GEC frequency for determinism.
    extend_rows.sort(key=lambda pair: (-pair[0].count, pair[0].error, pair[0].correct))
    new_groups = sorted(
        new_rows.items(),
        key=lambda kv: (
            not any(row.is_multiword for row in kv[1]),
            -sum(row.count for row in kv[1]),
            kv[0],
        ),
    )

    con = sqlite3.connect(sources_db)
    overlay_pairs: list[dict[str, Any]] = []
    total_emitted = 0

    def budget_left() -> int:
        return max_total_frames - total_emitted

    try:
        # --- Extend existing curated pairs -----------------------------
        by_native_slug: dict[str, dict[str, Any]] = {}
        used_sentences: dict[str, set[str]] = {}
        for row, owning_pair in extend_rows:
            if budget_left() <= 0:
                stats.capped_skipped.append({"error": row.error, "correct": row.correct, "reason": "global_cap"})
                continue
            if is_ambiguous_single_token(row.correct, vesum_db, ambiguity_cache):
                stats.homonym_ambiguous.append(
                    {"error": row.error, "correct": row.correct, "route": "extend_existing"}
                )
                continue
            slug = owning_pair.get("nativeSlug")
            overlay = by_native_slug.get(slug)
            if overlay is None:
                overlay = {"nativeSlug": slug, "frames": []}
                by_native_slug[slug] = overlay
                overlay_pairs.append(overlay)
                # Seed with sentences the curated pair already uses so a new
                # frame never duplicates an existing hand-authored one.
                used_sentences[slug] = {
                    frame["sentence_with_slot"]
                    for frame in (owning_pair.get("frames") or [])
                    if isinstance(frame, dict) and frame.get("sentence_with_slot")
                }
            if len(overlay["frames"]) >= max_frames_per_existing_pair:
                stats.per_pair_capped.append(
                    {"error": row.error, "correct": row.correct, "route": "extend_existing", "nativeSlug": slug}
                )
                continue
            carrier = find_carrier_sentence(
                con, row.correct, row.error, exclude_sentences=used_sentences[slug]
            )
            if carrier is None:
                stats.residual_no_carrier.append(
                    {"error": row.error, "correct": row.correct, "route": "extend_existing", "nativeSlug": slug}
                )
                continue
            overlay["frames"].append(build_frame((row.error, row.correct), carrier, row.count, row.doc_ids))
            used_sentences[slug].add(carrier.sentence_with_slot)
            stats.frames_emitted_extend += 1
            total_emitted += 1

        # --- New pairs ---------------------------------------------------
        for plain_correct, rows in new_groups:
            if budget_left() <= 0:
                for row in rows:
                    stats.capped_skipped.append({"error": row.error, "correct": row.correct, "reason": "global_cap"})
                continue
            native_entry = atlas_index[plain_correct]
            native_lemma = native_entry.get("lemma") or ""
            if is_ambiguous_single_token(native_lemma, vesum_db, ambiguity_cache):
                for row in rows:
                    stats.homonym_ambiguous.append(
                        {"error": row.error, "correct": row.correct, "route": "new_pair"}
                    )
                continue
            new_pair = build_new_pair(native_entry, rows)
            rows_sorted = sorted(rows, key=lambda r: (-r.count, r.error))
            emitted_for_pair = 0
            new_pair_sentences: set[str] = set()
            for row in rows_sorted:
                if emitted_for_pair >= max_frames_per_new_pair or budget_left() <= 0:
                    if budget_left() <= 0:
                        stats.capped_skipped.append(
                            {"error": row.error, "correct": row.correct, "reason": "global_cap"}
                        )
                    else:
                        stats.per_pair_capped.append(
                            {"error": row.error, "correct": row.correct, "route": "new_pair", "nativeSlug": new_pair["nativeSlug"]}
                        )
                    continue
                carrier = find_carrier_sentence(
                    con, row.correct, row.error, exclude_sentences=new_pair_sentences
                )
                if carrier is None:
                    stats.residual_no_carrier.append(
                        {"error": row.error, "correct": row.correct, "route": "new_pair", "nativeSlug": new_pair["nativeSlug"]}
                    )
                    continue
                new_pair["frames"].append(build_frame((row.error, row.correct), carrier, row.count, row.doc_ids))
                new_pair_sentences.add(carrier.sentence_with_slot)
                emitted_for_pair += 1
                stats.frames_emitted_new += 1
                total_emitted += 1
            if new_pair["frames"]:
                overlay_pairs.append(new_pair)
                stats.new_pairs_emitted += 1
    finally:
        con.close()

    return overlay_pairs, stats


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_overlay_yaml(path: Path, pairs: list[dict[str, Any]]) -> None:
    import yaml

    payload = {
        "schema_version": 1,
        "description": (
            "Wave-1 additive overlay (#6623): UA-GEC F/Calque pairs turned into corpus-carrier "
            "frames by scripts/lexicon/heritage_calque_wave.py. Merged into the curated "
            "heritage_pairs.yaml at build time by generate_practice_deck.read_heritage_pairs — "
            "the hand-curated file itself is never edited by this script. A row whose nativeSlug "
            "matches a curated pair contributes only new frames; an unseen nativeSlug is a new "
            "pair carrying its own required fields."
        ),
        "pairs": pairs,
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100),
        encoding="utf-8",
    )


def write_residual_json(path: Path, stats: WaveStats) -> None:
    payload = {
        "schema": "heritage-calque-wave1-residual",
        "counts": {
            "total_raw_rows": stats.total_raw_rows,
            "unique_clean_pairs": stats.unique_clean_pairs,
            "routed_extend_existing": stats.routed_extend_existing,
            "routed_new_candidate": stats.routed_new_candidate,
            "routed_unresolved": stats.routed_unresolved,
            "routed_sense_restricted_conflict": stats.routed_sense_restricted_conflict,
            "frames_emitted_extend": stats.frames_emitted_extend,
            "frames_emitted_new": stats.frames_emitted_new,
            "new_pairs_emitted": stats.new_pairs_emitted,
            "residual_no_carrier": len(stats.residual_no_carrier),
            "capped_skipped": len(stats.capped_skipped),
            "per_pair_capped": len(stats.per_pair_capped),
            "homonym_ambiguous": len(stats.homonym_ambiguous),
        },
        "residual_no_carrier": stats.residual_no_carrier,
        "capped_skipped": stats.capped_skipped,
        "per_pair_capped": stats.per_pair_capped,
        "homonym_ambiguous": stats.homonym_ambiguous,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_residual_report(path: Path, stats: WaveStats) -> None:
    total_emitted = stats.frames_emitted_extend + stats.frames_emitted_new
    lines = [
        "# Heritage calque wave-1 residual census (#6623)",
        "",
        "Generated by `scripts/lexicon/heritage_calque_wave.py`. Every count below is "
        "tool-backed against `data/sources.db` (`ua_gec_errors` where `error_type='F/Calque'`) "
        "and `data/atlas.db` at the run that produced "
        "`data/lexicon/heritage_pairs.wave1-calque.yaml`.",
        "",
        "## Pipeline counts",
        "",
        f"- UA-GEC `F/Calque` raw rows: {stats.total_raw_rows}",
        f"- Unique (error, correct) pairs after normalize/dedupe/quote-artifact drop: "
        f"{stats.unique_clean_pairs}",
        f"- Routed to extend an existing curated pair (correct matches an existing "
        f"pair's corrections/nativeLemma): {stats.routed_extend_existing}",
        f"- Routed to a new pair (correct exact-matches a public practice-eligible Atlas "
        f"lemma, non-proper-noun): {stats.routed_new_candidate}",
        f"- Structurally unresolved (correct has no practice-eligible Atlas lemma and no "
        f"existing pair) — cannot be emitted regardless of carrier availability: "
        f"{stats.routed_unresolved}",
        f"- Excluded: correct resolves to the same Atlas lemma as an existing "
        f"`sense_restricted` pair (e.g. `лікар` vs the curated `доктор` -> `лікар`) — "
        f"folding an undisambiguated mechanical frame into that pair would fail its "
        f"`disambiguated: true` requirement, so these are dropped rather than misfiled: "
        f"{stats.routed_sense_restricted_conflict}",
        "",
        "## Emission",
        "",
        f"- Frames emitted extending existing pairs: {stats.frames_emitted_extend}",
        f"- Frames emitted on new pairs: {stats.frames_emitted_new}",
        f"- New pairs emitted (>=1 frame found): {stats.new_pairs_emitted}",
        f"- **Total new frames emitted: {total_emitted}**",
        "",
        "## Residual — no carrier sentence found (fail-closed, never invented)",
        "",
        f"- {len(stats.residual_no_carrier)} routable (error, correct) rows found zero clean "
        "corpus sentence containing `correct` as a whole token within the 40-220 char / "
        "Ukrainian-script / single-occurrence / no-OCR-artifact gates. Full list: "
        "`data/lexicon/heritage_pairs.wave1-calque.residual.json`.",
        "",
        f"- {len(stats.capped_skipped)} additional routable rows were left unprocessed once the "
        "run's volume cap was reached (see `--max-total-frames`); they are not linguistic "
        "residual, just deferred to a future wave.",
        "",
        f"- {len(stats.per_pair_capped)} further routable rows were skipped purely by the "
        "per-pair frame cap (`--max-frames-per-existing-pair` / `--max-frames-per-new-pair`) "
        "keeping any single pair from dominating the wave; also deferred, not linguistic residual.",
        "",
        "## Excluded — cross-POS homonym risk",
        "",
        f"- {len(stats.homonym_ambiguous)} routable rows were excluded because `correct` VESUM-"
        "resolves to more than one distinct lemma (e.g. `збіг` the noun \"coincidence\" vs `збіг` "
        "the masculine past tense of `збігти` \"ran off\"). A carrier sentence is matched by "
        "literal string only, so an ambiguous token risks landing the fill-slot on the wrong "
        "sense; these are dropped rather than guessed at.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--atlas-db", type=Path, default=DEFAULT_ATLAS_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--heritage-pairs", type=Path, default=DEFAULT_HERITAGE_PAIRS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OVERLAY_OUT)
    parser.add_argument("--residual-json", type=Path, default=DEFAULT_RESIDUAL_JSON)
    parser.add_argument("--residual-report", type=Path, default=DEFAULT_RESIDUAL_REPORT)
    parser.add_argument("--max-frames-per-existing-pair", type=int, default=3)
    parser.add_argument("--max-frames-per-new-pair", type=int, default=2)
    parser.add_argument("--max-total-frames", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true", help="Compute and report; do not write output files.")
    args = parser.parse_args(argv)

    if not args.atlas_db.exists():
        print(f"ERROR: {args.atlas_db} not found; pass --atlas-db explicitly", file=sys.stderr)
        return 1
    if not args.sources_db.exists():
        print(f"ERROR: {args.sources_db} not found; pass --sources-db explicitly", file=sys.stderr)
        return 1
    if not args.vesum_db.exists():
        print(f"ERROR: {args.vesum_db} not found; pass --vesum-db explicitly", file=sys.stderr)
        return 1

    overlay_pairs, stats = run_wave(
        sources_db=args.sources_db,
        atlas_db=args.atlas_db,
        vesum_db=args.vesum_db,
        heritage_pairs_path=args.heritage_pairs,
        max_frames_per_existing_pair=args.max_frames_per_existing_pair,
        max_frames_per_new_pair=args.max_frames_per_new_pair,
        max_total_frames=args.max_total_frames,
    )
    total_emitted = stats.frames_emitted_extend + stats.frames_emitted_new
    print(
        f"routed: extend={stats.routed_extend_existing} new={stats.routed_new_candidate} "
        f"unresolved={stats.routed_unresolved} sense_restricted_conflict="
        f"{stats.routed_sense_restricted_conflict} | emitted frames: extend={stats.frames_emitted_extend} "
        f"new={stats.frames_emitted_new} total={total_emitted} | new_pairs={stats.new_pairs_emitted} "
        f"| residual_no_carrier={len(stats.residual_no_carrier)} capped={len(stats.capped_skipped)} "
        f"homonym_ambiguous={len(stats.homonym_ambiguous)}"
    )
    if args.dry_run:
        return 0

    write_overlay_yaml(args.out, overlay_pairs)
    write_residual_json(args.residual_json, stats)
    args.residual_report.parent.mkdir(parents=True, exist_ok=True)
    write_residual_report(args.residual_report, stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
