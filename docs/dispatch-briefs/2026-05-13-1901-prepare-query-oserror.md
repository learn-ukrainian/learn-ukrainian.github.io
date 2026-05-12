# Codex dispatch — #1901 textbook_grounding root cause: `_prepare_query` OSError swallow

**Issue:** [#1901](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1901)
**Filed by orchestrator (Claude) after 2026-05-13 morning diagnosis**
**Severity:** HARD blocker for A1 batch build (`a1/my-morning` cannot republish until this lands)
**Estimated effort:** 30-60 min (5-line bug fix + regression test + #1901 issue update)

## Verifiable claims this dispatch will produce (per #M-4)

| Claim | Tool that proves it | Expected output format |
|---|---|---|
| Bug reproduced before fix | `PYTHONPATH=scripts .venv/bin/python -c "..."` running the failing query | Raw `OSError: [Errno 63] File name too long` text |
| Fix applied to `scripts/wiki/sources_db.py:_prepare_query` | `git diff scripts/wiki/sources_db.py` | Diff hunk showing try/except OSError + bounded length check |
| Test added that exercises the OSError path | `.venv/bin/python -m pytest tests/test_sources_db_prepare_query.py -v` | `1 passed` line in pytest summary |
| All existing tests still pass | `.venv/bin/python -m pytest tests/test_sources_db*.py tests/test_textbook_grounding*.py -v` | Pytest summary line raw |
| Ruff clean | `.venv/bin/ruff check scripts/wiki/sources_db.py tests/test_sources_db_prepare_query.py` | `All checks passed!` raw |
| PR opened | `gh pr view <N> --json url` | Raw URL line |

Quote raw command output for each. "I checked X" without raw output is treated as hallucination per #M-4.

## The bug, reproduced

**Empirical repro (run from repo root):**

```bash
PYTHONPATH=scripts .venv/bin/python -c "
from wiki.sources_db import _prepare_query
plan_title = 'Караман Grade 10, p.176'
plan_topic = 'Мій ранок Прокидаюся, вмиваюся — зворотні дієслова та ранкова рутина Діалоги Діалог 1 — Ранкова рутина: — Коли ти прокидаєшся? — Я прокидаюся о сьомій. — Що ти робиш потім? — Вмиваюся, одягаюся і снідаю. ' * 3
query = f'{plan_title} {plan_topic}'
print(f'query length: {len(query)} chars')
_prepare_query(query, 'a1')  # raises OSError
"
```

Expected output BEFORE fix:
```
query length: <some N >= ~280 bytes>
Traceback (most recent call last):
  ...
OSError: [Errno 63] File name too long: 'Караман Grade 10, p.176 Мій ранок ...'
```

After fix the same script must run cleanly and return a tuple `(list, set, str)`.

**Why this matters for the curriculum:**

In `scripts/build/linear_pipeline.py:_build_textbook_excerpt_context` (line 786-827), the function builds a query as `f"{title} {topic_query}"` for each plan reference. `topic_query` (line 726-737) concatenates plan title + subtitle + every section name + first 3 points per section — easily >1 KB for realistic plans. When this hits `_prepare_query` → `Path(query).exists()` → OSError → swallowed by outer `try/except Exception: return []` (line 773-774 of `linear_pipeline.py`) → `_search_textbook_hits` returns `[]` → caller sets `ref["corpus_missing"] = True` for that reference. Result: **every** plan reference gets falsely marked `corpus_missing`, the `textbook_grounding` HARD gate fails with `reason=corpus_missing`, and the module is rejected even when the textbook page DOES exist in the corpus.

Direct DB verification of the bakeoff's "missing" pages:
```
karaman G10 p.176:    2 chunks indexed
kravtsova G4 p.113:   1 chunk indexed
zaharijchuk G4 p.162: 0 chunks indexed
```

Two of three pages cited in the failed bakeoff (`audit/bakeoff-2026-05-12-night/claude.python_qg.json`) are actually in the corpus. The gate's false-positive is the bug.

## The fix

`scripts/wiki/sources_db.py`, function `_prepare_query` at line 344-363:

**Current:**
```python
def _prepare_query(query: str | Path, track: str) -> tuple[list[str], set[str], str]:
    candidate_path = Path(query)
    if candidate_path.exists():
        bucket_a_phrases, bucket_b_keywords = build_query_buckets(candidate_path, track)
        return bucket_a_phrases, bucket_b_keywords, _build_dense_query(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_path.stem.replace("-", " "),
        )
    ...
```

**Fix (bounded path check + OSError guard):**
```python
# Per-component path length limit is ~255 bytes on macOS HFS+/APFS and most
# Linux filesystems. Long Cyrillic plan-topic concatenations (>1 KB) trigger
# OSError "File name too long" inside candidate_path.exists(). Caller swallows
# the OSError and returns no hits, falsely marking every plan reference as
# `corpus_missing` in the textbook_grounding gate (#1901). Bound the check
# upfront and guard the syscall.
_MAX_PATH_PROBE_BYTES = 255

def _prepare_query(query: str | Path, track: str) -> tuple[list[str], set[str], str]:
    candidate_path = Path(query)
    is_path = False
    if isinstance(query, Path) or len(str(query).encode("utf-8")) <= _MAX_PATH_PROBE_BYTES:
        try:
            is_path = candidate_path.exists()
        except OSError:
            is_path = False
    if is_path:
        bucket_a_phrases, bucket_b_keywords = build_query_buckets(candidate_path, track)
        return bucket_a_phrases, bucket_b_keywords, _build_dense_query(
            bucket_a_phrases,
            bucket_b_keywords,
            candidate_path.stem.replace("-", " "),
        )
    ...
```

The byte-length check (`encode("utf-8")`) is correct for Cyrillic — `len(str)` counts code points, not the bytes the OS will use. The defense-in-depth `try/except OSError` handles edge cases (very deep paths, exotic filesystems).

## Regression test

Create `tests/test_sources_db_prepare_query.py`:

```python
"""Regression tests for scripts/wiki/sources_db.py:_prepare_query.

Bug context: a >255-byte query string (typical for plan-driven textbook
excerpt retrieval) caused Path(query).exists() to raise OSError "File name
too long", which propagated past the outer try/except in linear_pipeline
and falsely marked every textbook reference as corpus_missing. See #1901.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from wiki.sources_db import _prepare_query  # noqa: E402


def test_long_cyrillic_query_does_not_raise() -> None:
    """A >1 KB Cyrillic query (realistic for plan-driven textbook search)
    must not raise OSError. It should be treated as a free-text query."""
    long_query = (
        "Караман Grade 10, p.176 Мій ранок Прокидаюся, вмиваюся — "
        "зворотні дієслова та ранкова рутина Діалоги Діалог 1 — Ранкова рутина: "
        "— Коли ти прокидаєшся? — Я прокидаюся о сьомій. — Що ти робиш потім? "
    ) * 6
    assert len(long_query.encode("utf-8")) > 255, "test fixture too short"

    bucket_a, bucket_b, dense = _prepare_query(long_query, track="a1")

    assert isinstance(bucket_a, list)
    assert isinstance(bucket_b, set)
    assert isinstance(dense, str)
    assert dense  # non-empty fallback


def test_existing_path_still_resolved_as_file() -> None:
    """If the query IS a real path (under the byte limit), the existing
    file-as-query branch must still fire."""
    discovery = REPO_ROOT / "curriculum" / "l2-uk-en" / "a1" / "discovery" / "my-morning.yaml"
    if not discovery.exists():
        pytest.skip("discovery fixture missing")

    # Should not raise; the function should take the Path branch.
    result = _prepare_query(discovery, track="a1")
    assert result is not None


def test_short_string_query_treated_as_text() -> None:
    """A short string that is not a real path stays a text query."""
    bucket_a, bucket_b, dense = _prepare_query("дієслова -ся", track="a1")
    assert dense == "дієслова -ся" or "дієслова" in dense
```

If `build_query_buckets` rejects the bare-string call, adapt the assertions but keep the `OSError`-must-not-raise contract intact. The load-bearing test is `test_long_cyrillic_query_does_not_raise`.

## Stale-comment cleanup (sibling-finder, per fix-then-prevent)

Once the bug is gone, the workaround comment in `scripts/build/pilot_uk_lesson.py:39-44` becomes false. Update it to:

```python
    # search_sources' _prepare_query now bounds the Path(query).exists() probe
    # by byte length (#1901 fix), so no 120-char workaround is needed. Still
    # cap the query length for relevance: very long queries dilute FTS scoring.
    query = " ".join(p.strip() for p in query_parts if p)
    query = " ".join(query.split())  # collapse whitespace
    query = query[:120]  # keep for FTS relevance, not for OSError avoidance
```

This is a tiny doc-only change in the same PR — proves the fix lands at the right layer.

## #1901 issue body update

After the PR is merged, comment on #1901 with:

```
Root cause was a 5-line OSError swallow bug in `scripts/wiki/sources_db.py:_prepare_query`,
NOT a writer-prompt issue. `Path(query).exists()` raised `OSError: File name too long`
on any plan-driven textbook query (>255 bytes Cyrillic), which got swallowed by the
outer `try/except Exception: return []` in `_search_textbook_hits` and falsely marked
every plan reference as `corpus_missing`.

Verified empirically:
- karaman G10 p.176: 2 chunks in corpus (bakeoff said missing)
- kravtsova G4 p.113: 1 chunk in corpus (bakeoff said missing)
- zaharijchuk G4 p.162: 0 chunks (genuinely absent — only 1 of 3)

Fixed in PR #<N> by bounding the path probe to 255 bytes and adding try/except OSError.
Regression test in tests/test_sources_db_prepare_query.py.

Path A (corpus expansion for zaharijchuk G4 p.162) is still warranted but no longer
blocking — `corpus_missing` is now meaningful again, not 100% false positive.
Path B (corpus-aware writer prompt) is downgraded from "recommended" to "optional
hardening" — the gate now correctly distinguishes real corpus misses from query-format
issues.

Closes #1901 (the original textbook_grounding HARD blocker).
```

## Dispatch checklist (per MEMORY DISPATCH-BRIEF CHECKLIST)

1. **Worktree setup:**
   ```bash
   git worktree add .worktrees/dispatch/codex/1901-prepare-query-oserror -b codex/1901-prepare-query-oserror origin/main
   cd .worktrees/dispatch/codex/1901-prepare-query-oserror
   ```
2. **File-level work:**
   - Edit `scripts/wiki/sources_db.py` per the fix above.
   - Create `tests/test_sources_db_prepare_query.py` per the test above.
   - Edit `scripts/build/pilot_uk_lesson.py` line 39-44 stale comment.
3. **Test suite (mandatory, per #M-7):**
   ```bash
   .venv/bin/python -m pytest tests/test_sources_db_prepare_query.py -v
   .venv/bin/python -m pytest tests/test_sources_db*.py tests/test_textbook_grounding*.py -v 2>&1 | tail -20
   ```
   Quote raw output of both in the PR description.
4. **Ruff:**
   ```bash
   .venv/bin/ruff check scripts/wiki/sources_db.py scripts/build/pilot_uk_lesson.py tests/test_sources_db_prepare_query.py
   .venv/bin/ruff format scripts/wiki/sources_db.py scripts/build/pilot_uk_lesson.py tests/test_sources_db_prepare_query.py
   ```
5. **Commit (conventional, atomic):**
   ```
   fix(sources_db): bound Path(query).exists() probe to avoid OSError swallow (#1901)

   Plan-driven textbook queries (>255 bytes Cyrillic) caused OSError "File name
   too long" inside _prepare_query's Path.exists() check. Outer try/except in
   _search_textbook_hits swallowed it and returned no hits, falsely marking
   every plan reference as corpus_missing in the textbook_grounding HARD gate.

   Bound the path probe to 255 bytes (per-component filesystem limit) and add
   defense-in-depth try/except OSError. Refresh stale workaround comment in
   pilot_uk_lesson.py. Regression test in tests/test_sources_db_prepare_query.py.

   Closes #1901.
   ```
6. **Push:**
   ```bash
   git push -u origin codex/1901-prepare-query-oserror
   ```
7. **Open PR:**
   ```bash
   gh pr create --title "fix(sources_db): bound Path(query).exists() probe (#1901)" --body "..."
   ```
   PR body MUST include:
   - The pre-fix OSError repro (raw output)
   - The post-fix repro (returns tuple cleanly, raw output)
   - Pytest summary lines (raw)
   - Ruff summary line (raw)
   - Link back to this brief
8. **DO NOT auto-merge.** Orchestrator (Claude) merges after CI green.

## Anti-fabrication preamble (per #M-4)

Every claim in the PR body must include the command that produced it. "Tests pass" without a quoted pytest summary line is forbidden. "Ruff clean" without the raw `All checks passed!` line is forbidden. Empty-state proofs ("no other tests affected") need `git diff --stat` + raw `pytest -k 'sources_db or textbook_grounding'` output.

## Out-of-scope (do NOT do in this PR)

- ❌ Path B (corpus-aware writer prompt rewrite) — no longer needed given the real root cause.
- ❌ Path A (corpus expansion for `zaharijchuk G4 p.162`) — separate concern, file a follow-up issue after merge if useful.
- ❌ Touching `_search_textbook_hits` / `_build_textbook_excerpt_context` in `linear_pipeline.py` — they're correct given a working `_prepare_query`.
- ❌ Rerunning `v7_build.py` — only the user runs builds (per CLAUDE.md). Suggest the rerun in PR body, don't trigger it.
