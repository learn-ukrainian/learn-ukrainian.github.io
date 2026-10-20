"""The single writer of ``data/lexdata.db`` (design r3 §3, §6, §9).

One build makes one new, self-contained generation file and swaps it in:

1. Under an exclusive ``flock`` on ``data/lexdata/.build.lock`` the build writes
   L1/L2/L3 and ``meta(status='candidate')`` into
   ``data/lexdata/lexdata.<gen>.db.tmp`` (``journal_mode=DELETE``; never WAL).
2. ``verify`` passes on the temp file; one transaction sets
   ``meta.status='published'`` and ``verify_receipt_sha256``.
3. The connection is closed, no ``-wal``/``-shm``/``-journal`` sidecar may
   remain, and the file is fsynced.
4. The current published generation is copied with the SQLite online backup
   API to ``data/lexdata/backups/`` (two kept; the oldest goes only after the
   new copy passes ``integrity_check``).
5. ``os.replace`` swaps the temp file into ``data/lexdata.db`` and both
   directories are fsynced. Nothing is written to either file afterwards.

L1 of a unit is copied from the published generation (ATTACHed read-only)
only when both its ``unit_input_fingerprint`` and its source's
``l1_transform_digest`` match (§6.1); otherwise every L1 field is re-derived.
L2/L3 are recomputed for every generation; adjudications are carried forward
and invalidated on any input-fingerprint drift (§5.4, §6.2).

L0 stores are resolved with ``resolve_store`` and only ever opened read-only:
parsers get ``open_readonly`` handles, and the build connection ATTACHes the
same validated files with ``mode=ro`` URIs for the L2 stage. Every source's
selection snapshot is taken before any source is read and must be unchanged,
together with the L2 stage's identity-store fingerprints, at the publication
barrier immediately before the swap (§6.6); unrelated L0 writes are allowed.

SQLite temp files (``temp_store=FILE``) go to ``data/lexdata/tmp`` (§9). The
build pins that directory itself and proves it with a forced temp-file probe
before it opens any connection and again at the publication barrier, refusing
otherwise. It cannot rely on ``SQLITE_TMPDIR``: SQLite reads that variable once,
when the ``sqlite3`` module initializes the library, so setting it inside a
running interpreter has no effect.
"""

from __future__ import annotations

import fcntl
import os
import shutil
import sqlite3
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root
from scripts.lexdata import generation as gen_reader
from scripts.lexdata import transforms, verify
from scripts.lexdata.canonical import canonical_json, sha256_canonical, sha256_text
from scripts.lexdata.derive import derive_leaf
from scripts.lexdata.l2_stage import L2Stage, PendingResolverStage
from scripts.lexdata.records import ParsedUnit, SourceAdapter, UnitInput
from scripts.lexdata.schema import FULL_DDL, GENERATION_SCHEMA_VERSION, L1_SCHEMA_VERSION
from scripts.lib.readonly_sqlite import import_named_module, open_readonly
from scripts.storage import topology

STORE_NAME = "lexdata.db"
WORK_DIR = "lexdata"
BACKUPS_KEPT = 2
GiB = 1024 ** 3


