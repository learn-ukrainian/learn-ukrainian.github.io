# Prompt & Context Engineering Review: imperative-and-requests

**Track:** a1 | **Sequence:** 47
**Date:** 2026-03-10
**Pipeline:** v5
**Model:** gemini-3-flash-preview
**Validate attempts:** 2
**Friction reports:** 1 (OUTLINE_COMPLIANCE, IMMERSION_LOW, GRAMMAR_VIOLATION)
**Gemini self-audit iterations:** 2
**Reference:** #731

---

## Context Engineering Analysis

### Instruction -> Understanding -> Output Gap

| Instruction (from prompt) | What Gemini produced | Gap type | Evidence |
|--------------------------|---------------------|----------|----------|
| "FORBIDDEN: Robotic dialogues where one speaker just echoes the other ('Читай!' / 'Я читаю.' repeated)" | 42 echo-drill patterns across all 5 sections. Pattern: command -> "Я [verb present tense]" or "Ми [verb]" | instruction_ignored | Section 1 alone has 40 dialogue lines, nearly all "Читай це слово!" -> "Я читаю." Every section opens and closes with the same echo-drill format. |
| "Limit to 2-3 dialogues per module" | 9+ distinct blockquote dialogue blocks across 5 sections (each section has 2+) | instruction_ignored | Наказовий спосіб: 40 dialogue lines; Вісім обов'язкових: 32 lines; Ввічливе прохання: 22 lines; Заборони: 24 lines; Підсумок: 16 lines |
| "Each dialogue MUST have a real situation, a purpose, varied responses" | Zero dialogues have situational framing (no market, classroom, cafe setting); all are abstract verb drills | instruction_ignored | Every dialogue block is a list of isolated command-response pairs with no setting or conversational thread. E.g., "Читай це слово!" -> "Я читаю." then immediately "Читайте ці слова!" -> "Ми читаємо." |
| "Bulleted example lists longer than 5 items (spam)" FORBIDDEN | Multiple bulleted lists with 5+ items (Section 1: 5 items, Section 2: 5 items, Section 3: 4 items, Section 4: 4 items) | borderline_compliance | Lists are at or near the 5-item limit. Not the primary issue. |
| "DISCOVER -> UNDERSTAND -> PRACTICE sequence per section" | Sections partially follow this: dialogue first (DISCOVER), English explanation (UNDERSTAND), second dialogue (PRACTICE). But the DISCOVER dialogues are drills, not discovery exercises. | instruction_too_weak | The prompt's DISCOVER instruction says "NO English explanation yet. Let the learner notice the pattern." But the opening dialogues don't build toward a discoverable pattern -- they just list all forms mechanically. |
| Plan H2: 5 exact section titles including "Практика" | Gemini initially wrote "## Практика" correctly but named summary "## Підсумок" at H2. Self-audit renamed Практика to H1 Підсумок, losing the Практика section. | instruction_conflict | The plan outline lists 5 H2s including "Практика" AND the output template shows "# Підсумок" as a required summary. Gemini merged them, causing PLAN_SECTION_MISSING for all 5 in fix loop. |
| "No textbook citations needed -- add `<!-- adapted from: -->`" | Zero citation comments in output | instruction_too_weak | Despite 6 textbook excerpts in the prompt and explicit citation instructions, output contains no `<!-- adapted from: -->` or `<!-- original: -->` comments. |

### Gemini Self-Audit Findings

- Iterations: 2
- Gates passed: Persona, Words, Engagement, Structure, Lint, Pedagogy, Research, Immersion
- Gates failed: none (after 2 iterations)
- Fixes applied: Changed H2 Підсумок to H1 (TOC fix). Replaced perfective past `взяв` with `візьму`. Added Ukrainian dialogues to boost immersion from 29.3% to 30.7%.
- What Gemini gave up on: Nothing explicitly -- all gates reported as PASS.
- Critical blind spot: The self-audit has NO gate for dialogue quality or echo-drill detection. Gemini passed all gates while producing content that violates explicit FORBIDDEN patterns.

### Immersion Breakdown (per section)

