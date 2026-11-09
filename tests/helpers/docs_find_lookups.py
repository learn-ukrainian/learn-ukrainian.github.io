"""The development lookups of scripts/docs/find.py (#9412), shared by the gates that rank them.

``tests/fixtures/docs_find_dev_lookups.yaml`` holds resources, documents, data stores, status
("is X current, what replaced it?") and process ("where is X implemented?") questions, each with
its authority path and the evidence that it is that authority;
``tests/fixtures/docs_find_dev_lookups_natural.yaml`` holds natural wording that avoids the
answer's own name, with a blind one-shot query. The held-out acceptance lookups are separate and
never used here.

One search of the whole tree takes about 3 s and keeps a 4-core CI runner busy on its own, so
the top-n sweep over both sets (about 270 searches) is split into ``PART_COUNT`` files,
``tests/test_docs_find_lookups_part<k>.py``, which the CI shard splitter places on different
shards (docs/runbooks/ci-gate.md, "pytest shards"). Each test ranks one lookup, so no test nears
the per-test timeout.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.docs.find import find

REPO = Path(__file__).resolve().parents[2]
DEV_LOOKUPS = yaml.safe_load((REPO / 'tests/fixtures/docs_find_dev_lookups.yaml').read_text(encoding='utf-8'))
NATURAL_LOOKUPS = yaml.safe_load((REPO / 'tests/fixtures/docs_find_dev_lookups_natural.yaml').read_text(encoding='utf-8'))
SETS = {'dev': DEV_LOOKUPS, 'natural': NATURAL_LOOKUPS}
DEV_KINDS = {'resource', 'doc', 'data_store', 'status', 'process'}
FIELDS = ('query', 'question')
PART_COUNT = 8


def verify_command(check: dict) -> list[str]:
    return ['git', '-C', str(REPO), 'grep', '--cached', '-n', '-F', '-i', '-e', check['contains'], '--', check['path']]


def rank(lookup: dict, field: str, limit: int | None = 50) -> int | None:
    """1-based rank of the first expected path among the hits, or None when none is listed.

    ``limit=None`` searches at the CLI's own default limit, whose read pool is the one a reader gets.
    """
    # Ranking, not latency, is measured here: a loaded CI runner must not cut the search short.
    args = (lookup[field],) if limit is None else (lookup[field], limit)
    result = find(*args, repo=REPO, budget_seconds=60)
    assert not result['coverage']['incomplete'], (lookup['id'], result['coverage']['incomplete_reasons'])
    paths = [hit['path'] for hit in result['hits']]
    return min((paths.index(p) + 1 for p in lookup['expect'] if p in paths), default=None)


def known_miss(name: str, lookup: dict, field: str) -> bool:
    return field in SETS[name]['known_misses'].get(lookup['id'], {})


def top_n_lookups() -> list[tuple[str, str, dict]]:
    """``(set, field, lookup)`` for every lookup the top-n sweep ranks, in fixture order.

    The dev set's multi-answer lookups (``gate:``) are ranked by their own gate in
    tests/test_docs_catalogue_coverage.py. The natural set's known misses are still searched (the
    search must be complete); only their rank is not held.
    """
    dev = [lk for lk in DEV_LOOKUPS['lookups'] if lk['id'] not in DEV_LOOKUPS['known_misses'] and 'gate' not in lk]
    return [(name, field, lk) for name, lookups in (('dev', dev), ('natural', NATURAL_LOOKUPS['lookups']))
            for field in FIELDS for lk in lookups]


def part(index: int) -> list:
    """The ``index``-th (1-based) of ``PART_COUNT`` interleaved slices of the sweep, as test parameters."""
    assert 1 <= index <= PART_COUNT
    return [pytest.param(name, field, lk, id=f'{name}-{field}-{lk["id"]}')
            for name, field, lk in top_n_lookups()[index - 1::PART_COUNT]]


def assert_answered_in_one_query(name: str, field: str, lookup: dict) -> None:
    bar = SETS[name]['top_n'][field]
    found = rank(lookup, field)
    if known_miss(name, lookup, field):
        return
    assert found is not None and found <= bar, (
        f'{name} {lookup["id"]}: expected path not within the first {bar} hits for {lookup[field]!r} (rank {found})')