class BuildRefused(RuntimeError):
    """The build may not start or must stop; ``reason`` is path-free and stable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class WriterTarget:
    data_dir: Path

    @property
    def published(self) -> Path:
        return self.data_dir / STORE_NAME

    @property
    def work_dir(self) -> Path:
        return self.data_dir / WORK_DIR

    @property
    def lock_path(self) -> Path:
        return self.work_dir / ".build.lock"

    @property
    def tmp_dir(self) -> Path:
        return self.work_dir / "tmp"

    @property
    def reports_dir(self) -> Path:
        return self.work_dir / "reports"

    @property
    def backups_dir(self) -> Path:
        return self.work_dir / "backups"


def _refuse_symlinks(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.is_symlink():
            raise BuildRefused("symlinked_parent")


def writer_target(repository_root: Path | None = None, *, test_data_dir: Path | None = None) -> WriterTarget:
    """The primary checkout's ``data/`` directory, or an explicit test binding.

    Refuses a linked worktree (a worktree never creates the canonical store), a
    symlinked ``data``/``data/lexdata``/``data/lexdata.db``, and a network or
    unknown filesystem.
    """
    if test_data_dir is not None:
        data_dir = test_data_dir
        _refuse_symlinks([data_dir])
    else:
        root = topology.default_repository_root(repository_root)
        primary = main_checkout_root(root.resolve()).resolve()
        if root.resolve() != primary:
            raise BuildRefused("linked_worktree")
        data_dir = primary / "data"
        _refuse_symlinks([data_dir])
    if not data_dir.is_dir():
        raise BuildRefused("data_dir_missing")
    target = WriterTarget(data_dir)
    _refuse_symlinks([target.work_dir, target.published, target.tmp_dir, target.reports_dir, target.backups_dir])
    if topology.store_locality(data_dir.resolve()) != "local":
        raise BuildRefused(f"locality_{topology.store_locality(data_dir.resolve())}")
    return target


@dataclass(frozen=True)
class Admission:
    """§9 budgets. A run refuses to start below peak + reserve and aborts below reserve."""

    peak_budget_bytes: int = 8_500_000_000
    reserve_bytes: int = 20_000_000_000
    rss_cap_bytes: int = 2 * GiB
    batch_rows: int = 5000


def current_rss_bytes() -> int:
    """Resident set size now; fails closed when it cannot be measured."""
    try:
        import psutil  # type: ignore

        return int(psutil.Process().memory_info().rss)
    except Exception:  # fall back to /proc, then refuse
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
        except OSError:
            pass
    raise BuildRefused("rss_unmeasurable")


@dataclass(frozen=True)
class AdjudicationInput:
    """A proposed or admitted adjudication entering a build (§5.4)."""

    item_key: str
    target_lexeme_id: str
    input_fingerprint: str
    evidence: Mapping[str, Any]
    resolver_version: str
    store_fingerprints: Mapping[str, str]
    seat: str
    model: str
    family: str
    harness: str
    receipt: str
    state: str = "proposed"

    def __post_init__(self) -> None:
        if self.state not in {"proposed", "admitted"}:
            raise ValueError("a new adjudication is proposed or admitted")
        for name in ("item_key", "target_lexeme_id", "seat", "model", "family", "harness", "receipt"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"adjudication {name} is required")


@dataclass
class BuildResult:
    generation: str
    published: Path
    size_bytes: int
    diff: dict[str, Any]
    verify_receipt: dict[str, Any]
    peak_rss_bytes: int
    backup: Path | None = None


@dataclass
class _Ids:
    unit: int = 1
    item: int = 1


@dataclass
class _Run:
    target: WriterTarget
    binding: transforms.TransformBinding
    admission: Admission
    conn: Any = None
    rows_since_commit: int = 0
    peak_rss: int = 0
    diff: dict[str, Any] = field(default_factory=dict)

    def checkpoint(self, *, force: bool = False) -> None:
        if not force and self.rows_since_commit < self.admission.batch_rows:
            return
        self.conn.commit()
        self.rows_since_commit = 0
        rss = current_rss_bytes()
        self.peak_rss = max(self.peak_rss, rss)
        if rss > self.admission.rss_cap_bytes:
            raise BuildRefused("rss_cap_exceeded")
        if shutil.disk_usage(self.target.data_dir).free < self.admission.reserve_bytes:
            raise BuildRefused("disk_reserve_reached")


@contextmanager
def build_lock(target: WriterTarget) -> Iterator[None]:
    """Exclusive non-blocking ``flock``: a second writer is refused, never queued."""
    target.work_dir.mkdir(exist_ok=True)
    fd = os.open(target.lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise BuildRefused("build_locked") from None
        yield
    finally:
        os.close(fd)


def _fsync_path(path: Path, *, directory: bool = False) -> None:
    fd = os.open(path, os.O_RDONLY | (os.O_DIRECTORY if directory else 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sidecars(path: Path) -> list[Path]:
    return [Path(f"{path}{suffix}") for suffix in ("-wal", "-shm", "-journal")]


def _remove_stale_temps(target: WriterTarget) -> None:
    for stale in target.work_dir.glob("lexdata.*.db.tmp*"):
        stale.unlink()


def _ro_uri(path: Path) -> str:
    return path.resolve().as_uri() + "?mode=ro"


def _open_build_connection(path: Path, tmp_dir: Path) -> Any:
    """The one read-write connection; refuses unless SQLite temp files land in ``tmp_dir``."""
    assert_sqlite_temp_dir(tmp_dir)
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=rwc", uri=True, isolation_level="DEFERRED")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-262144")
    conn.execute("PRAGMA mmap_size=0")
    conn.execute("PRAGMA temp_store=FILE")
    return conn


TEMP_PROBE_BYTES = 256 * 1024  # spills past a one-page temp cache, so SQLite must open a temp file


def _sqlite_temp_files() -> set[Path]:
    """Paths of the SQLite temp files (``etilqs_*``) this process holds open."""
    try:
        entries = list(Path("/proc/self/fd").iterdir())
    except OSError:
        raise BuildRefused("sqlite_tmpdir_unverifiable") from None
    found: set[Path] = set()
    for entry in entries:
        try:
            target = os.readlink(entry)
        except OSError:  # closed between listing and reading
            continue
        path = Path(target.removesuffix(" (deleted)"))
        if path.name.startswith("etilqs_"):
            found.add(path)
    return found


def _memory_connection() -> Any:
    """A private in-memory connection for process-wide SQLite settings and the temp probe."""
    return sqlite3.connect(":memory:")


def _get_sqlite_temp_dir() -> str:
    conn = _memory_connection()
    try:
        row = conn.execute("PRAGMA temp_store_directory").fetchone()  # no row while unset
        return "" if row is None or row[0] is None else str(row[0])
    finally:
        conn.close()


def _set_sqlite_temp_dir(directory: str) -> None:
    """Set SQLite's process-wide temp directory (``''`` restores the default lookup).

    ``PRAGMA temp_store_directory`` is deprecated upstream, but it is the only
    in-process control: ``SQLITE_TMPDIR`` is read once at library
    initialization. ``assert_sqlite_temp_dir`` proves the effect, so a build
    without the pragma refuses instead of spilling elsewhere.
    """
    conn = _memory_connection()
    try:
        conn.execute("PRAGMA temp_store_directory = '{}'".format(directory.replace("'", "''")))
    finally:
        conn.close()


def assert_sqlite_temp_dir(tmp_dir: Path) -> None:
    """Force a FILE temp table to spill and refuse unless its file is in ``tmp_dir``."""
    before = _sqlite_temp_files()
    conn = _memory_connection()
    try:
        conn.execute("PRAGMA temp_store=FILE")
        conn.execute("PRAGMA temp.cache_size=1")
        conn.execute("CREATE TEMP TABLE lexdata_tmpdir_probe (v BLOB)")
        conn.execute("INSERT INTO lexdata_tmpdir_probe VALUES (zeroblob(?))", (TEMP_PROBE_BYTES,))
        opened = _sqlite_temp_files() - before
    finally:
        conn.close()
    if not opened:
        raise BuildRefused("sqlite_tmpdir_unverifiable")
    if any(path.parent != tmp_dir.resolve() for path in opened):
        raise BuildRefused("sqlite_tmpdir_outside_budget")


@contextmanager
def pinned_sqlite_temp_dir(tmp_dir: Path) -> Iterator[None]:
    """Pin every SQLite temp file of this process to ``tmp_dir`` for the block (§9)."""
    previous = _get_sqlite_temp_dir()
    _set_sqlite_temp_dir(str(tmp_dir.resolve()))
    try:
        assert_sqlite_temp_dir(tmp_dir)
        yield
    finally:
        _set_sqlite_temp_dir(previous)


def _same_selection(a: Any, b: Any) -> bool:
    return (a.query, a.row_count, a.digest) == (b.query, b.row_count, b.digest)


def _assert_inputs_unchanged(adapters: Mapping[str, SourceAdapter], l0: Mapping[str, Any],
                             starts: Mapping[str, Any], stage: L2Stage,
                             store_fingerprints: Mapping[str, str]) -> None:
    """§6.6 over the complete build: every selected snapshot and identity store is unchanged."""
    for source_id in sorted(starts):
        if not _same_selection(adapters[source_id].snapshot(l0), starts[source_id]):
            raise BuildRefused(f"input_snapshot_changed:{source_id}")
    if dict(stage.store_fingerprints(l0)) != dict(store_fingerprints):
        raise BuildRefused("identity_store_changed")


def _load_adapter(spec: transforms.SourceSpec) -> SourceAdapter:
    if not spec.adapter or ":" not in spec.adapter:
        raise BuildRefused(f"adapter_unregistered:{spec.source_id}")
    module_name, attr = spec.adapter.split(":", 1)
    return getattr(import_named_module(module_name), attr)()


def _resolve_stores(names: Iterable[str], repository_root: Path | None,
                    injected: Mapping[str, topology.StoreBinding] | None) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name in sorted(set(names)):
        if name == "lexdata":
            raise BuildRefused("lexdata_is_not_an_l0_store")
        binding = None if injected is None else injected.get(name)
        resolved = topology.resolve_store(name, repository_root, binding=binding)  # type: ignore[arg-type]
        if isinstance(resolved, topology.StoreRefusal):
            raise BuildRefused(f"store_{name}:{resolved.reason}")
        paths[name] = resolved.path
    return paths


def _previous(target: WriterTarget) -> dict[str, Any] | None:
    """Meta of the published generation, or None when there is none to reuse."""
    if not target.published.is_file():
        return None
    conn = open_readonly(target.published)
    try:
        meta = gen_reader.read_meta(conn)
    except gen_reader.MetaMalformed:
        # Carry-forward reads this meta; a silent fresh start would drop adjudications.
        raise BuildRefused("published_meta_malformed") from None
    finally:
        conn.close()
    if meta is None or meta.get("status") != "published":
        return None
    return meta


def _insert_parsed(run: _Run, parsed: ParsedUnit, *, digest: str, spec: transforms.SourceSpec,
                   parser_version: str, ids: _Ids) -> None:
    conn, unit = run.conn, parsed.unit
    unit_id = ids.unit
    ids.unit += 1
    conn.execute(
        "INSERT INTO l1_source_unit (unit_id, source_id, l0_locator, unit_input_fingerprint, l1_transform_digest, "
        "unit_kind, parent_l0_locator) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (unit_id, unit.source_id, unit.l0_locator, unit.unit_input_fingerprint, digest, unit.unit_kind,
         unit.parent_locator))
    conn.executemany("INSERT INTO l1_unit_input VALUES (?, ?, ?)",
                     [(unit_id, row.locator, row.fingerprint) for row in unit.l0_rows])
    conn.execute("INSERT INTO l1_unit_disposition VALUES (?, ?)", (unit_id, parsed.disposition))
    conn.executemany("INSERT INTO l1_line VALUES (?, ?, ?, ?)",
                     [(unit_id, line.line_no, sha256_text(line.raw_line), line.disposition)
                      for line in parsed.lines])
    item_ids: dict[str, int] = {}
    for item in parsed.ordered_items():
        fields = derive_leaf(unit, item, normalizer=run.binding.normalizer.impl, rights_class=spec.rights_class,
                             importer_version=f"{spec.parser_id}/{parser_version}")
        item_id = ids.item
        ids.item += 1
        item_ids[item.local_id] = item_id
        conn.execute(
            "INSERT INTO l1_lex_item (item_id, unit_id, item_key, line_no, span_start, span_end, parent_item_id, "
            "member_index, role, raw_span, surface, key_stressed, key_unstressed, key_fold, case_signal, "
            "grammar_raw, grammar_parsed, homonym_marker, norm_flags, proposed_repairs, refusal_code, "
            "rights_class, row_sha256, importer_version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, unit_id, fields["item_key"], fields["line_no"], fields["span_start"], fields["span_end"],
             None if item.parent is None else item_ids[item.parent], fields["member_index"], fields["role"],
             fields["raw_span"], fields["surface"], fields["key_stressed"], fields["key_unstressed"],
             fields["key_fold"], fields["case_signal"], fields["grammar_raw"], fields["grammar_parsed"],
             fields["homonym_marker"], fields["norm_flags"], fields["proposed_repairs"], fields["refusal_code"],
             fields["rights_class"], fields["row_sha256"], fields["importer_version"]))
        conn.executemany("INSERT INTO l1_sense VALUES (?, ?, ?, ?)",
                         [(item_id, s.sense_no, s.gloss_raw, s.applies_to) for s in item.senses])
        conn.executemany("INSERT INTO l1_example VALUES (?, ?, ?, ?)",
                         [(item_id, e.ex_no, e.uk_raw, e.en_raw) for e in item.examples])
        conn.executemany("INSERT INTO l1_verb_form VALUES (?, ?, ?, ?, ?, ?)",
                         [(item_id, n, f.aspect, f.tense, f.person_number, f.form_raw)
                          for n, f in enumerate(item.verb_forms, 1)])
        conn.executemany("INSERT INTO l1_government VALUES (?, ?, ?)",
                         [(item_id, n, g.pattern_raw) for n, g in enumerate(item.governments, 1)])
    run.rows_since_commit += 1 + len(parsed.items) + len(parsed.lines)


_COPY_UNIT_SQL = (
    "INSERT INTO main.l1_source_unit (unit_id, source_id, l0_locator, unit_input_fingerprint, l1_transform_digest, "
    "unit_kind, parent_l0_locator) SELECT unit_id, source_id, l0_locator, unit_input_fingerprint, "
    "l1_transform_digest, unit_kind, parent_l0_locator FROM prev.l1_source_unit WHERE unit_id = ?1",
    "INSERT INTO main.l1_unit_input SELECT * FROM prev.l1_unit_input WHERE unit_id = ?1",
    "INSERT INTO main.l1_unit_disposition SELECT * FROM prev.l1_unit_disposition WHERE unit_id = ?1",
    "INSERT INTO main.l1_line SELECT * FROM prev.l1_line WHERE unit_id = ?1",
    "INSERT INTO main.l1_lex_item SELECT * FROM prev.l1_lex_item WHERE unit_id = ?1 ORDER BY item_id",
    *(f"INSERT INTO main.{table} SELECT * FROM prev.{table} WHERE item_id IN "
      "(SELECT item_id FROM prev.l1_lex_item WHERE unit_id = ?1)"
      for table in ("l1_sense", "l1_example", "l1_verb_form", "l1_government")),
)


def _copy_unit(run: _Run, prev_unit_id: int) -> None:
    """Copy one unit's L1 rows unchanged (digests matched), keeping their ids."""
    for sql in _COPY_UNIT_SQL:
        run.conn.execute(sql, (prev_unit_id,))
    run.rows_since_commit += 1 + run.conn.execute(
        "SELECT count(*) FROM main.l1_lex_item WHERE unit_id = ?", (prev_unit_id,)).fetchone()[0]


