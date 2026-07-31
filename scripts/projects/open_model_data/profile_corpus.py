"""Stream configured corpus sources through the pinned VESUM interface.

The profiler is diagnostic infrastructure, not an admission or correction
engine.  It reads source databases in read-only mode, keeps corpus text out of
receipts, emits unresolved token-level candidates, and fails closed whenever
provenance, rights, origin, contamination, or permitted-use evidence is not
complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data.inventory_existing_assets import WORD_RE
from scripts.verification.vesum import verify_words

CONFIG_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/corpus_profile_config_v1.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/review_candidate_v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/corpus_profile_receipt_v1.schema.json"

SCHEMA_VERSION = "corpus_profile_receipt_v1"
CANDIDATE_SCHEMA_VERSION = "review_candidate_v1"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CYRILLIC_RE = re.compile(r"[\u0400-\u052f]")
CANDIDATE_LOCATOR_RE = re.compile(r"^sqlite:[^#]+#[^/]+/.+$")
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "‘": "'", "`": "'", "´": "'"})
STRESS_MARKS = frozenset({"\u0300", "\u0301"})
USAGE_MARKERS = frozenset({"alt", "arch", "bad", "obsc", "rare", "slang", "subst", "vulg"})
PROTECTED_PERIODS = frozenset(
    {
        "historical",
        "historical_documents",
        "historical_literary_ukrainian",
        "middle_ukrainian",
        "old_east_slavic",
        "regional_dialectal",
    }
)
PROTECTED_REGISTER_FRAGMENTS = ("dialect", "folk", "heritage", "histor", "regional")


@dataclass(frozen=True)
class ProfileRunResult:
    """Paths and status returned by one deterministic profiling run."""

    summary: dict[str, Any]
    summary_path: Path
    candidates_path: Path

    @property
    def complete(self) -> bool:
        return bool(self.summary["coverage"]["complete"])


def canonical_json(value: Any) -> str:
    """Serialize JSON with a stable byte representation."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash a file without retaining it in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_form(surface: str) -> str:
    """Return the stress-insensitive, apostrophe-canonical VESUM lookup form."""
    normalized = unicodedata.normalize("NFKD", surface.translate(APOSTROPHES))
    without_marks = "".join(character for character in normalized if character not in STRESS_MARKS)
    return unicodedata.normalize("NFC", without_marks).casefold()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_and_validate_config(path: Path) -> dict[str, Any]:
    schema = _load_json(CONFIG_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    config = _load_json(path)
    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda item: list(item.path))
    if errors:
        messages = [f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors]
        raise ValueError("profile config invalid:\n" + "\n".join(messages))
    source_families = [source["source_family"] for source in config["sources"]]
    if len(source_families) != len(set(source_families)):
        raise ValueError("profile config has duplicate source_family values")
    return config


def _identifier(value: str) -> str:
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_identifier(table)})")}


def _source_query(source: Mapping[str, Any], columns: set[str]) -> tuple[str, tuple[Any, ...]]:
    adapter = source["adapter"]
    required = {adapter["id_column"], adapter["text_column"], adapter["locator_column"]}
    for dimension in adapter["dimensions"].values():
        if "column" in dimension:
            required.add(dimension["column"])
    exclusion = adapter.get("exclude")
    if exclusion:
        required.add(exclusion["column"])
    missing = sorted(required - columns)
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")

    selections = [
        f'{_identifier(adapter["id_column"])} AS "__record_id"',
        f'{_identifier(adapter["text_column"])} AS "__text"',
        f'{_identifier(adapter["locator_column"])} AS "__locator"',
    ]
    for name, dimension in sorted(adapter["dimensions"].items()):
        if "column" in dimension:
            selections.append(f"{_identifier(dimension['column'])} AS {_identifier('__' + name)}")
    parameters: tuple[Any, ...] = ()
    where = ""
    if exclusion:
        values = tuple(exclusion["values"])
        placeholders = ",".join("?" for _ in values)
        where = f" WHERE {_identifier(exclusion['column'])} NOT IN ({placeholders})"
        parameters = values
    query = (
        f"SELECT {', '.join(selections)} FROM {_identifier(adapter['table'])}"
        f"{where} ORDER BY {_identifier(adapter['id_column'])} ASC, "
        f"{_identifier(adapter['locator_column'])} ASC"
    )
    return query, parameters


