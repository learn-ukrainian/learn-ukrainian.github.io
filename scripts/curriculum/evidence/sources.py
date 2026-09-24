"""The word store's sole boundary to dictionaries and morphology tools.

Use one Sources instance per build (and close it). Results preserve source
bytes; normalization applies only to lookup inputs. Database wrappers share one
read-only connection that pins a single SQLite snapshot for the whole session
(a deferred read transaction; in WAL mode a concurrent writer keeps committing
and the session keeps seeing the rows it started with). The identity of a
sources.db read is the digest of the rows returned, never a digest of the file:
that is what an evidence lock cites and what verification recomputes (rows-v2).
VESUM is a static file and keeps its metadata/file identity.
"""

import hashlib
import json
import shutil
import sqlite3
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from contextlib import closing, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.rag.config import VESUM_DB_PATH
from scripts.verification import stress, vesum

from . import codes, config, tags

BATCH_SIZE = 500
SOURCES_DB_SCHEME = "rows-v2"
LEGACY_SOURCES_DB_SCHEME = "file-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "\u2018": "'"})
# Exact POS equivalences only, never text/translation matching.
GLOSS_POS = {
    "noun": ("noun",),
    "verb": ("verb",),
    "adj": ("adjective", "adj"),
    "adv": ("adverb",),
    "numr": ("numeral",),
    "part": ("particle",),
    "prep": ("preposition",),
    "conj": ("conjunction",),
    "intj": ("interjection",),
}


@dataclass(frozen=True)
class SourceResult[T]:
    raw: T
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParadigmResult(SourceResult[dict]):
    forms_by_entry: dict[int, list[dict]] = field(default_factory=dict)


def normalize_spelling(word: str) -> str:
    return word.translate(APOSTROPHES)


