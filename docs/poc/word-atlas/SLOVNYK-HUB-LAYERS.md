# Slovnyk multi-dict hub — Atlas lemma page design

**Status:** proposed implementation standard (2026-08-08)  
**Tracks:** #6460 · design #6461 · epic #4387  
**Supersedes for content fill:** thin mphdict/WordNet-first synonym chips; single-blob idioms; davydov-as-warning-only.

## Problem

slovnyk.me exposes ~70 dictionary surfaces. Independent multi-lemma sampling shows high-value UA layers that the Word Atlas PoC named only partially and that production filled poorly (truncation, flat synonyms, amalgamated phraseology, missing proverbs/usage essays).

## Design change (summary)

Treat each lemma page as a **typed hub of dictionary layers**, not a single scraped gloss plus chips.

### Learner section order

1. Header (lemma, stress, POS, CEFR, heritage)
2. **Значення** — multi-sense defs (VTS primary; optional SUM-20 examples; optional Грінченко heritage card)
3. **Синоніми за значеннями** — sense nests (`synsets`), not only flat chips
4. **Фразеологізми** — multi-item (one head phrase per card)
5. **Приповідки** — new section
6. **Стиль і норма (Як ми говоримо)** — full davydov essays when present; voloschak/shtepa full notes when corrective
7. **Переклад (EN)** — ukreng / dmklinger only (not ukrrus as pillar)
8. **Етимологія** — stages if evidenced; else short Kaikki inheritance (no invented OES→Middle UA)
9. **Морфологія** — VESUM (+ compact orthography/holoskevych/orthoepy strip)
10. Literature / course / external — as today

### Source policy

| Prefer | Avoid as default learner pillars |
| --- | --- |
| vts, newsum, synonyms, phraseology, proverbs, davydov, hrinchenko, orthography, holoskevych, orthoepy, slang_lviv (labelled), ukreng | ukrrus/rusukr; domain encyclopedias; inventing etymology stages |

### Data shapes

```text
sections.synonyms = { items[], synsets[{id, gloss?, members[{lemma, stressed, gloss?}]}], source, source_urls }
sections.idioms = { items[{phrase, text, definition, source}], source, source_urls }
sections.proverbs = { items[{text, gloss?, source}], source, source_urls }   # NEW
sections.usage_notes = { items[{title?, text, source, source_url}], source }  # NEW (davydov family)
```

### Quality rules

- No mid-definition / mid-idiom hard cuts
- One idiom head = one item; one synonym sense nest = one synset
- Always source pill + official URL when known
- Residual after re-enrich must be counted (coverage %), never invented “done”

### Disk / deploy hygiene

- Mass re-enrich on VPS atlas-runner
- Reap worktrees/temps after each large job; keep ≥15% free when possible
- No sealed formal CF / multi-GB lu-review trees
- Publish shard pointer only with integrity hashes + residual metrics

## Implementation map (GH)

| Issue | Scope |
| --- | --- |
| #6458 | No mid-definition truncation |
| #6459 | Sense synonyms + multi-idioms |
| #6462 | Proverbs |
| #6463 | Davydov usage essays |
| #6464 | Грінченко definition card |
| #6465 | Form strip (orthography/holoskevych/orthoepy) |
| #6466 | Full-catalog re-enrich + export + disk budget |

## Discovery note (2026-08-08)

~73 slovnyk dict slugs observed. Sample hit rates (10 lemmas) ranked vts/newsum/sum/synonyms/phraseology/proverbs/orthography/holoskevych/slang_lviv as high-coverage learner-relevant; many bilingual RU-facing dicts high-coverage but excluded as pillars.


## Cross-agent review deltas (2026-08-08)

### Gemini / AGY (language) — fold into UX order
- Elevate **EN gloss** to header dual-anchor (monolingual VTS still primary).
- Elevate **morphology / stress strip** earlier (not buried under enrichment).
- Davydov: **structured summary + expand full essay** (not dump full text in-flow).
- Progressive disclosure: top card always on; synonym nests per sense; phraseology/proverbs expandable with counts.

### Kimi K3 (design) — **APPROVE** with required schema deltas
1. `usage_notes` must include block-level `source_urls` + `mirror_source_urls` split (УМІФ attribution).
2. Proverb section items: optional `entry_slug?` when a standalone `proverb` entry exists (dedup with entry model).
3. `gloss?` on proverbs = **UK paraphrase only** (EN stays in translation layer).
4. Policy: **data stores full text**; UI may first-paragraph+expand for long davydov essays; register new section keys in conformance gates before publish.
5. Ship **phased** (#6458 → #6459 → additive #6462–#6465 → #6466 full re-enrich last).

### Revised “always visible” top card
Lemma + stress/IPA + POS + aspect link (verbs) + quick EN gloss + primary VTS senses + compact VESUM strip.