def _dimension(row: sqlite3.Row, source: Mapping[str, Any], name: str) -> str:
    specification = source["adapter"]["dimensions"][name]
    value = specification.get("constant") if "constant" in specification else row[f"__{name}"]
    text = str(value or "").strip()
    return text if text else "unknown"


def _iter_batches(cursor: sqlite3.Cursor, batch_size: int) -> Iterator[list[sqlite3.Row]]:
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            return
        yield rows


def _lookup_vesum(forms: Iterable[str], *, database: Path, batch_size: int) -> dict[str, list[dict]]:
    ordered = sorted(set(forms))
    result: dict[str, list[dict]] = {}
    for index in range(0, len(ordered), batch_size):
        chunk = ordered[index : index + batch_size]
        matches = verify_words(chunk, db_path=database)
        for form in chunk:
            result[form] = sorted(
                matches.get(form, []),
                key=lambda item: (str(item["lemma"]), str(item["pos"]), str(item["tags"])),
            )
    return result


def _usage_markers(tags: str) -> tuple[str, ...]:
    tokens = set(re.findall(r"[a-z]+", tags.casefold()))
    return tuple(sorted(tokens & USAGE_MARKERS))


def _candidate_category(surface: str, period: str, register: str) -> tuple[str, str]:
    lowered_register = register.casefold()
    if period.casefold() in PROTECTED_PERIODS or any(
        fragment in lowered_register for fragment in PROTECTED_REGISTER_FRAGMENTS
    ):
        return "protected_variation_candidate", "low"
    if CYRILLIC_RE.search(surface) is None:
        return "foreign_language_candidate", "low"
    if surface[:1].isupper():
        return "proper_name_candidate", "low"
    return "non_ukrainian_form_candidate", "medium"


def _gate_reasons(source: Mapping[str, Any], origin: str) -> tuple[str, ...]:
    evidence = source["evidence"]
    checks = (
        (evidence["provenance_status"] == "complete", "provenance_incomplete"),
        (evidence["rights_status"] == "granted", "rights_not_granted"),
        (
            evidence["origin_status"] == "verified_human_authorship" and origin == "human_authored_source",
            "origin_not_verified",
        ),
        (evidence["contamination_status"] == "cleared", "contamination_not_cleared"),
        (evidence["permitted_use"] == "training_eligible", "permitted_use_not_training_eligible"),
    )
    return tuple(reason for passed, reason in checks if not passed)


def _add_distribution(
    distributions: dict[str, dict[str, dict[str, int]]],
    axis: str,
    value: str,
    *,
    rows: int,
    words: int,
) -> None:
    bucket = distributions[axis].setdefault(value, {"lexical_words": 0, "rows": 0})
    bucket["rows"] += rows
    bucket["lexical_words"] += words


