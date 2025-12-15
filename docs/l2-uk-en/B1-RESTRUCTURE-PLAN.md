# B1 Restructure Plan - Implementation Strategy

## Goal
Establish a robust implementation strategy for the B1 Curriculum (Modules 01-80) to bridge the gap from A2 basic competence to independent usage.

**Status Assessment (2025-12-15):**
- **Existing Modules**: M01-M05 (Aspect Theory).
- **Missing Modules**: M06-M80.
- **Quality**: Existing modules use the **Bilingual Approach** (English theory, Ukrainian examples). This is valid for B1.1 but needs strictly graduated immersion.
- **Restructure Need**: **Low**. Focus is on **Creation**.

## Proposed Changes

### 1. Implementation Strategy: Greenfield Creation & Graduated Immersion
For Modules 06-80, we will follow the **"Create"** strategy with strict adherence to the 8-phase curriculum structure.

1.  **Pedagogy**: **TTT (Test-Teach-Test)**.
    *   *Approach*: Start with a complex text → Analyze grammar → Practice.
2.  **Graduated Immersion Scale**:
    *   **B1.1 (M01-M10)**: 45-50% Ukrainian. (M01-05 are complete).
    *   **B1.2 (M11-M20)**: 50-55% Ukrainian.
    *   **B1.3-B1.4 (M21-M45)**: 55-60% Ukrainian.
    *   **B1.5-B1.6 (M46-M65)**: 60-65% Ukrainian.
    *   **B1.7-B1.8 (M66-M80)**: 65-70% Ukrainian.
3.  **Vocabulary Strategy: Expansion & De-duplication**
    1.  **Expansion**: ~30-40 *new* words per module.
    2.  **Context**: Narrative-driven (stories >300 words), NO lists.
    3.  **Drilling Focus**: Distinguish Active (drilled) vs Passive (contextual) vocabulary.
    4.  **De-duplication Policy**:
        *   **Check**: Verify against `vocab.db` (A1/A2 corpus).
        *   **Exceptions**: Polysemy (teaching new meaning) or register shifts are allowed but must be tagged.
        *   **Base Forms**: Ensure uniqueness of base forms unless teaching morphology.

### 2. State Standard Compliance
The B1 plan has been updated (Issue 113) to address previous gaps. New modules must implement:
*   **Participle Phrases**: Dedicated focus (M38).
*   **One-member Sentences**: Explicit teaching (M40).
*   **Synthetic Future**: *читатиму* vs *буду читати* (M04 - done).

## Acceptance Criteria for B1 Compliance

### 1. Pedagogical Compliance
- [ ] **Method**: TTT approach for Grammar modules.
- [ ] **Immersion**: Validated against the specific B1.x phase target.
- [ ] **Narrative**: Every vocabulary module must have a >300 word story.

### 2. Module Richness (Audit Pass)
- [ ] **Word Count**: > 1000 words.
- [ ] **Activity Density**: > 12 activities, > 12 items per activity.
- [ ] **Culture**: Every module must have a "Culture Bite".

## Phase Tracking (Aligned with B1-CURRICULUM-PLAN.md)

| Phase | Modules | Theme | Count | Status |
|-------|---------|-------|-------|--------|
| **B1.1** | M01-M10 | Aspect Mastery | 10 | M01-05 Done, M06-10 Planned |
| **B1.2** | M11-M20 | Motion Verbs | 10 | Planned |
| **B1.3** | M21-M35 | Complex Sentences | 15 | Planned |
| **B1.4** | M36-M45 | Advanced Grammar | 10 | Planned |
| **B1.5** | M46-M55 | Vocabulary I (Thematic) | 10 | Planned |
| **B1.6** | M56-M65 | Vocabulary II (Strategies) | 10 | Planned |
| **B1.7** | M66-M75 | Contemporary Ukraine | 10 | Planned |
| **B1.8** | M76-M80 | Skills & Integration | 5 | Planned |

**Total: 80 modules** (5 complete, 75 to create)

## GitHub Tracking

**Parent Issue:** [#115 - Build modules 01-80](https://github.com/krisztiankoos/curricula-opus/issues/115)

| Phase | Issue | Modules | Status |
|-------|-------|---------|--------|
| B1.1b | [#149](https://github.com/krisztiankoos/curricula-opus/issues/149) | M06-M10 (5) | ⏳ Ready |
| B1.2 | [#150](https://github.com/krisztiankoos/curricula-opus/issues/150) | M11-M20 (10) | ⏳ Planned |
| B1.3 | [#151](https://github.com/krisztiankoos/curricula-opus/issues/151) | M21-M35 (15) | ⏳ Planned |
| B1.4 | [#152](https://github.com/krisztiankoos/curricula-opus/issues/152) | M36-M45 (10) | ⏳ Planned |
| B1.5 | [#153](https://github.com/krisztiankoos/curricula-opus/issues/153) | M46-M55 (10) | ⏳ Planned |
| B1.6 | [#154](https://github.com/krisztiankoos/curricula-opus/issues/154) | M56-M65 (10) | ⏳ Planned |
| B1.7 | [#155](https://github.com/krisztiankoos/curricula-opus/issues/155) | M66-M75 (10) | ⏳ Planned |
| B1.8 | [#156](https://github.com/krisztiankoos/curricula-opus/issues/156) | M76-M80 (5) | ⏳ Planned |

**Related Issues:**
- [#113](https://github.com/krisztiankoos/curricula-opus/issues/113) - State Standard compliance ✅ Closed
- [#114](https://github.com/krisztiankoos/curricula-opus/issues/114) - Curriculum plan improvements ✅ Closed
- [#116](https://github.com/krisztiankoos/curricula-opus/issues/116) - Vocabulary finalization (final step)
