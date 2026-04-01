# Plan: Fix B2 Plans Properly (Issue #1116)

## Context

Issue #1116 requires all B2 plans to be complete, correct, and aligned with the Ukrainian State Standard 2024. Gemini wrote most plans in earlier iterations but they were found wanting across 5 review rounds. Gemini's latest attempt (just reverted) rewrote 304 files, introduced YAML errors, downgraded word targets, and destroyed schemas. All reverted.

## Two Problems

### Problem 1: Missing fields in existing 89 plans
- ❌ 85/89 missing `activity_hints`
- ❌ 86/89 missing `references`
- ❌ 11 missing `reading_situations`, 16 missing `writing_tasks`
- ❌ 4 YAML parse errors, 7 English headers, 1 orphan file

### Problem 2: State Standard 2024 coverage gaps (AFTER cross-level reconciliation)

Initial B2-only analysis found 6 gaps. Cross-level reconciliation against B1/C1/C2 **eliminated 2 false gaps** (topics already covered at B1):

| # | Gap | SS Section | Severity | Action |
|---|-----|-----------|----------|--------|
| ~~1~~ | ~~Prefixed motion verbs~~ | ~~SS 4.2.4~~ | ~~HIGH~~ | **FALSE GAP** — B1 has 7 dedicated modules on motion verb prefixes |
| ~~2~~ | ~~Adj/adv comparison~~ | ~~SS 4.2.1-2~~ | ~~HIGH~~ | **FALSE GAP** — B1 has 3 comparison modules + adverb comparison. Expand existing B2 module for register usage only |
| 3 | **Advanced pronouns** — reflexive себе, reciprocal один одного, definitive сам/самий/весь/кожний | SS 4.1.1.4 | 🟡 MED-HIGH | **New module**: `pronoun-system-advanced` |
| 4 | **Collective & fractional numerals** — двоє/троє, одна друга, півтора | SS 4.1.1.3 | 🟡 MEDIUM | Expand `numeral-declension-compound-numbers` |
| 5 | **Advanced noun declension** — невідмінювані, іншомовні, -у/-ю alternation | SS 4.1.1.1 | 🟡 MEDIUM | Expand `advanced-case-semantics` or new module |
| 6 | **Zero-suffix deverbals** — переїзд, розгляд, виклик | SS 4.2.7 | 🟢 LOW-MED | Add section to `word-formation-abstract-nouns` |

**Revised proposal:** Add 1 new module (#3) + expand 3 existing modules (#2,4,6). Decide on #5 during Group 5. B2 goes from 89 → 90 modules. Update `curriculum.yaml`.

Full analysis: `docs/plans/cross-level-reconciliation.md` + `docs/plans/ethereal-sniffing-locket-agent-aabf0cb1111959685.md`

## Approach: Group-by-Group, Not Batch

Plans are lesson blueprints. Each one determines how a real person learns a topic. The approach is to work through the 89 modules in their natural pedagogical groups, doing RAG research per topic area, reviewing existing content, and adding missing fields with proper grounding.

**Why not field-by-field (all activity_hints first, then all references)?**
- RAG research is topic-clustered — searching for "пасивний стан" returns results for modules 1-10 simultaneously
- Activity hints and references are interdependent — both need the same textbook grounding
- Cross-module coherence within groups — activity progression shouldn't repeat

## New Module Placement (if approved)

| New Module | Insert After | Group | Rationale |
|-----------|-------------|-------|-----------|
| `pronoun-system-advanced` | `advanced-case-semantics` (M57) | 6: Lexicology | Case semantics → pronouns in cases — natural pairing |

This module needs a FULL plan written from scratch with RAG research, State Standard alignment, and all required fields.

**Also update `curriculum/l2-uk-en/curriculum.yaml`** — add the new module entry. B2 goes from 89 → 90 modules.

## Phase 0: Mechanical Fixes

Do these first, they're deterministic and safe.

| Fix | Files | What |
|-----|-------|------|
| Delete orphan | `passive-voice.yaml` | Not in curriculum.yaml, superseded by `passive-voice-system.yaml` |
| Fix YAML | `word-formation-abstract-nouns.yaml` | Remove trailing `,` after `focus_points` array (line 27) |
| Fix YAML | `word-formation-adjective-formation.yaml` | Same pattern |
| Fix YAML | `word-formation-adverbs-integration.yaml` | Same pattern |
| Fix YAML | `word-formation-place-object-names.yaml` | Same pattern |
| Fix English | `news-analysis-basics.yaml` | `"Джерела та перевірка фактів (Fact-checking)"` → `"Джерела та верифікація фактів"` |
| Fix English | `professional-email-advanced.yaml` | `"Супровідні та мотиваційні листи (Cover Letters)"` → `"Супровідні та мотиваційні листи"` |
| Fix English | `professional-reports-advanced.yaml` | `"Адаптація звіту під аудиторію (Stakeholder Management)"` → `"Адаптація звіту під цільову аудиторію"` |

**Validate:** Run YAML parse check on all 89 files after fixes.

## Phases 1-8: Group-by-Group Deep Fix

### Workflow per group:

1. **RAG research** — search textbooks for the group's topic area (Заболотний Grade 9-11, Авраменко)
2. **Read each plan** — check all required fields against AC checklist
3. **Add missing fields** with proper grounding:
   - `activity_hints` (3-5) — must test LANGUAGE not content
   - `references` — real textbook pages from RAG + State Standard sections
   - `reading_situations` / `writing_tasks` where missing
4. **Version bump** each modified plan
5. **Validate** — YAML parse, field presence, outline sum = 4000

### Group schedule:

| Phase | Group | Modules | Plans | Topic |
|-------|-------|---------|-------|-------|
| 1 | Passive Voice | M01-M10 | 10 | Passive constructions, participles |
| 2 | Syntax | M11-M24 | 14 | Phrases, sentence members, complex sentences |
| 3 | Stylistics & Register | M25-M38 | 14 | Stylistic devices, functional styles |
| 4 | Domain Vocabulary | M39-M42 | 4 | Politics, law, economics |
| 5 | Advanced Morphology | M43-M56 | 14 | Aspect, pluperfect, numerals, word formation |
| 6 | Lexicology | M57-M68 | 12 | Synonymy, proverbs, idioms, neologisms |
| 7 | Professional Comm | M69-M80 | 12 | Emails, reports, presentations |
| 8 | Content & Capstone | M81-M89 | 9 | Domain content, capstones, final exam |

### Per-plan checklist:

```
[ ] word_target: 4000
[ ] content_outline sections sum to 4000
[ ] reading_situations (1-2)
[ ] writing_tasks (1-2) with model_answer
[ ] listening_situations OR discussion_topics (1+)
[ ] activity_hints (3-5, type/focus/items)
[ ] references (textbook pages + State Standard)
[ ] No English in section headers
[ ] YAML parses cleanly
[ ] version bumped
```

## Verification

After each group:
- YAML parse check on all modified files
- Run the B2 audit script: `.venv/bin/python -c "..."` to check field presence
- Spot-check activity_hints: "Does this test a linguistic skill or content recall?"

After all groups:
- Full B2 audit sweep
- Adversarial review via Gemini

## Critical Files

- `curriculum/l2-uk-en/plans/b2/*.yaml` — the 89 plan files
- `docs/l2-uk-en/state-standard-2024-mapping.yaml` — B2 section (line ~2452)
- `docs/best-practices/b2-c2-plan-architecture.md` — field format reference
- `scripts/audit/config.py` — B2 audit thresholds
