# C1 Restructure Plan - Implementation Strategy

## Goal
Establish a robust implementation strategy for the C1 Curriculum (Modules 03-115) to ensure they match the "Gold Standard" quality of the existing Modules 01-02.

**Status Assessment (2025-12-15):**
- **Existing Modules**: M01, M02.
- **Quality**: **GOLD STANDARD**. These modules perfectly exemplify the V2 Richness Guidelines (TTT approach, deep cultural context, high activity density).
- **Restructure Need**: **NONE**. The existing modules do not need restructuring. The "Restructure Plan" for C1 is effectively an **Implementation Governance Plan**.

## Proposed Changes
Since C1 is a greenfield project (mostly new creation), the focus is on **Process Quality** rather than identifying gaps in legacy code.

### 1. Implementation Strategy: Greenfield Creation
For Modules 03-115, we will follow the **"Create"** strategy exclusively.

1.  **Template**: Use M02 (`02-academic-style-markers.md`) as the primary template for "pure C1" modules. M01 is a B2-bridge and has slightly different structure.
2.  **Pedagogy**: Maintain the **TTT (Test-Teach-Test)** and **Immersion & Analysis** philosophy.
    *   *Diagnostic*: Always start with a difficult task to reveal gaps.
    *   *Analysis*: Deep linguistic breakdown (not just rules, but *why*).
    *   *Cultural Context*: Mandatory "Myth Buster" or Historical/Literary context in every module.
3.  **Vocabulary Strategy: Expansion & De-duplication**
    We will conduct a **Vocabulary Review** for every module during the creation process:

    1.  **Expansion**: Ensure each module introduces ~25-30 *new* academic/professional words.
    2.  **Drilling Focus**: Distinguish between "Active Vocabulary" (drilled in activities) and "Passive Vocabulary" (contextual in reading).
    3.  **De-duplication Policy**:
        *   **Check**: Verify new words against the `vocab.db` (or accumulated project vocabulary A1-B2) to prevent re-teaching known words.
        *   **Register Shift**: Duplicates are allowed *only* if the focus is on a register shift (e.g., teaching *одежа* in A2 vs *вбрання* in C1).
        *   **Form**: Ensure base forms are unique unless teaching specific stylistic variants.

### 2. State Standard Compliance
The C1 plan is already aligned with the 2024 State Standard. Every new module must verify:
*   **Register Awareness**: Does it distinguish between neutral, formal, and academic registers?
*   **Stylistics**: Does it cover rhetorical devices and syntactic complexity?

## Acceptance Criteria for C1 Compliance

### 1. Pedagogical Compliance
- [ ] **Register**: Explicit focus on register shifting (e.g., transforming casual -> formal).
- [ ] **Immersion**: **100% Ukrainian**. English is allowed ONLY in vocabulary table translations.
- [ ] **Structure**: Must include `Diagnostic`, `Analysis`, `Deep Dive`, `Practice` sections.

### 2. Module Richness (Audit Pass)
- [ ] **Word Count**: > 1200 words (C1 modules are text-heavy).
- [ ] **Activity Density**: > 16 activities, > 15 items per activity (per C1-CURRICULUM-PLAN.md).
- [ ] **Narrative/Context**: Every module must feature a simulated "Professional Scenario" (Conference, Editing, Negotiation).

### 3. Verification
- [ ] **Automated**: `audit_module.py` passes.
- [ ] **Manual**: "Vibe Check" - does it feel like a university textbook?

## Phase Tracking (Aligned with C1-CURRICULUM-PLAN.md)

| Phase | Modules | Theme | Count | Status |
|-------|---------|-------|-------|--------|
| **C1.1** | M01-M20 | Academic Foundation | 20 | M01-02 Done, M03-20 Planned |
| **C1.2** | M21-M35 | Professional & Social Context | 15 | Planned |
| **C1.3** | M36-M55 | Advanced Stylistics & Rhetoric | 20 | Planned |
| **C1.4** | M56-M80 | Folk Culture & Arts | 25 | Planned |
| **C1.5** | M81-M95 | Literature I - Classics | 15 | Planned |
| **C1.6** | M96-M115 | Literature II - Modern & Capstone | 20 | Planned |

**Total: 115 modules** (2 complete, 113 to create)

## GitHub Tracking

Issues to be created when implementation begins:

| Phase | Issue Title | Modules |
|-------|-------------|---------|
| C1.1 | Implement C1.1 Academic Foundation (M03-M20) | 18 modules |
| C1.2 | Implement C1.2 Professional & Social (M21-M35) | 15 modules |
| C1.3 | Implement C1.3 Stylistics & Rhetoric (M36-M55) | 20 modules |
| C1.4 | Implement C1.4 Folk Culture & Arts (M56-M80) | 25 modules |
| C1.5 | Implement C1.5 Literature I - Classics (M81-M95) | 15 modules |
| C1.6 | Implement C1.6 Literature II & Capstone (M96-M115) | 20 modules |

> **Note:** GitHub issues will be created when C1 implementation begins (after B2 completion).