def _build_source(run: _Run, adapter: SourceAdapter, spec: transforms.SourceSpec, l0: Mapping[str, Any],
                  start: Any, digest: str, has_prev: bool, ids: _Ids) -> dict[str, Any]:
    parser = run.binding.parsers[spec.parser_id]
    counts: Counter[str] = Counter()
    seen: list[str] = []
    for unit in adapter.iter_units(l0):
        if not isinstance(unit, UnitInput) or unit.source_id != spec.source_id:
            raise BuildRefused(f"adapter_unit_mismatch:{spec.source_id}")
        seen.append(unit.l0_locator)
        prev = None
        if has_prev:
            prev = run.conn.execute(
                "SELECT unit_id, unit_input_fingerprint, l1_transform_digest FROM prev.l1_source_unit "
                "WHERE source_id = ? AND l0_locator = ?", (spec.source_id, unit.l0_locator)).fetchone()
        if prev is not None and prev[1] == unit.unit_input_fingerprint and prev[2] == digest:
            _copy_unit(run, prev[0])
            counts["reused"] += 1
        else:
            parsed = adapter.parse(unit)
            if not isinstance(parsed, ParsedUnit) or parsed.unit != unit:
                raise BuildRefused(f"adapter_parse_mismatch:{spec.source_id}")
            _insert_parsed(run, parsed, digest=digest, spec=spec, parser_version=parser.version, ids=ids)
            counts["reparsed"] += 1
            counts["new" if prev is None else "transform_changed" if prev[2] != digest else "input_changed"] += 1
        run.checkpoint()
    if not _same_selection(adapter.snapshot(l0), start):  # early stop; the barrier re-checks every source
        raise BuildRefused(f"input_snapshot_changed:{spec.source_id}")
    tombstoned = 0
    if has_prev:
        current = set(seen)
        tombstoned = sum(1 for (locator,) in run.conn.execute(
            "SELECT l0_locator FROM prev.l1_source_unit WHERE source_id = ?", (spec.source_id,))
            if locator not in current)
    return {
        "snapshot": start.as_json(),
        "units": len(seen),
        "reused_units": counts["reused"],
        "reparsed_units": counts["reparsed"],
        "reparse_reasons": {k: counts[k] for k in ("new", "input_changed", "transform_changed") if counts[k]},
        "tombstoned_units": tombstoned,
    }


