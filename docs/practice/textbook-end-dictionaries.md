# Textbook end-dictionaries → practice coverage path

**Issue:** #6188 · Parent #6132 · Epic #4387  
**Inventory:** `data/lexicon/textbook-end-dictionaries/`  
**Extractor:** `.venv/bin/python scripts/practice_deck/end_dictionaries.py`

## What this unlocks

School **українська мова** end-glossaries in `textbook_sections`
(наголоси, колоритна лексика, фразеологізми, тлумачний додаток, словнички).

The extractor writes a machine-readable inventory (`atlas-end-dictionary-inventory`)
with section metadata and structured rows:

| Field | Notes |
| --- | --- |
| `lemmaPlain` | Always |
| `stress` | Only when combining acute is present in OCR |
| `gloss` | Gloss / phrase sense when layout provides it |
| `multiword` | Phraseology and multi-token heads |
| `locator` | `textbook_sections:{id}` (rights-safe; no full_text in git) |

## Honesty / cloze policy

**Definitions and lemma lists are not blankable cloze sentences.**

`generate_practice_deck.py --end-dictionary-inventory` wires the sidecar as:

1. **Inventory evidence** for residual taxonomy (lemma present in end-dict).
2. **Optional stress overlay** only for rows with combining acute (does not invent
   stress from acute-less stress lists).
3. **Never** fabricates cloze from gloss text.

Cloze coverage therefore stays unchanged until a blankable public sentence exists
for the lemma (sentence inventory / reviewed sources).

## Layout residual (tool-named)

- **Packed academic morph (grade 9 «З тлумачного словника»):** high-precision
  parse only; full recall not claimed.
- **OCR Latin lookalikes (some Zabolotnyi synonym/ortho appendices):** corrupted
  heads skipped rather than mis-repaired.
- **Stress mini-dicts without acute:** inventory priority only.

## Regenerate

```bash
.venv/bin/python scripts/practice_deck/end_dictionaries.py \
  --sources-db data/sources.db \
  --out-dir data/lexicon/textbook-end-dictionaries
```
