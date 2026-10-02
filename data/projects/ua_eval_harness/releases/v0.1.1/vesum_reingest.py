"""Reproducibly build a marker-preserving VESUM shadow database.

The locked ``dict_corp_vis.txt.bz2`` release asset is a sequence of paradigm
blocks: every unindented analysis opens a block and its indented analyses are
forms of that lemma.  Inline comments on the block header apply to that
paradigm.  This module deliberately keeps the source block identity instead of
joining analyses by lemma, which would transfer markers between homographs.
"""

from __future__ import annotations

import bz2
import hashlib
import json
import os
import sqlite3
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK_PATH = PROJECT_ROOT / "scripts" / "config" / "vesum_source.lock.json"
PRODUCTION_DB_PATH = PROJECT_ROOT / "data" / "vesum.db"
OPERATOR_ENTRYPOINT_PATH = PROJECT_ROOT / "scripts" / "rag" / "build_vesum_shadow.py"

SCHEMA_VERSION = "vesum-reingest-v1"
MARKER_POLICY_VERSION = "v1"
IMPORTER_VERSION = "v1"
COMPATIBILITY_HIDDEN_MARKERS = frozenset({"bad", "subst", "obsc"})
COMPATIBILITY_HIDDEN_MARKERS_SQL = ", ".join(
    f"'{marker}'" for marker in sorted(COMPATIBILITY_HIDDEN_MARKERS)
)
TAG_MARKERS: dict[str, tuple[str, str]] = {
    "alt": ("orthographic_variant", "tag"),
    "arch": ("archaic", "tag"),
    "bad": ("invalid", "tag"),
    "obsc": ("obscene", "tag"),
    "slang": ("slang", "tag"),
    "subst": ("nonstandard", "tag"),
    "vulg": ("vulgar", "tag"),
}
DIALECT_MARKER = ("dialect", "comment", "dialect")


class VesumReingestError(RuntimeError):
    """Raised when a release asset or its locked semantic contract is invalid."""


@dataclass(frozen=True)
class Analysis:
    """One upstream analysis with block-local provenance."""

    entry_id: int
    word_form: str
    lemma: str
    pos: str
    tags: str
    source_comment: str | None
    source_location: str


@dataclass
class _UnfinalizedBlock:
    entry_id: int
    lemma: str
    header_comment: str | None
    start_line: int
    end_line: int
    rows: list[tuple[str, str, str | None]]


@dataclass(frozen=True)
class BuildSummary:
    """Values which identify the semantics of a built shadow database."""

    analysis_count: int
    block_count: int
    forms_compatibility_count: int
    marker_counts: dict[str, int]
    canonical_jsonl_sha256: str
    fixture_manifest_sha256: str | None = None

    def as_lock_expected(self) -> dict[str, object]:
        """Return the summary shape stored in the source lock."""
        result: dict[str, object] = {
            "analysis_count": self.analysis_count,
            "forms_all_count": self.analysis_count,
            "forms_compatibility_count": self.forms_compatibility_count,
            "block_count": self.block_count,
            "marker_counts": dict(sorted(self.marker_counts.items())),
            "canonical_jsonl_sha256": self.canonical_jsonl_sha256,
        }
        if self.fixture_manifest_sha256 is not None:
            result["fixture_manifest_sha256"] = self.fixture_manifest_sha256
        return result


