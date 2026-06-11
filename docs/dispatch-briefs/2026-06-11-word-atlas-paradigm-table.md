# Dispatch brief — Word Atlas morphology paradigm table (design §4 #4)

**Owner lane:** Word Atlas (Claude). **Issue:** #2882. **Agent:** codex (gpt-5.5, xhigh).
**Mode:** danger + worktree. **No auto-merge.** **/code-review** after (touches pipeline + render).

## Goal
Replace the flat, alphabetical-by-label morphology **form-grid** in the Word Atlas detail page
with a structured **case×number paradigm table** per design `docs/best-practices/word-atlas-design.md`
§4 #4 + §6 data model, matching the PoC `docs/poc/word-atlas/detail.html` (`paradigm-table`:
`Відмінок | Однина | Множина`). Browser-verified by Claude that the current grid renders forms in
alpha-label order with confusing duplicates (e.g. `вікну/давальний` next to `вікну/місцевий`).

## Current state (verified 2026-06-11)
- `scripts/lexicon/enrich_manifest.py` emits `enrichment.morphology = {pos, form_count, forms:
  [{form, label}], source}`. Labels are VESUM-derived strings (grammar below).
- `starlight/src/pages/lexicon/[lemma].astro` renders `forms` as a flat `<ul class="atlas-form-grid">`.
  (Just refactored in #2980 — the morphology section is `{enrichment?.morphology && (<section>…)}`.)

## Exact label grammar (extracted from the live manifest — build the paradigm parser from THIS)
- **Noun** — singular: `«{gender}., {case}»` where gender ∈ {`чол.`,`жін.`,`сер.`}, case ∈
  {`називний`,`родовий`,`давальний`,`знахідний`,`орудний`,`місцевий`,`кличний`}; plural:
  `«множина, {case}»`. (Gender is the noun's inherent gender — constant across its singular forms.)
- **Verb** — `«{tense}, {number}, {N} ос.»` tense ∈ {`теперішній`,`майбутній`}, number ∈
  {`однина`,`множина`}, person ∈ 1/2/3; imperative `«наказовий, {number}, {N} ос.»`; past
  `«минулий, {gender|множина}»` (gender ∈ чол./жін./сер.); `«інфінітив»`.
- **Multiple orthographic variants per cell** (reflexive `-ся/-сь`, e.g. `навчатимемось` /
  `навчатимемося` / `навчатимемся` all = майбутній·множина·1ос). COLLAPSE per cell: join distinct
  variants with `« / »` (primary first). Do NOT drop variants silently.
- Adverbs/numerals/other POS: usually no clean case/person slots → see fallback.

## Approach (design §6 = structure the data, then render)
1. **`enrich_manifest.py`** — add a deterministic `paradigm` builder that groups `forms` by parsing
   the labels above into a structured object. Keep `forms` as-is for back-compat; ADD:
   ```
   morphology.paradigm = {
     kind: "noun" | "verb" | "other",
     # noun:
     cases: {  # canonical order: nom,gen,dat,acc,ins,loc,voc
       називний: { singular: "вікно", plural: "вікна" }, родовий: {...}, …
     },
     # verb:
     infinitive: "навчатися / навчатись",
     tenses: { теперішній: { однина: {1:"…",2:"…",3:"…"}, множина:{…} }, майбутній:{…} },
     imperative: { однина:{2:"…"}, множина:{1:"…",2:"…"} },
     past: { чол:"…", жін:"…", сер:"…", множина:"…" },
   }
   ```
   Emit `paradigm` ONLY when the parser cleanly fills slots; otherwise omit it (render falls back).
   Canonical case order is fixed (Н-Р-Д-З-О-М-Кл) — never alpha. Pretty UK case labels for render
   (Називний/Родовий/…); keep a label map.
2. **`[lemma].astro`** — render `morphology.paradigm` when present:
   - noun → `Відмінок | Однина | Множина` table, cases in canonical order (PoC `paradigm-table`).
   - verb → infinitive line; present + future tables (rows = 1/2/3 особа, cols = однина/множина);
     imperative table; past row (чол./жін./сер./множина). Omit any sub-block with no data.
   - **Fallback:** when `paradigm` is absent, keep the existing flat `atlas-form-grid` (don't regress
     adverbs/numerals/anything the parser can't slot).
   - Style with existing `--lu-*` tokens + a `.atlas-paradigm-table` class (reuse the page's
     border/surface system; AA-contrast both themes — mirror the existing atlas CSS patterns).
3. Regenerate `starlight/src/data/lexicon-manifest.json` (`.venv/bin/python scripts/lexicon/enrich_manifest.py …` — find the exact invocation in the script's `__main__`/CLI; do NOT hand-edit the JSON).

## Tests
- `tests/` (python): paradigm builder unit tests — feed the exact label samples above; assert
  noun `вікно` → 7 cases × {singular,plural} correct; verb `навчатися` → infinitive variants joined,
  present/future/imperative/past slots filled, reflexive variants collapsed with ` / `; an
  adverb/no-slot case → `paradigm` omitted (fallback path). Run `.venv/bin/pytest` on the new test.
- Frontend: `npm run build` (astro) must pass; if a vitest covers lexicon render, extend it.

## #M-4 — verifiable claims (quote raw)
| Claim | Check |
|---|---|
| Paradigm built for noun | `python3 -c` dumping `вікно` morphology.paradigm.cases |
| Verb slots filled | same for `навчатися` |
| Variants collapsed | grep a cell shows `…ось / …ося / …мся` joined |
| Manifest regenerated | `git diff --stat` shows lexicon-manifest.json changed |
| Tests pass | `.venv/bin/pytest <new test>` final summary line raw |
| Frontend builds | `npm run build` final success line raw |
| ruff clean | `.venv/bin/ruff check scripts/lexicon/enrich_manifest.py` final line |

## Steps
1. `git worktree add` off `origin/main`.
2. enrich_manifest.py paradigm builder + label parser (per the grammar above).
3. astro per-POS paradigm tables + flat-grid fallback + CSS.
4. Regenerate manifest.
5. python tests + `.venv/bin/pytest`; `npm run build`; `.venv/bin/ruff check`.
6. Commit (conventional): `feat(lexicon): morphology paradigm table for Word Atlas [#2882]`.
7. `git push -u origin <branch>`; `gh pr create` with raw evidence. **NO auto-merge.**

## Gotchas
- Don't regress the flat grid for POS the parser can't slot (adv/numeral/phrase) — fallback MUST work.
- enrich_manifest.py is Python → pytest before push (#M-7). Don't hand-edit the manifest JSON.
- Don't touch `codex/2888-a2-*` (A2 lane). graphql may 401 → REST. Only required check = `Test (pytest)` + Frontend build.
- Claude will browser-verify `/lexicon/вікно/` (noun) + a verb lemma after the PR; design target is the PoC `paradigm-table`.
