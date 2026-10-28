# Restore Ohoiko headwords split by detached OCR acutes

The 1000-word parser took each numbered entry's first physical line as its
complete header. In raw entry 685, `проєк` is followed by a new line beginning
with U+0301 and `т`. Entry 352 splits both `клієнт` and `клієнтка` this way.
The suffix and English gloss became body text, so the curated intake received
an incomplete `Entry.headword` and supplied its placeholder gloss.

The defect is at the `_ENTRY_START_RE` match and `headword` assignment in
`scripts/ingest/ohoiko_books_ingest.py::parse_book`. The verb parser cached the
first physical line in `scripts/ingest/ohoiko_verbs_ingest.py::parse_book`;
`curated_ohoiko_ulp_repromote.py::collect_book_headwords` then selected only its
first token. Three verb headers have their detached continuation after the
English gloss. Both ingesters now reuse the existing Ohoiko OCR line rejoiners
before exposing headword metadata. The word parser rejoins only unfinished
headers; the verb parser preserves its original body bytes.

Git blame traces the word parser to `9c54ad802909` and the curated collector to
`0e901273a160`. The later `scripts/lexdata/transforms.py` registry binds the
lexical adapter and normalizer; neither that registry nor
`scripts/lexdata/normalize.py` produced the historical truncated inventory.
The raw L0 chunks remain unchanged. Rejoining an OCR acute does **not** establish
its stress position; canonical intake heads strip it. Stress requires the
Sources stress oracle, never the displaced OCR mark.

## Damage census

Both parser revisions ran over the same 1,000 numbered word records and 500
numbered verb records from the read-only Sources store. The source selection's
canonical SHA-256 is
`d1c207d94e69a516ffe82e3238b1f6b418a353babf27d3f08413687990fc0d49`.
Exactly five entries change; every restored head below is CLEAN in Sources
`inspect_words` and present in `verify_words` (2026-10-28, VESUM source version
`53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680`).

| Raw entry | Damaged head | Restored canonical heads | Existing hold |
| --- | --- | --- | --- |
| 1000-words 352 | клієн | клієнт, клієнтка | 10181-02 |
| 1000-words 685 | проєк | проєкт | none of the six |
| 500-verbs 277 | об'єд | об'єднувати, об'єднати | 10181-04 |
| 500-verbs 341 | поєд | поєднувати, поєднати | 10181-05 |
| 500-verbs 365 | приєд | приєднувати, приєднати | 10181-06 |

The separate `лет` candidate comes from
`ohoiko-book-002::verb-0234::token-0026`. That page prints `леч-/лет-` as stems;
its head `летіти | полетіти` is intact. It is not changed or guessed into a
lemma. Its existing `needs_more_evidence` decision and #11904 withholding stay.
Page 383's separate stems-before-head layout is also unchanged by this fix.

The correction delta follows the existing OCR space-collapse inventory pattern.
It contains nine unstressed heads and their raw-record hashes, not source prose.
Optional `[ся]` remains under the existing lexical adapter's expansion rules;
the curated book intake continues to select bare infinitives.

The historical bulk inventory, original approval ledger and all six #10181
holds are immutable. Regenerating the bulk would invalidate pinned origins and
approval digests. The correction inventory uses a distinct source id, path and
locators, so the canonical heads receive fresh source evidence without releasing
or retargeting a held contribution. There is no conflict with the six decisions.

## Regenerate the source delta

From a dispatch worktree, use the project interpreter and a read-only local
Sources database. The pre-fix revision is fixed for this census:

```bash
.venv/bin/python -m scripts.lexicon.repair_ohoiko_headwords \
  --sources-db data/sources.db \
  --baseline-ref 8c7830abccffc626bd7964ab64ef7c1fd8105ceb \
  --write-source-data
```

This writes only the dedicated `ohoiko-ocr-acute-rejoin-2026-10-28` inventory and
its matching approval ledger. It does not re-ingest Sources, regenerate the
historical bulk, edit any pointer, or publish an Atlas artifact.

## Prepare the next runtime's input

The next Atlas build must consume the corrected source delta and repair legacy
identities before migration. This task does not build or publish that runtime.

1. In the build's staging area, use `repair_ohoiko_headwords --manifest INPUT`
   to inspect the identity plan, then `--repair-out OUTPUT` to write a separately
   verified input. The four held damaged entries are removed only when their
   bytes match the preserved #10181 payloads. A changed or mixed contribution
   fails closed. The `проєк` duplicate requires its Ohoiko entry-685 provenance,
   an existing canonical `проєкт` article, and the existing curated alias to it.
   Removing that duplicate lets the existing alias resolve to the canonical
   article. No held evidence is copied into the canonical entries.
2. Use `curated_ohoiko_ulp_repromote.build_candidates` on the correction inventory,
   then `plan_source_inventory_promotion` with its explicit `--decision-file` and
   the staged manifest. Apply through `apply_source_inventory_promotion`, including
   `--overlay-existing-provenance`, the same candidate file and decision file.
   Existing heads merge by the established lemma key; missing heads are additions.
   On the inspected manifest, eight heads already exist and `клієнтка` is new.
   Recompute these counts against the build's actual input.
3. Enrich new entries, run the normal manifest/disposition/conformance checks,
   regenerate the fingerprint, and use the usual runtime migration and export.
   Publication remains a separate release action. A failed full manifest check
   must be resolved before using the repaired input.
4. Verify all nine canonical heads, no damaged articles, valid alias targets,
   and fresh Ohoiko provenance on the resulting runtime. Keep #11904 discovery
   withholding until that runtime carries the correction. This change does not
   edit `site/src/data/lexicon-practice-deck.pointer.json` or any release pointer.
