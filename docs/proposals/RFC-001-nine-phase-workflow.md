# RFC-001: Nine-Phase Module Workflow

**Status:** Draft
**Author:** Claude (with user direction)
**Created:** 2026-01-21
**Target:** Tracks (b2-hist, c1-bio, lit) + C2 levels

---

## Executive Summary

Replace the current 4-stage module workflow with a 9-phase workflow for content-heavy modules. The primary goal is creating smaller, focused prompts that LLMs actually read and follow.

**Key changes:**
- Split monolithic Stage 4 (900+ lines) into 4 focused QA phases
- Lock each phase's output before proceeding (no retroactive modifications)
- Add integration phase to verify cross-file alignment
- Parallel rollout: new workflow for tracks + C2 only

---

## Problem Statement

### Current State

| File | Lines | Purpose |
|------|-------|---------|
| stage-1-skeleton.md | 160 | Create meta |
| stage-2-content.md | 296 | Write prose |
| stage-3-activities.md | 858 | Create activities |
| stage-4-review-fix.md | 868 | Validate EVERYTHING |
| module-stage-*.md | 808 | Command wrappers |
| review-content*.md | 2,879 | Quality checks |
| **TOTAL** | **~6,400** | |

### Core Issues

1. **Stage 4 is monolithic** - 900+ lines trying to validate everything at once. LLMs don't read it all, leading to missed checks.

2. **No phase locking** - Agents have modified meta.yaml to pass audit checks, which is unacceptable. Once a phase is finalized, it must be immutable.

3. **Review-content features scattered** - Quality checks split across multiple files with unclear ownership.

4. **No integration verification** - No explicit check that meta, content, activities, and vocabulary align with each other.

---

## Proposed Solution

### 9-Phase Workflow

```
┌─────────────────┐     ┌─────────────────┐
│  module-meta    │────▶│  module-meta-qa │
└─────────────────┘     └────────┬────────┘
                                 │ LOCKED
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│  module-lesson  │────▶│ module-lesson-qa│
└─────────────────┘     └────────┬────────┘
                                 │ LOCKED
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│  module-act     │────▶│  module-act-qa  │
└─────────────────┘     └────────┬────────┘
                                 │ LOCKED
                                 ▼
┌─────────────────┐     ┌─────────────────┐
│  module-vocab   │────▶│ module-vocab-qa │
└─────────────────┘     └────────┬────────┘
                                 │ LOCKED
                                 ▼
                        ┌─────────────────┐
                        │ module-integrate│
                        └─────────────────┘
```

### Phase Descriptions

| Phase | Creates | Reads | Validates |
|-------|---------|-------|-----------|
| **1. module-meta** | `meta/{slug}.yaml` | Curriculum plan, outline | - |
| **2. module-meta-qa** | - | meta.yaml | Required fields, word targets, objectives, activity hints |
| **3. module-lesson** | `{slug}.md` | meta.yaml (LOCKED) | - |
| **4. module-lesson-qa** | - | meta.yaml, {slug}.md | Word count, sections, richness, naturalness, no AI contamination |
| **5. module-act** | `activities/{slug}.yaml` | meta + content (LOCKED) | - |
| **6. module-act-qa** | - | All above | Schema, counts, density, types, format rules |
| **7. module-vocab** | `vocabulary/{slug}.yaml` | All above (LOCKED) | - |
| **8. module-vocab-qa** | - | All files | Schema, counts, integration, uniqueness |
| **9. module-integrate** | - | All files | Cross-file alignment, final validation |

### Locking Mechanism

**Implementation:** Instruction-based, not tooling-based.

Each phase prompt explicitly states:
> "The following files are LOCKED and must NOT be modified: [list]. If you cannot pass validation without modifying locked files, STOP and report the issue."

Rationale: If an agent cannot follow this simple instruction, the problem is the agent, not the tooling. Adding hash checks or write blockers adds complexity without solving the root cause.

### Phase Rewind Protocol

When a fundamental flaw is found in a locked file that blocks progress:

1. Agent outputs: **"PHASE UNLOCK REQUIRED: [reason]"**
2. Agent identifies which upstream phase needs correction
3. Agent fixes the upstream file
4. Agent re-runs the QA phase for that upstream file
5. Only after upstream QA passes, agent resumes the blocked phase

Example:
```
PHASE UNLOCK REQUIRED: meta.yaml activity_hints specify "quiz" but
content has no factual recall material suitable for quiz questions.

Rewinding to: module-meta
Fix: Update activity_hints to match actual content possibilities
Re-running: module-meta-qa
```

