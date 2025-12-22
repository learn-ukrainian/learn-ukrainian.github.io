# C2 Restructure Plan - Implementation Strategy

## Goal
Establish a robust implementation strategy for the C2 Curriculum (Modules 03-80) to ensure they match the "Gold Standard" quality of the existing Modules 01-02.

**Status Assessment (2025-12-15):**
- **Existing Modules**: M01 (`01-c1-bridge-assessment.md`), M02 (`02-euphony-complete-system.md`).
- **Quality**: **GOLD STANDARD**. M01 is an exhaustive diagnostic (1200+ words). M02 is a deep dive into Euphony (1300+ words). Excellent density.
- **Restructure Need**: **NONE**. The C2 curriculum is proceeding correctly. This document establishes **Implementation Governance**.

## Proposed Changes
C2 is a greenfield project focused on **Mastery & Stylistics**.

### 1. Implementation Strategy: Greenfield Creation
For Modules 03-80, we will follow the **"Create"** strategy with strict adherence to the 4-phase curriculum structure.

1.  **Template**: Use M02 (`02-euphony-complete-system.md`) as the template for "Concept Heavy" modules.
2.  **Pedagogy**: Focus on **Stylistic Precision** and **Creative Production**.
    *   *Activities*: Must include "Transform" (Style rewriting) and "Analyze" (Literary critique).
    *   *Immersion*: **100% Ukrainian**. English is allowed ONLY in vocabulary table translations.
3.  **Vocabulary Strategy: Expansion & De-duplication**
    We will conduct a **Vocabulary Review** for every module during the creation process:

    1.  **Expansion**: Ensure each module introduces ~25 *new* high-level stylistic/literary words.
    2.  **Drilling Focus**: Distinguish between "Active Vocabulary" (drilled in activities) and "Passive Vocabulary" (contextual in literary readings).
    3.  **De-duplication Policy**:
        *   **Check**: Verify new words against the `vocab.db` (accumulated A1-C1 vocabulary) to prevent re-teaching known words.
        *   **Register/Shade**: Duplicates allowed ONLY if analyzing shade of meaning (e.g., *йти* vs *шкандибати* vs *чимчикувати*).
        *   **Form**: Ensure base forms are unique unless teaching specific stylistic variants.

### 2. State Standard Compliance
Aligned with C2 ("Рівень вільного володіння другого ступеня").
*   **Key Requirements**:
    *   Full euphonic mastery (M02 - done).
    *   Publication-ready academic writing (M03-M13).
    *   Literary creation (M21-M40).

## Acceptance Criteria for C2 Compliance

### 1. Pedagogical Compliance
- [ ] **Stylistic Transformation**: Every module must task the learner with rewriting a text from one style to another.
- [ ] **Model Answers**: MANDATORY for all creative writing tasks.
- [ ] **Immersion**: 100% Ukrainian (English only in vocabulary translations).

### 2. Module Richness (Audit Pass)
- [ ] **Word Count**: > 1200 words (C2 modules are dense theoretical & literary texts).
- [ ] **Activity Density**: > 16 activities, > 15 items per activity (per C2-CURRICULUM-PLAN.md).
- [ ] **Authenticity**: Use excerpts from real modern Ukrainian literature/media.

### 3. Verification
- [ ] **Automated**: `audit_module.py` passes.
- [ ] **Manual**: "Vibe Check" - does it feel like a native-level literary text?

## Phase Tracking (Aligned with C2-CURRICULUM-PLAN.md)

| Phase | Modules | Theme | Count | Status |
|-------|---------|-------|-------|--------|
| **C2.1** | M01-M20 | Stylistic Perfection | 20 | M01-02 Done, M03-20 Planned |
| **C2.2** | M21-M40 | Literary Mastery | 20 | Planned |
| **C2.3** | M41-M60 | Preparation for Professional Specialization | 20 | Planned |
| **C2.4** | M61-M80 | Mastery & Capstone | 20 | Planned |

**Total: 80 modules** (2 complete, 78 to create)

## GitHub Tracking

Issues to be created when implementation begins:

| Phase | Issue Title | Modules |
|-------|-------------|---------|
| C2.1 | Implement C2.1 Stylistic Perfection (M03-M20) | 18 modules |
| C2.2 | Implement C2.2 Literary Mastery (M21-M40) | 20 modules |
| C2.3 | Implement C2.3 Professional Specialization (M41-M60) | 20 modules |
| C2.4 | Implement C2.4 Mastery & Capstone (M61-M80) | 20 modules |

> **Note:** GitHub issues will be created when C2 implementation begins (after C1 completion).
