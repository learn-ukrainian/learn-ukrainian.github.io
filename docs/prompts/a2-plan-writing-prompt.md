# A2 Plan Writing — Gemini Interactive Prompt

> Use this in a Gemini interactive session with RAG access.
> Process one phase at a time (6-7 modules per phase, 8 phases total).
> After each phase, commit the plans and review before continuing.

## Session setup

Start Gemini with project context:
```bash
gemini -m gemini-3.1-pro-preview
```

Then paste the prompt below, replacing {PHASE} with the current phase (A2.1, A2.2, etc.).

---

## Prompt

You are writing plan YAMLs for the A2 level of a Ukrainian language curriculum. These plans are the source of truth for content generation — they must be detailed, accurate, and grounded in Ukrainian textbook pedagogy.

### Your tools
- **search_text** — search Ukrainian textbooks (Grades 1-11) for grammar explanations and examples
- **verify_word / verify_words** — check Ukrainian words exist in VESUM (409K lemmas)
- **search_literary** — search literary sources for usage examples
- **query_pravopys** — check Ukrainian orthography rules

### What you're writing

A2 plans for phase **{PHASE}**. The curriculum design is in `docs/l2-uk-en/A2-CURRICULUM-V3.md`. Read the relevant phase table to get: sequence, slug, title, focus, core content.

### Plan format

Follow the B1 plan format exactly. Example: `curriculum/l2-uk-en/plans/b1/adjectives-comparative.yaml`

Each plan YAML must have:
- `module`, `level` (A2), `sequence`, `slug`, `version` ('1.0'), `title`, `subtitle` (Ukrainian)
- `focus` (grammar/communication/review/bridge), `pedagogy` (PPP/review), `phase`
- `word_target`: 2000 (regular) or 1500 (checkpoint) — check with: `.venv/bin/python -c "import sys; sys.path.insert(0, 'scripts'); from audit.config import LEVEL_CONFIG; print(LEVEL_CONFIG['A2'])"`
- `objectives`: 4-5 specific, measurable outcomes
- `content_outline`: 4-5 sections with `section` (Ukrainian title), `words`, `points` (detailed, with textbook references)
- `vocabulary_hints`: `required` (8-12 words with translations) + `recommended` (5-8)
- `activity_hints`: 3-4 exercises with `type`, `focus`, `items`
- `connects_to`, `prerequisites`, `grammar`, `register`, `references`

### Quality requirements

1. **Search textbooks** for every grammar point. Cite: "Заболотний Grade 5, §12" or "Авраменко Grade 7, p.45"
2. **Verify every vocabulary word** with verify_word/verify_words before adding to vocabulary_hints
3. **Use Ukrainian section titles** — "Родовий відмінок без прийменника", not "Grammar 1"
4. **Include real Ukrainian examples** in section points — not just rules, but example sentences
5. **Track vocabulary progression** — don't repeat words from A1 (check curriculum/l2-uk-en/plans/a1/ for what's already taught)
6. **Match the design doc** — every grammar point from the Core Content column must appear in the plan

### Process

For each module in the phase:
1. Read the design doc entry (slug, title, focus, core content)
2. Search textbooks for the grammar topic
3. Write the plan YAML
4. Verify vocabulary with VESUM
5. Output the complete YAML

Write all plans for this phase, then I'll review and commit.

### Phase {PHASE} modules

Read from `docs/l2-uk-en/A2-CURRICULUM-V3.md`, section "A2.{N}".

---

## Phase order

Run 8 sessions total:
1. A2.1: Foundation + Aspect (M01-M07) — 7 plans
2. A2.2: Genitive Complete (M08-M14) — 7 plans
3. A2.3: Dative (M15-M20) — 6 plans
4. A2.4: Instrumental (M21-M27) — 7 plans
5. A2.5: Case Synthesis + Plurals (M28-M34) — 7 plans
6. A2.6: Aspect + Motion (M35-M41) — 7 plans
7. A2.7: Complex Syntax (M42-M47) — 6 plans
8. A2.8: Refinement + Graduation (M48-M60) — 13 plans
