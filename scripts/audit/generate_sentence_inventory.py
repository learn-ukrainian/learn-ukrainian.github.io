"""Extract short, source-attested examples for Word Atlas practice and Daily Word.

The committed inventory contains only learner-facing sentences plus an
attribution-safe provenance record.  It intentionally never copies a local
ULP filename, transcript identifier, URL, or any other private locator.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DEFAULT_DAILY_POOL = Path("site/src/data/lexicon-daily-pool.json")
DEFAULT_PRACTICE_LEXEMES_DIR = Path("site/public/lexicon")
DEFAULT_SOURCES_DB = Path("data/sources.db")
DEFAULT_VESUM_DB = Path("data/vesum.db")
DEFAULT_OUT = Path("site/src/data/lexicon-sentence-inventory.json")
PRACTICE_LEVELS = ("A1", "A2", "B1", "B2", "C1")
APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "’": "'",
        "ʼ": "'",
        "ʻ": "'",
        "ʹ": "'",
        "＇": "'",
    }
)

UK_TOKEN_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
SPACE_RE = re.compile(r"\s+")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u00ad\ufeff\u200b-\u200d]")
LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
NON_UKRAINIAN_ALPHA_RE = re.compile(r"[^\W\d_А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]")
COMBINING_MARK_RE = re.compile(r"[\u0300-\u036f]")
MIDWORD_JOIN_RE = re.compile(r"[а-щьюяєіїґ][А-ЩЬЮЯЄІЇҐ]")
ENUMERATION_RE = re.compile(
    r"(?<!\w)[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:,\s*[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+){3,}[.!?]$"
)
TITLE_CASE_RUN_RE = re.compile(
    r"^\s*(?:[А-ЩЬЮЯЄІЇҐ][а-щьюяєіїґ]+\s+){3,}"
    r"[А-ЩЬЮЯЄІЇҐ][а-щьюяєіїґ]+\s*[.!?]$"
)
ACRONYM_JOIN_RE = re.compile(
    r"\b[А-ЩЬЮЯЄІЇҐ]{3,}\s+[А-ЩЬЮЯЄІЇҐ][а-щьюяєіїґ]+\b"
)
FORMULA_MARKER_RE = re.compile(
    r"(?:[=<>≤≥→←↔⇒⇔∑√±×÷§]|(?:^|\s)\d+\s*[.)](?:\s|$)|"
    r"(?<!\w)[A-Za-z]\s*[=<>]|(?:—|–|-)\s*[»>])"
)
OPTION_LABEL_RE = re.compile(
    r"(?<![А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])[А-ЩЬЮЯЄІЇҐ]\s+(?=[А-ЩЬЮЯЄІЇҐ])"
)
WORKSHEET_RE = re.compile(
    r"\b(?:виконай|виконайте|запиши|запишіть|вибери|виберіть|обери|оберіть|"
    r"познач|позначте|підкресли|підкресліть|випиши|випишіть|спиши|спишіть|"
    r"перепиши|перепишіть|доповни|доповніть|знайди|знайдіть|доведи|доведіть|"
    r"прочитай|прочитайте|склади|складіть|заповни|заповніть|перевір|перевірте|"
    r"запропонуй|запропонуйте|визнач|визначте|назви|назвіть|поміркуй|поміркуйте|"
    r"поясни|поясніть|вимов|вимовте|добери|доберіть|скопіюй|скопіюйте|"
    r"збережи|збережіть|зроби|зробіть|обговори|обговоріть|напиши|напишіть|"
    r"створи|створіть|підсумуй|підсумуймо|уяви|уявіть|обґрунтуй|обґрунтуйте|"
    r"сформулюй|сформулюйте|порівняй|порівняймо|порівняйте|розкажи|розкажіть|"
    r"опиши|опишіть|утвори|утворіть|"
    r"завдан(?:ня|ні)|вправ(?:а|и|у)|запитання|відповід(?:ь|і)|тест|розділ)\b",
    re.IGNORECASE,
)
BRACKET_RE = re.compile(r"[\[\]()]")
LEADING_NUMBER_RE = re.compile(
    r"^\s*\d+(?:\.\d+)*\s+(?P<word>[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)"
)
MONTH_WORDS = frozenset(
    {
        "січня",
        "лютого",
        "березня",
        "квітня",
        "травня",
        "червня",
        "липня",
        "серпня",
        "вересня",
        "жовтня",
        "листопада",
        "грудня",
    }
)
LEADING_ITEM_MARKER_RE = re.compile(r"^\s*\d+(?:\.\d+)*\s*[.)•·▪◦°]+\s*")
BULLET_RE = re.compile(r"[•·▪◦]")
LEADING_FRAGMENT_RE = re.compile(r"^\s*[,;:…]")
LEADING_LOWERCASE_RE = re.compile(r"^\s*[а-щьюяєіїґ]")
QUESTION_PROMPT_RE = re.compile(r"\bу яких\b", re.IGNORECASE)
SINGLE_LETTER_PAIR_RE = re.compile(
    r"(?<!\w)[А-ЩЬЮЯЄІЇҐ]\s+[А-ЩЬЮЯЄІЇҐ](?!\w)"
)
FORMULA_TERM_RE = re.compile(
    r"\b(?:ОДЗ|параметр\w*|площин\w*)\b|(?<!\w)[Ьь](?!\w)",
    re.IGNORECASE,
)
DECORATIVE_SYMBOL_RE = re.compile(r"[★☆◆◇◊▪▫●○]")
MIXED_ALNUM_RE = re.compile(
    r"(?:[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]\d+|\d+[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])"
)
FILL_BLANK_RE = re.compile(r"_{2,}")
LEADING_HEADING_RE = re.compile(
    r"^\s*(?:правило|вправа|завдання|розділ|тема|назва|підсумок)\b",
    re.IGNORECASE,
)
# VESUM contains imperative analyses for common homonymous conjunctions,
# nouns, and adjectives; these surfaces are retained when their sentence
# clearly uses the non-imperative reading.
IMPERATIVE_HOMONYM_EXCEPTIONS = frozenset(
    {
        "коли",
        "при",
        "нехай",
        "причини",
        "обряди",
        "пар",
        "наприклад",
        "напри",
        "добрий",
        "синій",
        "злий",
        "гори",
        "вчи",
        "відходи",
    }
)
MALFORMED_PUNCT_RE = re.compile(r"\s+[,.!?]")
SLASH_FORM_RE = re.compile(r"/")
SHORT_TOKEN_RUN_RE = re.compile(
    r"(?<!\w)(?:[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]{1,2}\s+){3,}"
    r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]{1,2}(?!\w)"
)
TRAILING_SINGLE_TOKEN_RE = re.compile(r"(?:^|\s)[А-ЩЬЮЯЄІЇҐ]\s*[.!?]$")
UPPERCASE_HEADING_RE = re.compile(r"\b[А-ЩЬЮЯЄІЇҐ]{4,}\b")

TEXTBOOK_LICENSE = {
    "status": "not_openly_licensed",
    "useBasis": "short educational quotation with attribution",
}
ULP_LICENSE = {
    "status": "copyrighted_source",
    "useBasis": "short educational quotation with attribution",
}


def _text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _normalise(text: str) -> str:
    # OCR frequently breaks a word at the end of a visual line (``до-\nпомогу``).
    text = re.sub(r"(?<=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])-\s+(?=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])", "", text)
    return SPACE_RE.sub(" ", text).strip()


def _tokens(text: str) -> list[str]:
    return UK_TOKEN_RE.findall(text)


def _vesum_token_variants(token: str) -> tuple[str, ...]:
    normalized = token.translate(APOSTROPHE_TRANSLATION)
    return tuple(dict.fromkeys((token, token.casefold(), normalized, normalized.casefold())))


def _canonical_surface(value: str) -> str:
    return value.translate(APOSTROPHE_TRANSLATION).casefold()


def _exact_target_present(sentence: str, lemma: str) -> bool:
    target = _canonical_surface(lemma)
    return any(_canonical_surface(token) == target for token in _tokens(sentence))


def _single_target_surface(sentence: str, lemma: str) -> str | None:
    """Return the one exact target token when a sentence can be safely blanked."""
    target = _canonical_surface(lemma)
    matches = [token for token in _tokens(sentence) if _canonical_surface(token) == target]
    return matches[0] if len(matches) == 1 else None


def _is_source_sentence_noise(
    sentence: str,
    *,
    vesum: VesumSentenceVerifier | None = None,
) -> bool:
    """Reject textbook worksheet, formula, and OCR fragments before mining.

    The textbook corpus contains exercises alongside prose.  A terminal
    punctuation mark and one VESUM verb are not enough to distinguish a
    learner-facing sentence from an algebra variable, answer-choice list, or
    dictionary/worksheet fragment, especially for one- and two-character
    lemmas.  These are conservative fail-closed shape gates; they do not make
    lexical or grammatical claims about a target.
    """
    leading_number = LEADING_NUMBER_RE.match(sentence)
    if LEADING_ITEM_MARKER_RE.match(sentence):
        return True
    if leading_number and leading_number.group("word").casefold() not in MONTH_WORDS:
        return True
    tokens = _tokens(sentence)
    if (
        vesum is not None
        and tokens
        and tokens[0].casefold() not in IMPERATIVE_HOMONYM_EXCEPTIONS
        and vesum.has_imperative(tokens[0])
    ):
        return True
    return any(
        (
            CONTROL_CHAR_RE.search(sentence),
            LATIN_CHAR_RE.search(sentence),
            NON_UKRAINIAN_ALPHA_RE.search(sentence),
            COMBINING_MARK_RE.search(sentence),
            MIDWORD_JOIN_RE.search(sentence),
            ENUMERATION_RE.search(sentence),
            TITLE_CASE_RUN_RE.search(sentence),
            ACRONYM_JOIN_RE.search(sentence),
            FORMULA_MARKER_RE.search(sentence),
            len(OPTION_LABEL_RE.findall(sentence)) >= 2,
            WORKSHEET_RE.search(sentence),
            BRACKET_RE.search(sentence),
            BULLET_RE.search(sentence),
            LEADING_FRAGMENT_RE.search(sentence),
            LEADING_LOWERCASE_RE.search(sentence),
            QUESTION_PROMPT_RE.search(sentence),
            SINGLE_LETTER_PAIR_RE.search(sentence),
            FORMULA_TERM_RE.search(sentence),
            DECORATIVE_SYMBOL_RE.search(sentence),
            MIXED_ALNUM_RE.search(sentence),
            FILL_BLANK_RE.search(sentence),
            LEADING_HEADING_RE.search(sentence),
            MALFORMED_PUNCT_RE.search(sentence),
            SLASH_FORM_RE.search(sentence),
            SHORT_TOKEN_RUN_RE.search(sentence),
            TRAILING_SINGLE_TOKEN_RE.search(sentence),
            UPPERCASE_HEADING_RE.search(sentence),
        )
    )


class VesumSentenceVerifier:
    """Small cached VESUM lookup used only for sentence-shape screening."""

    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path)
        self.cache: dict[str, bool] = {}
        self.imperative_cache: dict[str, bool] = {}

    def has_verb(self, tokens: Iterable[str]) -> bool:
        for token in tokens:
            variants = _vesum_token_variants(token)
            key = token.translate(APOSTROPHE_TRANSLATION).casefold()
            known = self.cache.get(key)
            if known is None:
                placeholders = ", ".join("?" for _ in variants)
                known = (
                    self.conn.execute(
                        f"SELECT 1 FROM forms WHERE word_form IN ({placeholders}) AND pos = 'verb' LIMIT 1",
                        variants,
                    ).fetchone()
                    is not None
                )
                self.cache[key] = known
            if known:
                return True
        return False

    def has_imperative(self, token: str) -> bool:
        """Return whether a surface form has a VESUM imperative analysis.

        This is intentionally used only for the first lexical token of a
        candidate.  Imperatives later in a sentence can be quoted speech or
        ordinary prose; a leading imperative is the reliable structural shape
        of a textbook exercise command.
        """
        variants = _vesum_token_variants(token)
        key = token.translate(APOSTROPHE_TRANSLATION).casefold()
        known = self.imperative_cache.get(key)
        if known is None:
            placeholders = ", ".join("?" for _ in variants)
            rows = self.conn.execute(
                f"SELECT tags FROM forms WHERE word_form IN ({placeholders}) AND pos = 'verb'",
                variants,
            )
            known = any(
                "impr" in (tags := row[0]).split(":")
                and bool({"1", "2"}.intersection(tags.split(":")))
                for row in rows
            )
            self.imperative_cache[key] = known
        return known

    def close(self) -> None:
        self.conn.close()


def _candidate_sentences(text: str, lemma: str, *, vesum: VesumSentenceVerifier | None = None) -> Iterable[str]:
    """Yield readable, short sentences containing the exact target lemma.

    We deliberately require the surface to equal the target lemma.  This keeps
    the inventory lemma-linked without making unverified morphology claims; the
    cloze workflow separately VESUM-checks the selected form.
    """
    for raw_sentence in SENTENCE_SPLIT_RE.split(_normalise(text)):
        sentence = raw_sentence.strip(" \t\n—–")
        tokens = _tokens(sentence)
        if not (3 <= len(tokens) <= 18 and 15 <= len(sentence) <= 180):
            continue
        if sentence.isupper() or not sentence.endswith((".", "!", "?")):
            continue
        if not _exact_target_present(sentence, lemma):
            continue
        # OCR headings, web addresses, formulas, and worksheet noise are poor
        # practice examples even when the FTS match is exact.
        if (
            "http" in sentence.casefold()
            or sentence.count("*") > 1
            or _is_source_sentence_noise(sentence, vesum=vesum)
        ):
            continue
        if vesum is not None and not vesum.has_verb(tokens):
            continue
        yield sentence


def _fts_rows(
    conn: sqlite3.Connection,
    *,
    fts_table: str,
    content_table: str,
    lemma: str,
    where_sql: str = "",
) -> Iterable[sqlite3.Row]:
    query = f'"{lemma.replace(chr(34), "")}"'
    sql = f"""
        SELECT source.text, source.title, source.chunk_id
        FROM {fts_table} AS fts
        JOIN {content_table} AS source ON source.id = fts.rowid
        WHERE {fts_table} MATCH ? {where_sql}
        ORDER BY bm25({fts_table})
        LIMIT 20
    """
    yield from conn.execute(sql, (query,))


def _source_sentences(
    conn: sqlite3.Connection,
    *,
    target: dict[str, str],
    source_kind: str,
    limit: int,
    vesum: VesumSentenceVerifier | None = None,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("source sentence limit must be positive")
    lemma = target["lemma"]
    if source_kind == "textbook":
        rows = _fts_rows(
            conn,
            fts_table="textbooks_fts",
            content_table="textbooks",
            lemma=lemma,
        )
        source_label = "Ukrainian school textbook"
        license_info = TEXTBOOK_LICENSE
    else:
        rows = _fts_rows(
            conn,
            fts_table="external_fts",
            content_table="external_articles",
            lemma=lemma,
            where_sql="AND source.source_file = 'ulp_youtube'",
        )
        # No local identifier is committed for this source family.
        source_label = "Ukrainian Lessons Podcast"
        license_info = ULP_LICENSE

    results: list[dict[str, Any]] = []
    seen_sentences: set[str] = set()
    for row in rows:
        text = _text(row["text"])
        if text is None:
            continue
        for sentence in _candidate_sentences(text, lemma, vesum=vesum):
            target_form = _single_target_surface(sentence, lemma)
            if target_form is None:
                # ``read_sentence_inventory`` replaces exactly one literal
                # target token.  Reject repeated targets here so every emitted
                # row is independently blankable and retain the source's
                # capitalization in ``targetForm``.
                continue
            sentence_key = sentence.casefold()
            if sentence_key in seen_sentences:
                continue
            seen_sentences.add(sentence_key)
            provenance: dict[str, Any] = {
                "source": source_kind,
                "label": source_label,
            }
            if source_kind == "textbook":
                # This is a public textbook chunk identifier, sufficient for
                # attribution while keeping the inventory independent of DB ids.
                provenance["locator"] = _text(row["chunk_id"])
                provenance["title"] = _text(row["title"])
            results.append(
                {
                    "lemma": lemma,
                    "lemmaId": target["lemmaId"],
                    "sentence": sentence,
                    "targetForm": target_form,
                    "cefr": target.get("cefr"),
                    "uses": ["example"],
                    "provenance": provenance,
                    "license": dict(license_info),
                }
            )
            if len(results) >= limit:
                return results
    return results


def load_daily_lemmas(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("daily pool must be a JSON list")
    lemmas = {_text(row.get("lemma")) for row in payload if isinstance(row, dict)}
    return sorted(lemma for lemma in lemmas if lemma is not None)


def load_daily_targets(path: Path) -> list[dict[str, str]]:
    """Load daily lemma ids and CEFR labels without relying on a manifest checkout."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("daily pool must be a JSON list")
    targets: dict[str, dict[str, str]] = {}
    for row in payload:
        if not isinstance(row, dict):
            continue
        lemma = _text(row.get("lemma"))
        lemma_id = _text(row.get("slug"))
        if lemma is None or lemma_id is None:
            continue
        target = {"lemma": lemma, "lemmaId": lemma_id}
        cefr = _text(row.get("cefr"))
        if cefr is not None:
            target["cefr"] = cefr
        targets[lemma] = target
    return [targets[lemma] for lemma in sorted(targets)]


