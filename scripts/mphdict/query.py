"""Fast, read-only queries over the local mphdict SQLite exports.

The source databases encode stress with a double quote placed after the
stressed vowel (for example ``га"рний``).  They are treated as immutable.
This module creates a separate sidecar lookup index keyed by normalized lemma,
which keeps ordinary queries indexed without adding expression indexes to the
ODbL source databases.
"""

from __future__ import annotations

import html
import os
import re
import sqlite3
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SYNSETS_DB_NAME = "synsets_ua.db"
ETYM_DB_NAME = "etym.db"
HEADWORD_DB_NAME = "mph_ua.db"
SIDECAR_NAME = ".mphdict-lookup.sqlite3"
SIDECAR_SCHEMA_VERSION = 1

_COMBINING_STRESS = frozenset({"\u0300", "\u0301"})
_MARKUP_RE = re.compile(r"\[(?P<tag>[A-Za-z]+)\](?P<text>.*?)\[/\1\]", re.DOTALL)
_HTML_TAG_RE = re.compile(r"</?(?:b|br|em|i|strong|u)\b[^>]*>", re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class _IndexSpec:
    """One normalized-word lookup table in an immutable mphdict database."""

    database: str
    table: str
    id_column: str
    word_column: str


_SYNSET_INDEX = _IndexSpec(SYNSETS_DB_NAME, "wlist", "id", "word")
_ETYM_INDEX = _IndexSpec(ETYM_DB_NAME, "etymons", "id", "word")
_HEADWORD_INDEX = _IndexSpec(HEADWORD_DB_NAME, "nom", "nom_old", "reestr")


def _main_checkout_root(root: Path) -> Path | None:
    """Return the shared checkout root when called from a dispatch worktree."""
    parts = root.parts
    try:
        worktrees_index = parts.index(".worktrees")
    except ValueError:
        return None
    return Path(*parts[:worktrees_index])


def _default_db_dir() -> Path:
    override = os.environ.get("MPHDICT_DATA_DIR")
    if override:
        return Path(override).expanduser()

    local = ROOT / "data" / "mphdict"
    if local.exists():
        return local

    main_root = _main_checkout_root(ROOT)
    if main_root:
        shared = main_root / "data" / "mphdict"
        if shared.exists():
            return shared
    return local


def _database_path(spec: _IndexSpec, db_dir: Path | str | None) -> Path:
    return Path(db_dir).expanduser() / spec.database if db_dir else _default_db_dir() / spec.database


def _sidecar_path(db_dir: Path | str | None, index_path: Path | str | None) -> Path:
    if index_path is not None:
        return Path(index_path).expanduser()
    override = os.environ.get("MPHDICT_INDEX_PATH")
    if override:
        return Path(override).expanduser()
    return (Path(db_dir).expanduser() if db_dir else _default_db_dir()) / SIDECAR_NAME


def normalize_lookup(value: object) -> str:
    """Normalize a source or user word to the stress-free lookup key.

    ЕСУМ uses combining acute stress while the synonym and orthography exports
    use the embedded double quote convention.  Removing both supports a plain
    user lemma in every source without changing the stored display form.
    """
    decomposed = unicodedata.normalize("NFD", str(value or ""))
    without_stress = "".join(
        character
        for character in decomposed
        if character != '"' and character not in _COMBINING_STRESS
    )
    normalized = unicodedata.normalize("NFC", without_stress)
    normalized = normalized.replace("`", "'").replace("’", "'").replace("ʼ", "'")
    return _SPACE_RE.sub(" ", normalized).strip().casefold()


def decode_stress(value: object) -> str:
    """Turn mphdict's embedded quote stress marker into displayable acute stress."""
    source = str(value or "")
    out: list[str] = []
    for character in source:
        if character == '"' and out:
            out.append("\u0301")
        else:
            out.append(character)
    return unicodedata.normalize("NFC", "".join(out))


def normalize_gloss(value: object) -> dict[str, Any]:
    """Make mphdict gloss markup learner-readable while retaining tagged detail."""
    raw = html.unescape(str(value or "")).strip()
    markup: list[dict[str, str]] = []

    def replace_markup(match: re.Match[str]) -> str:
        text = _HTML_TAG_RE.sub("", html.unescape(match.group("text")))
        text = _SPACE_RE.sub(" ", text).strip()
        if text:
            markup.append({"tag": match.group("tag").upper(), "text": text})
        return text

    text = _MARKUP_RE.sub(replace_markup, raw)
    text = _HTML_TAG_RE.sub("", text)
    # Angle-bracketed source labels (for example <рідко.>) are meaningful
    # learner information, not HTML; retain their text but remove the wrappers.
    text = re.sub(r"<([^<>]+)>", r"\1", text)
    text = re.sub(r"(?<=[.!?])(?=[А-ЯІЇЄҐ])", " ", text)
    text = re.sub(r"\s*;\s*;\s*", "; ", text)
    text = _SPACE_RE.sub(" ", text).strip(" ;")
    result: dict[str, Any] = {"text": text}
    if markup:
        result["markup"] = markup
    return result


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _sidecar_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = WAL;
        CREATE TABLE IF NOT EXISTS metadata (
            source_key TEXT PRIMARY KEY,
            source_size INTEGER NOT NULL,
            source_mtime_ns INTEGER NOT NULL,
            schema_version INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS normalized_words (
            source_key TEXT NOT NULL,
            lookup_key TEXT NOT NULL,
            row_id INTEGER NOT NULL,
            PRIMARY KEY (source_key, row_id)
        );
        CREATE INDEX IF NOT EXISTS normalized_words_lookup
            ON normalized_words (source_key, lookup_key);
        """
    )


def _source_key(path: Path, spec: _IndexSpec) -> str:
    return f"{path.resolve()}::{spec.table}::{spec.id_column}::{spec.word_column}"


def _batched(rows: Iterable[tuple[int, object]], size: int = 2_000) -> Iterator[list[tuple[int, object]]]:
    batch: list[tuple[int, object]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _ensure_index(path: Path, spec: _IndexSpec, sidecar: Path) -> str:
    """Build or refresh a sidecar index without writing to ``path``."""
    stat = path.stat()
    source_key = _source_key(path, spec)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(sidecar) as index_connection:
        _sidecar_schema(index_connection)
        row = index_connection.execute(
            "SELECT source_size, source_mtime_ns, schema_version FROM metadata WHERE source_key = ?",
            (source_key,),
        ).fetchone()
        unchanged = row == (stat.st_size, stat.st_mtime_ns, SIDECAR_SCHEMA_VERSION)
        if unchanged:
            return source_key

        index_connection.execute("DELETE FROM normalized_words WHERE source_key = ?", (source_key,))
        with _connect_read_only(path) as source_connection:
            source_rows = source_connection.execute(
                f"SELECT {spec.id_column}, {spec.word_column} FROM {spec.table}"
            )
            for batch in _batched(source_rows):
                index_connection.executemany(
                    "INSERT INTO normalized_words (source_key, lookup_key, row_id) VALUES (?, ?, ?)",
                    [
                        (source_key, normalize_lookup(source_word), int(row_id))
                        for row_id, source_word in batch
                        if normalize_lookup(source_word)
                    ],
                )
        index_connection.execute(
            """
            INSERT INTO metadata (source_key, source_size, source_mtime_ns, schema_version)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(source_key) DO UPDATE SET
                source_size = excluded.source_size,
                source_mtime_ns = excluded.source_mtime_ns,
                schema_version = excluded.schema_version
            """,
            (source_key, stat.st_size, stat.st_mtime_ns, SIDECAR_SCHEMA_VERSION),
        )
    return source_key


def _indexed_row_ids(
    path: Path,
    spec: _IndexSpec,
    lookup_key: str,
    sidecar: Path,
) -> list[int]:
    source_key = _ensure_index(path, spec, sidecar)
    with sqlite3.connect(sidecar) as index_connection:
        rows = index_connection.execute(
            """
            SELECT row_id FROM normalized_words
            WHERE source_key = ? AND lookup_key = ?
            ORDER BY row_id
            """,
            (source_key, lookup_key),
        ).fetchall()
    return [int(row[0]) for row in rows]


def _chunks(values: list[int], size: int = 900) -> Iterator[list[int]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _optional_int(value: object) -> int | None:
    return int(value) if value not in (None, "") else None


def mphdict_synonyms_available(*, db_dir: Path | str | None = None) -> bool:
    """Whether the primary local synonym database is present for enrichment."""
    return _database_path(_SYNSET_INDEX, db_dir).is_file()


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _source_form(word: object) -> dict[str, str]:
    source_word = str(word or "")
    return {
        "lemma": normalize_lookup(source_word),
        "stressed": decode_stress(source_word),
        "encoded_stressed": source_word,
    }


def mphdict_synonyms(
    word: str,
    *,
    db_dir: Path | str | None = None,
    index_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Return distinct mphdict synonym groups for a plain or stressed lemma.

    ``wlist.id_set`` is deliberately retained as a boundary: a word may occur
    in several senses, and flattening those groups would recreate the
    cross-sense synonym errors this source replaces.
    """
    lookup_key = normalize_lookup(word)
    if not lookup_key:
        return None
    path = _database_path(_SYNSET_INDEX, db_dir)
    if not path.is_file():
        return None
    sidecar = _sidecar_path(db_dir, index_path)
    matching_ids = _indexed_row_ids(path, _SYNSET_INDEX, lookup_key, sidecar)
    if not matching_ids:
        return {"lemma": lookup_key, "synsets": []}

    with _connect_read_only(path) as connection:
        set_ids: set[int] = set()
        for chunk in _chunks(matching_ids):
            placeholders = ", ".join("?" for _ in chunk)
            set_ids.update(
                int(row[0])
                for row in connection.execute(
                    f"SELECT DISTINCT id_set FROM wlist WHERE id IN ({placeholders})", chunk
                )
            )

        groups: list[dict[str, Any]] = []
        for chunk in _chunks(sorted(set_ids)):
            placeholders = ", ".join("?" for _ in chunk)
            rows = connection.execute(
                f"""
                SELECT w.id_set, w.id_syn, w.id, w.word, w.interpretation,
                       w.sign, w.hyperonym, w.homonym,
                       s.interpretation AS synset_interpretation, p.name AS pos
                FROM wlist AS w
                LEFT JOIN synsets AS s ON s.id = w.id_set
                LEFT JOIN pofs AS p ON p.id = s.pofs
                WHERE w.id_set IN ({placeholders})
                ORDER BY w.id_set, w.id
                """,
                chunk,
            ).fetchall()
            by_set: dict[int, list[sqlite3.Row]] = {}
            for row in rows:
                by_set.setdefault(int(row["id_set"]), []).append(row)
            for set_id in sorted(by_set):
                members: list[dict[str, Any]] = []
                first = by_set[set_id][0]
                for row in by_set[set_id]:
                    member = {
                        "id": int(row["id"]),
                        "sense_id": int(row["id_syn"]),
                        **_source_form(row["word"]),
                    }
                    gloss = normalize_gloss(row["interpretation"])
                    if gloss["text"]:
                        member["gloss"] = gloss
                    if _optional_int(row["sign"]) is not None:
                        member["sign"] = _optional_int(row["sign"])
                    hyperonym = _optional_text(row["hyperonym"])
                    if hyperonym:
                        member["hyperonym"] = _source_form(hyperonym)
                    homonym = _optional_int(row["homonym"])
                    if homonym:
                        member["homonym"] = homonym
                    members.append(member)
                group: dict[str, Any] = {
                    "id": set_id,
                    "pos": _optional_text(first["pos"]),
                    "members": members,
                }
                group_gloss = normalize_gloss(first["synset_interpretation"])
                if group_gloss["text"]:
                    group["gloss"] = group_gloss
                groups.append(group)
    return {"lemma": lookup_key, "synsets": groups}


def _citation(root: sqlite3.Row) -> dict[str, Any]:
    volume = _optional_int(root["volume_num"])
    first_page = _optional_int(root["page_initial"])
    last_page = _optional_int(root["page_last"])
    display_parts: list[str] = []
    if volume is not None:
        display_parts.append(f"т. {volume}")
    if first_page is not None:
        page = f"с. {first_page}"
        if last_page is not None and last_page != first_page:
            page += f"–{last_page}"
        display_parts.append(page)
    return {
        "volume": volume,
        "page_initial": first_page,
        "page_last": last_page,
        "display": ", ".join(display_parts),
    }


def _etymon_from_row(row: sqlite3.Row) -> dict[str, Any]:
    etymon: dict[str, Any] = {
        "id": int(row["id"]),
        "word_num": int(row["word_num"]),
        "is_head": bool(row["ishead"]),
        **_source_form(row["word"]),
        "language_marker": _optional_text(row["lang_marker"]),
        "language": _optional_text(row["lang_name"]),
    }
    for field in ("homonym", "dialect", "antroponym"):
        value = _optional_int(row[field])
        if value:
            etymon[field] = bool(value) if field != "homonym" else value
    for field in ("lang_note", "note", "sense", "bibliography"):
        value = _optional_text(row[field])
        if value:
            etymon[field] = value
    class_text = _optional_text(row["subclass_text"])
    etymon["class"] = {
        "type": int(row["class_type"]),
        "number": int(row["class_num"]),
        "subclass_number": int(row["subclass_num"]),
        "is_formal": bool(row["formal_type"]),
        "text": class_text,
    }
    return etymon


def mphdict_etymology(
    word: str,
    *,
    db_dir: Path | str | None = None,
    index_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Return every ЕСУМ root containing ``word``, with etymons and citations."""
    lookup_key = normalize_lookup(word)
    if not lookup_key:
        return None
    path = _database_path(_ETYM_INDEX, db_dir)
    if not path.is_file():
        return None
    sidecar = _sidecar_path(db_dir, index_path)
    matching_ids = _indexed_row_ids(path, _ETYM_INDEX, lookup_key, sidecar)
    if not matching_ids:
        return {"lemma": lookup_key, "roots": []}

    with _connect_read_only(path) as connection:
        root_ranks: dict[int, int] = {}
        for chunk in _chunks(matching_ids):
            placeholders = ", ".join("?" for _ in chunk)
            for row in connection.execute(
                f"""
                SELECT ec.id_root, MAX(e.ishead) AS matching_head
                FROM etymons AS e
                JOIN e_classes AS ec ON ec.id = e.id_e_classes
                WHERE e.id IN ({placeholders})
                GROUP BY ec.id_root
                """,
                chunk,
            ):
                root_ranks[int(row["id_root"])] = int(row["matching_head"] or 0)

        # A direct article headword is authoritative.  A plain form can also
        # occur as an embedded comparison under unrelated derived-word roots;
        # use those only when ЕСУМ has no matching article headword at all.
        has_direct_headword = any(root_ranks.values())
        candidate_root_ids = [
            root_id for root_id, rank in root_ranks.items() if rank or not has_direct_headword
        ]
        roots: list[dict[str, Any]] = []
        ordered_root_ids = sorted(candidate_root_ids, key=lambda root_id: (-root_ranks[root_id], root_id))
        for chunk in _chunks(ordered_root_ids):
            placeholders = ", ".join("?" for _ in chunk)
            root_rows = connection.execute(
                f"""
                SELECT id, volume_num, page_initial, page_last
                FROM root WHERE id IN ({placeholders})
                """,
                chunk,
            ).fetchall()
            roots_by_id = {int(row["id"]): row for row in root_rows}
            for root_id in chunk:
                root = roots_by_id[root_id]
                etymon_rows = connection.execute(
                    """
                    SELECT e.id, e.word_num, e.ishead, e.word, e.homonym, e.dialect,
                           e.antroponym, e.lang_marker, e.lang_note, e.note, e.sense,
                           e.bibliography, la.lang_name, ec.class_type, ec.class_num,
                           ec.subclass_num, ec.formal_type, ec.subclass_text
                    FROM e_classes AS ec
                    JOIN etymons AS e ON e.id_e_classes = ec.id
                    LEFT JOIN lang_all AS la ON la.lang_code = e.lang_code
                    WHERE ec.id_root = ?
                    ORDER BY ec.class_num, ec.subclass_num, e.word_num, e.id
                    """,
                    (root_id,),
                ).fetchall()
                bibliography = [
                    {
                        "number": int(row["biblio_num"]),
                        "text": str(row["biblio_text"] or "").strip(),
                    }
                    for row in connection.execute(
                        "SELECT biblio_num, biblio_text FROM bibl WHERE id_root = ? ORDER BY biblio_num, id",
                        (root_id,),
                    )
                    if str(row["biblio_text"] or "").strip()
                ]
                links = [
                    {
                        "type": int(row["link_type"]),
                        "number": int(row["link_num"]),
                        "word": _optional_text(row["word"]),
                        "homonym": _optional_int(row["homonym"]),
                    }
                    for row in connection.execute(
                        "SELECT link_type, link_num, word, homonym FROM links WHERE id_root = ? ORDER BY link_type, link_num, id",
                        (root_id,),
                    )
                ]
                roots.append(
                    {
                        "id": root_id,
                        "match": {
                            "is_direct_headword": bool(root_ranks[root_id]),
                            "kind": "headword" if root_ranks[root_id] else "embedded_comparison",
                        },
                        "citation": _citation(root),
                        "etymons": [_etymon_from_row(row) for row in etymon_rows],
                        "bibliography": bibliography,
                        "links": links,
                    }
                )
    return {"lemma": lookup_key, "roots": roots}


def mphdict_headword(
    word: str,
    *,
    db_dir: Path | str | None = None,
    index_path: Path | str | None = None,
) -> dict[str, Any] | None:
    """Return mphdict's preferred stressed orthographic registry headword and POS.

    Full paradigm generation remains intentionally out of scope: VESUM is the
    Atlas form source.  mphdict's ``nom`` registry is used here only for its
    official written headword and part-of-speech record.
    """
    lookup_key = normalize_lookup(word)
    if not lookup_key:
        return None
    path = _database_path(_HEADWORD_INDEX, db_dir)
    if not path.is_file():
        return None
    sidecar = _sidecar_path(db_dir, index_path)
    matching_ids = _indexed_row_ids(path, _HEADWORD_INDEX, lookup_key, sidecar)
    if not matching_ids:
        return None

    with _connect_read_only(path) as connection:
        rows: list[sqlite3.Row] = []
        for chunk in _chunks(matching_ids):
            placeholders = ", ".join("?" for _ in chunk)
            rows.extend(
                connection.execute(
                    f"""
                    SELECT n.nom_old, n.reestr, n.part, n.type, n.isdel, n.isproblem,
                           p.part AS pos_code, p.com AS pos
                    FROM nom AS n
                    LEFT JOIN parts AS p ON p.id = n.part
                    WHERE n.nom_old IN ({placeholders}) AND COALESCE(n.isdel, 0) = 0
                    """,
                    chunk,
                ).fetchall()
            )
    if not rows:
        return None
    row = min(
        rows,
        key=lambda item: (
            int(item["isdel"] or 0),
            int(item["isproblem"] or 0),
            int(item["nom_old"]),
        ),
    )
    return {
        "registry_id": int(row["nom_old"]),
        **_source_form(row["reestr"]),
        "pos": _optional_text(row["pos"]),
        "pos_code": _optional_text(row["pos_code"]),
        "part_id": int(row["part"]),
        "flexion_type": int(row["type"]),
    }
