# Prompt Engineering Review: the-cyrillic-code-iii

**Track:** a1 | **Sequence:** 3
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (both NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Callout instruction buried | MEDIUM | phase-2-prompt.md | Callout types listed but no minimum count stated in the content prompt. Gemini produced 0 boxes on first pass. The audit gate requires 3 for A1, but the prompt doesn't say "you MUST include at least 3 callout boxes". |
| Summary section optional-sounding | LOW | phase-2-prompt.md | Section 6 (Підсумок — Summary, 100 words) was skipped by Gemini on first pass. The outline lists it but doesn't flag it as mandatory. |
| Immersion target not prominent | HIGH | phase-2-prompt.md | Immersion target (10-25% Ukrainian) is in placeholders but the content prompt doesn't emphasize it. First pass produced only 3.8% Ukrainian content. For M3 (23 letters), Gemini needs explicit guidance: "Include Ukrainian reading blocks, example words in Ukrainian script, and at least N Ukrainian sentences." |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| DECODABLE_VOCABULARY is empty | No impact this time (M3 uses plan vocab_hints), but inconsistent — M1/M2 get curated word lists | pipeline_lib.py already returns empty for M3; low priority |
| No prior module vocabulary list | Gemini can't verify which words students already know from M1-M2 | Inject cumulative vocab from M1-M2 as context for M3 content |
| VIDEO_DISCOVERY empty but PRONUNCIATION_VIDEOS has 9 links | No impact — videos were injected via PRONUNCIATION_VIDEOS | Discovery found no videos (channel search failed) but static links exist in plan. Working as designed. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|--------------|
| Gemini reports NONE friction | — | Both friction reports say NONE, yet validate needed 2 fix attempts. Gemini didn't self-diagnose its failures. | Not actionable — friction is self-reported |
| 0 engagement boxes | **template_gap** | Prompt lists callout types but doesn't state a minimum count. Gemini treated them as optional decoration. | Add explicit minimum: "Include at least 3 callout boxes (> [!tip], > [!warning], etc.)" |
| Missing Підсумок section | **template_gap** | The content_outline has 6 sections but no instruction says "you MUST write ALL sections". Gemini dropped the smallest one (100 words). | Add: "Write ALL sections from the outline. Do not skip any section, even short ones." |
| Immersion 3.8% (target 10-25%) | **template_gap** | The immersion target is stated in placeholders but not operationalized. Gemini wrote too much English explanation, not enough Ukrainian text. | Add: "For M3+, include Ukrainian reading blocks with 5-10 words per block. Target: at least 10% of content should be Ukrainian script." |
| Pedagogy gate fail | **template_gap** | Unclear what specific pedagogy violation triggered. Fix2 prompt says "1 violation" but doesn't specify what. | Improve fix prompt to include the specific violation text |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix 1: engagement boxes (0→4) + missing section. Fix 2: pedagogy + immersion (3.8%→10.2%) | **YES** — all 4 issues are preventable with clearer prompt instructions |

**Fix 1** added engagement boxes and the missing summary section. Straightforward.

**Fix 2** fixed pedagogy and boosted immersion from 3.8% to 10.2%. This required adding Ukrainian content blocks — exactly the kind of work that should happen in the initial content pass, not a fix loop.

**Cost of fix loop:** ~6 minutes of Gemini calls + 2 audit runs. Preventable.

## Suggested Template Fixes

### Fix 1: Explicit engagement box minimum (Priority: HIGH)
**Prevents:** LOW_ENGAGEMENT on first pass (caused fix loop)
**Scope:** All A1-A2 modules
**Template file:** `claude_extensions/phases/gemini/beginner-activities.md` or content prompt template

The engagement minimum is in the audit gate but not in the content prompt. Gemini needs to know upfront.

```diff
  Use these callout types: `[!tip]`, `[!warning]`, `[!did-you-know]`, `[!culture]`
+
+ **MANDATORY:** Include at least {ENGAGEMENT_MIN} callout boxes in your content.
+ Spread them across sections — do not stack multiple callouts in one section.
```

### Fix 2: Mandatory section completeness (Priority: HIGH)
**Prevents:** PLAN_SECTION_MISSING (dropped summary section)
**Scope:** All modules
**Template file:** Content prompt template

```diff
  Write the lesson content following this outline:
+
+ **CRITICAL:** You MUST write ALL sections listed below. Do not skip any section,
+ even short ones like Summary (100 words). Missing sections fail validation.
```

### Fix 3: Operationalize immersion target for M3+ (Priority: MEDIUM)
**Prevents:** Immersion below target (3.8% vs 10-25%)
**Scope:** A1 M3-M6 modules
**Template file:** Content prompt template

```diff
  IMMERSION_RULE: 10-25% Ukrainian, 75-90% English
+
+ **How to hit this target:** Include Ukrainian reading blocks after each letter
+ introduction. Show 3-5 example words in Ukrainian script per section. Add a
+ "Практика читання" (Reading Practice) section with Ukrainian sentences using
+ only decodable letters.
```

### Fix 4: Fix prompt should include violation details (Priority: LOW)
**Prevents:** Vague fix instructions that may need multiple attempts
**Scope:** All modules (fix prompt template)
**Template file:** Validate fix prompt template

The fix2 prompt says "Gate `Pedagogy` FAIL — 1 violation" but doesn't say what the violation is. Include the actual violation text.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. **Explicit engagement box minimum** — prevents the most common fix loop trigger across A1 modules
2. **Mandatory section completeness** — Gemini drops small sections; explicit instruction prevents this
3. **Operationalize immersion target** — M3+ needs concrete guidance on how much Ukrainian to include, not just a percentage target
