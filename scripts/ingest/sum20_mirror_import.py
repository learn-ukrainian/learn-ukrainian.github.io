#!/usr/bin/env python3
"""Import the staged СУМ-20 mirror into a new, verified ``sources.db`` generation (#8579).

``import`` takes the store writer lock, then copies the selected generation
with the SQLite online backup API into a candidate file in ``data/``. It
imports every staged slovnyk.me ``newsum`` article from the frozen staging
bytes into the candidate's ``sum20_mirror_*`` tables (``scripts.wiki.sum20_mirror``)
and verifies the candidate. It then publishes the candidate as a new generation
through ``scripts.storage.generations.publish_generation``, still under the
same lock. The official ``sum20_*`` tables, their quarantine marks and the
crawl tables are never written, and verification proves them unchanged.

The selected generation is only read, and the publisher is the only thing that
changes the selection (docs/runbooks/storage-topology.md, "Sources store
generations"). A reader that opened the store before the switch keeps the
previous generation, whole and unchanged. Every generation is retained, so a
rollback selects the previous one with
``python -m scripts.storage restore-generation``.

The writer runs only from the primary checkout, on a local filesystem, after
the one-time generation bootstrap. A busy writer lock is refused, never waited
for. It makes no network request.

Examples:
  .venv/bin/python -m scripts.ingest.sum20_mirror_import plan
  .venv/bin/python -m scripts.ingest.sum20_mirror_import import --expect-staging-sha256 <sha256>

Outputs: one JSON object on stdout.
Exit codes: 0 published; 1 verification failed (selection unchanged); 2 refused
(arguments, locality, layout, lock, staging, disk space, publication; selection
unchanged); 3 published, but a step after the selector switch failed (the new
generation is selected).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.repo_root import main_checkout_root
from scripts.lexicon import reconcile_sum20
from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage import generations, topology
from scripts.wiki import sum20_mirror
from scripts.wiki.sum20_official import live_article_predicate, normalize_sum20_lookup

STAGING_NAME = "sum20_slovnyk_staging.db"
OFFICIAL_TABLES = (
    ("sum20_articles", "id"),
    ("sum20_senses", "id"),
    ("sum20_citations", "id"),
    ("sum20_crawl_checkpoint", "singleton"),
    ("sum20_crawl_outcomes", "wordid"),
)
SAMPLE_PER_RELATION = 5
BATCH_ROWS = 5000
CHUNK = 8 * 1024 * 1024


class Refused(RuntimeError):
    """Stopped before the selection changed; ``reason`` is path-free."""

    def __init__(self, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class PostSwitchFailure(RuntimeError):
    """The publisher failed after the selector switch: the new generation is already selected."""

    def __init__(self, reason: str, generation: str, previous: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.generation = generation
        self.previous = previous


class VerificationFailed(RuntimeError):
    """The candidate failed a check; the selection was not changed."""

    def __init__(self, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.detail = detail


@dataclass(frozen=True)
class Target:
    data_dir: Path
    root: Path

    @property
    def selector(self) -> Path:
        return self.data_dir / topology.SELECTOR_NAME

    @property
    def staging(self) -> Path:
        return self.data_dir / STAGING_NAME


def writer_target(repository_root: Path | None = None, *, test_data_dir: Path | None = None) -> Target:
    """The primary checkout's ``data/``, or an explicit test directory.

    Like the lexdata writer it refuses a linked worktree, a symlinked ``data/``
    and a network or unknown filesystem. The store is always the canonical
    selector of that directory, never an environment override.
    """
    if test_data_dir is not None:
        data_dir, root = test_data_dir, test_data_dir.parent
    else:
        root = topology.default_repository_root(repository_root).resolve()
        primary = main_checkout_root(root).resolve()
        if root != primary:
            raise Refused("linked_worktree")
        data_dir = primary / "data"
    if data_dir.is_symlink():
        raise Refused("symlinked_path")
    if not data_dir.is_dir():
        raise Refused("data_dir_missing")
    target = Target(data_dir.resolve(), root)
    locality = topology.store_locality(target.data_dir)
    if locality != "local":
        raise Refused(f"locality_{locality}")
    return target


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _sidecars(path: Path) -> list[Path]:
    return [Path(f"{path}{suffix}") for suffix in ("-wal", "-shm", "-journal")]


def _remove(paths: Sequence[Path]) -> None:
    for path in paths:
        if path.exists() or path.is_symlink():
            path.unlink()


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


# --- staging ---------------------------------------------------------------------------------------------


def _staging_identity(path: Path) -> tuple:
    info = path.stat()
    wal = Path(f"{path}-wal")
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        wal.stat().st_size if wal.exists() else 0,
        Path(f"{path}-journal").exists(),
    )


def snapshot_staging(target: Target, expect_sha256: str) -> tuple[Path, str]:
    """Copy the staging main file while hashing it, so the imported bytes are the admitted bytes.

    A WAL holding frames, a rollback journal, or any change during the copy
    refuses: committed content outside the main file would escape the digest.
    The snapshot is read only with ``immutable=1``.
    """
    resolved = topology.resolve_store("sources", target.root, binding=topology.StoreBinding("sources", target.staging))
    if isinstance(resolved, topology.StoreRefusal):
        raise Refused(f"staging_{resolved.reason}")
    before = _staging_identity(resolved.path)
    if before[4] or before[5]:
        raise Refused("staging_not_checkpointed")
    snapshot = target.data_dir / f".{STAGING_NAME}.{os.getpid()}.snapshot"
    digest = hashlib.sha256()
    try:
        with resolved.path.open("rb") as source, snapshot.open("wb") as copy:
            while chunk := source.read(CHUNK):
                digest.update(chunk)
                copy.write(chunk)
            copy.flush()
            os.fsync(copy.fileno())
        if _staging_identity(resolved.path) != before:
            raise Refused("staging_changed_during_snapshot")
        if digest.hexdigest() != expect_sha256.lower():
            raise Refused("staging_digest_mismatch")
        snapshot.chmod(0o444)
    except BaseException:
        _remove([snapshot])
        raise
    return snapshot, digest.hexdigest()


def _open_ro(path: Path, *, immutable: bool = False) -> SQLiteConnection:
    conn = open_readonly(path, immutable=immutable)
    conn.row_factory = sqlite3.Row
    return conn


def staging_summary(conn: SQLiteConnection) -> dict[str, Any]:
    """A complete checkpoint: every article has an ``ok`` outcome and the checkpoint counts them all."""
    records = conn.execute("SELECT COUNT(*) FROM sum20_slovnyk_articles").fetchone()[0]
    ok = conn.execute(
        "SELECT COUNT(*) FROM sum20_slovnyk_articles AS a JOIN sum20_slovnyk_outcomes AS o "
        "ON o.url = a.url WHERE o.status = 'ok'"
    ).fetchone()[0]
    outcomes = conn.execute("SELECT COUNT(*) FROM sum20_slovnyk_outcomes").fetchone()[0]
    checkpoint = conn.execute(
        "SELECT completed_count, last_url, updated_at FROM sum20_slovnyk_checkpoint WHERE singleton = 1"
    ).fetchone()
    if checkpoint is None or not records or not (records == ok == outcomes == checkpoint[0]):
        raise Refused("staging_incomplete")
    return {
        "records": records,
        "checkpoint_count": checkpoint[0],
        "checkpoint_last_url": checkpoint[1],
        "checkpoint_updated_at": checkpoint[2],
    }


def staged_articles(conn: SQLiteConnection) -> Iterator[sqlite3.Row]:
    yield from conn.execute(
        "SELECT url, source_url, mirror, lemma, headword, title, text, senses_json, fetched_at, content_sha256 "
        "FROM sum20_slovnyk_articles ORDER BY url"
    )


def _row_digest(digest: Any, *fields: str) -> None:
    *head, text = fields
    digest.update(json.dumps([*head, hashlib.sha256(text.encode("utf-8")).hexdigest()]).encode("utf-8") + b"\n")


def staging_digest(conn: SQLiteConnection) -> str:
    digest = hashlib.sha256()
    for row in staged_articles(conn):
        _row_digest(
            digest,
            row["url"],
            row["source_url"],
            row["mirror"],
            row["lemma"],
            row["headword"],
            row["title"],
            row["fetched_at"],
            row["content_sha256"],
            row["senses_json"],
            row["text"],
        )
    return digest.hexdigest()


def imported_digest(conn: SQLiteConnection) -> str:
    digest = hashlib.sha256()
    for row in conn.execute(
        "SELECT mirror_url, source_url, mirror, lemma, headword, title, fetched_at, content_sha256, senses_json, "
        "article_text FROM sum20_mirror_articles ORDER BY mirror_url"
    ):
        _row_digest(digest, *row)
    return digest.hexdigest()


# --- official rows and the rule ------------------------------------------------------------------------


def official_digest(conn: SQLiteConnection) -> str:
    """Full-row digest of the official collection and its crawl tables (absent tables digest as absent)."""
    digest = hashlib.sha256()
    for table, key in OFFICIAL_TABLES:
        columns = [str(row[1]) for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
        digest.update(json.dumps([table, columns]).encode("utf-8") + b"\n")
        if not columns:
            continue
        for row in conn.execute(f'SELECT * FROM "{table}" ORDER BY "{key}"'):
            digest.update(json.dumps(list(row), ensure_ascii=False).encode("utf-8") + b"\n")
    return digest.hexdigest()


def table_counts(conn: SQLiteConnection) -> dict[str, int]:
    """Row counts of every ordinary table outside the mirror tables."""
    names = [
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "AND sql NOT LIKE 'CREATE VIRTUAL TABLE%' ORDER BY name"
        )
    ]
    return {
        name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        for name in names
        if name not in sum20_mirror.MIRROR_TABLES
    }


def official_by_key(conn: SQLiteConnection) -> dict[str, list[tuple[str, str, str, bool]]]:
    columns = [str(row[1]) for row in conn.execute("PRAGMA table_info(sum20_articles)").fetchall()]
    grouped: dict[str, list[tuple[str, str, str, bool]]] = {}
    if not columns:
        return grouped
    for headword, text, key, live in conn.execute(
        f"SELECT headword, article_text, normalized_lookup_key, ({live_article_predicate(columns)}) "
        "FROM sum20_articles ORDER BY wordid"
    ):
        grouped.setdefault(str(key), []).append((str(headword or ""), str(text or ""), str(key), bool(live)))
    return grouped


def classify_staging(staging: SQLiteConnection, official: SQLiteConnection) -> dict[str, Any]:
    """Relation counts under the rule, plus the reconciliation report's differences mapped onto them.

    ``reconcile_sum20`` groups by URL lemma; every identity it reports as differing
    must stay served and flagged under the import's headword identity.
    """
    by_key = official_by_key(official)
    relations: Counter[str] = Counter()
    by_lemma: dict[str, set[str]] = {}
    samples: dict[str, list[str]] = {relation: [] for relation in sum20_mirror.RELATIONS}
    for row in staged_articles(staging):
        key = sum20_mirror.mirror_key(row["headword"])
        if not key:
            raise Refused("staging_headword_missing")
        relation = sum20_mirror.classify(row["headword"], row["text"], by_key.get(key, []))
        relations[relation] += 1
        by_lemma.setdefault(normalize_sum20_lookup(row["lemma"]), set()).add(relation)
        if len(samples[relation]) < SAMPLE_PER_RELATION and key not in samples[relation]:
            samples[relation].append(key)
    _, staged = reconcile_sum20._inventory(staging, staging=True)
    _, ingested = reconcile_sum20._inventory(official, staging=False)
    differing = sorted(key for key in staged.keys() & ingested.keys() if staged[key] != ingested[key])
    flagged = {sum20_mirror.DIFFERS, sum20_mirror.OFFICIAL_QUARANTINED}
    return {
        "relation_counts": sum20_mirror.relation_counts(relations.elements()),
        "reconcile_differing": len(differing),
        "reconcile_differing_unflagged": [key for key in differing if not by_lemma.get(key, set()) <= flagged],
        "samples": samples,
    }


# --- build -------------------------------------------------------------------------------------------------


def _copy_live(live: Path, destination: Path) -> None:
    """SQLite online backup from a read-only connection into a fresh file."""
    with closing(open_readonly(live)) as source, closing(sqlite3.connect(destination)) as copy:
        source.backup(copy)


def _import(
    conn: SQLiteConnection,
    staging: SQLiteConnection,
    info: dict[str, Any],
    plan: dict[str, Any],
    label: str,
    official: str,
) -> None:
    """Replace only the derived mirror rows; earlier import receipts stay as history."""
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(sum20_mirror.SCHEMA_SQL)
    conn.execute("DELETE FROM sum20_mirror_articles")
    cursor = conn.execute(
        "INSERT INTO sum20_mirror_imports (generation, rule_version, staging_sha256, staging_records, "
        "checkpoint_count, checkpoint_last_url, checkpoint_updated_at, official_digest, relation_counts, imported_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            label,
            sum20_mirror.RULE_VERSION,
            info["sha256"],
            info["records"],
            info["checkpoint_count"],
            info["checkpoint_last_url"],
            info["checkpoint_updated_at"],
            official,
            json.dumps(plan["relation_counts"], sort_keys=True),
            _now(),
        ),
    )
    import_id = cursor.lastrowid
    batch: list[tuple] = []
    for row in staged_articles(staging):
        batch.append(
            (
                row["url"],
                row["source_url"],
                row["mirror"],
                row["lemma"],
                row["headword"],
                sum20_mirror.mirror_key(row["headword"]),
                row["title"],
                row["text"],
                row["senses_json"],
                row["fetched_at"],
                row["content_sha256"],
                import_id,
            )
        )
        if len(batch) >= BATCH_ROWS:
            _insert(conn, batch)
            batch = []
    if batch:
        _insert(conn, batch)
    conn.commit()


def _insert(conn: SQLiteConnection, batch: list[tuple]) -> None:
    conn.executemany(
        "INSERT INTO sum20_mirror_articles (mirror_url, source_url, mirror, lemma, headword, normalized_lookup_key, "
        "title, article_text, senses_json, fetched_at, content_sha256, import_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        batch,
    )


def _imported_relations(conn: SQLiteConnection) -> Iterator[str]:
    by_key = official_by_key(conn)
    for headword, text, key in conn.execute(
        "SELECT headword, article_text, normalized_lookup_key FROM sum20_mirror_articles"
    ):
        yield sum20_mirror.classify(str(headword), str(text), by_key.get(str(key), []))


def verify(
    path: Path, live: Path, staging: SQLiteConnection, pre: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    """Every check the new generation must pass before it may become a candidate."""
    from scripts.wiki.sources_db import query_sum20

    failures: list[str] = []
    with closing(_open_ro(path)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            failures.append("integrity_check")
        if conn.execute("PRAGMA foreign_key_check(sum20_mirror_articles)").fetchall():
            failures.append("foreign_key_check")
        if imported_digest(conn) != staging_digest(staging):
            failures.append("mirror_rows_differ_from_staging")
        if official_digest(conn) != pre["official_digest"]:
            failures.append("official_rows_changed")
        if table_counts(conn) != pre["table_counts"]:
            failures.append("other_table_counts_changed")
        counts = sum20_mirror.relation_counts(_imported_relations(conn))
    if counts != plan["relation_counts"]:
        failures.append("relation_counts_differ_from_plan")
    if plan["reconcile_differing_unflagged"]:
        failures.append("reconcile_difference_not_flagged")
    sampled = 0
    for relation, keys in plan["samples"].items():
        for key in keys:
            records = query_sum20(key, db_path=path)
            mirror = [r for r in records if r.get("source_role") == "mirror"]
            official = [r for r in records if r.get("source_role") == "official"]
            if sum20_mirror.is_served(relation):
                if not any(r["official_relation"] == relation for r in mirror):
                    failures.append(f"sample_not_served:{relation}")
            elif mirror or not official:
                failures.append(f"sample_not_suppressed:{relation}")
            before = [r for r in query_sum20(key, db_path=live) if r.get("source_role") == "official"]
            if official != before:
                failures.append(f"sample_official_changed:{relation}")
            sampled += 1
    if failures:
        raise VerificationFailed(",".join(sorted(set(failures))))
    return {"checks": "passed", "sampled_lookups": sampled, "relation_counts": counts}


def _seal(path: Path) -> None:
    """Persist WAL mode in the header and close last, so the candidate is one self-contained file.

    The verification reads leave empty sidecars; this last read-write
    connection removes them on close, so none outlives the candidate's name.
    """
    with closing(sqlite3.connect(path)) as conn:
        if str(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower() != "wal":
            raise VerificationFailed("journal_mode_not_wal")
    if any(sidecar.exists() for sidecar in _sidecars(path)):
        raise VerificationFailed("sidecar_left_after_close")


# --- plan and import ---------------------------------------------------------------------------------------


def _selected(target: Target) -> Path:
    """The file the store selects now (the selected generation, or the pre-bootstrap file); read only."""
    resolved = topology.resolve_store("sources", target.root, binding=topology.StoreBinding("sources", target.selector))
    if isinstance(resolved, topology.StoreRefusal):
        raise Refused(f"live_{resolved.reason}")
    return resolved.path


def plan(target: Target) -> dict[str, Any]:
    """Read-only relation counts against the live official rows; nothing is copied or written."""
    with closing(_open_ro(target.staging)) as staging, closing(_open_ro(_selected(target))) as live:
        summary = staging_summary(staging)
        result = classify_staging(staging, live)
    return {
        "status": "plan",
        "rule_version": sum20_mirror.RULE_VERSION,
        "staging_records": summary["records"],
        **result,
    }


def _build_candidate(target: Target, current: Path, expect_sha256: str) -> tuple[Path, dict[str, Any]]:
    """Copy ``current``, import the staged mirror into the copy and verify it; ``current`` is only read."""
    snapshot, staging_sha = snapshot_staging(target, expect_sha256)
    # In data/ itself: the publisher hard-links the candidate, so it must share the store's filesystem.
    candidate = target.data_dir / f".{topology.SELECTOR_NAME}.{os.getpid()}.{secrets.token_hex(4)}.sum20-mirror"
    try:
        with closing(_open_ro(snapshot, immutable=True)) as staging:
            info = {"sha256": staging_sha, **staging_summary(staging)}
            with closing(_open_ro(current)) as live:
                pre = {"official_digest": official_digest(live), "table_counts": table_counts(live)}
                result = classify_staging(staging, live)
            if result["reconcile_differing_unflagged"]:
                raise VerificationFailed("reconcile_difference_not_flagged")
            _copy_live(current, candidate)
            label = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
            with closing(sqlite3.connect(candidate)) as conn:
                _import(conn, staging, info, result, label, pre["official_digest"])
            checks = verify(candidate, current, staging, pre, result)
        _seal(candidate)
    except BaseException:
        _remove([candidate, *_sidecars(candidate)])
        raise
    finally:
        _remove([snapshot])
    details = {
        "import_label": label,
        "staging_sha256": staging_sha,
        "staging_records": info["records"],
        "rule_version": sum20_mirror.RULE_VERSION,
        "reconcile_differing": result["reconcile_differing"],
        "samples": result["samples"],
        "verification": checks,
    }
    return candidate, details


def _switched_to(target: Target, previous: Path) -> Path | None:
    """The generation now selected when it is not ``previous``; ``None`` when the selection is unchanged or unreadable."""
    try:
        state = generations.inspect_selector(target.selector)
    except Exception:
        return None
    if state.layout != "selector" or state.generation is None or state.generation == previous:
        return None
    return state.generation


def run_import(target: Target, expect_sha256: str) -> dict[str, Any]:
    """Build, verify and publish one new generation, holding the store writer lock throughout.

    The lock is taken before the selector is read and kept until the publisher
    has switched it, so no writer changes the generation the candidate was
    copied from. A refusal or failed verification leaves the selection as it
    was; the candidate file is removed. An error raised by the publisher after
    the selector switch is a ``PostSwitchFailure``, never a refusal: the new
    generation is already selected.
    """
    try:
        with generations.writer_lock(target.selector) as held:
            if held.layout != "selector" or held.generation is None:
                raise Refused("import_requires_selector")
            current = held.generation
            if not generations.is_held(current):
                raise Refused("current_generation_writable")
            # The candidate and the staging snapshot, each with the publisher's margin.
            generations.require_free_space(target.data_dir, current.stat().st_size + 2 * target.staging.stat().st_size)
            candidate, details = _build_candidate(target, current, expect_sha256)
            try:
                publication = generations.publish_generation(candidate, held)
            except BaseException as exc:
                _remove([candidate, *_sidecars(candidate)])
                if isinstance(exc, Exception) and (switched := _switched_to(target, current)) is not None:
                    reason = exc.reason if isinstance(exc, generations.GenerationError) else type(exc).__name__
                    raise PostSwitchFailure(reason, switched.name, current.name) from exc
                raise
    except generations.GenerationError as exc:
        raise Refused(exc.reason) from None
    return {
        "status": "published",
        "generation": publication.generation.name,
        "previous": None if publication.previous is None else publication.previous.name,
        "sha256": publication.sha256,
        **details,
        "default_reader": default_reader_check(details["samples"]),
    }


def default_reader_check(samples: dict[str, list[str]]) -> dict[str, Any]:
    """Whether the default ``query_sum20`` selection now serves a sampled mirror-only key."""
    from scripts.wiki.sources_db import query_sum20

    keys = samples.get(sum20_mirror.MIRROR_ONLY) or []
    if not keys:
        return {"key_sampled": False}
    records = query_sum20(keys[0])
    return {"key_sampled": True, "serves_mirror": any(r.get("source_role") == "mirror" for r in records)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import the staged СУМ-20 mirror into a new verified sources.db generation and publish it. "
            "Primary checkout only; never writes the official sum20 tables."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ingest.sum20_mirror_import plan\n"
            "  .venv/bin/python -m scripts.ingest.sum20_mirror_import import --expect-staging-sha256 <sha256>\n"
            "  .venv/bin/python -m scripts.storage restore-generation data/sources-generations/<previous>  # rollback\n\n"
            "Outputs: JSON on stdout; the new generation under data/sources-generations/.\n"
            "Exit codes: 0 published; 1 verification failed (selection unchanged); 2 refused (selection unchanged);\n"
            "3 published, but a step after the selector switch failed (the new generation is selected).\n"
            "Related: issue #8579; docs/runbooks/dictionary-acquisition.md; docs/runbooks/storage-topology.md."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Read-only relation counts for the staged mirror against the live official rows.")
    import_cmd = sub.add_parser(
        "import", help="Build, verify and publish a new generation under the store writer lock."
    )
    import_cmd.add_argument(
        "--expect-staging-sha256",
        required=True,
        help="SHA-256 of the admitted staging file (required), e.g. the admission record's digest.",
    )
    return parser


def main(argv: list[str] | None = None, *, test_data_dir: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        target = writer_target(test_data_dir=test_data_dir)
        payload = plan(target) if args.command == "plan" else run_import(target, args.expect_staging_sha256)
    except Refused as exc:
        print(json.dumps({"status": "refused", "reason": exc.reason, **exc.detail}, ensure_ascii=False))
        return 2
    except PostSwitchFailure as exc:
        print(
            json.dumps(
                {
                    "status": "published_post_switch_failed",
                    "reason": exc.reason,
                    "generation": exc.generation,
                    "previous": exc.previous,
                },
                ensure_ascii=False,
            )
        )
        return 3
    except VerificationFailed as exc:
        print(json.dumps({"status": "verification_failed", "reason": str(exc), **exc.detail}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
