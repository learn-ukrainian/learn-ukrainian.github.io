# Daily sentence inventory

`site/src/data/lexicon-sentence-inventory.json` is the source-attested example
layer for Daily Word. It is deliberately a sibling of
`lexicon-practice-cloze-sources.json`: a daily example only needs a lemma-linked
sentence, while a cloze row additionally needs a verified blank form, case rule,
and distractor contract.

Regenerate it from the hydrated Practice lexeme shards with:

```bash
.venv/bin/python -m scripts.audit.generate_sentence_inventory \
  --sources-db data/sources.db \
  --vesum-db data/vesum.db \
  --max-per-lemma 1
```

The default target set is all A1-C1 `practice-lexemes.*.json` shards under
`site/public/lexicon/`; the extractor searches textbook FTS for an exact
practice-lemma surface, accepts only short sentence-shaped matches with a
VESUM-attested verb, rejects a VESUM-identified leading imperative exercise
command, and keeps one blankable sentence per target lemma. The inventory
records the source label, locator, and licence status for every row.
`--include-ulp` may add ULP fallback rows, but its provenance is intentionally
only the safe source-family label — never a local file, transcript id, URL, or
private locator. `targetForm` preserves the exact source capitalization so the
deck can replace one and only one attested token with `___`.

The legacy Daily Word target set remains available explicitly:

```bash
.venv/bin/python -m scripts.audit.generate_sentence_inventory \
  --daily-pool site/src/data/lexicon-daily-pool.json \
  --sources-db data/sources.db \
  --vesum-db data/vesum.db \
  --max-per-lemma 1
```

For a bounded fixture or selected level, repeat `--practice-lexemes path`.

## After-merge publish path

The inventory and deck are regenerated only after the change is merged. From a
hydrated checkout with read-only `data/sources.db` and `data/vesum.db` links:

```bash
npm --prefix site run hydrate:manifest
npm --prefix site run hydrate:practice
.venv/bin/python -m scripts.audit.generate_sentence_inventory \
  --include-ulp \
  --sources-db data/sources.db \
  --vesum-db data/vesum.db
.venv/bin/python scripts/audit/generate_practice_deck.py \
  --atlas-db data/atlas.db \
  --vesum-db data/vesum.db \
  --out-dir site/public/lexicon
.venv/bin/python scripts/practice_deck/publish.py
```

The final command validates the generated 45-shard package, uploads the
versioned and canonical release assets, and writes the new
`lexicon-practice-deck.pointer.json`. It must run only after the merged build
has passed its review and CI gates. The inventory path uses textbook sentences
with optional ULP fallback; it never admits private teacher-lesson material.

The daily generator overlays this inventory after its existing entry-enrichment
example lookup and preserves `exampleProvenance` and `exampleLicense` in the
published daily-pool row. The licence field records source status and use basis;
it is not an assertion that a source is open-licensed. A future cloze reuse must
separately select and VESUM-check its target inflected form.
