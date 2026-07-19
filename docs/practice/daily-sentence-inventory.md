# Daily sentence inventory

`site/src/data/lexicon-sentence-inventory.json` is the source-attested example
layer for Daily Word. It is deliberately a sibling of
`lexicon-practice-cloze-sources.json`: a daily example only needs a lemma-linked
sentence, while a cloze row additionally needs a verified blank form, case rule,
and distractor contract.

Regenerate it from the current daily pool with:

```bash
.venv/bin/python -m scripts.audit.generate_sentence_inventory \
  --daily-pool site/src/data/lexicon-daily-pool.json \
  --sources-db data/sources.db \
  --vesum-db data/vesum.db
```

The extractor searches textbook FTS for an exact daily-lemma surface, accepts
only short sentence-shaped matches with a VESUM-attested verb, and records the
source label, locator, and licence status for every row. The default inventory
uses textbook matches. `--include-ulp` may add ULP fallback rows, but its
provenance is intentionally only the safe source-family label — never a local
file, transcript id, URL, or private locator.

The daily generator overlays this inventory after its existing entry-enrichment
example lookup and preserves `exampleProvenance` and `exampleLicense` in the
published daily-pool row. The licence field records source status and use basis;
it is not an assertion that a source is open-licensed. A future cloze reuse must
separately select and VESUM-check its target inflected form.
