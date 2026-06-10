# Dispatch brief — Heritage Attestation Engine: shared classifier module (Task 6 of #2882)

**Authority (now on `main` — READ IT, it is the spec):**
`docs/best-practices/heritage-attestation-engine.md`. Build the shared, deterministic, local,
CI-reproducible classifier it specifies. Atlas lane owns this build; the folk/gate lane consumes it.

## Build `scripts/lexicon/heritage_classifier.py` — two entry points
1. **`classify_lemma(lemma)`** → the spec §3 `heritage_status` dict: `classification` ∈
   {authentic-archaism, dialect, historism, borrowing, standard, russianism, surzhyk, calque, unknown},
   `attestations` (each citing source + ref), `is_russianism`, `russian_shadow`, `sovietization_risk`,
   `calque_warning`. For the Word Atlas "Походження + статус" badges.
2. **`classify_surface_form(form)`** → same shape, with the **§4 surface-form path**: VESUM present ⇒
   `standard`; else a heritage-dictionary surface hit, OR **`verify_quote` against `literary_texts`**
   (the inflected form attested verbatim) ⇒ authentic. For the `_vesum_gate`.

## Sources (spec §3 priority; all local `data/sources.db` / `data/vesum.db`)
VESUM → Грінченко 1907 → СУМ-20/slovnyk.me (cached) → `literary_texts` via `verify_quote` (surface
attestation) → Антоненко-Давидович + UA-GEC (calque/russianism evidence) → `check_russian_shadow`
(**negative signal only — never decides alone**; false-positives on archaic homographs like `другоє`).
**Etymology evidence = Горох + Wiktionary, NOT ЕСУМ** (OCR-garbled cognates).

## Classification population (verified data-availability)
- SUM-11 ремарки in `sum11.definition`: `заст.`→authentic-archaism, `іст.`→historism, `діал.`→dialect
  (confirmed present: заст. 4895, іст. 2046, діал. 5908 rows; 23/63 A1 lemmas carry ≥1).
- русизм via `check_russian_shadow` + R2U + Антоненко.
- **Principle:** authentic ⇔ attested in ANY heritage source with `is_russianism=false`; russianism ⇔
  attested NOWHERE + russian-pattern + has a Ukrainian standard alternative. VESUM-absence alone ≠ russianism.

## Wiring (this dispatch)
- Wire `scripts/lexicon/enrich_manifest.py` to call `classify_lemma()` and emit `heritage_status` per lemma.
- **Do NOT modify `linear_pipeline.py::_vesum_gate`** — the folk lane wires + reviews that. Just ship
  `classify_surface_form()` ready for them to import.

## Tests (the spec's evidence cases — must pass)
`tests/test_heritage_classifier.py`: `другоє`→authentic-archaism (verify_quote 1.0 «на другоє літо
поховаємо»); `ягілка`/`гагілка`→dialect; `перекличка`→standard/borrowing (VESUM-missing but attested);
`протиріччя`/`діюча`→russianism (attested nowhere, UK standard = суперечність/чинна).

## #M-4 verification (final report = command + cwd + raw output)
- `classify_surface_form` raw output for the 5 evidence forms above (proving the verdicts).
- `.venv/bin/python -m pytest tests/test_heritage_classifier.py` final line raw.
- regenerate `lexicon-manifest.json`; show 2 lemmas' new `heritage_status` raw.
- `.venv/bin/ruff check scripts/lexicon/heritage_classifier.py scripts/lexicon/enrich_manifest.py`.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree (base = origin/main, has the spec).
2. Build the module (both entry points) + tests + wire `enrich_manifest.py` (not the gate).
3. Run the evidence-case tests + #M-4 verification.
4. ruff.
5. Commit (conventional + `X-Agent` trailer): `feat(lexicon): heritage attestation classifier — shared Atlas/gate engine [#2882 Task 6]`.
6. `git push -u origin <branch>`; `gh pr create` with the evidence-case raw output. **DO NOT merge** — goes to review (+ folk lane needs to see it for the gate side).