def sha256_file(path: Path) -> str:
    """Return the SHA-256 of ``path`` without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_lock(lock_path: Path = DEFAULT_LOCK_PATH) -> dict[str, object]:
    """Read and minimally validate a VESUM source lock."""
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VesumReingestError(f"Cannot read VESUM source lock {lock_path}: {exc}") from exc

    asset = lock.get("release_asset")
    if not isinstance(asset, dict):
        raise VesumReingestError("VESUM source lock has no release_asset object")
    for key in ("url", "sha256", "size_bytes", "version"):
        if key not in asset:
            raise VesumReingestError(f"VESUM source lock release_asset misses {key!r}")
    return lock


def _release_asset(lock: dict[str, object]) -> dict[str, object]:
    asset = lock["release_asset"]
    if not isinstance(asset, dict):  # guarded by load_lock; keeps this helper total.
        raise VesumReingestError("VESUM source lock release_asset is invalid")
    return asset


def verify_release_asset(asset_path: Path, lock: dict[str, object]) -> None:
    """Fail closed unless a local asset exactly matches the pinned release bytes."""
    asset = _release_asset(lock)
    if not asset_path.is_file():
        raise VesumReingestError(f"VESUM release asset does not exist: {asset_path}")

    expected_size = asset["size_bytes"]
    expected_sha256 = asset["sha256"]
    if not isinstance(expected_size, int) or not isinstance(expected_sha256, str):
        raise VesumReingestError("VESUM source lock has an invalid asset size or SHA-256")
    actual_size = asset_path.stat().st_size
    if actual_size != expected_size:
        raise VesumReingestError(
            f"VESUM release size mismatch: expected {expected_size}, got {actual_size}"
        )
    actual_sha256 = sha256_file(asset_path)
    if actual_sha256 != expected_sha256:
        raise VesumReingestError(
            f"VESUM release SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        )


def verify_pipeline_identity(lock: dict[str, object]) -> None:
    """Fail closed when the lock does not describe this parser and entry point."""
    pipeline = lock.get("pipeline")
    if not isinstance(pipeline, dict):
        raise VesumReingestError("VESUM source lock has no pipeline identity")
    expected = {
        "parser_module": ("scripts/rag/vesum_reingest.py", sha256_file(Path(__file__))),
        "operator_entrypoint": (
            "scripts/rag/build_vesum_shadow.py",
            sha256_file(OPERATOR_ENTRYPOINT_PATH),
        ),
    }
    for key, (expected_path, actual_sha256) in expected.items():
        value = pipeline.get(key)
        if not isinstance(value, dict):
            raise VesumReingestError(f"VESUM source lock pipeline misses {key}")
        if value.get("path") != expected_path or value.get("sha256") != actual_sha256:
            raise VesumReingestError(
                f"VESUM pipeline identity mismatch for {key}; update the lock only with a reviewed build"
            )


def fetch_release_asset(lock: dict[str, object], cache_dir: Path) -> Path:
    """Fetch the pinned release asset and verify its size and SHA-256.

    A matching cache is reused, but every return path is verified.  The URL is
    intentionally constrained to the pinned dict_uk GitHub release path so a
    malformed lock cannot turn this operator tool into an arbitrary fetcher.
    """
    asset = _release_asset(lock)
    url = asset["url"]
    version = asset["version"]
    if not isinstance(url, str) or not isinstance(version, str):
        raise VesumReingestError("VESUM source lock has an invalid release URL or version")

    parsed = urllib.parse.urlsplit(url)
    expected_prefix = f"/brown-uk/dict_uk/releases/download/{version}/"
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith(expected_prefix):
        raise VesumReingestError(f"Refusing non-pinned VESUM release URL: {url!r}")

    destination = cache_dir / Path(parsed.path).name
    if destination.exists():
        try:
            verify_release_asset(destination, lock)
        except VesumReingestError:
            destination.unlink()
        else:
            return destination

    cache_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=cache_dir, prefix="vesum-download-", suffix=".part", delete=False) as temp:
        temporary_path = Path(temp.name)
    try:
        urllib.request.urlretrieve(url, temporary_path)  # nosec B310 -- URL is pinned above.
        verify_release_asset(temporary_path, lock)
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return destination


def _parse_analysis_line(line: str, line_number: int) -> tuple[str, str, str | None]:
    """Split one visible-dictionary analysis while retaining its inline comment."""
    analysis, has_comment, comment = line.partition("#")
    analysis = analysis.rstrip()
    if not analysis.strip():
        raise VesumReingestError(f"Missing VESUM analysis at source line {line_number}")
    parts = analysis.split(None, 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise VesumReingestError(f"Malformed VESUM analysis at source line {line_number}: {line!r}")
    normalized_comment = comment.strip() if has_comment and comment.strip() else None
    return parts[0], parts[1], normalized_comment


def _analysis_comment(block_comment: str | None, line_comment: str | None) -> str | None:
    """Propagate a block comment and retain any distinct form-line comment."""
    comments = [comment for comment in (block_comment, line_comment) if comment]
    if len(comments) == 2 and comments[0] == comments[1]:
        comments.pop()
    return "\n".join(comments) if comments else None


def _finalize_block(block: _UnfinalizedBlock) -> Iterator[Analysis]:
    source_location = f"{block.start_line}-{block.end_line}"
    for word_form, tags, line_comment in block.rows:
        yield Analysis(
            entry_id=block.entry_id,
            word_form=word_form,
            lemma=block.lemma,
            pos=tags.partition(":")[0],
            tags=tags,
            source_comment=_analysis_comment(block.header_comment, line_comment),
            source_location=source_location,
        )


def iter_analyses(lines: Iterable[str]) -> Iterator[Analysis]:
    """Yield analyses from a VESUM visible-dictionary block stream.

    ``entry_id`` is the one-based block ordinal.  Each source location covers
    the complete block, making an analysis reproducible from the hash-locked
    release asset without an unsafe lemma-based join.
    """
    current: _UnfinalizedBlock | None = None
    block_count = 0

    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.rstrip("\n")
        content = line.partition("#")[0].rstrip()
        if not content.strip():
            if current is not None:
                current.end_line = line_number
            continue

        indented = content[0].isspace()
        word_form, tags, line_comment = _parse_analysis_line(line, line_number)
        if not indented:
            if current is not None:
                yield from _finalize_block(current)
            block_count += 1
            current = _UnfinalizedBlock(
                entry_id=block_count,
                lemma=word_form,
                header_comment=line_comment,
                start_line=line_number,
                end_line=line_number,
                rows=[(word_form, tags, line_comment)],
            )
            continue

        if current is None:
            raise VesumReingestError(f"Indented VESUM form without a header at source line {line_number}")
        current.rows.append((word_form, tags, line_comment))
        current.end_line = line_number

    if current is not None:
        yield from _finalize_block(current)


def marker_rows(tags: str, source_comment: str | None) -> tuple[tuple[str, str, str], ...]:
    """Normalize marker evidence without conflating it with grammatical tags."""
    rows: set[tuple[str, str, str]] = set()
    for token in tags.split(":"):
        marker = TAG_MARKERS.get(token)
        if marker is not None:
            marker_class, origin = marker
            rows.add((token, origin, marker_class))
    if source_comment is not None and any(
        line.strip().casefold() == "діалект" for line in source_comment.splitlines()
    ):
        rows.add(DIALECT_MARKER)
    return tuple(sorted(rows))


SCHEMA_SQL = f"""
PRAGMA foreign_keys = ON;
CREATE TABLE forms_all (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    word_form TEXT NOT NULL,
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    tags TEXT NOT NULL,
    source_comment TEXT,
    source_location TEXT NOT NULL
);
CREATE TABLE form_markers (
    form_id INTEGER NOT NULL REFERENCES forms_all(id) ON DELETE CASCADE,
    marker TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('tag', 'comment')),
    marker_class TEXT NOT NULL,
    PRIMARY KEY (form_id, marker, origin)
);
CREATE TABLE vesum_build_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE VIEW forms AS
SELECT word_form, lemma, tags, pos
FROM forms_all AS form
WHERE NOT EXISTS (
    SELECT 1
    FROM form_markers AS marker
    WHERE marker.form_id = form.id
      AND marker.marker IN ({COMPATIBILITY_HIDDEN_MARKERS_SQL})
);
"""


def _flush_batches(
    connection: sqlite3.Connection,
    form_rows: list[tuple[object, ...]],
    marker_rows_to_insert: list[tuple[object, ...]],
) -> None:
    if not form_rows:
        return
    connection.executemany(
        """
        INSERT INTO forms_all(
            id, entry_id, word_form, lemma, pos, tags, source_comment, source_location
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        form_rows,
    )
    if marker_rows_to_insert:
        connection.executemany(
            """
            INSERT INTO form_markers(form_id, marker, origin, marker_class)
            VALUES (?, ?, ?, ?)
            """,
            marker_rows_to_insert,
        )
    form_rows.clear()
    marker_rows_to_insert.clear()


