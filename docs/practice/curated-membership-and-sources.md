# Curated Practice membership, expansion, and multi-mode sources

**Status:** binding operator policy (2026-08-02)  
**Epic:** #4387 · Mandate board: #6132  
**Related:** #6188 (cloze coverage), #6143 (CEFR soft guidance), #4223 / #4220 (Ohoiko intake), #3797 (reviewed cloze), Track T in `docs/plans/2026-07-27-atlas-practice-gradual-ramp.md`

This document is the durable memory for **what belongs in the Curated / teacher Practice pool**, **how we expand without discarding existing work**, and **where content for each activity mode may come from** (not cloze alone). Agents must not invent a narrower “done” bar.

After each 2×2 teacher-lesson cycle, an operator runs the local teacher-table sync command with the approved exact heading, reviews the reported count, and commits the public lemma-only set. In the picker, that set is **📋 Приклад розробника / Dev's example deck**: a shared example from the developer's classroom list.

---

## 1. Membership = union (never throw away the 5k)

| Layer | Approx scale (tool-remeasure when shipping) | Role |
| --- | ---: | --- |
| **A. Homework / teacher curated table** | ~1037 rows / ~1019 unique lemmas (package expected original ~1018) | **Mandatory floor** — every lemma the learner must practice from the homework table |
| **B. Teacher-lesson inventory Curated Deck** | ~5093–5096 lemmas (UI keys from `lexicon-teacher-cloze.json` / intake `auto_merge`) | **Keep** — multi-year lesson inventory; welcome richness; **not** a substitute for A |
| **C. Inspiration lemma queues** | Ohoiko «1000 words», «500+ verbs», ULP notes, related inventory | **Expand candidates** — lemma + level priors only (see §3) |

**Binding rules**

1. **Do not remove B to “focus on A.”** Target membership is **A ∪ B ∪ C_lemmas** (after VESUM cleanup).  
2. **A is mandatory:** residual count for homework-table unique lemmas not in Curated/practice membership must go to **0** (or tool-proved impossible), measured after each ship.  
3. **B is not discarded** when A is incomplete — **add missing A** into membership; keep all of B.  
4. The public UI “Curated Deck” (~5k keys) historically came from intake auto-merge + cloze bake, **not** from selecting only A. Agents must not treat “5k list” as identical to “homework table.”  
5. Local package SSOT for A: `.claude/atlas-epic/plans/curated-seed/` (private dual-write; full master document never in public git). Design **DC-E** still holds: document curated table is Practice seed vocabulary authority for Track T.

---

## 2. Multi-mode activities — not every mode needs a sentence

Practice is multi-mode. **Cloze is only one surface.** Coverage work must unlock modes that do not require curated prose first.

| Mode | Needs full sentence? | Primary data sources |
| --- | --- | --- |
| Flashcards | No | Atlas lexeme: lemma, gloss, IPA, paradigm |
| Matching | No | lemma ↔ gloss |
| Choice (meaning MC) | No | lemma + gloss + same-POS distractors |
| Stress | No | stress form (atlas / VESUM / stress dict) |
| Classify | No | POS / semantic buckets from atlas |
| Paradigm | No | morphology paradigm + VESUM verification |
| Synonym | No | reviewed pairs (`data/lexicon/synonym_pair_verdicts.yaml`) |
| Heritage | No | `data/lexicon/heritage_pairs.yaml` |
| Paronym | No | reviewed paronym sets in deck |
| **Cloze** | **Yes** | Public / rights-clear sentences only (§4) |

**Priority for factory work**

1. Lemma admitted to practice + atlas (gloss, paradigm, CEFR prior) → recognition + structure modes.  
2. Pair modes when reviewed pair data exists.  
3. Cloze when a **rights-clear** blankable sentence exists.  
4. Residual cloze without a public sentence is honest residual — word remains playable in non-sentence modes.

---

## 3. Inspiration sources (Ohoiko / ULP / 1000 words / 500 verbs)

**Allowed**