def _candidate_record(
    *,
    source: Mapping[str, Any],
    record_id: str,
    locator: str,
    surface: str,
    normalized: str,
    token_count: int,
    period: str,
    register: str,
    origin: str,
) -> dict[str, Any]:
    category, confidence = _candidate_category(surface, period, register)
    return {
        "automatic_error_label": False,
        "candidate_category": category,
        "confidence": confidence,
        "evidence_status": "vesum_unknown_context_required",
        "locator": (f"sqlite:{source['adapter']['database']}#{source['adapter']['table']}/{locator}"),
        "normalized_form": normalized,
        "origin": origin,
        "period": period,
        "register": register,
        "review_disposition": "unresolved",
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "source_family": source["source_family"],
        "source_record_id": f"{source['inventory_asset_id']}:{record_id}",
        "surface_form": surface,
        "token_count_in_record": token_count,
        "vesum_evidence": {
            "analyses": [],
            "attested": False,
            "lookup_form": normalized,
        },
    }


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (canonical_json(value) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    os.replace(temporary, path)


def _prepare_spool(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE unknown_forms (
            normalized TEXT NOT NULL,
            source_family TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            PRIMARY KEY (normalized, source_family)
        );
        CREATE TABLE lemmas (lemma TEXT PRIMARY KEY);
        """
    )
    return connection


def _build_validator(schema_path: Path) -> Draft202012Validator:
    schema = _load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate_value(
    value: Mapping[str, Any],
    *,
    validator: Draft202012Validator,
    label: str,
) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ValueError(f"{label} does not satisfy its schema at {path}: {errors[0].message}")


def _validate_candidate(
    candidate: Mapping[str, Any],
    *,
    validator: Draft202012Validator,
    fully_validated_shapes: set[tuple[Any, Any]],
) -> None:
    """Enforce every dynamic field and schema-check each source/category shape.

    Full jsonschema evaluation on all multi-million candidates roughly doubles
    profiler runtime.  The record builder has one fixed shape per
    source/category pair, so each pair is checked by the canonical schema once;
    the data-dependent constraints are then checked for every record.
    """
    required_strings = {
        "source_record_id": 3,
        "source_family": 3,
        "surface_form": 1,
        "normalized_form": 1,
        "period": 1,
        "register": 1,
        "origin": 1,
    }
    for field, minimum in required_strings.items():
        value = candidate.get(field)
        if not isinstance(value, str) or len(value) < minimum:
            raise ValueError(f"review candidate has invalid {field}")
    locator = candidate.get("locator")
    if not isinstance(locator, str) or CANDIDATE_LOCATOR_RE.search(locator) is None:
        raise ValueError("review candidate has invalid locator")
    token_count = candidate.get("token_count_in_record")
    if type(token_count) is not int or token_count < 1:
        raise ValueError("review candidate has invalid token_count_in_record")

    vesum_evidence = candidate.get("vesum_evidence")
    if not isinstance(vesum_evidence, Mapping):
        raise ValueError("review candidate has invalid vesum_evidence")
    if vesum_evidence.get("lookup_form") != candidate["normalized_form"]:
        raise ValueError("review candidate lookup_form differs from normalized_form")

    shape = (candidate.get("source_family"), candidate.get("candidate_category"))
    if shape not in fully_validated_shapes:
        _validate_value(candidate, validator=validator, label="review candidate")
        fully_validated_shapes.add(shape)


def profile_corpus(
    *,
    config_path: Path,
    input_root: Path,
    summary_output: Path,
    candidates_output: Path,
) -> ProfileRunResult:
    """Profile every accessible configured record and write deterministic outputs."""
    config = _load_and_validate_config(config_path)
    candidate_validator = _build_validator(CANDIDATE_SCHEMA_PATH)
    receipt_validator = _build_validator(RECEIPT_SCHEMA_PATH)
    fully_validated_candidate_shapes: set[tuple[Any, Any]] = set()
    vesum_path = input_root / config["vesum"]["database"]
    if not vesum_path.is_file():
        raise FileNotFoundError(f"VESUM database inaccessible: {config['vesum']['database']}")

    expected_rows = sum(source["expected"]["rows"] for source in config["sources"])
    expected_words = sum(source["expected"]["lexical_words"] for source in config["sources"])
    counts = Counter()
    exclusion_reasons: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()
    usage_counts: Counter[str] = Counter()
    source_results: list[dict[str, Any]] = []
    inaccessible_sources: list[dict[str, str]] = []
    distributions = {axis: {} for axis in ("genre", "origin", "period", "register", "source_family")}

    candidates_output.parent.mkdir(parents=True, exist_ok=True)
    temporary_candidates = candidates_output.with_name(candidates_output.name + ".tmp")
    candidate_count = 0
    with tempfile.TemporaryDirectory(prefix="foundry-profile-") as temporary_directory:
        spool = _prepare_spool(Path(temporary_directory) / "profile.sqlite")
        try:
            with temporary_candidates.open("w", encoding="utf-8", newline="\n") as candidates:
                for source in config["sources"]:
                    database_path = input_root / source["adapter"]["database"]
                    source_rows = source_words = 0
                    connection: sqlite3.Connection | None = None
                    try:
                        connection = _connect_read_only(database_path)
                        columns = _table_columns(connection, source["adapter"]["table"])
                        query, parameters = _source_query(source, columns)
                    except (FileNotFoundError, sqlite3.Error, ValueError) as exc:
                        if connection is not None:
                            connection.close()
                        inaccessible_sources.append(
                            {
                                "reason": type(exc).__name__,
                                "source_family": source["source_family"],
                            }
                        )
                        continue

                    with closing(connection):
                        cursor = connection.execute(query, parameters)
                        for rows in _iter_batches(cursor, config["record_batch_size"]):
                            prepared: list[dict[str, Any]] = []
                            lookup_forms: set[str] = set()
                            for row in rows:
                                text = str(row["__text"] or "")
                                surfaces: dict[str, Counter[str]] = {}
                                for surface in WORD_RE.findall(text):
                                    normalized = normalize_form(surface)
                                    if not normalized:
                                        continue
                                    surfaces.setdefault(normalized, Counter())[surface] += 1
                                lookup_forms.update(surfaces)
                                prepared.append(
                                    {
                                        "genre": _dimension(row, source, "genre"),
                                        "locator": str(row["__locator"]),
                                        "origin": _dimension(row, source, "origin"),
                                        "period": _dimension(row, source, "period"),
                                        "record_id": str(row["__record_id"]),
                                        "register": _dimension(row, source, "register"),
                                        "surfaces": surfaces,
                                        "word_count": sum(sum(values.values()) for values in surfaces.values()),
                                    }
                                )

                            vesum_matches = _lookup_vesum(
                                lookup_forms,
                                database=vesum_path,
                                batch_size=config["vesum"]["batch_size"],
                            )
                            for record in prepared:
                                word_count = record["word_count"]
                                source_rows += 1
                                source_words += word_count
                                counts["processed_rows"] += 1
                                counts["processed_lexical_words"] += word_count
                                for axis in distributions:
                                    value = source["source_family"] if axis == "source_family" else record[axis]
                                    _add_distribution(
                                        distributions,
                                        axis,
                                        value,
                                        rows=1,
                                        words=word_count,
                                    )

                                gate_reasons = _gate_reasons(source, record["origin"])
                                if gate_reasons:
                                    counts["excluded_rows"] += 1
                                    counts["excluded_lexical_words"] += word_count
                                    for reason in gate_reasons:
                                        exclusion_reasons[reason] += 1
                                else:
                                    counts["training_eligible_rows"] += 1
                                    counts["training_eligible_lexical_words"] += word_count

                                for normalized, surface_counts in sorted(record["surfaces"].items()):
                                    token_count = sum(surface_counts.values())
                                    analyses = vesum_matches[normalized]
                                    if analyses:
                                        counts["vesum_attested_tokens"] += token_count
                                        primary = analyses[0]
                                        lemma = str(primary.get("lemma") or "").strip()
                                        pos = str(primary.get("pos") or "").strip()
                                        markers = _usage_markers(str(primary.get("tags") or ""))
                                        if lemma:
                                            counts["tokens_with_lemma"] += token_count
                                            spool.execute("INSERT OR IGNORE INTO lemmas(lemma) VALUES (?)", (lemma,))
                                        if pos:
                                            counts["tokens_with_pos"] += token_count
                                            pos_counts[pos] += token_count
                                        if markers:
                                            counts["tokens_with_usage_marker"] += token_count
                                            for marker in markers:
                                                usage_counts[marker] += token_count
                                        continue

                                    counts["vesum_unknown_tokens"] += token_count
                                    spool.execute(
                                        """
                                        INSERT INTO unknown_forms(normalized, source_family, token_count)
                                        VALUES (?, ?, ?)
                                        ON CONFLICT(normalized, source_family) DO UPDATE SET
                                            token_count = token_count + excluded.token_count
                                        """,
                                        (normalized, source["source_family"], token_count),
                                    )
                                    surface = sorted(
                                        surface_counts,
                                        key=lambda item: (-surface_counts[item], item),
                                    )[0]
                                    candidate = _candidate_record(
                                        source=source,
                                        record_id=record["record_id"],
                                        locator=record["locator"],
                                        surface=surface,
                                        normalized=normalized,
                                        token_count=token_count,
                                        period=record["period"],
                                        register=record["register"],
                                        origin=record["origin"],
                                    )
                                    _validate_candidate(
                                        candidate,
                                        validator=candidate_validator,
                                        fully_validated_shapes=fully_validated_candidate_shapes,
                                    )
                                    candidates.write(canonical_json(candidate) + "\n")
                                    candidate_count += 1
                            spool.commit()

                    expected = source["expected"]
                    source_results.append(
                        {
                            "actual": {"lexical_words": source_words, "rows": source_rows},
                            "expected": expected,
                            "inventory_asset_id": source["inventory_asset_id"],
                            "matches_expected": (
                                source_rows == expected["rows"] and source_words == expected["lexical_words"]
                            ),
                            "source_family": source["source_family"],
                        }
                    )
            os.replace(temporary_candidates, candidates_output)

            unknown_distinct = int(spool.execute("SELECT COUNT(DISTINCT normalized) FROM unknown_forms").fetchone()[0])
            lemma_distinct = int(spool.execute("SELECT COUNT(*) FROM lemmas").fetchone()[0])
            top_unknown: list[dict[str, Any]] = []
            top_rows = spool.execute(
                """
                SELECT normalized, SUM(token_count) AS total
                FROM unknown_forms
                GROUP BY normalized
                ORDER BY total DESC, normalized ASC
                LIMIT ?
                """,
                (config["top_unknown_limit"],),
            ).fetchall()
            for normalized, total in top_rows:
                source_distribution = {
                    str(source_family): int(token_count)
                    for source_family, token_count in spool.execute(
                        """
                        SELECT source_family, token_count FROM unknown_forms
                        WHERE normalized = ? ORDER BY source_family ASC
                        """,
                        (normalized,),
                    )
                }
                top_unknown.append(
                    {
                        "normalized_form": str(normalized),
                        "source_distribution": source_distribution,
                        "token_count": int(total),
                    }
                )
        finally:
            spool.close()
            temporary_candidates.unlink(missing_ok=True)

    all_sources_match = len(source_results) == len(config["sources"]) and all(
        result["matches_expected"] for result in source_results
    )
    summary = {
        "admission_safety": {
            "excluded_lexical_words": counts["excluded_lexical_words"],
            "excluded_rows": counts["excluded_rows"],
            "exclusion_reason_row_counts": dict(sorted(exclusion_reasons.items())),
            "training_eligible_lexical_words": counts["training_eligible_lexical_words"],
            "training_eligible_rows": counts["training_eligible_rows"],
            "zero_current_admissions": counts["training_eligible_rows"] == 0,
        },
        "coverage": {
            "complete": not inaccessible_sources and all_sources_match,
            "expected_lexical_words": expected_words,
            "expected_rows": expected_rows,
            "inaccessible_sources": sorted(
                inaccessible_sources,
                key=lambda item: (item["source_family"], item["reason"]),
            ),
            "processed_lexical_words": counts["processed_lexical_words"],
            "processed_rows": counts["processed_rows"],
            "source_results": sorted(source_results, key=lambda item: item["source_family"]),
        },
        "determinism": {
            "candidate_order": "config source order, SQLite record id, normalized form",
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
        },
        "distributions": {axis: dict(sorted(values.items())) for axis, values in sorted(distributions.items())},
        "measurement_contract": {
            "lexical_words": r"[^\W\d_]+(?:[’'][^\W\d_]+)*",
            "normalization": "NFKD; strip acute/grave stress only; canonical apostrophe; casefold; NFC",
            "primary_analysis": "lexicographically first (lemma, pos, tags) VESUM analysis",
            "record_text_in_receipt": False,
            "tokenizer_diagnostics": "not_run; no approved tokenizer interface is required for this foundation",
        },
        "outputs": {
            "review_candidates": {
                "bytes": candidates_output.stat().st_size,
                "records": candidate_count,
                "sha256": sha256_file(candidates_output),
            }
        },
        "profile_id": config["profile_id"],
        "schema_version": SCHEMA_VERSION,
        "source_snapshot_id": config["source_snapshot_id"],
        "unknown_forms": {
            "distinct_normalized_forms": unknown_distinct,
            "top_by_frequency": top_unknown,
        },
        "vesum": {
            "distinct_lemmas_observed": lemma_distinct,
            "interface": config["vesum"]["interface"],
            "pos_token_distribution": dict(sorted(pos_counts.items())),
            "snapshot_id": config["vesum"]["snapshot_id"],
            "tokens_attested": counts["vesum_attested_tokens"],
            "tokens_unknown": counts["vesum_unknown_tokens"],
            "tokens_with_lemma": counts["tokens_with_lemma"],
            "tokens_with_pos": counts["tokens_with_pos"],
            "tokens_with_usage_marker": counts["tokens_with_usage_marker"],
            "usage_marker_token_distribution": dict(sorted(usage_counts.items())),
        },
    }
    _validate_value(summary, validator=receipt_validator, label="aggregate receipt")
    _write_json_atomic(summary_output, summary)
    return ProfileRunResult(summary=summary, summary_path=summary_output, candidates_path=candidates_output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stream configured corpus records through pinned VESUM diagnostics")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--input-root", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    parser.add_argument("--candidates-output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = profile_corpus(
        config_path=args.config,
        input_root=args.input_root,
        summary_output=args.summary_output,
        candidates_output=args.candidates_output,
    )
    print(canonical_json(result.summary))
    return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
