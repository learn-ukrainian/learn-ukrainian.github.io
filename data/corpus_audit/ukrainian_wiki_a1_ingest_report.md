# Ukrainian Wiki A1 Ingest Report

- Generated: 2026-04-21T01:08:02Z
- Articles scanned: 55
- Articles ingested: 55
- Articles failed: 0
- Total segmented chunks: 612
- Total chunks ingested: 609
- Total chunks skipped by admission gate: 3

## Suspicious Chunk Counts

- Low threshold: `< 7.00` chunk(s)
- High threshold: `> 15.00` chunk(s)
- Suspiciously low articles: sounds-letters-and-hello
- Suspiciously high articles: checkpoint-time-nature, verbs-group-one

## Per-Article Chunk Counts

| Article | Track | Inserted | Segmented | Skipped | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| `a1-finale` | `a1` | 11 | 11 | 0 | ok |
| `around-the-city` | `a1` | 13 | 13 | 0 | ok |
| `at-the-cafe` | `a1` | 9 | 9 | 0 | ok |
| `checkpoint-actions` | `a1` | 9 | 9 | 0 | ok |
| `checkpoint-communication` | `a1` | 8 | 8 | 0 | ok |
| `checkpoint-first-contact` | `a1` | 11 | 11 | 0 | ok |
| `checkpoint-food-shopping` | `a1` | 10 | 10 | 0 | ok |
| `checkpoint-my-world` | `a1` | 9 | 9 | 0 | ok |
| `checkpoint-places` | `a1` | 11 | 11 | 0 | ok |
| `checkpoint-time-nature` | `a1` | 16 | 16 | 0 | suspiciously high |
| `colors` | `a1` | 11 | 11 | 0 | ok |
| `days-and-months` | `a1` | 13 | 13 | 0 | ok |
| `emergencies` | `a1` | 8 | 8 | 0 | ok |
| `euphony` | `a1` | 12 | 12 | 0 | ok |
| `food-and-drink` | `a1` | 12 | 12 | 0 | ok |
| `free-time` | `a1` | 10 | 10 | 0 | ok |
| `health` | `a1` | 12 | 12 | 0 | ok |
| `hey-friend` | `a1` | 11 | 11 | 0 | ok |
| `holidays` | `a1` | 12 | 12 | 0 | ok |
| `how-many` | `a1` | 10 | 10 | 0 | ok |
| `i-eat-i-drink` | `a1` | 10 | 11 | 1 | 1 gate-skipped chunk(s) |
| `i-want-i-can` | `a1` | 8 | 8 | 0 | ok |
| `linking-ideas` | `a1` | 11 | 11 | 0 | ok |
| `many-things` | `a1` | 11 | 11 | 0 | ok |
| `my-city` | `a1` | 9 | 9 | 0 | ok |
| `my-day` | `a1` | 12 | 12 | 0 | ok |
| `my-family` | `a1` | 10 | 10 | 0 | ok |
| `my-morning` | `a1` | 12 | 12 | 0 | ok |
| `my-plans` | `a1` | 13 | 13 | 0 | ok |
| `my-story` | `a1` | 12 | 12 | 0 | ok |
| `people-around-me` | `a1` | 9 | 9 | 0 | ok |
| `please-do-this` | `a1` | 12 | 12 | 0 | ok |
| `questions` | `a1` | 13 | 13 | 0 | ok |
| `reading-ukrainian` | `a1` | 13 | 13 | 0 | ok |
| `shopping` | `a1` | 11 | 11 | 0 | ok |
| `sounds-letters-and-hello` | `a1` | 6 | 7 | 1 | suspiciously low; 1 gate-skipped chunk(s) |
| `special-signs` | `a1` | 8 | 8 | 0 | ok |
| `stress-and-melody` | `a1` | 11 | 11 | 0 | ok |
| `things-have-gender` | `a1` | 11 | 11 | 0 | ok |
| `this-and-that` | `a1` | 11 | 11 | 0 | ok |
| `transport` | `a1` | 12 | 12 | 0 | ok |
| `verbs-group-one` | `a1` | 17 | 17 | 0 | suspiciously high |
| `verbs-group-two` | `a1` | 9 | 9 | 0 | ok |
| `weather` | `a1` | 9 | 10 | 1 | 1 gate-skipped chunk(s) |
| `what-happened` | `a1` | 11 | 11 | 0 | ok |
| `what-i-like` | `a1` | 12 | 12 | 0 | ok |
| `what-is-it-like` | `a1` | 12 | 12 | 0 | ok |
| `what-time` | `a1` | 14 | 14 | 0 | ok |
| `what-will-happen` | `a1` | 10 | 10 | 0 | ok |
| `when-and-where` | `a1` | 13 | 13 | 0 | ok |
| `where-from` | `a1` | 13 | 13 | 0 | ok |
| `where-is-it` | `a1` | 9 | 9 | 0 | ok |
| `where-to` | `a1` | 12 | 12 | 0 | ok |
| `who-am-i` | `a1` | 14 | 14 | 0 | ok |
| `yesterday` | `a1` | 11 | 11 | 0 | ok |

## Skipped Chunks

| Article | Passage | Chunk Index | Reason |
| --- | --- | ---: | --- |
| `i-eat-i-drink` | `i-eat-i-drink:p12-12` | 11 | 44 chars < 50 |
| `sounds-letters-and-hello` | `sounds-letters-and-hello:p8-8` | 7 | 43 chars < 50 |
| `weather` | `weather:p13-13` | 8 | 43 chars < 50 |

## Verification

- Focused verification passed:
  `.venv/bin/ruff check scripts/wiki/ukrainian_wiki_corpus.py tests/wiki/test_ukrainian_wiki_corpus.py`
  and `.venv/bin/pytest tests/wiki/test_ukrainian_wiki_corpus.py` (`8 passed`).
- Repo-wide `.venv/bin/ruff check` is currently blocked by unrelated pre-existing lint debt outside A.6 scope
  (for example `curriculum/l2-uk-en/b2/fix_all.py`, `docs/reports/check_b2_plans.py`,
  `docs/reports/fix_mdx_frontmatter.py`, `plans/fix_b2_36.py`).
- Repo-wide `.venv/bin/pytest` was started and observed advancing through the baseline suite
  past `74%` with no A.6-specific failures surfaced during sampled output.
