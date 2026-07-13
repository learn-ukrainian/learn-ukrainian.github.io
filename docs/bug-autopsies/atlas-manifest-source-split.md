# Atlas manifest source split silently shrinks a relation-only rebuild

**Date:** 2026-07-13
**Issue:** #4975
**Category:** atlas-build / source-split
**Affected commands:** `make atlas`, `make atlas-publish`, and the release
relation workflow

## Outcome

The 8,552-entry released manifest is an intentional superset of the
course-vocabulary builder's output. It contains promoted content and source
inventory entries that `scripts.lexicon.build_data_manifest` never reads.
Running `make atlas` before a relation-only publication replaces that superset
with the course-only layer; it is not a reproducing release build.

This is not a recent regression in the builder or a false comparison. It is an
old source-boundary mismatch that the stale release instructions obscured. No
published data was lost: the pointer still resolves to the 8,552-entry release
asset, and the re-enrichment must start by hydrating that asset.

## Evidence

`87cc0772ce259cb91f6f19f06fa202cace3d668b` (2026-07-10) records the
8,552-entry Phase-A publish. Its commit message states that a promoted
8,706-entry manifest received a course-usage backfill and then
`park_thin_entries --limit 154`, resulting in 8,552 live entries.

`58a00e70e18b97178209586d7503a9a72705b579` (2026-07-11) moved the pointer to
the current `27e87936efb4…` asset after re-enriching **all 8,552 entries** with
antonym, homonym, and paronym relations. The current pointer pins raw JSON SHA
`27e87936efb4beb23a15a25fa548766fb7aa519741e21f52a8a0b9a67dff4fa1`; its
gzip SHA is `99fee5e9b01cd8e5d8d8c0ab8e78eefdd8effee623fe4a0a12f30d35a8239bbe`.

The release asset has 8,552 `entries`, 8,552 unique normalized lemma keys, and
`stats.lemmas_total == 8552`. Its primary-source composition is:

| Source | Entries |
| --- | ---: |
| `built_vocabulary` | 4,793 |
| `built_vocabulary_form` | 336 |
| `built_vocabulary_normalized` | 36 |
| `built_vocabulary_canonicalized` | 4 |
| `content_lexicon_grow` | 2,857 |
| `source_inventory_grow` | 519 |
| `heritage_status_seed` | 4 |
| `surzhyk_to_avoid` | 3 |

`build_data_manifest` enumerates only built `vocabulary.yaml` records and its
seed sets. `enrich_manifest` enriches the entries already present; it cannot
recreate the 3,376 promoted grow/source-inventory records.

This was not introduced between the Phase-A publish and #4975: the Phase-A
commit and current `HEAD` resolve `scripts/lexicon/build_data_manifest.py` to
the same blob (`1c385c3da9a1c9db1c85a2c030fed983cc366390`) and `Makefile` to the
same blob (`f642eb31d3243aac4e9e48842cf9e90602c55441`).

## Count and set comparison

The reported data-enabled run was 6,852 entries (6,841 built plus 13 seeds),
which is 1,700 fewer than the release. The source-only builder invoked directly
in this dispatch's `HEAD` returned 6,823 entries (6,812 built plus 13 seeds),
so that exact 6,852 run has a separate 29-entry input-state discrepancy. It
does not change the conclusion: neither course-only result contains the
promoted source layer.

For the current checked-out inputs and the pointer-pinned asset, a deterministic
comparison produced 5,004 shared normalized lemma keys, 3,548 release-only
keys, and 1,819 builder-only keys. The count-only difference is therefore not a
membership delta: overwriting the release would discard 3,548 existing entries
while adding 1,819 different course entries, for a net 1,729-entry shrink in
this checkout.

The raw manifest is intentionally gitignored and absent from the `87cc077` tree;
the committed pointer is the reproducible source for the released bytes. Thus
the exact 6,852 membership delta is not recoverable from committed files alone.
To reproduce the current comparison without writing a manifest, download the
pointer asset, call `build_manifest()`, and compare each entry's normalized
`lemma` key. Verify the downloaded JSON SHA against the pointer before using
the result.

## Guard semantics

`manifest_io._entry_count()` compares `len(manifest["entries"])` when it is a
list. The builder emits that same list shape, and the released asset has unique
lemma keys, so this is not an apples-to-oranges guard.

`_refuse_richer_local()` has a narrower purpose than its name may suggest: it
raises only if the local manifest has more entries than the release or a newer
timestamp. A poorer 6,852-entry local manifest is hydrated over by the pinned
8,552-entry release; `tests/test_manifest_io.py::test_load_manifest_hydrates_stale_poorer_local_manifest`
covers that behavior. The safety outcome is correct, but it is not a direct
"refuse 6,852 over 8,552" publish check.

## Correct publish preparation

Do not run `make atlas-publish` for relation-only work: it first runs the
course-only builder. In a primary checkout with the required local data, use:

```bash
.venv/bin/python -c \
  "from scripts.lexicon.manifest_io import load_manifest; print(len(load_manifest()['entries']))"
.venv/bin/python scripts/lexicon/enrich_manifest.py
.venv/bin/python -m scripts.audit.generate_search_index
.venv/bin/python scripts/lexicon/export_open_dataset.py
.venv/bin/python -m scripts.audit.generate_daily_pool
.venv/bin/python scripts/lexicon/verify_manifest.py
.venv/bin/python -m scripts.lexicon.publish_manifest
```

`load_manifest()` hydrates a missing or poorer local file and refuses to clobber
an in-flight richer/newer intake manifest. The final command performs the
external publish and is intentionally not run for this diagnosis.

For a deliberately superseding growth release, hydrate first, run the reviewed
grow-candidate promotion and any required course-usage backfill/thin-entry park,
then continue from `enrich_manifest.py` in the sequence above. That preserves
the existing asset as the base rather than rebuilding only the curriculum layer.