def _file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _signature(path: Path) -> tuple[int, int, int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _sources_path() -> Path:
    path = REPO_ROOT / "data/sources.db"
    if path.is_file():
        return path
    from scripts.guardrails.worktree_containment import resolve_main_root

    return resolve_main_root(REPO_ROOT) / "data/sources.db"


def _canonical(value: Any) -> bytes:
    # ensure_ascii=False keeps Ukrainian bytes readable; bytes values raise (no cited table has a BLOB).
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def row_digest(row: Mapping[str, Any]) -> str:
    """Identity of one source row exactly as the accessor returned it (no column excluded)."""
    if not isinstance(row, Mapping):
        raise TypeError(f"row_digest expects a row mapping, got {type(row).__name__}")
    return hashlib.sha256(_canonical(dict(row))).hexdigest()


def batch_digest(batch: Mapping[Any, Any]) -> str:
    """Identity of a keyed batch read: canonical sorted list of [key-as-list, value] pairs."""
    pairs = []
    for key, value in batch.items():
        key_list = [*key] if isinstance(key, tuple) else [key]
        pairs.append([key_list, value])
    pairs.sort(key=lambda pair: pair[0])
    return hashlib.sha256(_canonical(pairs)).hexdigest()


def aggregate_digest(cited: Iterable[tuple[str, str]]) -> str:
    """built_with.sources_db under rows-v2: sorted unique [locator, row_sha256] pairs; no rows → sha256("[]")."""
    pairs = sorted({(str(locator), str(digest)) for locator, digest in cited})
    return hashlib.sha256(_canonical([list(pair) for pair in pairs])).hexdigest()


def open_readonly(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def open_snapshot(path: Path) -> sqlite3.Connection:
    """Read-only connection pinned to one snapshot for its lifetime.

    isolation_level=None keeps Python's sqlite3 module from issuing its own
    BEGIN/COMMIT; the explicit deferred BEGIN plus the probe read is what fixes
    the read mark (a bare BEGIN pins nothing until the first read).
    """
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("BEGIN")
    conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
    return conn


def journal_mode_from_header(path: Path) -> str | None:
    """SQLite header bytes 18-19: 2,2 means WAL; 1,1 legacy (rollback) journal. None when unreadable."""
    try:
        with Path(path).open("rb") as stream:
            header = stream.read(20)
    except OSError:
        return None
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return None
    if header[18] == 2 and header[19] == 2:
        return "wal"
    if header[18] == 1 and header[19] == 1:
        return "delete"
    return "unknown"


class Sources:
    """Build-scoped source access. Caller owns batching progress and final reports."""

    def __init__(
        self,
        *,
        sources_db: Path | None = None,
        vesum_db: Path | None = None,
        standard_path: Path | None = None,
        report: Callable[[str], None] | None = None,
        wal_ceiling_bytes: int | None = None,
        free_disk_floor_bytes: int | None = None,
    ):
        self.sources_db = Path(sources_db) if sources_db is not None else _sources_path()
        self.vesum_db = Path(vesum_db) if vesum_db is not None else VESUM_DB_PATH
        self.standard_path = (
            Path(standard_path)
            if standard_path is not None
            else REPO_ROOT / "docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt"
        )
        self.mapper = tags.TagMapper(report=report)
        self.report = report
        self.wal_ceiling_bytes = int(wal_ceiling_bytes) if wal_ceiling_bytes is not None else config.wal_ceiling_bytes()
        self.free_disk_floor_bytes = (
            int(free_disk_floor_bytes) if free_disk_floor_bytes is not None else config.free_disk_floor_bytes()
        )
        self._conn: sqlite3.Connection | None = None
        self._fingerprints: dict[Path, tuple[tuple, str, dict]] = {}
        self._vesum_snapshot: tuple[tuple, str, dict] | None = None
        self.journal_mode: str | None = None
        self._snapshot_started: float | None = None
        self._wal_bytes_start: int | None = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self) -> None:
        """Release the pinned snapshot (rollback, never commit) and report its lifetime."""
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        try:
            with closing(conn), suppress(sqlite3.Error):
                conn.execute("ROLLBACK")
        finally:
            age = self.snapshot_age()
            self._progress_line(
                f"snapshot: released after {age:.1f}s; journal_mode: {self.journal_mode}; "
                f"wal_bytes: {self._wal_bytes_start} -> {self.wal_bytes()}"
            )
            self._snapshot_started = None

    # -- snapshot observability -------------------------------------------------

    def snapshot_age(self) -> float:
        """Seconds since the sources.db snapshot was pinned; 0.0 when none is open."""
        if self._snapshot_started is None:
            return 0.0
        return time.monotonic() - self._snapshot_started

    def wal_bytes(self) -> int:
        """Current size of the sources.db WAL sidecar (0 when absent)."""
        wal = Path(f"{self.sources_db}-wal")
        try:
            return wal.stat().st_size
        except OSError:
            return 0

    def free_disk_bytes(self) -> int:
        """Free bytes on the volume holding sources.db."""
        return shutil.disk_usage(self.sources_db.parent if self.sources_db.parent.exists() else Path.cwd()).free

    def snapshot_report(self) -> dict[str, Any]:
        return {
            "journal_mode": self.journal_mode,
            "wal_bytes": self.wal_bytes(),
            "wal_bytes_start": self._wal_bytes_start,
            "snapshot_seconds": round(self.snapshot_age(), 3),
            "free_disk_bytes": self.free_disk_bytes(),
        }

    def _guard(self) -> None:
        """Stop before the next read when the pinned snapshot exceeds its WAL or free-disk budget."""
        wal = self.wal_bytes()
        free = self.free_disk_bytes()
        reason = None
        if wal > self.wal_ceiling_bytes:
            reason = f"WAL {wal} bytes exceeds ceiling {self.wal_ceiling_bytes} bytes"
        elif free < self.free_disk_floor_bytes:
            reason = f"free disk {free} bytes below floor {self.free_disk_floor_bytes} bytes"
        if reason is None:
            return
        age = self.snapshot_age()
        self.close()
        raise RuntimeError(f"{codes.SNAPSHOT_LIMIT}: {reason}; snapshot released after {age:.1f}s")

    def _file_fingerprint(self, path: Path) -> tuple[str, dict]:
        wal = Path(f"{path}-wal")
        signature = (_signature(path), _signature(wal))
        if signature[0] is None:
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(path)!r}")
        if path in self._fingerprints:
            before, digest, metadata = self._fingerprints[path]
            if before != signature:
                raise ValueError(f"{codes.SOURCE_CHANGED}: {str(path)!r} during source session")
            return digest, metadata
        db_digest = _file_hash(path)
        metadata = {"db_sha256": db_digest}
        digest = db_digest
        if signature[1] is not None and signature[1][1]:
            metadata["wal_sha256"] = _file_hash(wal)
            digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if signature != (_signature(path), _signature(wal)):
            raise ValueError(f"{codes.SOURCE_CHANGED}: {str(path)!r} while hashing")
        self._fingerprints[path] = (signature, digest, metadata)
        return digest, metadata

    def _db(self) -> sqlite3.Connection:
        if self._conn is None:
            if not self.sources_db.is_file():
                raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(self.sources_db)!r}")
            self._conn = open_snapshot(self.sources_db)
            self._snapshot_started = time.monotonic()
            self.journal_mode = str(self._conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            self._wal_bytes_start = self.wal_bytes()
            self._progress_line(
                f"snapshot: pinned; journal_mode: {self.journal_mode}; wal_bytes: {self._wal_bytes_start}; "
                f"free_disk_bytes: {self.free_disk_bytes()}"
            )
        self._guard()
        return self._conn

    def _db_result[T](self, raw: T) -> SourceResult[T]:
        """rows-v2: the identity of a DB read is the digest of the rows it returned."""
        return SourceResult(raw, batch_digest(raw), {"scheme": SOURCES_DB_SCHEME})

    def _vesum_identity(self) -> tuple[str, dict]:
        # Metadata is the canonical content identity, not an incidental DB file hash.
        signature = (_signature(self.vesum_db), _signature(Path(f"{self.vesum_db}-wal")))
        if self._vesum_snapshot is not None:
            before, digest, metadata = self._vesum_snapshot
            if signature != before:
                raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM during source session")
            return digest, dict(metadata)
        with closing(open_readonly(self.vesum_db)) as conn:
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='vesum_build_metadata'").fetchone()
            metadata = dict(conn.execute("SELECT key, value FROM vesum_build_metadata")) if exists else {}
        digest = metadata.get("canonical_jsonl_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            digest, file_metadata = self._file_fingerprint(self.vesum_db)
            metadata.update(file_metadata)
        if signature != (_signature(self.vesum_db), _signature(Path(f"{self.vesum_db}-wal"))):
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM while reading metadata")
        self._vesum_snapshot = (signature, digest, dict(metadata))
        return digest, metadata

    def inspect_lemma_forms(self, lemma: str, pos: str) -> ParadigmResult:
        digest, metadata = self._vesum_identity()
        raw = vesum.inspect_lemma(normalize_spelling(lemma), db_path=self.vesum_db).as_dict()
        if raw["status"] == "unavailable":
            raise ValueError(f"{codes.SOURCE_UNAVAILABLE}: VESUM inspection for {lemma!r}")
        grouped: dict[int, list[dict]] = {}
        for form in raw["forms"]:
            if form["pos"] == pos:
                grouped.setdefault(form["entry_id"], []).append(form)
        if self._vesum_identity()[0] != digest:
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM for {lemma!r}")
        return ParadigmResult(raw, digest, metadata, grouped)

    def inspect_many(self, requests: Iterable[tuple[str, str]]) -> dict[tuple[str, str], ParadigmResult]:
        unique = list(dict.fromkeys((normalize_spelling(lemma), pos) for lemma, pos in requests))
        results = {}
        for start in range(0, len(unique), BATCH_SIZE):
            for lemma, pos in unique[start : start + BATCH_SIZE]:
                results[lemma, pos] = self.inspect_lemma_forms(lemma, pos)
            self._progress("paradigms", min(start + BATCH_SIZE, len(unique)), len(unique))
        return results

    def verify_words(self, words: Iterable[str], pos: str | None = None) -> SourceResult[dict]:
        requested = list(dict.fromkeys(map(normalize_spelling, words)))
        digest, metadata = self._vesum_identity()
        raw = {}
        for start in range(0, len(requested), BATCH_SIZE):
            raw.update(vesum.verify_words(requested[start : start + BATCH_SIZE], pos_filter=pos, db_path=self.vesum_db))
            self._progress("words", min(start + BATCH_SIZE, len(requested)), len(requested))
        if self._vesum_identity()[0] != digest:
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM batch")
        return SourceResult(raw, digest, metadata)

    def stress_for_form(self, form: str, vesum_tags: str) -> SourceResult[dict]:
        """Return the oracle envelope unchanged. Builder handles monosyllables first."""
        raw = stress.verify_stress(normalize_spelling(form), tags=self.mapper(vesum_tags))
        # The trie alone does not identify exact-form override changes.
        override_digest = _file_hash(stress.STRESS_OVERRIDES_PATH) if stress.STRESS_OVERRIDES_PATH.exists() else None
        return SourceResult(raw, raw["source"]["digest"], {"overrides_sha256": override_digest})

    def stress_many(self, requests: Iterable[tuple[str, str]]) -> dict[tuple[str, str], SourceResult[dict]]:
        requested = list(dict.fromkeys((normalize_spelling(form), tag) for form, tag in requests))
        result = {}
        for start in range(0, len(requested), BATCH_SIZE):
            for form, tag in requested[start : start + BATCH_SIZE]:
                result[form, tag] = self.stress_for_form(form, tag)
            self._progress("stress", min(start + BATCH_SIZE, len(requested)), len(requested))
        return result

    def ulif_entries(self, lemmas: Iterable[str]) -> SourceResult[dict[str, list[dict]]]:
        """Raw entry rows + ordered raw sections. No unchecked group can be eligible."""
        conn = self._db()
        requested = list(dict.fromkeys(map(normalize_spelling, lemmas)))
        result: dict[str, list[dict]] = {lemma: [] for lemma in requested}
        for start in range(0, len(requested), BATCH_SIZE):
            batch = requested[start : start + BATCH_SIZE]
            slots = ",".join("?" for _ in batch)
            rows = conn.execute(
                f"SELECT * FROM ulif_dictua_entries WHERE normalized_query IN ({slots}) ORDER BY normalized_query, homonym_index, id",
                batch,
            ).fetchall()
            entries = {row["id"]: dict(row) for row in rows}
            for row in entries.values():
                row["sections"] = []
                result[row["normalized_query"]].append(row)
            if entries:
                # Join on requested spellings to stay within SQLite's variable cap.
                sections = conn.execute(
                    f"SELECT s.* FROM ulif_dictua_sections s JOIN ulif_dictua_entries e ON e.id=s.entry_id WHERE e.normalized_query IN ({slots}) ORDER BY s.entry_id, s.kind, s.source_order, s.id",
                    batch,
                )
                for section in sections:
                    entries[section["entry_id"]]["sections"].append(dict(section))
            self._progress("ulif", min(start + BATCH_SIZE, len(requested)), len(requested))
        return self._db_result(result)

    @staticmethod
    def ulif_group_checked(entries: list[dict]) -> bool:
        return bool(entries) and all(row.get("homonym_checked") == 1 and row.get("status") == "ok" for row in entries)

    def gloss_rows(self, requests: Iterable[tuple[str, str]]) -> SourceResult[dict[tuple[str, str], list[dict]]]:
        """Exact lemma + explicit POS equivalents, ordered by stable row id.

        No accent stripping or prefix/fuzzy fallback: a stressed-only headword
        that differs from the requested spelling is absent under brief rule 6.
        """
        conn = self._db()
        requested = list(dict.fromkeys((normalize_spelling(lemma), pos) for lemma, pos in requests))
        result = {key: [] for key in requested}
        for start in range(0, len(requested), BATCH_SIZE):
            batch = requested[start : start + BATCH_SIZE]
            words = list(dict.fromkeys(lemma for lemma, _ in batch))
            slots = ",".join("?" for _ in words)
            rows = conn.execute(f"SELECT * FROM dmklinger_uk_en WHERE word IN ({slots}) ORDER BY id", words).fetchall()
            for key in batch:
                result[key] = [
                    dict(row)
                    for row in rows
                    if row["word"] == key[0] and row["pos"] in GLOSS_POS.get(key[1], (key[1],))
                ]
            self._progress("glosses", min(start + BATCH_SIZE, len(requested)), len(requested))
        return self._db_result(result)

    def cefr_levels(self, lemmas: Iterable[str]) -> SourceResult[dict]:
        """Raw PULS hits; consumers must reject the upstream helper's prefix fallback."""
        from scripts.wiki import sources_db

        with sources_db.using_connection(self._db()):
            raw = sources_db.query_cefr_levels(list(dict.fromkeys(map(normalize_spelling, lemmas))))
        return self._db_result(raw)

    def heritage(self, words: Iterable[str]) -> SourceResult[dict]:
        from scripts.wiki import sources_db

        with sources_db.using_connection(self._db()):
            raw = {}
            requested = list(dict.fromkeys(map(normalize_spelling, words)))
            for index, word in enumerate(requested, 1):
                hits = sources_db.search_heritage(word, include_live_slovnyk=False)
                # Each hit is a deterministic projection of the dictionary rows it was
                # read from on this snapshot; its digest is the identity the word record cites.
                for hit in hits:
                    hit["row_sha256"] = heritage_hit_digest(hit)
                raw[word] = hits
                if index % BATCH_SIZE == 0 or index == len(requested):
                    self._progress("heritage", index, len(requested))
        return self._db_result(raw)

    def russian_patterns(self, words: Iterable[str]) -> SourceResult[dict]:
        from scripts.lexicon import calque_corrections
        from scripts.verification import check_ru_morph

        requested = list(dict.fromkeys(map(normalize_spelling, words)))
        verified = self.verify_words(requested)
        raw = check_ru_morph.check_russian_patterns_batch(
            requested, verified_words={word for word, hits in verified.raw.items() if hits}
        )
        # Hash the actual morphology dictionaries and implementation inputs.
        files = [Path(check_ru_morph.__file__), Path(calque_corrections.__file__)]
        for analyzer in (check_ru_morph._morph_ru, check_ru_morph._morph_uk):
            files.extend(sorted(Path(analyzer.dictionary.path).rglob("*")))
        hashes = [_file_hash(path) for path in files if path.is_file()]
        hashes.append(verified.content_hash)
        digest = hashlib.sha256("\n".join(hashes).encode()).hexdigest()
        return SourceResult(raw, digest, {"vesum": verified.content_hash})

    def tag_inventory(self) -> SourceResult[dict]:
        digest, metadata = self._vesum_identity()
        with closing(open_readonly(self.vesum_db)) as conn:
            atoms = sorted(
                {atom for row in conn.execute("SELECT DISTINCT tags FROM forms_all") for atom in row[0].split(":")}
            )
            markers = [row[0] for row in conn.execute("SELECT DISTINCT marker FROM form_markers ORDER BY marker")]
        return SourceResult({"atoms": atoms, "markers": markers}, digest, metadata)

    def get_textbook_chunk(self, chunk_id: str | int) -> dict | None:
        conn = self._db()
        sql = """
            SELECT t.*, s.page_start AS page
            FROM textbooks t
            LEFT JOIN textbook_sections s ON t.parent_section_id = s.section_id
            WHERE t.chunk_id = ?
        """
        row = conn.execute(sql, (str(chunk_id),)).fetchone()
        if row is None:
            return None
        res = dict(row)
        if res.get("page") is not None:
            res["page"] = int(res["page"])
        return res

    def get_textbook_file_chunks(self, source_file: str) -> list[dict]:
        conn = self._db()
        sql = """
            SELECT t.*, s.page_start AS page, s.section_number
            FROM textbooks t
            LEFT JOIN textbook_sections s ON t.parent_section_id = s.section_id
            WHERE t.source_file = ?
            ORDER BY s.section_number, t.parent_section_id, t.id
        """
        rows = conn.execute(sql, (source_file,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("page") is not None:
                d["page"] = int(d["page"])
            result.append(d)
        return result

    def get_literary_chunk(self, chunk_id: str | int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM literary_texts WHERE chunk_id = ?", (str(chunk_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_literary_file_chunks(self, source_file: str) -> list[dict]:
        conn = self._db()
        rows = conn.execute("SELECT * FROM literary_texts WHERE source_file = ? ORDER BY id", (source_file,)).fetchall()
        return [dict(r) for r in rows]

    def find_ua_gec_error(self, error: str, correct: str) -> list[dict]:
        conn = self._db()
        rows = conn.execute(
            "SELECT id, error, correct, error_type, doc_id, annotator_id, partition, is_native, source_lang FROM ua_gec_errors WHERE error = ? AND correct = ? ORDER BY id",
            (error, correct),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_ua_gec_error_by_id(self, error_id: int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM ua_gec_errors WHERE id = ?", (int(error_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_style_guide_entry(self, entry_id: int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM style_guide WHERE id = ?", (int(entry_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_standard_file_hash(self) -> str:
        if not self.standard_path.is_file():
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: Standard file not found at {self.standard_path}")
        return _file_hash(self.standard_path)

    def get_standard_lines(self, start_line: int, end_line: int) -> tuple[str, str]:
        if not self.standard_path.is_file():
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: Standard file not found at {self.standard_path}")
        file_hash = _file_hash(self.standard_path)
        content = self.standard_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        total_lines = len(lines)
        if start_line < 1 or end_line < start_line or end_line > total_lines:
            raise ValueError(
                f"{codes.INVALID_REQUEST}: line range {start_line}-{end_line} out of bounds (1..{total_lines})"
            )
        selected_lines = lines[start_line - 1 : end_line]
        text = "\n".join(selected_lines)
        return text, file_hash

    def check_url(self, url: str, timeout: float = 10.0) -> dict[str, Any]:
        return check_url(url, timeout=timeout)

    def _progress(self, kind: str, count: int, total: int) -> None:
        self._progress_line(f"{kind}: {count}/{total}")

    def _progress_line(self, line: str) -> None:
        if self.report:
            self.report(line)


def heritage_hit_digest(hit: Mapping[str, Any]) -> str:
    """Identity of one heritage hit as copied into a word record (its own row_sha256 excluded)."""
    return row_digest({key: value for key, value in hit.items() if key != "row_sha256"})


def check_url(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Check a video URL with a hard timeout and one retry; follows redirects."""
    if timeout is None or timeout <= 0:
        raise ValueError("check_url requires a positive timeout")
    headers = {"User-Agent": "learn-ukrainian-evidence-pack/1.0"}
    req = urllib.request.Request(url, headers=headers)
    last_exc = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                date_str = datetime.now(UTC).strftime("%Y-%m-%d")
                return {
                    "http_status": resp.status,
                    "final_url": resp.geturl(),
                    "content_type": resp.headers.get_content_type() if resp.headers else None,
                    "date": date_str,
                }
        except urllib.error.HTTPError as exc:
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")
            return {
                "http_status": exc.code,
                "final_url": exc.geturl(),
                "content_type": exc.headers.get_content_type() if exc.headers else None,
                "date": date_str,
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(0.5)
    raise ConnectionError(f"Failed to check URL {url} after retry: {last_exc}")


@lru_cache(maxsize=1)
def _default() -> Sources:
    return Sources()


def inspect_lemma_forms(lemma: str, pos: str) -> ParadigmResult:
    return _default().inspect_lemma_forms(lemma, pos)


def stress_for_form(form: str, vesum_tags: str) -> SourceResult[dict]:
    return _default().stress_for_form(form, vesum_tags)
