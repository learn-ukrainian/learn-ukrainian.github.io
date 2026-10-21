"""Synthetic L0 stores, a fixture source adapter and a fixture L2 stage for lexdata tests.

Every SQLite file here is a hermetic scratch fixture under ``tmp_path``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from scripts.lexdata import build_store, transforms
from scripts.lexdata.canonical import sha256_file
from scripts.storage import topology
from tests.lexdata.fixture_parser import FIXTURE_PARSER, FIXTURE_SOURCE, FixtureAdapter

NO_BUDGET = build_store.Admission(peak_budget_bytes=0, reserve_bytes=0)
TEST_MODULE = "tests/lexdata/fixture_parser.py"


def make_sqlite(path: Path, script: str, rows: Iterable[tuple[str, tuple[Any, ...]]] = ()) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(script)
        for sql, params in rows:
            conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
    return path


def make_sources(path: Path, words: Mapping[int, str]) -> Path:
    return make_sqlite(path, "CREATE TABLE fixture_words (id INTEGER PRIMARY KEY, word TEXT NOT NULL);",
                       [("INSERT INTO fixture_words VALUES (?, ?)", (k, v)) for k, v in sorted(words.items())])


def mutate_sqlite(path: Path, sql: str, params: tuple[Any, ...] = ()) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


@dataclass
class FixtureStage:
    """Deterministic stand-in for the slice (e) resolver.

    ``candidates`` maps key_fold to [(lexeme_id, eligibility)]; keys in ``held``
    become ``held:unknown_competitor``. List parents are ``split``.
    """

    candidates: Mapping[str, list[tuple[str, str]]] = field(default_factory=dict)
    held: frozenset[str] = frozenset()
    resolver_version: str = "fixture-resolver/1"
    stores: tuple[str, ...] = ()
    fingerprints: Mapping[str, str] = field(default_factory=dict)

    def store_fingerprints(self, l0: Mapping[str, Any]) -> dict[str, str]:
        return dict(self.fingerprints)

    def link(self, conn: Any) -> None:
        rows = conn.execute(
            "SELECT i.item_id, i.key_stressed, i.key_unstressed, i.key_fold, i.refusal_code, "
            "(SELECT count(*) FROM l1_lex_item c WHERE c.parent_item_id = i.item_id) "
            "FROM l1_lex_item i ORDER BY i.item_id").fetchall()
        for item_id, ks, ku, kf, refusal, children in rows:
            cands = [] if refusal else list(self.candidates.get(kf, []))
            eligible = [c for c in cands if c[1] == "eligible"]
            unknown = [c for c in cands if c[1] == "unknown"]
            lexeme, hold = None, None
            if refusal:
                status = "refused"
            elif children >= 2:
                status, cands = "split", []
            elif kf in self.held:
                status, hold = "held", "unknown_competitor"
            elif len(eligible) == 1 and not unknown:
                status, lexeme = "exact", eligible[0][0]
            elif len(eligible) > 1:
                status = "ambiguous"
            elif unknown:
                status, hold = "held", "unknown_competitor"
            else:
                status = "unmatched"
            cursor = conn.execute(
                "INSERT INTO l2_link (item_id, key_stressed, key_unstressed, key_fold, status, hold_reason, "
                "lexeme_id, resolver_version) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, ks, ku, kf, status, hold, lexeme, self.resolver_version))
            conn.executemany(
                "INSERT INTO l2_candidate (link_id, lexeme_id, eligibility, entry_fingerprint) VALUES (?, ?, ?, ?)",
                [(cursor.lastrowid, lex, elig, "e" * 64) for lex, elig in cands])


def fixture_binding(normalizer: transforms.NormalizerBinding | None = None,
                    expected_units: int | None = None) -> transforms.TransformBinding:
    base = transforms.TransformBinding()
    return replace(
        base,
        normalizer=normalizer or base.normalizer,
        parsers={FIXTURE_PARSER: transforms.ParserSpec(FIXTURE_PARSER, "1", (TEST_MODULE,))},
        sources={FIXTURE_SOURCE: transforms.SourceSpec(FIXTURE_SOURCE, FIXTURE_PARSER, "fixture_internal",
                                                       expected_units=expected_units)},
    )


@dataclass
class Harness:
    """A fixture repository root (``scripts/`` + ``data/``) and a synthetic sources store.

    Store resolution is anchored at the fixture root, never at the calling
    worktree (whose own ``data/*.db`` would correctly be refused).
    """

    repository_root: Path
    sources_path: Path

    @property
    def data_dir(self) -> Path:
        return self.repository_root / "data"

    @property
    def target(self) -> build_store.WriterTarget:
        return build_store.writer_target(test_data_dir=self.data_dir)

    def stores(self) -> dict[str, topology.StoreBinding]:
        return {"sources": topology.StoreBinding("sources", self.sources_path)}

    def build(self, *, binding: transforms.TransformBinding | None = None, stage: Any = None,
              adapter: Any = None, adjudications=(), admission=NO_BUDGET) -> build_store.BuildResult:
        return build_store.build(self.target, binding=binding or fixture_binding(),
                                 adapters={FIXTURE_SOURCE: adapter or FixtureAdapter()}, l2_stage=stage,
                                 adjudications=adjudications, stores=self.stores(),
                                 repository_root=self.repository_root, admission=admission)

    def published_sha(self) -> str:
        return sha256_file(self.target.published)