def discover_practice_lexeme_paths(directory: Path) -> list[Path]:
    """Return the complete hydrated A1-C1 Practice lexeme shard set.

    The default inventory target is the public Practice surface, so silently
    mining only the shards that happen to be present would recreate the old
    partial-coverage failure.  Callers that intentionally need a smaller
    fixture can pass explicit paths to ``load_practice_targets`` instead.
    """
    paths = [directory / f"practice-lexemes.{level}.json" for level in PRACTICE_LEVELS]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"missing hydrated practice lexeme shards: {formatted}")
    return paths


def load_practice_targets(paths: Iterable[Path]) -> list[dict[str, str]]:
    """Load lemma-linked targets from hydrated Practice lexeme shards.

    Each shard is authoritative for its level.  ``lemmaId`` is the stable
    identity used by the deck; duplicate identities across shards are allowed
    only when their lemma and CEFR agree exactly, and are emitted once.
    """
    targets: dict[str, dict[str, str]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != "atlas-practice-lexemes":
            raise ValueError(f"practice lexeme shard must use atlas-practice-lexemes schema: {path}")
        if payload.get("schemaVersion") != 1:
            raise ValueError(f"practice lexeme shard schemaVersion must be 1: {path}")
        level = _text(payload.get("level"))
        if level not in PRACTICE_LEVELS:
            raise ValueError(f"practice lexeme shard has unsupported level {level!r}: {path}")
        rows = payload.get("lexemes")
        if not isinstance(rows, list):
            raise ValueError(f"practice lexeme shard lexemes must be a list: {path}")
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"practice lexeme {path}:{index + 1} must be an object")
            lemma = _text(row.get("lemma"))
            lemma_id = _text(row.get("lemmaId"))
            if lemma is None or lemma_id is None:
                raise ValueError(f"practice lexeme {path}:{index + 1} requires lemma and lemmaId")
            cefr = _text(row.get("cefr")) or level
            if cefr != level:
                raise ValueError(
                    f"practice lexeme {path}:{index + 1} CEFR {cefr!r} does not match shard level {level!r}"
                )
            target = {"lemma": lemma, "lemmaId": lemma_id, "cefr": cefr}
            previous = targets.get(lemma_id)
            if previous is not None and previous != target:
                raise ValueError(f"conflicting practice target for lemmaId {lemma_id!r}")
            targets[lemma_id] = target
    return [
        targets[lemma_id]
        for lemma_id in sorted(
            targets,
            key=lambda value: (PRACTICE_LEVELS.index(targets[value]["cefr"]), targets[value]["lemma"], value),
        )
    ]