def _link_and_adjudicate(run: _Run, stage: L2Stage, has_prev: bool,
                         adjudications: Sequence[AdjudicationInput]) -> dict[str, int]:
    conn = run.conn
    stage.link(conn)
    for (link_id,) in conn.execute("SELECT link_id FROM l2_link ORDER BY link_id").fetchall():
        conn.execute("UPDATE l2_link SET candidate_set_sha256 = ? WHERE link_id = ?",
                     (verify.candidate_set_sha256(conn, link_id), link_id))
    carried: list[dict[str, Any]] = []
    if has_prev:
        cursor = conn.execute("SELECT * FROM prev.l2_adjudication ORDER BY adjudication_id")
        names = [column[0] for column in cursor.description]
        carried = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
    for new in adjudications:
        carried.append({
            "item_key": new.item_key, "target_lexeme_id": new.target_lexeme_id,
            "evidence": canonical_json(dict(new.evidence)), "input_fingerprint": new.input_fingerprint,
            "resolver_version": new.resolver_version,
            "store_fingerprints": canonical_json(dict(new.store_fingerprints)), "seat": new.seat,
            "model": new.model, "family": new.family, "harness": new.harness, "receipt": new.receipt,
            "state": new.state, "invalidated_reason": None,
        })
    states: Counter[str] = Counter()
    admitted: dict[int, tuple[str, int]] = {}
    invalidated: set[int] = set()
    for adj in carried:
        # Judged against the stage's own result, before any adjudication applies.
        found = conn.execute(
            "SELECT l.link_id, i.row_sha256, l.candidate_set_sha256, l.status FROM l1_lex_item i "
            "JOIN l2_link l USING (item_id) WHERE i.item_key = ?", (adj["item_key"],)).fetchone()
        state, reason = adj["state"], adj["invalidated_reason"]
        link_id = None if found is None else found[0]
        if state != "invalidated":
            if found is None:
                state, reason = "invalidated", "leaf_absent"
            elif verify.adjudication_input_fingerprint(found[1], found[2]) != adj["input_fingerprint"]:
                state, reason = "invalidated", "input_fingerprint_drift"
            elif not conn.execute("SELECT 1 FROM l2_candidate WHERE link_id = ? AND lexeme_id = ? "
                                  "AND dropped_by_rule IS NULL", (link_id, adj["target_lexeme_id"])).fetchone():
                state, reason = "invalidated", "target_not_candidate"
        cursor = conn.execute(
            "INSERT INTO l2_adjudication (item_key, link_id, target_lexeme_id, evidence, input_fingerprint, "
            "resolver_version, store_fingerprints, seat, model, family, harness, receipt, state, "
            "invalidated_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (adj["item_key"], link_id, adj["target_lexeme_id"], adj["evidence"], adj["input_fingerprint"],
             adj["resolver_version"], adj["store_fingerprints"], adj["seat"], adj["model"], adj["family"],
             adj["harness"], adj["receipt"], state, reason))
        states[state] += 1
        if found is None or found[3] in {"refused", "unavailable"}:
            continue
        if state == "invalidated":
            invalidated.add(found[0])
        elif state == "admitted" and found[3] == "held":
            # Only a held link is resolved by adjudication (§7.1); the latest admitted one wins.
            admitted[found[0]] = (adj["target_lexeme_id"], int(cursor.lastrowid))
    for link_id, (lexeme_id, adjudication_id) in admitted.items():
        conn.execute("UPDATE l2_link SET lexeme_id = ?, adjudication_id = ? WHERE link_id = ?",
                     (lexeme_id, adjudication_id, link_id))
    for link_id in invalidated - set(admitted):
        conn.execute("UPDATE l2_link SET status = 'held', hold_reason = 'adjudication_invalidated', "
                     "unavailable_reason = NULL, lexeme_id = NULL, adjudication_id = NULL WHERE link_id = ?",
                     (link_id,))
    return dict(sorted(states.items()))