| Section | Approx. English words | Approx. Ukrainian words | Ukrainian % | Containers used |
|---------|----------------------|------------------------|-------------|----------------|
| Наказовий спосіб | ~120 | ~180 | ~60% | 2 dialogues, 1 table, 1 list, 1 tip callout |
| Вісім обов'язкових дієслів | ~90 | ~150 | ~62% | 2 dialogues, 1 table, 1 list, 1 warning callout |
| Ввічливе прохання | ~130 | ~130 | ~50% | 2 dialogues, 1 table, 1 list, 1 culture callout |
| Заборони | ~80 | ~110 | ~58% | 2 dialogues, 1 list |
| Підсумок | ~100 | ~90 | ~47% | 1 dialogue, 1 list |
| **TOTAL** | **~520** | **~660** | **~33.2%** | 9 dialogues, 3 tables, 4 lists, 3 callouts |

Note: The audit tool reports 33.2% immersion after stripping tables (which contribute 0%). The high Ukrainian ratio in individual sections comes almost entirely from the echo-drill dialogues.

### Root Cause Verdict

**Primary gap:** instruction_ignored (dialogue quality rules)
**Explanation:** The prompt contains an explicit FORBIDDEN pattern for echo-drill dialogues with a BAD example that exactly matches what Gemini produced, plus GOOD examples showing situated dialogues. Gemini ignored both the prohibition and the positive examples. This is the dominant quality problem: 42 echo-drill patterns inflate immersion numbers while providing poor pedagogical value. The content reads as a conjugation drill disguised as dialogue, not as communicative language teaching.

**Secondary gap:** instruction_conflict (section headings)
**Explanation:** The plan outline lists "Практика" as an H2 section, but the output template requires "# Підсумок" as the summary heading. Gemini conflated these, then the self-audit "fixed" it by eliminating the Практика section, causing all 5 plan sections to fail validation. Two fix loops were needed to resolve heading mismatches.

---

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dialogue quality rules violated despite explicit FORBIDDEN example | **CRITICAL** | phase-2-prompt.md (Section 3) | Lines 254-283 contain both BAD and GOOD dialogue examples. Gemini produced the exact BAD pattern. The rule may need stronger enforcement or structural enforcement (e.g., requiring named speakers, location headers). |
| Plan "Практика" vs template "Підсумок" conflict | HIGH | phase-2-prompt.md (line 227-228) | Plan H2 list includes "Практика" at ~175 words, but the word budget table lists "Підсумок" at 175 words. These appear to be the same section with two names, but Gemini must choose one. |
| "Max 2 sentences per concept" buried in immersion rules | MEDIUM | phase-2-prompt.md (line 151) | This rule is nested inside the IMMERSION_RULE block. Most English paragraphs in the output comply (2-4 sentences), but the rule isn't prominent enough to override Gemini's default verbose behavior. |
| Self-audit has no dialogue quality gate | HIGH | phase-2-prompt.md (Section 5) | The self-audit checklist checks word count, sections, callouts, word bank, Russianisms, and bilingual ping-pong. It does NOT check: dialogue situational framing, echo-drill patterns, or dialogue count limits. |
| GOOD dialogue examples use vocabulary outside sandbox | MEDIUM | phase-2-prompt.md (lines 272-281) | GOOD examples include хліб, каву, свіжий, біжи, тримай, руку, мамо, добре -- none in the M47 sandbox. Gemini may dismiss these as inapplicable. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| No self-audit gate for dialogue quality | Gemini passes all gates while producing 42 echo-drills | Add checklist item: "No echo-drill dialogues (command -> 'Я [verb]' pattern). Each dialogue must have a situation and varied responses." |
| GOOD dialogue examples use out-of-sandbox vocabulary | Gemini can't follow the GOOD examples with M47's limited word bank | Provide GOOD examples using ONLY sandbox words. E.g., a classroom scenario with читай/пиши/слухай that has natural responses, not echoes. |
| No structural enforcement for dialogue framing | Soft rule ("MUST have a real situation") easily ignored | Require a location/context header before each dialogue, e.g., `> **(At a market)** or **(In a classroom)**` |
| Практика/Підсумок naming ambiguity | 2 fix loops wasted on heading mismatch | Unify: either the plan uses "Підсумок" or the template uses "Практика". One name, one section. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|-------------|
| OUTLINE_COMPLIANCE: Section Практика not in outline | instruction_conflict | Plan outline has "Практика" as H2 but meta outline has "Підсумок". Gemini merged them. Self-audit renamed Практика to H1 Підсумок, losing the section. | Align plan and template: use consistent naming |
| IMMERSION_LOW: 29.3% initial | template_gap | Table stripping warning is now present in template (line 186), but Gemini still started with tables and had to rewrite. The warning works but Gemini's first instinct is still tables. | Move table stripping warning ABOVE the immersion target, not below it. Make it the FIRST thing Gemini reads about immersion. |
| GRAMMAR_VIOLATION: perfective past взяв | instruction_conflict | Level constraints say "only imperfective aspect verbs" but plan-aware exemptions allow "perfective aspect for imperative forms." Gemini used perfective PAST (взяв) which is not an imperative. | Clarify: "Perfective is allowed ONLY in imperative forms (скажи, дай). Perfective past/future (сказав, скаже) remain FORBIDDEN unless the verb is in the sandbox." |
| Echo-drill dialogues (42 instances) | instruction_ignored | Prompt explicitly FORBIDS this pattern with a BAD example. Gemini produced it anyway across all sections. | See Fix 1 below -- needs structural enforcement, not just prohibition. |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|-------------|
| content (self-audit) | 2 | H2->H1 heading fix, perfective past fix, immersion boost | PARTIALLY -- heading conflict is a template bug; perfective past fix was correct self-correction |
| validate-fix1 | 1 | PLAN_SECTION_MISSING (5 sections), LOW_TEXTBOOK_CITATION, Activities gate FAIL (4/8) | YES -- heading alignment prevents PLAN_SECTION_MISSING; activity count is a content-phase issue |
| validate-fix2 | 1 | PLAN_SECTION_MISSING persisted after fix1 | YES -- same root cause as fix1 |