This ensures locked files are only modified through explicit, auditable rewind - not silently edited to pass validation.

---

## Design Details

### Phase 1: module-meta

**Creates:** `meta/{slug}.yaml`

**Input:**
- Curriculum plan for the level
- Module position in sequence
- Previous modules' vocabulary (for cumulative tracking)

**Output structure:**
```yaml
module_type: history  # or: grammar, vocabulary, cultural, biography, integration
title: "Трипільська культура"
slug: trypillian-civilization
level: B2
word_target: 1200
estimated_duration_minutes: 45

objectives:
  - Describe Trypillia settlements and artifacts
  - Explain agricultural practices of Trypillian culture
  - Analyze significance of Trypillia for Ukrainian identity

content_outline:
  - heading: "Відкриття Трипілля"
    word_target: 200
    key_points:
      - Discovery by Vikentiy Khvoyka
      - Dating and geographical extent
  - heading: "Побут та господарство"
    word_target: 350
    key_points:
      - Agriculture and animal husbandry
      - Pottery and crafts

vocabulary_hints:
  - городище
  - розкопки
  - кераміка

activity_hints:
  - type: reading
    focus: Primary source excerpt
  - type: quiz
    focus: Factual recall
  - type: essay-response
    focus: Significance analysis

sources:
  - "Археологія України" - standard reference
  - National Museum of History resources
```

### Phase 2: module-meta-qa

**Validates:**

| Check | Source | Pass Criteria |
|-------|--------|---------------|
| Required fields | schema | All present |
| word_target | config.py | Within level range (B2: 1000-1500) |
| objectives | manual | Use measurable verbs (describe, explain, analyze, compare) |
| content_outline | check_outline_compliance | Each section has word_target |
| activity_hints | check_seminar_meta_requirements | Match pedagogy for module type |
| sources | manual | At least 2 listed |

**Output:** PASS or list of violations with fix instructions.

### Phase 3: module-lesson

**Creates:** `{slug}.md`

**Input:** meta.yaml (LOCKED)

**Constraints:**
- Follow content_outline exactly (headings, order, approximate word counts)
- Use vocabulary from vocabulary_hints
- Meet word_target (±10%)
- No activities in this file

**Output:** Markdown prose following template structure.

### Phase 4: module-lesson-qa

**Validates:**

| Check | Source | Pass Criteria |
|-------|--------|---------------|
| Word count | evaluate_word_count | Within 10% of target |
| Sections | check_outline_compliance | Match meta.content_outline |
| Cultural callouts | evaluate_engagement | Present for cultural/history modules |
| Russianisms | check_content_quality | None detected |
| AI contamination | AI_CONTAMINATION_PATTERNS | None detected |
| Political errors | validate_tone | No "The Ukraine", "Kiev" |
| Richness | evaluate_richness | Score ≥ 7/10 |
| Naturalness | evaluate_naturalness | Score ≥ 8/10 |
| Markdown | check_markdown_format | Valid structure |
| Section order | check_section_order | Matches template |
| Forbidden patterns | check_content_quality | None present |
| State standard | check_state_standard_compliance | Compliant |

**NOT validated here (no activities yet):**
- Activity counts
- Activity schemas
- Immersion % (B2+ is 100% immersed by definition)

### Phase 5: module-act

**Creates:** `activities/{slug}.yaml`

**Input:** meta.yaml + {slug}.md (LOCKED)

**Constraints:**
- Activity types follow activity_hints from meta
- Content references lesson material
- Item counts meet minimums per MODULE-RICHNESS-GUIDELINES-v2.md
- Reading activities properly linked to analysis activities

### Phase 6: module-act-qa

**Validates:**

| Check | Source | Pass Criteria |
|-------|--------|---------------|
| YAML schema | check_activity_yaml_schema | Valid |
| Activity count | evaluate_activity_count | Meets minimum |
| Item density | evaluate_density | Per guidelines |
| Type variety | evaluate_unique_types | Required types present |
| Priority types | evaluate_priority_types | Level-appropriate |
| mark-the-words | check_mark_the_words_format | Correct format |
| error-correction | check_error_correction_format | Correct format |
| cloze syntax | check_cloze_syntax_errors | Valid |
| unjumble | check_unjumble_word_match | Words match |
| reading-analysis | check_seminar_reading_pairing | Properly linked |
| external URLs | check_external_resources | Valid and accessible |
| naturalness | evaluate_naturalness | Score ≥ 7/10 |
| English hints | check_english_hints_in_activities | None in B2+ |
| morpheme patterns | check_morpheme_patterns | Valid |