def _canonical_jsonl_line(
    analysis: Analysis,
    markers: Sequence[tuple[str, str, str]],
) -> bytes:
    """Return one canonical JSONL analysis record in locked source order."""
    record = {
        "entry_id": analysis.entry_id,
        "word_form": analysis.word_form,
        "lemma": analysis.lemma,
        "pos": analysis.pos,
        "tags": analysis.tags,
        "source_comment": analysis.source_comment,
        "source_location": analysis.source_location,
        "markers": [
            {"marker": marker, "origin": origin, "marker_class": marker_class}
            for marker, origin, marker_class in markers
        ],
    }
    return (
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _canonical_jsonl_sha256(connection: sqlite3.Connection) -> str:
    """Hash the lexically sorted canonical JSONL export from the shadow DB."""
    cursor = connection.execute(
        """
        SELECT
            form.id,
            form.entry_id,
            form.word_form,
            form.lemma,
            form.pos,
            form.tags,
            form.source_comment,
            form.source_location,
            marker.marker,
            marker.origin,
            marker.marker_class
        FROM forms_all AS form
        LEFT JOIN form_markers AS marker ON marker.form_id = form.id
        ORDER BY
            form.entry_id,
            form.word_form,
            form.lemma,
            form.pos,
            form.tags,
            form.source_location,
            COALESCE(form.source_comment, ''),
            form.id,
            marker.marker,
            marker.origin
        """
    )
    digest = hashlib.sha256()
    current_id: int | None = None
    current_analysis: Analysis | None = None
    current_markers: list[tuple[str, str, str]] = []

    def write_current() -> None:
        if current_analysis is not None:
            digest.update(_canonical_jsonl_line(current_analysis, current_markers))

    for row in cursor:
        form_id = int(row[0])
        if form_id != current_id:
            write_current()
            current_id = form_id
            current_analysis = Analysis(
                entry_id=int(row[1]),
                word_form=str(row[2]),
                lemma=str(row[3]),
                pos=str(row[4]),
                tags=str(row[5]),
                source_comment=str(row[6]) if row[6] is not None else None,
                source_location=str(row[7]),
            )
            current_markers = []
        if row[8] is not None:
            current_markers.append((str(row[8]), str(row[9]), str(row[10])))
    write_current()
    return digest.hexdigest()


def _marker_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        str(marker): int(count)
        for marker, count in connection.execute(
            "SELECT marker, COUNT(*) FROM form_markers GROUP BY marker ORDER BY marker"
        )
    }