def _backup_published(target: WriterTarget, generation_id: str) -> Path | None:
    """Online backup of the current published generation, then rotate (§6.5 step 4)."""
    if not target.published.is_file():
        return None
    target.backups_dir.mkdir(exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = target.backups_dir / f"lexdata-{generation_id}-{stamp}.db"
    source = open_readonly(target.published)
    copy = sqlite3.connect(destination)
    try:
        source.backup(copy)
        if copy.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise BuildRefused("backup_integrity_failed")
        copy.execute("PRAGMA journal_mode=DELETE")
    except BaseException:
        copy.close()
        destination.unlink(missing_ok=True)
        raise
    finally:
        source.close()
    copy.close()
    _fsync_path(destination)
    backups = sorted(target.backups_dir.glob("lexdata-*.db"), key=lambda p: p.stat().st_mtime_ns)
    for old in backups[:-BACKUPS_KEPT]:
        old.unlink()
    return destination


def _write_report(target: WriterTarget, name: str, payload: Mapping[str, Any]) -> None:
    target.reports_dir.mkdir(exist_ok=True)
    path = target.reports_dir / name
    path.write_text(canonical_json(dict(payload)), encoding="utf-8")
    _fsync_path(path)


def build(
    target: WriterTarget,
    *,
    binding: transforms.TransformBinding = transforms.DEFAULT_BINDING,
    adapters: Mapping[str, SourceAdapter] | None = None,
    l2_stage: L2Stage | None = None,
    adjudications: Sequence[AdjudicationInput] = (),
    stores: Mapping[str, topology.StoreBinding] | None = None,
    repository_root: Path | None = None,
    admission: Admission | None = None,
) -> BuildResult:
    """Build, verify and publish one generation. Raises ``BuildRefused`` on any stop."""
    admission = admission or Admission()
    transforms.assert_registry_closed(binding)
    stage = l2_stage or PendingResolverStage()
    sources = sorted(binding.sources)
    if adapters is None:
        adapters = {source_id: _load_adapter(binding.sources[source_id]) for source_id in sources}
    if set(adapters) != set(sources):
        raise BuildRefused("adapters_do_not_match_registered_sources")
    for source_id, adapter in adapters.items():
        if adapter.source_id != source_id or adapter.parser_id != binding.sources[source_id].parser_id:
            raise BuildRefused(f"adapter_identity_mismatch:{source_id}")

    with build_lock(target), ExitStack() as stack:
        _remove_stale_temps(target)
        if shutil.disk_usage(target.data_dir).free < admission.peak_budget_bytes + admission.reserve_bytes:
            raise BuildRefused("disk_admission_refused")
        target.tmp_dir.mkdir(exist_ok=True)
        _refuse_symlinks([target.tmp_dir])
        stack.enter_context(pinned_sqlite_temp_dir(target.tmp_dir))
        store_paths = _resolve_stores([s for a in adapters.values() for s in a.stores] + list(stage.stores),
                                      repository_root, stores)
        l0 = {}
        for name, path in store_paths.items():
            l0[name] = open_readonly(path)
            stack.callback(l0[name].close)
        starts = {source_id: adapters[source_id].snapshot(l0) for source_id in sources}
        digests = {source_id: transforms.transform_digest(source_id, binding) for source_id in sources}
        manifests = {source_id: transforms.transform_manifest(source_id, binding) for source_id in sources}
        normalizer_manifest = transforms.normalizer_manifest(binding)
        prev_meta = _previous(target)
        seq = 1 if prev_meta is None else int(prev_meta["generation_seq"]) + 1
        created = datetime.now(UTC)
        generation_id = f"g{seq:06d}-{created.strftime('%Y%m%dT%H%M%SZ')}"
        tmp = target.work_dir / f"lexdata.{generation_id}.db.tmp"
        run = _Run(target, binding, admission)
        try:
            run.conn = _open_build_connection(tmp, target.tmp_dir)
            run.conn.executescript(FULL_DDL)
            for name, path in store_paths.items():
                run.conn.execute(f"ATTACH DATABASE ? AS src_{name}", (_ro_uri(path),))
            has_prev = prev_meta is not None
            ids = _Ids()
            if has_prev:
                run.conn.execute("ATTACH DATABASE ? AS prev", (_ro_uri(target.published),))
                ids.unit = run.conn.execute("SELECT coalesce(max(unit_id), 0) + 1 FROM prev.l1_source_unit").fetchone()[0]
                ids.item = run.conn.execute("SELECT coalesce(max(item_id), 0) + 1 FROM prev.l1_lex_item").fetchone()[0]
            per_source = {source_id: _build_source(run, adapters[source_id], binding.sources[source_id], l0,
                                                   starts[source_id], digests[source_id], has_prev, ids)
                          for source_id in sources}
            run.conn.execute(
                "UPDATE l1_source_unit SET parent_unit_id = (SELECT p.unit_id FROM l1_source_unit p "
                "WHERE p.source_id = l1_source_unit.source_id AND p.l0_locator = l1_source_unit.parent_l0_locator) "
                "WHERE parent_l0_locator IS NOT NULL")
            dropped_sources = []
            if has_prev:
                dropped_sources = [row[0] for row in run.conn.execute(
                    "SELECT source_id, count(*) FROM prev.l1_source_unit GROUP BY source_id ORDER BY source_id")
                    if row[0] not in per_source]
                for source_id in dropped_sources:
                    per_source[source_id] = {"units": 0, "reused_units": 0, "reparsed_units": 0,
                                             "reparse_reasons": {}, "tombstoned_units": run.conn.execute(
                                                 "SELECT count(*) FROM prev.l1_source_unit WHERE source_id = ?",
                                                 (source_id,)).fetchone()[0]}
            run.checkpoint(force=True)
            store_fingerprints = dict(stage.store_fingerprints(l0))
            adjudication_states = _link_and_adjudicate(run, stage, has_prev, adjudications)
            input_manifest = {
                "sources": {s: {"parser_id": binding.sources[s].parser_id, **per_source[s]["snapshot"]}
                            for s in sources},
                "stores": sorted(store_paths),
                "adjudication_inputs": len(adjudications),
                "previous_generation": None if prev_meta is None else prev_meta["generation"],
            }
            run.diff = {"previous_generation": input_manifest["previous_generation"],
                        "sources": {s: {k: v for k, v in d.items() if k != "snapshot"}
                                    for s, d in sorted(per_source.items())},
                        "dropped_sources": dropped_sources, "adjudications": adjudication_states}
            run.conn.execute(
                "INSERT INTO meta VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', NULL)",
                (generation_id, seq, GENERATION_SCHEMA_VERSION, L1_SCHEMA_VERSION, created.isoformat(),
                 canonical_json(input_manifest), sha256_canonical(input_manifest), canonical_json(manifests),
                 canonical_json(digests), canonical_json(normalizer_manifest),
                 sha256_canonical(normalizer_manifest), canonical_json(store_fingerprints), stage.resolver_version,
                 canonical_json(run.diff)))
            run.checkpoint(force=True)
            if has_prev:
                run.conn.execute("DETACH DATABASE prev")
            for name in store_paths:
                run.conn.execute(f"DETACH DATABASE src_{name}")

            # §6.5 step 2: verify the temp file, then publish its meta in one transaction.
            report = verify.verify_generation(run.conn, binding=binding, expect_status="candidate")
            receipt = report.receipt()
            _write_report(target, f"verify-{generation_id}.json", receipt)
            if not report.ok:
                raise BuildRefused("verify_failed")
            with run.conn:
                run.conn.execute("UPDATE meta SET status = 'published', verify_receipt_sha256 = ? "
                                 "WHERE singleton = 1", (report.receipt_sha256(),))
            # Step 3: self-contained file, no sidecar, synced.
            if run.conn.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
                raise BuildRefused("journal_mode_not_delete")
            run.conn.close()
            run.conn = None
            if any(path.exists() for path in _sidecars(tmp)):
                raise BuildRefused("sidecar_remains")
            _fsync_path(tmp)
            _write_report(target, f"build-{generation_id}.json", {
                "generation": generation_id, "diff": run.diff, "verify_receipt_sha256": report.receipt_sha256(),
                "peak_rss_bytes": run.peak_rss, "size_bytes": tmp.stat().st_size, "status": "verified_pre_swap"})
            # Step 4: back up the current published generation.
            backup = _backup_published(target, prev_meta["generation"]) if prev_meta else None
            # Publication barrier (§6.6, §9): after the last L0 read, before the swap.
            _assert_inputs_unchanged(adapters, l0, starts, stage, store_fingerprints)
            assert_sqlite_temp_dir(target.tmp_dir)
            # Step 5: atomic swap; nothing is written to either file after it.
            if tmp.stat().st_dev != target.data_dir.stat().st_dev:
                raise BuildRefused("cross_device_swap")
            size = tmp.stat().st_size
            os.replace(tmp, target.published)
            _fsync_path(target.data_dir, directory=True)
            _fsync_path(target.work_dir, directory=True)
            return BuildResult(generation_id, target.published, size, run.diff, receipt, run.peak_rss, backup)
        except BaseException:
            if run.conn is not None:
                run.conn.close()
            for path in (tmp, *_sidecars(tmp)):
                path.unlink(missing_ok=True)
            raise
