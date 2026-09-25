# Phase P1 notes (#8809)

Scope: the 67 P1 rows of `classification-v1.tsv` (60 K moved to `registry/`, 7 A untracked, bytes kept).

## K blobs that changed (path-string-only edits, spec §8.3)

All other 57 K files keep the table blob and mode. These three are LLM/human workflow instructions
whose only change is `data/translations/…` → `registry/translations/…`:

- `registry/translations/input/INSTRUCTIONS.md` (2 lines)
- `registry/translations/input/README.md` (1 line)
- `registry/translations/input/TRANSLATE-ME.txt` (1 line)

`registry/canonical_anchors.yaml` stays byte-identical: `scripts/build/alignment_manifest.py` stamps
`sha256(canonical_anchors.yaml)` into build manifests, so a comment-only edit would mark every stamped module stale.

## Embedded path strings (spec §3, last bullet)

| Location | String | Disposition |
| --- | --- | --- |
| `registry/corpus_audit/draft_tickets/*.md` (11 files) | `data/sources.db` | logical id (runtime DB path unchanged) |
| `registry/canonical_anchors.yaml:307` | comment `Path("data/canonical_anchors.yaml")` | logical id (comment; blob kept for hash stability) |
| `registry/translations/input/*` | `data/translations/…` | rewritten (reader is a human/LLM workflow) |
| `curriculum/l2-uk-en/b1/gerunds-imperfective/resources.yaml:12` | `source_ref: data/miyklas/grammar_index.yaml` | logical id (citation label; no reader resolves `source_ref`); not edited to avoid a content change |
| `wiki/.reviews/**/*-LOCKED.md`, `docs/{dev,research,decisions,handoffs,dispatch-briefs,salvage-manifest}` | historical `data/…` mentions | logical id (locked or historical record); only two broken research links were repointed |
| `site/src/data/practice-zno.residual.json` | `markupIntegrity.overlayPath: "data/practice/zno-markup-overlay.json"` | logical id (generated provenance label; no reader resolves it; the next regeneration writes `registry/practice/…`) |
| A files (7) | none contain `data/<P1 path>` strings | n/a |

## A writers routed through `publish` (spec §3)

`scripts.storage.artifacts.write_artifact()` stages the bytes and calls `publish` when the target is a manifest artifact,
and writes any other path directly. Writers that can target a published A path now use it:

- `scripts/navsi200_captions.py` (captions ledger), `scripts/navsi200_asr_bakeoff.py` (bake-off ledger)
- `scripts/wiki/diagnostics/corpus_gaps/audit.py` (`coverage_map.json`; its reviewed outputs now go to `registry/corpus_audit/`)
- `scripts/wiki/ukrainian_wiki_corpus.py` (`--report-path`, for `ukrainian_wiki_a2_ingest_report.md`)

`data/raw/pravopys.html`, `data/references/interference-patterns-walexy.json` and
`data/youtube_discovery/ulp_grammar_guide_backfill.jsonl` have no committed writer. Readers resolve through `artifact_path()`
(`module_memory.find_pravopys_files`, `navsi200_*` ledger loaders, `corpus_gaps.load_coverage_map`).

## Other consumers found beyond the literal-path grep

- `scripts/deploy/auto_deploy_eligibility.py`: `registry/` added to the content-drift prefixes (it was `data/` only).
- `scripts/wiki/migrate_external_chunks.py`, `tests/test_wiki_channels.py`, `tests/test_channels_registry.py`:
  the channel registry moved; the scraped `*.jsonl` corpus stays under untracked `data/external_articles/`.
- `scripts/storage/consumers.py` now also finds the `registry/` twin of a K path and a quoted `"data/"` prefix.

## Merge-time commands for the driver (spec §4 steps 8 and 10)

Before merging, in every long-lived checkout (primary, Mac clone, any materialised dispatch worktree):
`.venv/bin/python -m scripts.storage.artifacts snapshot --phase P1`. After the pull:
`.venv/bin/python -m scripts.storage.artifacts hydrate --phase P1` then `… verify`. `git pull` deletes files untracked upstream.

## needs_artifact tests (spec §5)

13 tests validate real produced data and skip in CI (`registry/artifacts/needs-artifact-expected.txt`): the 8 captions-ledger and
4 bake-off-ledger tests, plus `test_load_coverage_map_resolves_the_published_artifact`. Their passing host run is
`registry/artifacts/host-run-p1.junit.xml` (see `test-baseline.p1.dispositions.json`).