def build_shadow_database(asset_path: Path, output_path: Path) -> BuildSummary:
    """Build a new marker-preserving database from a verified release asset.

    This low-level function does not fetch or validate a lock so hermetic tests
    can feed it synthetic block samples.  Operator-facing callers must use
    :func:`build_from_lock`.
    """
    if output_path.resolve() == PRODUCTION_DB_PATH.resolve():
        raise VesumReingestError(
            "Refusing to replace data/vesum.db: step 1 only builds an explicit shadow database"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    temporary_path.unlink(missing_ok=True)

    connection = sqlite3.connect(temporary_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = OFF")
        connection.execute("PRAGMA synchronous = OFF")
        connection.executescript(SCHEMA_SQL)

        form_rows: list[tuple[object, ...]] = []
        marker_rows_to_insert: list[tuple[object, ...]] = []
        next_id = 1
        analysis_count = 0
        block_count = 0
        forms_compatibility_count = 0
        marker_counts: Counter[str] = Counter()
        last_entry_id = 0

        with bz2.open(asset_path, "rt", encoding="utf-8") as source:
            for analysis in iter_analyses(source):
                analysis_count += 1
                if analysis.entry_id != last_entry_id:
                    block_count += 1
                    last_entry_id = analysis.entry_id
                form_id = next_id
                next_id += 1
                form_rows.append(
                    (
                        form_id,
                        analysis.entry_id,
                        analysis.word_form,
                        analysis.lemma,
                        analysis.pos,
                        analysis.tags,
                        analysis.source_comment,
                        analysis.source_location,
                    )
                )
                normalized_markers = marker_rows(analysis.tags, analysis.source_comment)
                if not {marker for marker, _, _ in normalized_markers} & COMPATIBILITY_HIDDEN_MARKERS:
                    forms_compatibility_count += 1
                for marker, origin, marker_class in normalized_markers:
                    marker_rows_to_insert.append((form_id, marker, origin, marker_class))
                    marker_counts[marker] += 1
                if len(form_rows) >= 50_000:
                    _flush_batches(connection, form_rows, marker_rows_to_insert)
        _flush_batches(connection, form_rows, marker_rows_to_insert)

        connection.execute("CREATE INDEX idx_forms_all_word_form ON forms_all(word_form)")
        connection.execute("CREATE INDEX idx_forms_all_lemma ON forms_all(lemma)")
        connection.execute("CREATE INDEX idx_form_markers_form_id ON form_markers(form_id)")
        connection.execute("CREATE INDEX idx_form_markers_marker ON form_markers(marker)")
        canonical_sha256 = _canonical_jsonl_sha256(connection)
        metadata = {
            "schema_version": SCHEMA_VERSION,
            "marker_policy_version": MARKER_POLICY_VERSION,
            "compatibility_hidden_markers": json.dumps(sorted(COMPATIBILITY_HIDDEN_MARKERS)),
            "canonical_jsonl_sha256": canonical_sha256,
        }
        connection.executemany(
            "INSERT INTO vesum_build_metadata(key, value) VALUES (?, ?)",
            sorted(metadata.items()),
        )
        connection.commit()
    except Exception:
        connection.close()
        temporary_path.unlink(missing_ok=True)
        raise
    else:
        connection.close()
        os.replace(temporary_path, output_path)

    return BuildSummary(
        analysis_count=analysis_count,
        block_count=block_count,
        forms_compatibility_count=forms_compatibility_count,
        marker_counts=dict(sorted(marker_counts.items())),
        canonical_jsonl_sha256=canonical_sha256,
    )


def _fixture_row(connection: sqlite3.Connection, marker: str | None) -> sqlite3.Row:
    connection.row_factory = sqlite3.Row
    if marker is None:
        query = """
            SELECT form.*
            FROM forms_all AS form
            WHERE NOT EXISTS (SELECT 1 FROM form_markers WHERE form_id = form.id)
            ORDER BY form.word_form, form.lemma, form.tags, form.entry_id, form.id
            LIMIT 1
        """
        params: tuple[str, ...] = ()
    else:
        query = """
            SELECT form.*
            FROM forms_all AS form
            JOIN form_markers AS marker_row ON marker_row.form_id = form.id
            WHERE marker_row.marker = ?
            ORDER BY form.word_form, form.lemma, form.tags, form.entry_id, form.id
            LIMIT 1
        """
        params = (marker,)
    row = connection.execute(query, params).fetchone()
    if row is None:
        label = marker or "clean"
        raise VesumReingestError(f"Cannot generate required {label!r} VESUM fixture from the asset")
    return row


def generate_fixture_manifest(
    database_path: Path,
    lock: dict[str, object],
    output_path: Path,
) -> str:
    """Generate the attributed, deterministic source-derived fixture manifest."""
    release_asset = _release_asset(lock)
    fixture_markers: Sequence[tuple[str, str | None]] = (
        ("clean", None),
        ("alt", "alt"),
        ("arch", "arch"),
        ("bad", "bad"),
        ("obsc", "obsc"),
        ("slang", "slang"),
        ("subst", "subst"),
        ("vulg", "vulg"),
        ("dialect", "dialect"),
    )
    connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        fixtures = []
        for fixture_class, marker in fixture_markers:
            row = _fixture_row(connection, marker)
            markers = [
                dict(marker_row)
                for marker_row in connection.execute(
                    """
                    SELECT marker, origin, marker_class
                    FROM form_markers
                    WHERE form_id = ?
                    ORDER BY marker, origin
                    """,
                    (row["id"],),
                )
            ]
            fixtures.append(
                {
                    "class": fixture_class,
                    "entry_id": row["entry_id"],
                    "word_form": row["word_form"],
                    "lemma": row["lemma"],
                    "pos": row["pos"],
                    "tags": row["tags"],
                    "source_comment": row["source_comment"],
                    "source_location": row["source_location"],
                    "markers": markers,
                    "compatibility_visible": not any(
                        marker_row["marker"] in COMPATIBILITY_HIDDEN_MARKERS
                        for marker_row in markers
                    ),
                }
            )
        marker_counts = _marker_counts(connection)
    finally:
        connection.close()

    manifest = {
        "schema_version": "vesum-v6.8.0-fixtures-v1",
        "generated_by": {
            "module": "scripts/rag/vesum_reingest.py",
            "importer_version": IMPORTER_VERSION,
            "marker_policy_version": MARKER_POLICY_VERSION,
        },
        "source": {
            "name": "VESUM dict_uk visible dictionary release asset",
            "version": release_asset["version"],
            "url": release_asset["url"],
            "sha256": release_asset["sha256"],
            "license": "CC BY-NC-SA 4.0",
        },
        "selection": "lowest binary SQLite sort key per required marker class; never hand-picked",
        "fixtures": fixtures,
        "known_absent_classes": lock.get("known_absent_marker_classes", []),
        "marker_counts": marker_counts,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_expected_summary(lock: dict[str, object], summary: BuildSummary) -> None:
    """Reject a database whose locked semantic identity differs in any field."""
    expected = lock.get("expected")
    if not isinstance(expected, dict):
        raise VesumReingestError("VESUM source lock has no expected semantic summary")
    actual = summary.as_lock_expected()
    required = (
        "analysis_count",
        "block_count",
        "forms_all_count",
        "forms_compatibility_count",
        "marker_counts",
        "canonical_jsonl_sha256",
        "fixture_manifest_sha256",
    )
    missing = [key for key in required if key not in expected]
    if missing:
        raise VesumReingestError(f"VESUM source lock expected summary misses: {', '.join(missing)}")
    for key in required:
        if expected[key] != actual.get(key):
            raise VesumReingestError(
                f"VESUM semantic mismatch for {key}: expected {expected[key]!r}, got {actual.get(key)!r}"
            )


def build_from_lock(
    lock_path: Path,
    output_path: Path,
    fixture_manifest_path: Path,
    *,
    asset_path: Path | None = None,
    cache_dir: Path | None = None,
) -> BuildSummary:
    """Fetch/verify a locked release and build a fully validated shadow database."""
    lock = load_lock(lock_path)
    verify_pipeline_identity(lock)
    if asset_path is None:
        asset_path = fetch_release_asset(lock, cache_dir or PROJECT_ROOT / "data" / "vesum")
    verify_release_asset(asset_path, lock)
    summary = build_shadow_database(asset_path, output_path)
    fixture_manifest_sha256 = generate_fixture_manifest(output_path, lock, fixture_manifest_path)
    validated_summary = BuildSummary(
        analysis_count=summary.analysis_count,
        block_count=summary.block_count,
        forms_compatibility_count=summary.forms_compatibility_count,
        marker_counts=summary.marker_counts,
        canonical_jsonl_sha256=summary.canonical_jsonl_sha256,
        fixture_manifest_sha256=fixture_manifest_sha256,
    )
    validate_expected_summary(lock, validated_summary)
    return validated_summary