**Total fix cost:** 2 validate attempts. Root causes: (1) Практика/Підсумок naming conflict caused all PLAN_SECTION_MISSING errors. (2) Initial activity count of 4 required fix1 to add 4 more. Both are preventable with template fixes.

---

## Suggested Template Fixes

### Fix 1: Enforce dialogue quality structurally (Priority: CRITICAL)

**Prevents:** Echo-drill dialogues (the dominant quality defect in this build)
**Scope:** All beginner modules (A1, A2)
**Template file:** `claude_extensions/phases/gemini/beginner-full.md`

The current prohibition is correctly worded but ignored. The fix must make echo-drills structurally impossible by requiring a format that forces situational framing.

```diff
 ### Dialogue Quality (CRITICAL)

 Every blockquote dialogue MUST have:
 1. **A real situation** — where are the speakers? (market, classroom, street, home, cafe)
 2. **A purpose** — why are they talking? (asking for help, giving directions, buying something)
 3. **Varied responses** — the second speaker reacts naturally, not just echoes the command

+### Dialogue Format (ENFORCED)
+
+Every dialogue MUST start with a situation header in italics:
+
+```
+> **(In a classroom)**
+> — Читайте ці слова!
+> — Ми читаємо... А де слово «час»?
+> — Дивіться тут! Ось воно.
+```
+
+**HARD FAIL triggers:**
+- Any dialogue where 3+ consecutive responses follow the pattern "Я [present tense verb]" or "Ми [verb]"
+- Any dialogue with no situation header
+- More than 3 dialogue blocks per module (use tables and lists for remaining examples)
+
 **BAD** (echo drill — FORBIDDEN):
```

### Fix 2: Align Практика/Підсумок naming (Priority: HIGH)

**Prevents:** PLAN_SECTION_MISSING cascading through all sections, requiring 2 fix loops
**Scope:** All modules with a Практика section in the plan
**Template file:** `claude_extensions/phases/gemini/beginner-full.md`

```diff
 ## REQUIRED H2 Sections (use EXACT titles)

-Your output MUST use these EXACT H2 headings
+Your output MUST use these EXACT H2 headings. The LAST H2 section listed is
+your practice/summary section — do NOT create a separate "# Підсумок" heading
+unless the plan explicitly lists it.
+
+**Section Title Matching Rule:** Every H2 in your output must match a section
+title in the list below character-for-character. Extra H2s or renamed H2s will
+FAIL validation. The "# Підсумок" (H1) section in the output template is
+ONLY used when the plan does NOT include a practice section.
```

### Fix 3: Add sandbox-compatible GOOD dialogue examples (Priority: HIGH)

**Prevents:** Gemini dismissing GOOD examples as irrelevant due to out-of-sandbox vocabulary
**Scope:** A1 modules (especially verb-focused ones)
**Template file:** `claude_extensions/phases/gemini/beginner-full.md`