- Use **lemma / headword candidates** as a priority queue (“these words matter”).  
- Use **first-seen / book tier / list membership as CEFR or practice-level priors** (soft guidance; see #6143).  
- Normalize typos and multiword mess with **VESUM**.  
- Extract **pedagogy patterns** (see `docs/best-practices/ulp-presentation-pattern.md`) for our own curriculum writing.  
- Link out to external ULP/Ohoiko products where product policy allows.

**Forbidden (IP / rights)**

- **No verbatim** ULP lesson notes, book pages, exercises, glossary definitions, or proprietary list packaging in public product text.  
- Private Ohoiko/ULP corpora under gitignored private paths stay **local reference only** (`docs/corpus-inventory.md`: never quote verbatim in pipeline outputs).  
- Do not ship her materials as “our list” in learner-facing form (order, framing, and book text remain hers).  
- Do not use private teacher-lesson **prose** as public cloze without explicit rights GO (words may be admitted under local/private policy separately).

**Leveling prior (soft)**

| Inspiration signal | Soft prior (not hard gate) |
| --- | --- |
| Early ULP / A1-oriented materials / 1000-words core | A1 bias |
| 500 verbs / mid ULP | A2–B1 bias |
| Late ULP denser notes | B1+ bias |
| Conflict with atlas CEFR or homework context | Prefer atlas + homework context; keep Ohoiko as `level_prior` provenance only |

Never present “level from Ohoiko book” as a learner-facing citation of her work.

---

## 4. Where sentences come from (cloze + optional examples)

### Public / redistributable (default for live site)

| Source | Role |
| --- | --- |
| School textbooks in `data/sources.db` (`textbooks` / `textbooks_fts`) | Primary public sentence mine |
| `site/src/data/lexicon-sentence-inventory.json` | Provenanced inventory for cloze regen |
| Reviewed allowlists (`lexicon-practice-cloze-sources.json`, reviewed sources) | Fail-closed vetted frames |
| Tatoeba (full license + IDs) | Open-license sentences with attribution |
| Our published curriculum modules | Project-owned examples |
| Other corpora only if `source_license_map` / rights policy allows | Residual fill |

### Private / local-only (not public product text)

| Source | Role |
| --- | --- |
| ULP notes, Ohoiko books | Lemma + level prior; **never** public cloze body |
| Private teacher materials | Local practice / rights-gated; not silent public export |

### Project-authored

| Artifact | Role |
| --- | --- |
| Glosses, distractors, case rules, UI chrome | Always ours |
| Original example sentences when no public hit | Optional; labeled project-authored; quality gate required |

**Rule of thumb for the fleet:**  
**Words** from homework ∪ teacher inventory ∪ inspiration lemmas;  
**sentences** from public textbooks / open licenses / our modules;  
**never** from Ohoiko/ULP or private lesson prose on the public site.

Generator entrypoint: `scripts/audit/generate_practice_deck.py` (inventory, allowlists, synonym/heritage YAML, atlas morphology).

---

## 5. Deploy readiness (operator bars)

Public deploy is **manual** (`deploy-pages.yml` / `workflow_dispatch`). Do not call “ready for live” until tool-backed:

1. **Primary:** rich multi-mode membership for **A ∪ B** (homework floor + keep 5k); cloze residual only tool-proved for public sentence gaps.  
2. **Secondary:** current atlas pin acceptable or explicitly refreshed.  
3. **UX:** Curated session playable (selection perf shipped #6252); no invented partial-done thresholds.

Measure examples (re-run, do not trust memory):

- Homework unique lemmas in curated keys / practice index  
- Curated 5k still present (no silent shrink)  
- Per-mode eligibility counts (not card vanity alone)  
- Cloze: `clozeEligibleLexemes / practice_lexemes` by level (#6188)

---

## 6. Related tickets (see GH inventory comments for live state)

| Ticket | Role under this policy |
| --- | --- |
| #4387 | Umbrella epic |
| #6132 | Practice factory + any-deck mandate board |
| #6188 | Cloze coverage metric (sentence layer) |
| #6143 | CEFR soft guidance (inspiration priors fit here) |
| #3797 | Reviewed cloze sources |
| #4220 / #4223 | Ohoiko / full-corpus intake (lemma layer) |
| #4700 | Practice/Atlas UX |
| #6135–#6140 | Mode factory subtasks (non-sentence + pairs) |
| #5790 / #6064 | Teacher seed / residual (historical; check open state) |

Track T in the gradual-ramp plan remains: homework list in Practice **immediately**, parallel to atlas-wide ramp — **without** dropping the larger curated inventory.

---

## 7. OPSEC

Public issues, PRs, commits, and this doc use **teacher** only for private people. No personal names in the public tree.

X-Agent: grok-atlas  
Operator session: 2026-08-02
