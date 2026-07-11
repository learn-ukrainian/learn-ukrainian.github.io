"""Shared offline helpers for reviewable lexical-relation candidates.

The generators in this directory deliberately stop at a candidate artifact.
Nothing here mutates the Atlas manifest or treats a generated relation as
learner-facing truth.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator, Mapping
from itertools import pairwise
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = PROJECT_ROOT / "data" / "lexicon" / "relation_candidates.json"
DEFAULT_VESUM_DB = PROJECT_ROOT / "data" / "vesum.db"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"

RELATIONS = ("paronyms", "synonyms", "antonyms", "homonyms")
UK_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ]+(?:['’ʼ-][A-Za-zА-Яа-яЄєІіЇїҐґ]+)*")
CORPUS_TOKEN_RE = re.compile(r"[А-Яа-яЄєІіЇїҐґ]+(?:['’ʼ-][А-Яа-яЄєІіЇїҐґ]+)*")
APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "′": "'"})


def normalize_word(value: object) -> str:
    """Normalize a lemma without guessing at morphology."""
    text = unicodedata.normalize("NFKC", str(value or "")).strip().casefold()
    text = text.translate(APOSTROPHE_TRANSLATION)
    text = "".join(char for char in unicodedata.normalize("NFD", text) if char not in "\u0300\u0301")
    return unicodedata.normalize("NFC", text)


def is_single_word(value: object) -> bool:
    text = normalize_word(value)
    return bool(text and UK_WORD_RE.fullmatch(text))


def shared_prefix_length(first: str, second: str) -> int:
    length = 0
    for left, right in zip(first, second, strict=False):
        if left != right:
            break
        length += 1
    return length


def levenshtein(first: str, second: str, cutoff: int | None = None) -> int:
    """Return Levenshtein distance, stopping once a row exceeds ``cutoff``."""
    if first == second:
        return 0
    if len(first) > len(second):
        first, second = second, first
    if cutoff is not None and len(second) - len(first) > cutoff:
        return cutoff + 1
    previous = list(range(len(first) + 1))
    for right_index, right in enumerate(second, 1):
        current = [right_index]
        row_min = right_index
        for left_index, left in enumerate(first, 1):
            value = min(
                current[-1] + 1,
                previous[left_index] + 1,
                previous[left_index - 1] + (left != right),
            )
            current.append(value)
            row_min = min(row_min, value)
        if cutoff is not None and row_min > cutoff:
            return cutoff + 1
        previous = current
    return previous[-1]


class VesumIndex:
    """Small, read-only exact-lemma index over the VESUM SQLite artifact."""

    def __init__(self, db_path: Path = DEFAULT_VESUM_DB) -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> VesumIndex:
        return self

    def __exit__(self, _exc_type: object, _exc_value: object, _traceback: object) -> None:
        self.close()

    def exact_lemmas(self, positions: Iterable[str] | None = None) -> dict[str, set[str]]:
        query = "SELECT lemma, pos FROM forms WHERE word_form = lemma"
        params: list[str] = []
        allowed = sorted(set(positions or ()))
        if allowed:
            query += " AND pos IN (" + ",".join("?" for _ in allowed) + ")"
            params.extend(allowed)
        rows = self.conn.execute(query, params)
        result: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            lemma = normalize_word(row["lemma"])
            if is_single_word(lemma):
                result[lemma].add(str(row["pos"]))
        return dict(result)

    def exact_members(self, words: Iterable[str]) -> dict[str, set[str]]:
        normalized = sorted({normalize_word(word) for word in words if is_single_word(word)})
        if not normalized:
            return {}
        result: dict[str, set[str]] = defaultdict(set)
        for start in range(0, len(normalized), 800):
            batch = normalized[start : start + 800]
            placeholders = ",".join("?" for _ in batch)
            rows = self.conn.execute(
                f"SELECT lemma, pos FROM forms WHERE word_form = lemma AND word_form IN ({placeholders})",
                batch,
            )
            for row in rows:
                result[normalize_word(row["lemma"])].add(str(row["pos"]))
        return dict(result)

    def forms_for_lemmas(self, lemmas: Iterable[str]) -> dict[str, dict[str, set[str]]]:
        normalized = sorted({normalize_word(lemma) for lemma in lemmas if is_single_word(lemma)})
        result: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for start in range(0, len(normalized), 800):
            batch = normalized[start : start + 800]
            placeholders = ",".join("?" for _ in batch)
            rows = self.conn.execute(
                f"SELECT word_form, lemma, pos FROM forms WHERE lemma IN ({placeholders})",
                batch,
            )
            for row in rows:
                result[normalize_word(row["lemma"])][normalize_word(row["word_form"])].add(str(row["pos"]))
        return {lemma: dict(forms) for lemma, forms in result.items()}

    def are_inflectional_variants(self, first: str, second: str) -> bool:
        row = self.conn.execute(
            """
            SELECT 1 FROM forms
            WHERE (word_form = ? AND lemma = ?)
               OR (word_form = ? AND lemma = ?)
            LIMIT 1
            """,
            (first, second, second, first),
        ).fetchone()
        return row is not None

    def verify_exact(self, word: str, pos: str | None = None) -> bool:
        normalized = normalize_word(word)
        query = "SELECT 1 FROM forms WHERE word_form = lemma AND word_form = ?"
        params: list[str] = [normalized]
        if pos:
            query += " AND pos = ?"
            params.append(pos)
        return self.conn.execute(query, params).fetchone() is not None


class FrequencySource:
    """Deterministic frequency evidence from a supplied map or literary corpus."""

    def __init__(
        self,
        *,
        vesum: VesumIndex,
        corpus_db: Path | None = DEFAULT_SOURCES_DB,
        frequency_json: Path | None = None,
    ) -> None:
        self.vesum = vesum
        self.corpus_db = Path(corpus_db) if corpus_db else None
        self.frequency_json = Path(frequency_json) if frequency_json else None
        self.source = "none"
        self._map: dict[str, int] | None = None

    def _load_map(self) -> dict[str, int]:
        if self._map is not None:
            return self._map
        if self.frequency_json:
            payload = json.loads(self.frequency_json.read_text(encoding="utf-8"))
            if not isinstance(payload, Mapping):
                raise ValueError("frequency JSON must be an object keyed by lemma")
            values: dict[str, int] = {}
            for raw_word, raw_value in payload.items():
                value = raw_value.get("freq") if isinstance(raw_value, Mapping) else raw_value
                try:
                    values[normalize_word(raw_word)] = int(value)
                except (TypeError, ValueError):
                    continue
            self.source = "frequency_json"
            self._map = values
            return values
        self._map = {}
        return self._map

    def count(self, lemmas: Iterable[str]) -> dict[str, int | None]:
        requested = sorted({normalize_word(lemma) for lemma in lemmas if is_single_word(lemma)})
        if not requested:
            return {}
        values = self._load_map()
        if values:
            return {lemma: values.get(lemma, 0) for lemma in requested}
        if not self.corpus_db or not self.corpus_db.exists():
            return {lemma: None for lemma in requested}

        forms_by_lemma = self.vesum.forms_for_lemmas(requested)
        surface_to_lemmas: dict[str, set[str]] = defaultdict(set)
        for lemma, forms in forms_by_lemma.items():
            for surface in forms:
                surface_to_lemmas[surface].add(lemma)
        return self._count_surface_map(surface_to_lemmas, requested)

    def count_exact_lemmas(self, lemmas: Iterable[str]) -> dict[str, int | None]:
        """Count exact lemma spellings, a fast corpus floor for candidate mining."""
        requested = sorted({normalize_word(lemma) for lemma in lemmas if is_single_word(lemma)})
        if not requested:
            return {}
        values = self._load_map()
        if values:
            return {lemma: values.get(lemma, 0) for lemma in requested}
        if not self.corpus_db or not self.corpus_db.exists():
            return {lemma: None for lemma in requested}
        surface_to_lemmas = {lemma: {lemma} for lemma in requested}
        return self._count_surface_map(surface_to_lemmas, requested)

    def _count_surface_map(self, surface_to_lemmas: Mapping[str, set[str]], requested: list[str]) -> dict[str, int]:
        counts: Counter[str] = Counter()
        conn = sqlite3.connect(str(self.corpus_db))
        try:
            for (text,) in conn.execute("SELECT text FROM literary_texts WHERE text != ''"):
                for token in CORPUS_TOKEN_RE.findall(str(text)):
                    key = token.casefold()
                    if "’" in key or "ʼ" in key or "`" in key or "′" in key:
                        key = key.translate(APOSTROPHE_TRANSLATION)
                    for lemma in surface_to_lemmas.get(key, ()):
                        counts[lemma] += 1
        finally:
            conn.close()
        self.source = "literary_texts"
        return {lemma: counts.get(lemma, 0) for lemma in requested}


def _deletion_signatures(word: str, max_deletions: int = 2) -> Iterator[tuple[str, int]]:
    """Yield exact deletion signatures used for edit-distance candidate lookup."""
    seen: set[tuple[str, int]] = set()
    for deletion_count in range(max_deletions + 1):
        if deletion_count == 0:
            variants = (word,)
        elif deletion_count == 1:
            variants = (word[:index] + word[index + 1 :] for index in range(len(word)))
        else:
            variants = (
                word[:first] + word[first + 1 : second] + word[second + 1 :]
                for first in range(len(word))
                for second in range(first + 1, len(word))
            )
        for signature in variants:
            key = (signature, deletion_count)
            if key not in seen:
                seen.add(key)
                yield signature, deletion_count


def iter_edit_pairs(
    exact_lemmas: Mapping[str, set[str]],
    *,
    max_distance: int = 2,
) -> Iterator[tuple[str, str, str, int]]:
    """Yield unique same-POS lemma pairs within the requested edit radius."""
    words_by_pos: dict[str, list[str]] = defaultdict(list)
    for word, positions in exact_lemmas.items():
        for pos in sorted(positions):
            words_by_pos[pos].append(word)
    for pos in sorted(words_by_pos):
        words = sorted(set(words_by_pos[pos]))
        signatures: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for word in words:
            for signature, deletion_count in _deletion_signatures(word, max_distance):
                signatures[signature].append((word, deletion_count))
        seen: set[tuple[str, str, str]] = set()
        for candidates in signatures.values():
            if len(candidates) < 2:
                continue
            for index, (first, first_deletions) in enumerate(candidates):
                for second, second_deletions in candidates[index + 1 :]:
                    if first == second or first > second or abs(len(first) - len(second)) > max_distance:
                        continue
                    if abs(first_deletions - second_deletions) > max_distance:
                        continue
                    pair = (first, second, pos)
                    if pair in seen:
                        continue
                    distance = levenshtein(first, second, cutoff=max_distance)
                    if distance <= max_distance:
                        seen.add(pair)
                        yield first, second, pos, distance


def orthographic_variant(first: str, second: str) -> bool:
    """Reject only normalization-equivalent spelling variants."""
    return normalize_word(first) == normalize_word(second)


def load_artifact(path: Path = DEFAULT_ARTIFACT) -> dict[str, Any]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"relation artifact must be an object: {path}")
    else:
        payload = {}
    payload.setdefault("schema_version", 1)
    payload.setdefault("artifact", "reviewable_relation_candidates")
    payload.setdefault("relations", {})
    if not isinstance(payload["relations"], dict):
        raise ValueError("relation artifact relations must be an object")
    for relation in RELATIONS:
        payload["relations"].setdefault(relation, [])
    return payload


def _row_key(row: Mapping[str, Any]) -> str:
    relation = str(row.get("relation") or "")
    first = normalize_word(row.get("word_a", row.get("word", "")))
    second = normalize_word(row.get("word_b", row.get("antonym", "")))
    source = str(row.get("source") or "")
    url = str(row.get("source_url") or "")
    affix = str(row.get("affix") or "")
    pos = str(row.get("pos") or "")
    return "\x1f".join((relation, first, second, pos, source, url, affix))


def merge_rows(payload: dict[str, Any], relation: str, rows: Iterable[Mapping[str, Any]]) -> int:
    if relation not in RELATIONS:
        raise ValueError(f"unknown relation: {relation}")
    existing = payload["relations"].setdefault(relation, [])
    if not isinstance(existing, list):
        raise ValueError(f"artifact relation {relation} must be a list")
    known = {_row_key(row) for row in existing if isinstance(row, Mapping)}
    added = 0
    for raw in rows:
        row = dict(raw)
        row.setdefault("relation", relation[:-1] if relation.endswith("s") else relation)
        key = _row_key(row)
        if key in known:
            continue
        existing.append(row)
        known.add(key)
        added += 1
    existing.sort(key=lambda row: _row_key(row) if isinstance(row, Mapping) else "")
    return added


def write_artifact(payload: Mapping[str, Any], path: Path = DEFAULT_ARTIFACT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_rows(rows: list[Mapping[str, Any]], *, sample_seed: int, sample_size: int = 20) -> dict[str, Any]:
    import random

    rng = random.Random(sample_seed)
    sample = list(rows)
    rng.shuffle(sample)
    return {"count": len(rows), "samples": sample[:sample_size]}
