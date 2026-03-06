# Prompt Engineering Review: checkpoint-daily-life

**Track:** a1 | **Sequence:** M44
**Pipeline:** v4
**Validate attempts:** 3
**Friction reports:** 2 (content: NONE; activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Section heading mismatch between outline and plan | HIGH | phase-2-prompt.md | Research outline uses "Підсумок та самоперевірка" but plan expected "Інтеграційне завдання (Integration Task)". Fix1 was entirely about PLAN_SECTION_MISSING (3 sections). The content prompt says "Follow the content_outline from meta" but the meta outline didn't match the plan section titles. |
| Checkpoint format not specified | MEDIUM | phase-2-prompt.md | Fix2 and Fix3 both flagged "CHECKPOINT FORMAT ERRORS" but the content template has no checkpoint-specific format guidance. The template treats all modules identically. Checkpoints need: Overview section, skill-based H2s, integration task. |
| Dative ban vs "пові" false positive | LOW | validate-fix2-prompt.md | Audit flagged "пові" as dative -- this is likely a false positive from the word "повторити" or similar, not an actual dative case. The fix prompt passed it along without contextual analysis. |
| Robotic structure "can you..." x3 | LOW | validate-fix2-prompt.md | Self-check questions all starting with "Can you..." flagged as robotic. This is a false positive for self-check question blocks. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| No checkpoint template | HIGH -- caused 3 fix iterations | Create a checkpoint-specific content template or add checkpoint guidance to the beginner template |
| Research outline != plan section titles | HIGH | Pipeline should validate outline against plan sections before content generation |
| Quiz prompt length validation unclear | LOW | Fix2 flagged quiz prompts of 4 words (target 5-10). Not stated in content prompt. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|----------------|---------|--------------|
| 3 missing plan sections in fix1 | schema_mismatch | Research outline generated different section titles than the plan expected. Meta outline used "Огляд" but plan had "Огляд (Overview)" with bilingual format. | Pre-validate outline sections against plan before content phase |
| Missing "## Summary" in fix2 | template_gap | Content template shows "# Підсумок" but audit expected "## Summary". Checkpoint modules may have different summary expectations. | Clarify summary heading format for checkpoints |
| Checkpoint format errors in fix2, fix3 | template_gap | No checkpoint-specific format guidance in content template | Add checkpoint module template |
| VESUM not found: "ло" | model_limitation | Fragment of a word split across lines. Not a real vocabulary issue. | Improve VESUM tokenizer |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| Validate | 3 | Fix1: section heading mismatch (3 missing). Fix2: summary structure, dative false positive, quiz sizes, robotic. Fix3: checkpoint format. | YES -- a checkpoint template and outline-plan pre-validation would prevent all 3 iterations. |

## Suggested Template Fixes

### Fix 1: Create checkpoint module template (Priority: HIGH)
**Before:** All modules use same beginner content template
**After:** Checkpoint modules get specific guidance: required "Огляд" section, skill-based H2 naming convention, integration task section, relaxed immersion gate
**Applies to:** All checkpoint modules (M44, M54, etc.)

### Fix 2: Pre-validate outline sections against plan (Priority: HIGH)
**Before:** Research generates outline freely, mismatch discovered only at validation
**After:** Pipeline script compares meta outline section titles against plan sections before launching content phase. Flag mismatches immediately.
**Applies to:** All modules

### Fix 3: Exempt self-check question blocks from robotic detector (Priority: MEDIUM)
**Before:** "Can you..." repeated in self-check questions triggers robotic flag
**After:** Robotic structure detector exempts content inside "Self-Check" or "Самоперевірка" sections
**Applies to:** All modules with self-check sections

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Create checkpoint-specific template -- prevents 3-attempt fix loops for all checkpoint modules
2. Pre-validate outline section titles against plan -- catches mismatches before content generation
3. Exempt self-check blocks from robotic structure detection
