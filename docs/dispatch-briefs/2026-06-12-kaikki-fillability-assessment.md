# Dispatch brief — kaikki.org Ukrainian (Wiktionary) fillability assessment vs Atlas lemmas

**Agent:** agy (unmetered) · worktree · commit + push + PR (NOT draft) · no auto-merge.
**Base:** `main`.
**Context:** The Word Atlas (EPIC #2985) presents per-lemma data. The `motî` dictionary app the user liked is a
front-end over **English Wiktionary** (CC BY-SA 3.0). The canonical machine-readable form is the **kaikki.org
Ukrainian extract** (wiktextract). This task measures how much of our taught-vocab Atlas it can fill —
feeds #2882 (fillability assessment) and the #2985 sourcing table. Honest constraint: kaikki glosses are in
ENGLISH (English-mediated) — it does NOT solve the authentic-UA-synonym gap; it helps definitions/etymology/
examples/IPA only. Say so in the report.

## Inputs (already on disk — do NOT re-download)
- **kaikki extract:** `~/.cache/learn-ukrainian-kaikki/kaikki-uk.jsonl` (~252 MB, JSONL, one JSON object/line).
- **Taught lemmas:** union of `curriculum/l2-uk-en/*/*/vocabulary.yaml`, lemma key = `lemma | word | uk | term`
  (A1 uses `lemma`, A2 uses `word`). Dedupe case-insensitively. EXCLUDE non-lemma surface forms to match the
  Atlas: drop multi-token phrases (contain whitespace), entries ending in `!`/`?`, and slash-notations
  (contain `/`). Report both the raw union count and the clean-lemma count.
- **Current Atlas manifest (for NET-ADD):** `starlight/src/data/lexicon-manifest.json` on `main` (the
  `entries` list). Each entry's enrichment may already carry `meaning`/definitions, `etymology`, `examples`,
  and `stress`. Use it to compute what kaikki ADDS beyond what we already populate.

## kaikki JSONL schema (use THESE fields — do not guess)
Each line is one word-sense-group object. Relevant keys:
- `word` (str) — the headword/lemma. `lang_code` == `"uk"` (filter to this; the file is already Ukrainian but verify).
- `pos` (str) — part of speech.
- `senses` (list) — each sense has `glosses` (list[str], ENGLISH) and may have `examples`
  (list of objects with `text` (Ukrainian) and often `english`).
- `etymology_text` (str, optional) — etymology prose.
- `sounds` (list, optional) — objects with `ipa` (str) and/or `tags`. IPA presence = pronunciation coverage.
- `forms` (list, optional) — inflected forms.
Note: a lemma may span MULTIPLE lines (one per pos/etymology). Aggregate by `word` (case-insensitive) before scoring.

## Deliverable 1 — analysis script `scripts/lexicon/assess_kaikki_fillability.py`
A CLI that takes `--kaikki PATH --vocab-glob 'curriculum/l2-uk-en/*/*/vocabulary.yaml' --manifest PATH
--out REPORT.md`. It must:
1. Build the clean taught-lemma set (per Inputs above).
2. **Stress-normalize before matching** (CRITICAL — preview showed ~250 false-misses from this): strip combining
   acute U+0301 and standalone acute/grave accents from BOTH the taught lemma and the kaikki `word` before
   comparing (e.g. `абе́тка`→`абетка`, `ба́тько`→`батько`). Match on the stress-stripped, lowercased form.
3. Stream the kaikki JSONL (line-by-line, do NOT load all into RAM at once; aggregate a dict keyed by the
   stress-stripped lowercased `word` holding booleans: present, has_etymology, has_example, has_ipa, has_gloss, pos set).
3. For each taught lemma compute coverage flags; produce counts + percentages.
4. If `--manifest` given, compute NET-ADD per field (kaikki has it AND manifest entry lacks/empty it).
5. Write a markdown report (Deliverable 2). Print the headline counts to stdout (so they appear raw in logs).
Keep it deterministic and dependency-light (stdlib json/yaml/glob/argparse). ruff-clean.

## Deliverable 2 — report `docs/research/lexicon/kaikki-fillability-2026-06-12.md`
Tables with raw numbers (NOT prose estimates):
- Taught lemmas: raw union N, clean-lemma M.
- kaikki coverage over the M clean lemmas: present %, has-gloss %, has-etymology %, has-≥1-example %, has-IPA %.
- NET-ADD vs current manifest: per field, how many lemmas gain that field from kaikki.
- 15 sample COVERED lemmas (with the kaikki gloss/etym/ipa) + 15 NOT-covered lemmas.
- Caveat section: English-mediated glosses; CC BY-SA 3.0 attribution + share-alike obligation; does NOT fill
  authentic-UA synonyms/antonyms.
- One-paragraph recommendation: is kaikki worth wiring into the Atlas pipeline for etymology/examples/IPA, and
  for which fields specifically.

## Run + finalize (numbered)
1. `git worktree add` (dispatcher handles via --worktree).
2. Write the script. 3. Run it FOREGROUND:
   `.venv/bin/python scripts/lexicon/assess_kaikki_fillability.py --kaikki ~/.cache/learn-ukrainian-kaikki/kaikki-uk.jsonl --vocab-glob 'curriculum/l2-uk-en/*/*/vocabulary.yaml' --manifest starlight/src/data/lexicon-manifest.json --out docs/research/lexicon/kaikki-fillability-2026-06-12.md`
   (single streaming pass; if it runs >10 min something is wrong — stop + report).
4. `.venv/bin/ruff check scripts/lexicon/assess_kaikki_fillability.py` → clean.
5. Add a minimal test `tests/test_assess_kaikki_fillability.py` (tiny in-memory JSONL fixture → asserts the
   coverage counts). Run it green.
6. Commit (conventional; `X-Agent: agy` trailer). Do NOT commit the 252 MB extract.
7. `git push -u origin <branch>`. 8. `gh pr create` NON-draft, base main, no auto-merge.
9. Out of scope: do NOT modify the manifest, the §8 gate, course content, or `.python-version`/lint configs.

#M-4 preamble: every count in the report MUST come from the script's actual stdout — quote the raw headline
line in the PR body. No hand-estimated percentages.
