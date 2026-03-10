# Prompt & Context Engineering Review: imperative-and-requests (Build 5)

**Track:** a1 | **Sequence:** 47
**Date:** 2026-03-10
**Pipeline:** v5
**Model:** gemini-3-flash-preview
**Validate attempts:** 2 (+ Claude escalation)
**Friction reports:** 1 (IMMERSION_CALCULATION_MISMATCH)
**Gemini self-audit iterations:** 5
**Previous review:** Build 4 (2026-03-09)

---

## Context Engineering Analysis

### Instruction → Understanding → Output Gap

| Instruction (from prompt) | What Gemini produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| Plan H2 titles: 5 specific sections (Наказовий спосіб, Вісім обов'язкових дієслів, etc.) | Different H2 titles in initial build ("Introduction: Asking for Action", "Forming the Imperative") | instruction_ignored | Fix1 reported PLAN_SECTION_MISSING for all 5 sections. Fix2 (Claude) corrected headings. |
| Immersion target 30-55% | Initial ~14.7%, self-audit raised to 30.6% after 5 iterations | instruction_too_weak | Friction: "clean_for_immersion strips markdown tables entirely." Gemini switched from tables to blockquotes. |
| Sandbox-only vocabulary | Activities contain `взяйте`, `стояй`, `и` — none in VESUM | instruction_ignored | screen-result.json: 3 not-found words. `взяйте`→`візьміть`, `стояй`→`стій`, `и`→`і` (Russian). |
| Self-audit format | Gemini echoed template literally: `iterations: {number}` | structural_impossibility | Session JSON shows template text echoed, not filled. Pipeline extracted actual data separately. |

### Gemini Self-Audit Findings
- Iterations: 5
- Gates passed: Persona, Words, Engagement, Structure, Lint, Pedagogy, Research, Immersion
- Gates failed: none (after 5 iterations)
- Main fix: Rewrote tables → blockquote dialogues to increase immersion from 12% to 30.6%. Adjusted H2 headers.

### Root Cause Verdict
**Primary gap**: instruction_too_weak (immersion) + instruction_ignored (headings + morphology)
**Explanation**: Gemini wasted 3+ self-audit iterations discovering tables are stripped from immersion calculation. Section headings didn't match plan despite exact titles being in the prompt. Morphological errors (`взяйте`, `стояй`, `и`) in activities show Gemini applying regular patterns to irregular verbs.

---

## Changes from Build 4

### What Improved (Build 5 vs Build 4)
1. **No imperfective leakage in prose.** Build 4 had 19 out-of-sandbox words (давати forms, показувати, etc.). Build 5 prose contains zero leakage — content uses only imperative forms and simple present forms already in sandbox.
2. **No vocative name issues.** Build 4 used Ivanе/Aннo (VESUM fails). Build 5 avoids proper names entirely.
3. **Content redundancy resolved.** Build 4 had 83% redundancy. Build 5 uses varied dialogue contexts per section.
4. **Adapter framing partially visible.** New template adapter role present in prompt, though no `<!-- adapted from: -->` citations in output.

### What Regressed (Build 5 vs Build 4)
1. **Morphological errors in activities.** `взяйте` (should be `візьміть`), `стояй` (should be `стій`), `и` (Russian conjunction). Build 4 didn't have these specific errors.
2. **Content is flatter pedagogically.** Build 5 is essentially a vocabulary drill — blockquote after blockquote of command examples. Build 4 had more explanatory paragraphs and varied pedagogy.
3. **No textbook citations.** Despite adapter framing in prompt, zero `<!-- adapted from: -->` comments.

### What Persists
1. **Immersion barely above threshold** (30.3%). Same pattern as Build 4 (31.5%).
2. **Section heading mismatch** requiring fix loop.
3. **Table stripping not warned** in template — same friction point.

---

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Table stripping not warned | HIGH | beginner-full.md | Gemini wasted 3+ iterations using tables before discovering blockquotes work. Same issue as Build 4. |
| Section heading matching implicit | MEDIUM | beginner-full.md | Plan provides exact H2 titles but instruction to match them exactly isn't prominent. |
| Irregular verb forms not highlighted | MEDIUM | beginner-full.md | Activities generated `взяйте` (regular pattern) instead of `візьміть` (irregular). No warning about irregular imperatives. |
| Self-audit template echoed | LOW | beginner-full.md | Template delimiters caused literal echo instead of fill. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| Table stripping warning | Gemini wasted 3+ iterations (same as Build 4) | Add: "Tables are STRIPPED by immersion calculator. Use blockquotes for Ukrainian content." |
| Irregular imperative forms in activity context | 3 morphological errors in activities | Add critical irregular forms list near activity instructions |
| Textbook adaptation guidance | Zero citations despite adapter framing | Strengthen with specific examples from textbook excerpts in prompt |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| IMMERSION_CALCULATION_MISMATCH | template_gap | Same as Build 4 — template doesn't explain table stripping | Add explicit warning to immersion rules |
| PLAN_SECTION_MISSING (5 sections) | template_gap | Gemini wrote content with creative headings instead of plan-exact | Strengthen heading matching instruction |
| Morphological errors (взяйте, стояй, и) | template_gap | Activities apply regular patterns to irregular verbs | Add irregular form checklist |
| No textbook citations | template_gap | Adapter framing is new and soft-worded | Strengthen citation requirement |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| validate-fix1 | 1 | Headings, immersion, agreement, activity density | YES — heading + immersion warning prevents 2/5 |
| validate-fix2 (Claude) | 1 | Gemini fix1 failed (API error: "Premature close") | NO — infrastructure issue |

**Note:** Fix1 was attempted by Gemini but hit an API error (`Error: Premature close`). Fix2 was escalated to Claude, which successfully applied all 5 fixes.

---

## Suggested Template Fixes (Priority-ordered)

### Fix 1: Table stripping warning (Priority: HIGH) — CARRY-OVER FROM BUILD 4
**Prevents:** Multi-iteration immersion loops
**Scope:** All beginner modules (A1, A2)
**Template:** `claude_extensions/phases/gemini/beginner-full.md`
```diff
 TARGET: {IMMERSION_TARGET}% Ukrainian.
 **Structural containment**: English prose in paragraphs. Ukrainian in CONTAINERS ONLY.
+**⚠️ IMPORTANT**: The immersion calculator STRIPS markdown tables. Use blockquotes (> — **Ukrainian** — English) and lists for Ukrainian content. Tables work for English grammar explanations only.
```

### Fix 2: Section heading matching (Priority: HIGH) — CARRY-OVER
**Prevents:** PLAN_SECTION_MISSING errors requiring fix loops
**Scope:** All modules
**Template:** `claude_extensions/phases/gemini/beginner-full.md`
```diff
 ## Content Outline
 {CONTENT_OUTLINE}
+**CRITICAL**: Your H2 headings MUST match the section titles above EXACTLY (Ukrainian text included). Do NOT create alternative titles.
```

### Fix 3: Irregular imperative forms warning (Priority: MEDIUM) — NEW
**Prevents:** Morphological errors like взяйте, стояй in activities
**Scope:** A1 modules
**Template:** `claude_extensions/phases/gemini/beginner-full.md` (activity section)
```diff
 ## Activities
+**IRREGULAR FORMS**: Some verbs have irregular imperatives. NEVER guess — use forms from the content you wrote:
+- взяти → візьми/візьміть (NOT взяй/взяйте)
+- стояти → стій/стійте (NOT стояй/стояйте)
+- дати → дай/дайте (NOT дай/дайте — this one IS regular)
+- и is RUSSIAN. The Ukrainian conjunction is і.
```

### Fix 4: Textbook citation strengthening (Priority: LOW)
**Prevents:** Zero-citation outputs despite adapter framing
**Scope:** All modules with textbook excerpts
**Template:** `claude_extensions/phases/gemini/beginner-full.md`
```diff
 **Cite your adaptations:**
-For each dialogue or exercise you adapt from the textbook excerpts, add an HTML comment:
+For each dialogue or exercise you adapt, you MUST add an HTML comment (at least 2 per module):
 <!-- adapted from: Заболотний Grade 5, вправа 221 -->
```

---

## Summary

**Template health:** NEEDS WORK (same as Build 4)
**Build quality:** PASS but pedagogically flat — essentially a vocabulary drill in blockquote format

**Top 3 fixes by leverage:**
1. **Table stripping warning** — same fix as Build 4, still not applied, causes 3+ wasted iterations every build
2. **Section heading matching** — same fix as Build 4, still causing fix loops
3. **Irregular forms warning** — new issue in Build 5, prevents morphological errors in activities

**Comparison verdict:** Build 5 is cleaner than Build 4 (no sandbox leakage in prose, no redundancy) but pedagogically weaker (flatter content, less varied). The morphological errors in activities are new regressions. The two carry-over template fixes from Build 4 (#1, #2) should be applied before any more builds.

---

*Reviewed by Claude Opus 4.6 | Build 5 | 2026-03-10*
