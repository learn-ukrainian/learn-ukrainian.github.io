# Phase Workflow Analysis

Investigation into splitting current 4-stage workflow into 8-phase workflow.

## Current State

| File | Lines | Purpose |
|------|-------|---------|
| stage-1-skeleton.md | 160 | Create meta |
| stage-2-content.md | 296 | Write prose |
| stage-3-activities.md | 858 | Create activities |
| stage-4-review-fix.md | 868 | Validate EVERYTHING |
| module-stage-*.md | 808 | Command wrappers |
| review-content*.md | 2,879 | Quality checks |
| **TOTAL** | **~6,400** | |

**Problem:** Stage 4 tries to validate everything at once (900 lines). LLM doesn't read it all.

---

## Proposed 8-Phase Structure

### Phase 1: HYDRATE

**Creates:** `meta/{slug}.yaml`
**Reads:** curriculum plan, outline

### Phase 2: HYDRATE-QA

**Validates:** meta.yaml only

| Check | Source |
|-------|--------|
| Required fields present | validate_required_metadata |
| Word target reasonable for level | config.py |
| Objectives use proper verbs | manual |
| Outline sections have word counts | check_outline_compliance |
| Activity hints match pedagogy | check_seminar_meta_requirements |
| Sources listed | manual |

### Phase 3: CONTENT

**Creates:** `{slug}.md`
**Reads:** meta.yaml (LOCKED)

### Phase 4: CONTENT-QA

**Validates:** prose only (no activities yet)

| Check | Source |
|-------|--------|
| Word count vs target | evaluate_word_count |
| Sections match outline | check_outline_compliance |
| Has cultural callouts | evaluate_engagement |
| No Russianisms | check_content_quality |
| No AI contamination | AI_CONTAMINATION_PATTERNS |
| No "The Ukraine" / "Kiev" | validate_tone |
| Richness score | evaluate_richness |
| Naturalness score | evaluate_naturalness |
| Markdown format | check_markdown_format |
| Section order | check_section_order |
| No forbidden patterns | check_content_quality |
| State standard compliance | check_state_standard_compliance |

**NOT checked here (no activities yet):**
- Immersion % (only for A1-A2, and those are mostly done)
- Activity counts
- Activity schemas

### Phase 5: ACTIVITIES

**Creates:** `activities/{slug}.yaml`
**Reads:** meta.yaml (LOCKED), {slug}.md (LOCKED)

### Phase 6: ACTIVITIES-QA

**Validates:** activities only

| Check | Source |
|-------|--------|
| YAML schema valid | check_activity_yaml_schema |
| Activity count meets minimum | evaluate_activity_count |
| Item density per activity | evaluate_density |
| Type variety | evaluate_unique_types |
| Priority types present | evaluate_priority_types |
| Mark-the-words format | check_mark_the_words_format |
| No hints in activities | check_hints_in_activities |
| Error-correction format | check_error_correction_format |
| Cloze syntax | check_cloze_syntax_errors |
| Unjumble word match | check_unjumble_word_match |
| Reading-analysis pairing (seminar) | check_seminar_reading_pairing |
| External URLs valid (seminar) | check_external_resources |
| Model answers present | manual |
| Activity naturalness | evaluate_naturalness (activity text) |
| No English hints in A2+ | check_english_hints_in_activities |
| Morpheme patterns valid | check_morpheme_patterns |

### Phase 7: VOCABULARY

**Creates:** `vocabulary/{slug}.yaml`
**Reads:** meta.yaml, {slug}.md, activities.yaml (ALL LOCKED)

### Phase 8: VOCABULARY-QA

**Validates:** vocabulary only

| Check | Source |
|-------|--------|
| Schema valid (lemma, ipa, pos, gender) | schema |
| Count reasonable | evaluate_vocab |
| Words appear in content OR activities | check_vocabulary_integration |
| Words are NEW to level | check against cumulative DB |
| IPA format correct | manual/script |
| No duplicates | script |

---

## Checks That Span Multiple Phases

| Check | Currently | Solution |
|-------|-----------|----------|
| Immersion % | content + activities | A1-A2 only; B2+ is 100% immersed by definition |
| Vocabulary integration | vocab vs content + activities | Run in phase 8 after all exist |
| LLM self-validation | separate file | Run after activities-qa, before vocabulary |

---

## Review-Content Features Mapping

| Feature | Current | Proposed Phase |
|---------|---------|----------------|
| Template compliance | review-content §0 | hydrate-qa + content-qa |
| Coherence (1-5) | review-content §1 | content-qa |
| Relevance (1-5) | review-content §2 | content-qa |
| Educational value (1-5) | review-content §3 | content-qa |
| Language quality (1-5) | review-content §4 | content-qa |
| Pedagogical correctness (1-5) | review-content §5 | content-qa |
| Natural immersion (1-5) | review-content §6 | content-qa (B2+ = 100%) |
| Word salad check | review-content §7 | content-qa |
| Activity structural integrity | review-content §8a | activities-qa |
| Activity grammar + naturalness | review-content §8b | activities-qa |
| Difficulty calibration | review-content §8c | activities-qa |
| Distractor quality | review-content §8d | activities-qa |
| Activity engagement | review-content §8e | activities-qa |
| Activity variety | review-content §8f | activities-qa |
| External resources | review-content §8g | activities-qa |
| Red flags (auto-fail) | review-content §9 | content-qa + activities-qa |
| Content richness | review-content §10 | content-qa |
| Dryness flags | review-content §12 | content-qa |
| LLM fingerprint detection | review-content §13 | content-qa |
| Human warmth | review-content §14 | content-qa |
| Richness red flags | review-content §15 | content-qa |

---

## Feasibility Assessment

### CAN this be done?

**YES.** The checks are naturally separable:
- Meta checks don't need content
- Content checks don't need activities
- Activity checks don't need vocabulary
- Vocabulary checks run last with read access to everything

### Dependencies are read-only:

```
hydrate → (locked) → content → (locked) → activities → (locked) → vocabulary
                ↓                    ↓                      ↓
          content-qa           activities-qa          vocabulary-qa
```

No phase modifies outputs of previous phases.

### IS it worth doing?

**Arguments FOR:**
1. Smaller, focused prompts = LLM actually reads them
2. Clear separation = easier to debug failures
3. Locked phases = no gaming (agent can't change meta to pass audit)
4. Activities can be rebuilt without touching vetted content
5. Vocabulary computed properly from cumulative DB
6. Work can be delegated (different people/agents per phase)

**Arguments AGAINST:**
1. More steps = more overhead for simple modules
2. Some checks currently run together efficiently
3. Need to maintain 8 prompts instead of 4

### Recommendation

**DO IT** for content-heavy modules (B2-HIST, C1-BIO, LIT).

For simple A1-A2 modules, current workflow may be fine since those are mostly done.

---

## Next Steps (if approved)

1. [ ] Create GitHub milestone: "Phase Workflow Refactor"
2. [ ] Issue: Design hydrate + hydrate-qa prompts
3. [ ] Issue: Design content + content-qa prompts
4. [ ] Issue: Design activities + activities-qa prompts
5. [ ] Issue: Design vocabulary + vocabulary-qa prompts
6. [ ] Issue: Update audit_module.py to support --phase flag
7. [ ] Issue: Create orchestrator command
8. [ ] Issue: Update documentation
9. [ ] Issue: Test on 3 b2-hist modules
10. [ ] Issue: Migrate remaining modules
