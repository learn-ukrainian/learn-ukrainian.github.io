## Problem

As the curriculum expands from A1 to C2, we must ensure that vocabulary progression is systematic, non-redundant, and deeply integrated into the instructional core. Currently, we lack a cross-level audit to verify uniqueness and consistent usage of "Active Vocabulary" (words targeted for drilling).

## Proposed Plan

### 1. Vocabulary Source Verification

*   **Source Confirmation**: Verify that all core lists are aligned with the **Ukrainian State Standard 2024 (Каталог В)**.
*   **Documentation**: Formalize the methodology for how vocabulary was selected and assigned to specific modules.

### 2. Uniqueness Audit (A1-C2)

*   **Duplicate Detection**: Develop a script to scan all module vocabulary (YAML sidecars) from A1 to C2.
*   **Deduplication Rule**: If a word appears in multiple modules, the **later appearance** must be either replaced with a new word or re-classified as "Passive/Contextual" (not drilled). The earlier appearance remains the "introduction" point.
*   **Flagging**: Identify and flag any existing violations for manual review.

### 3. Integration Verification

*   **Activity Coverage**: Ensure at least **80%** of a module's unique core vocabulary is used in its activities.
*   **Lesson Integration**: Ensure at least **50%** of unique core vocabulary is used in the lesson text (narrative/explanations).
*   **Audit Expansion**: Update `scripts/audit_module.py` to report on these integration percentages.

### 4. Solution Proposal: YAML-First Management

*   **Centralized DB**: Maintain vocabulary in structured YAML per level (already partially implemented).
*   **Usage Flags**: Explicitly tag items as `active` (drilled) vs `passive` (contextual).
*   **Automated Auditing**: Continuous CI checks for uniqueness and integration rates.
*   **Phased Rollout**:
    1.  A1/A2 reconciliation.
    2.  B1/B2 narrative alignment.
    3.  C1/C2 literary/academic mapping.

## Success Criteria

*   [ ] Zero unintentional duplicates in "Active Vocabulary" across A1-C2.
*   [ ] Scripted report showing integration rates for every module.
*   [ ] Updated `audit_module.py` with integration gates.
*   [ ] Documentation updated with vocab source methodology.

## Related Documentation

*   `docs/l2-uk-en/UKRAINIAN-STANDARD-INDEX.md`
*   `docs/l2-uk-en/VOCABULARY-HANDLING-SYSTEM.md`