def build_inventory(
    targets: Iterable[dict[str, str]],
    sources_db: Path,
    *,
    include_ulp: bool = False,
    vesum_db: Path | None = None,
    max_per_lemma: int = 1,
) -> list[dict[str, Any]]:
    if max_per_lemma < 1:
        raise ValueError("max_per_lemma must be positive")
    conn = sqlite3.connect(sources_db)
    conn.row_factory = sqlite3.Row
    vesum = VesumSentenceVerifier(vesum_db) if vesum_db is not None and vesum_db.exists() else None
    try:
        rows: list[dict[str, Any]] = []
        for target in sorted(targets, key=lambda row: row["lemma"]):
            source_rows = _source_sentences(
                conn,
                target=target,
                source_kind="textbook",
                limit=max_per_lemma,
                vesum=vesum,
            )
            if not source_rows and include_ulp:
                source_rows = _source_sentences(
                    conn,
                    target=target,
                    source_kind="ulp",
                    limit=max_per_lemma,
                    vesum=vesum,
                )
            rows.extend(source_rows)
        return rows
    finally:
        conn.close()
        if vesum is not None:
            vesum.close()


def write_inventory(rows: list[dict[str, Any]], out_path: Path) -> None:
    payload = {
        "schema": "atlas-sentence-inventory",
        "schemaVersion": 1,
        "rows": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--include-ulp", action="store_true")
    parser.add_argument(
        "--max-per-lemma",
        type=int,
        default=1,
        help="Maximum distinct source sentences to retain for each target lemma.",
    )
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--daily-pool",
        type=Path,
        help="Use the legacy Daily Word pool as the target set instead of Practice shards.",
    )
    target_group.add_argument(
        "--practice-lexemes-dir",
        type=Path,
        default=DEFAULT_PRACTICE_LEXEMES_DIR,
        help="Directory containing the complete hydrated practice-lexemes.A1-C1.json set.",
    )
    target_group.add_argument(
        "--practice-lexemes",
        type=Path,
        action="append",
        dest="practice_lexeme_paths",
        help="Explicit practice lexeme shard; repeat for a bounded fixture or selected levels.",
    )
    args = parser.parse_args(argv)
    if args.daily_pool is not None:
        targets = load_daily_targets(args.daily_pool)
    elif args.practice_lexeme_paths:
        targets = load_practice_targets(args.practice_lexeme_paths)
    else:
        targets = load_practice_targets(discover_practice_lexeme_paths(args.practice_lexemes_dir))
    rows = build_inventory(
        targets,
        args.sources_db,
        include_ulp=args.include_ulp,
        vesum_db=args.vesum_db,
        max_per_lemma=args.max_per_lemma,
    )
    write_inventory(rows, args.out)
    print(f"sentence inventory: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