### Phase 7: module-vocab

**Creates:** `vocabulary/{slug}.yaml`

**Input:** All previous files (LOCKED)

**Constraints:**
- Extract vocabulary appearing in content AND activities
- Check against cumulative vocabulary database
- Only include words NEW to this level
- Follow schema: lemma, ipa, translation, pos, gender (if applicable)

**Cumulative dependency:**
- Tracks (b2-hist, c1-bio, lit): A1 → B2 core vocabulary
- C2: A1 → C1 core vocabulary

### Phase 8: module-vocab-qa

**Validates:**

| Check | Source | Pass Criteria |
|-------|--------|---------------|
| Schema | vocabulary schema | Valid structure |
| Count | evaluate_vocab | Within range for level |
| Integration | check_vocabulary_integration | Words appear in content or activities |
| Uniqueness | cumulative DB check | Words are NEW to level |
| IPA format | format check | Valid IPA |
| Duplicates | script | None |

### Phase 9: module-integrate

> **CRITICAL ADDITION:** This phase addresses a major gap in current workflows. Today, nothing verifies that `activity_hints` in meta actually match generated activities, or that content outline headings match the actual prose sections. Phase 9 catches cross-file misalignments that per-file QA cannot detect.

**Final alignment check:**

| Check | Description |
|-------|-------------|
| Meta-content alignment | content_outline headings match {slug}.md sections |
| Meta-activities alignment | activity_hints types present in activities.yaml |
| Content-activities alignment | Activities reference content appropriately |
| Vocabulary integration | All vocab words appear in content or activities |
| File completeness | All 4 files exist and are non-empty |
| MDX generation | `npm run pipeline` succeeds |

**Output:** PASS (ready for publication) or FAIL with specific alignment issues.

---

## Check Distribution

### From Current stage-4-review-fix.md

| Current Location | New Phase |
|------------------|-----------|
| Required metadata validation | module-meta-qa |
| Word count checks | module-lesson-qa |
| Outline compliance | module-lesson-qa |
| Content quality (Russianisms, AI) | module-lesson-qa |
| Richness/naturalness | module-lesson-qa |
| Activity schema | module-act-qa |
| Activity counts/density | module-act-qa |
| Activity format checks | module-act-qa |
| Vocabulary schema | module-vocab-qa |
| Vocabulary integration | module-vocab-qa |

### From review-content.md

| Current Section | New Phase |
|-----------------|-----------|
| §0 Template compliance | module-meta-qa + module-lesson-qa |
| §1-§6 Quality scores | module-lesson-qa |
| §7 Word salad check | module-lesson-qa |
| §8a-§8g Activity checks | module-act-qa |
| §9 Red flags | module-lesson-qa + module-act-qa |
| §10-§15 Richness checks | module-lesson-qa |

---

## Implementation Plan

### File Changes

**New files to create:**

```
claude_extensions/
├── phases/
│   ├── module-meta.md          # Phase 1 prompt
│   ├── module-meta-qa.md       # Phase 2 prompt
│   ├── module-lesson.md        # Phase 3 prompt
│   ├── module-lesson-qa.md     # Phase 4 prompt
│   ├── module-act.md           # Phase 5 prompt
│   ├── module-act-qa.md        # Phase 6 prompt
│   ├── module-vocab.md         # Phase 7 prompt
│   ├── module-vocab-qa.md      # Phase 8 prompt
│   └── module-integrate.md     # Phase 9 prompt
├── commands/
│   ├── module-meta.md          # /module-meta command
│   ├── module-meta-qa.md       # /module-meta-qa command
│   ├── module-lesson.md        # /module-lesson command
│   ├── module-lesson-qa.md     # /module-lesson-qa command
│   ├── module-act.md           # /module-act command
│   ├── module-act-qa.md        # /module-act-qa command
│   ├── module-vocab.md         # /module-vocab command
│   ├── module-vocab-qa.md      # /module-vocab-qa command
│   └── module-integrate.md     # /module-integrate command
```

**Script changes:**

```
scripts/
├── audit_module.py             # Add --phase flag for phase-specific audits
└── audit/
    └── checks/
        ├── meta_validation.py  # Extract meta-specific checks
        ├── lesson_validation.py # Extract lesson-specific checks
        ├── activity_validation.py # Extract activity-specific checks
        └── vocab_validation.py # Extract vocab-specific checks
```