```diff
 **GOOD** (at a market — speakers have real goals):
 > — Дайте, будь ласка, хліб.
 > — Візьміть. Ще щось?
 > — Покажіть це. Скільки?
 > — Двадцять. Дивіться — свіжий!

+**GOOD** (sandbox-safe — using only common A1 words):
+> **(In a classroom)**
+> — Читайте ці слова! Дивіться тут.
+> — А де слово «час»?
+> — Ось воно. Покажіть це слово.
+> — Це тут? Так, я читаю.
+> — Дуже добре. Пишіть там.
+
```

### Fix 4: Add dialogue quality to self-audit checklist (Priority: HIGH)

**Prevents:** Gemini passing self-audit while producing FORBIDDEN patterns
**Scope:** All modules
**Template file:** `claude_extensions/phases/gemini/beginner-full.md`

```diff
 ### Content Checks
 - [ ] Word count >= 1200?
 - [ ] Every plan section has prose?
 - [ ] 3+ callout boxes?
+- [ ] Max 3 dialogue blocks total? Each has a situation header?
+- [ ] No echo-drill patterns (command -> "Я [verb]" repeated 3+ times)?
 - [ ] No words outside the word bank?
```

### Fix 5: Clarify perfective exemption scope (Priority: MEDIUM)

**Prevents:** Incorrect use of perfective past/future outside imperatives
**Scope:** All A1 modules with perfective exemptions
**Template file:** Sequence constraint generation in `build_module_v5.py`

```diff
 PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module
 because the plan explicitly teaches these constructs: Perfective aspect
-(plan teaches perfective verbs).
+(plan teaches perfective verbs). NOTE: This exemption applies ONLY to
+imperative forms (скажи, дай, покажи). Perfective past (сказав) and
+perfective future (скаже) remain subject to sandbox rules — use them
+ONLY if the specific form appears in the Lexical Sandbox verb tables.
```

### Fix 6: Move table stripping warning above immersion target (Priority: MEDIUM)

**Prevents:** Gemini's first instinct being tables, then discovering they don't count
**Scope:** All modules
**Template file:** `claude_extensions/phases/gemini/beginner-full.md`

```diff
 ### Immersion Target

+**⚠️ CRITICAL**: The immersion calculator STRIPS markdown tables when counting
+Ukrainian content. Tables contribute ZERO to immersion. Use blockquote dialogues,
+bulleted example lists, and pattern boxes for Ukrainian that counts toward your
+score. Tables are for grammar paradigm DISPLAY only.
+
 TARGET: 30-55% Ukrainian.
-...
-**IMPORTANT**: The immersion calculator STRIPS markdown tables when counting Ukrainian content.
```

---

## Summary

**Template health:** NEEDS WORK
**Build quality:** PASS on gates, FAIL on pedagogical quality -- content is an echo-drill disguised as dialogue

**Top 3 fixes by leverage:**

1. **Enforce dialogue quality structurally** (Fix 1) -- The single biggest quality defect. 42 echo-drill patterns violate an explicit FORBIDDEN rule. Soft prohibition does not work; structural enforcement (situation headers, hard fail triggers, dialogue count limit) is needed. Affects all beginner modules.

2. **Align Praktyka/Pidsumok naming** (Fix 2) -- Caused 2 fix loops for this module. The plan lists "Практика" as H2 but the template expects "# Підсумок" as H1 summary. This naming conflict cascaded into PLAN_SECTION_MISSING for all 5 sections. Quick fix with high ROI.

3. **Add sandbox-compatible GOOD dialogue examples + self-audit gate** (Fixes 3+4) -- The current GOOD examples use vocabulary outside the sandbox, making them unusable for constrained modules. Adding an A1-safe example AND a self-audit checklist item creates both positive guidance and enforcement.

**Key observation:** Gemini's self-audit reports PASS on all gates, but the self-audit has zero checks for dialogue quality, echo patterns, or dialogue count. The audit system (screen-result.json) also passes because it checks word count, immersion %, activities, and structure -- none of which catch pedagogically poor content. This is a systemic gap: the pipeline has no quality gate between "structurally correct" and "pedagogically sound."

---

*Reviewed by Claude Opus 4.6 | #731 | 2026-03-10*