### Task Breakdown

| Task | Effort | Dependency |
|------|--------|------------|
| Create phase directory structure | S | - |
| Write module-meta phase prompt | M | - |
| Write module-meta-qa phase prompt | M | module-meta |
| Write module-lesson phase prompt | M | - |
| Write module-lesson-qa phase prompt | L | module-lesson |
| Write module-act phase prompt | M | - |
| Write module-act-qa phase prompt | L | module-act |
| Write module-vocab phase prompt | M | - |
| Write module-vocab-qa phase prompt | M | module-vocab |
| Write module-integrate phase prompt | M | All above |
| Create 9 command wrappers | S | All prompts |
| Add --phase flag to audit_module.py | M | - |
| Extract check modules | L | --phase flag |
| Test on 3 b2-hist modules | L | All above |
| Document new workflow | M | Testing complete |
| Update CLAUDE.md | S | Documentation |

**Effort key:** S = Small (< 1 hour), M = Medium (1-3 hours), L = Large (3+ hours)

---

## Migration Plan

### Scope

**ALL LEVELS** - New workflow applies everywhere, but in phases:

**Rollout Phase 1 - New Content:**
- b2-hist (new modules)
- c1-bio (new modules)
- lit (new modules)
- C2 (new modules)
- Any new modules in core levels (B1, B2, C1)

**Rollout Phase 2 - Migration:**
- A1 (34 modules)
- A2 (57 modules)
- B1 (91 modules)
- B2 core (94 modules)
- C1 core

> **Why migrate existing content?** Current review process misses errors. Example: A1 Module 12 had heading "Masculine Nouns Ending in -а" with examples ending in -о. Caught by human contributor in PR #443, not by AI review. Smaller, focused QA prompts will catch what monolithic reviews miss.

### Rollout Strategy

1. **Phase 1: Pilot**
   - Test new workflow on 3 b2-hist modules (existing, not new)
   - Compare results with current workflow
   - Refine prompts based on findings

2. **Phase 2: Tracks + C2**
   - Apply new workflow to all track modules and C2
   - Collect metrics: time to complete, audit pass rate, revision count

3. **Phase 3: Core Level Migration**
   - Run `module-lesson-qa` and `module-act-qa` on existing A1-C1 modules
   - Fix issues found
   - No full rebuild required - just QA pass and fixes

### Coexistence (Temporary)

During migration, both workflows exist:
- `/module-stage-1` through `/module-stage-4` - legacy, being phased out
- `/module-meta` through `/module-integrate` - new standard

After migration completes, legacy commands will be deprecated.

---

## Success Criteria

### Quantitative

| Metric | Target |
|--------|--------|
| Prompt size (each phase) | < 200 lines |
| First-pass audit rate | > 70% (vs current ~40%) |
| Meta modification attempts | 0 (locked phases) |
| Average revisions per module | < 3 (vs current ~5) |

### Qualitative

- Agents read and follow complete phase prompts
- Clear ownership of each validation check
- Easier debugging when issues occur
- Work can be delegated per phase

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| More overhead for simple modules | Medium | Low | Only apply to content-heavy tracks |
| Prompt duplication across phases | Medium | Medium | Shared reference docs, not inline content |
| Phase locking feels restrictive | Low | Medium | Clear escalation path for genuine blockers |
| Integration phase catches many issues | Medium | High | Strong QA in earlier phases |

---

## Design Decisions

1. **No orchestrator command (for now).** Keep phases manual so agent/user validates each gate individually. Chaining can be automated later once prompts are stable.

2. **Partial phase runs allowed.** If module-lesson-qa finds issues, re-run module-lesson without starting from module-meta. Use Phase Rewind Protocol only when upstream file itself is flawed.

## Open Questions

1. **Cumulative vocab database format?** Current per-level YAMLs vs unified database for cross-level queries.

---

## Appendix: Check Mapping Reference

See `docs/dev/PHASE-WORKFLOW-ANALYSIS.md` for the complete mapping of all 42 current checks to the proposed 9 phases.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-21 | Initial draft |
| 2026-01-21 | Add Phase Rewind Protocol (Gemini feedback) |
| 2026-01-21 | Decide: no orchestrator command for now (Gemini feedback) |
| 2026-01-21 | Emphasize Phase 9 as critical addition (Gemini feedback) |
| 2026-01-21 | Update migration: all levels will migrate, not just tracks |
