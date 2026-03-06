# Prompt Engineering Review: describing-things-adjectives (v5 Rebuild)

**Track:** a1 | **Sequence:** 11
**Pipeline:** v5
**Validate attempts:** 0
**Self-audit iterations:** 3
**Friction reports:** 2 (content: Immersion/Dative false positive, activities: NONE)
**Previous build:** 2 validate attempts, heading mismatch + immersion issues

## 1. Template Health

| Aspect | Status | Details |
|--------|--------|---------|
| Placeholder filling | GOOD | All placeholders resolved. CONTENT_PATH, META_PATH, PLAN_PATH, QUICK_REF_PATH all point to correct absolute paths. WORD_TARGET=1200, IMMERSION_RULE correctly injected. |
| Section titles | GOOD | `EXACT_SECTION_TITLES` placeholder now includes explicit `## REQUIRED H2 Sections (use EXACT titles)` with verbatim H2 headings. This is the P1 fix from the previous prompt review. All 5 H2 sections in output match exactly. |
| Constraint injection | GOOD | PEDAGOGICAL_CONSTRAINTS, LEVEL_CONSTRAINTS, VERB-FREE PATTERN BANK all present. No `{UNFILLED}` tokens found. |
| Self-audit snippet | GOOD | SELF_AUDIT_SNIPPET fully expanded with correct paths and bash commands. |
| Vocab hints | GOOD | VOCAB_HINTS includes all 8 required + 7 recommended items with collocations. VOCAB-IN-CONTENT RULE present. |

**Template health verdict: GOOD** -- All placeholders filled correctly. The P1 fix from the previous review (exact heading match instruction) is now integrated and worked perfectly.

## 2. Friction Analysis

### Friction 1: Content Phase (phase-2-friction-1.md)
- **Type:** Immersion Check + False Positive Dative
- **Root cause:** The audit script's dative regex matched the substring "чолові" within "чоловічий" (masculine) and flagged it as a dative case violation. Additionally, immersion was initially below 25%.
- **Classification:** TOOLING friction (dative false positive) + CONTENT friction (immersion shortfall)
- **Resolution:** Gemini removed "чоловічий" and used alternative Ukrainian sentences; increased Ukrainian content with bilingual translation pairs to reach 25.6%.
- **Proposed tooling fix (from Gemini):** Fix the dative regex in `audit_module` to avoid matching substrings like "чолові" within compound words.
- **Assessment:** The dative false positive is a real bug in the audit script. This is a legitimate tooling friction that should be fixed to prevent recurring issues across modules. The immersion fix was handled well.

### Friction 2: Activities Phase (phase-C-friction.md)
- **Type:** NONE
- **Assessment:** Clean run. The activities and vocabulary phase had zero friction. This is a significant improvement from earlier builds.

## 3. Self-Audit Effectiveness

**This is the key new feature being evaluated.**

| Metric | Value | Assessment |
|--------|-------|------------|
| Self-audit status | PASS | Gemini reported passing |
| Iterations | 3 | Gemini ran the audit 3 times (initial + 2 fix loops) |
| Final word count | 1737 | Well above 1200 target |
| Gates passed | Persona, Words, Engagement, Structure, Lint, Pedagogy, Research, Immersion | All required gates |
| Gates failed | none | Clean pass |
| Fixes applied | Fixed false positive dative + boosted immersion above 25% | Substantive fixes |

**Did Gemini actually run the audit script?** YES -- the self-audit output references specific gate names (Persona, Words, Engagement, Structure, Lint, Pedagogy, Research, Immersion) that match the audit script's output format. The word count of 1737 matches the screen-result.json COMPUTED_WORD_COUNT of 1737. This is consistent with real execution, not fabrication.

**Did it fix issues correctly?** YES -- The immersion percentage in the final audit is 25.6%, which is within the 25-40% target. The dative false positive was worked around by removing the triggering word.

**Was the self-audit report honest?** YES -- The report accurately reflects the final audit state. No discrepancies between self-audit output and screen-result.json.

**Self-audit verdict: EFFECTIVE** -- The self-audit feature achieved its primary goal: zero validate-fix attempts needed. In the previous build, this module required 2 validate fix attempts. The self-audit caught and fixed the same types of issues (immersion shortfall, structural compliance) before the validate phase even ran.

## 4. Fix Loop Efficiency

| Metric | Previous Build | Current Build |
|--------|---------------|---------------|
| Validate attempts | 2 | 0 |
| Self-audit iterations | N/A | 3 |
| Total LLM round-trips | 4 (content + fix1 + fix2 + activities) | 3 (content with self-audit + activities) |
| Fix types needed | Heading mismatch, low immersion, self-check English, robotic structure | Dative false positive, low immersion (both handled in self-audit) |

**Verdict:** The self-audit saved 1 LLM round-trip and eliminated all validate-phase fixes. This is the ideal outcome: content arrives at validation already passing.

## 5. Prompt Gaps

| Gap | Severity | Details | Suggested Fix |
|-----|----------|---------|---------------|
| Dative regex false positive | MEDIUM | The audit script flags substrings like "чолові" within "чоловічий". Gemini had to work around this by removing a legitimate word. | Fix the dative regex in `audit_module.sh` to use word-boundary matching, not substring matching. |
| Immersion target still borderline | LOW | 25.6% achieved vs 25% minimum. Verb-free constraint continues to make 25%+ difficult. Gemini had to add bilingual translation pairs to reach the threshold. | Same as previous review P3: consider 20-35% target for verb-free modules, or provide more verb-free patterns. |
| Textbook examples irrelevant for M11 | LOW | The prompt includes Grade 1 bukvar examples (syllable/sound exercises) under TEXTBOOK_EXAMPLES. These are irrelevant for an adjective agreement module. The prompt itself says "NOTE: ...For modules M15+, focus on communicative patterns, not letter/syllable exercises" but M11 still gets these. | Filter textbook examples by module type. Adjective modules should get adjective-relevant textbook examples from the RAG chunks (the discovery phase found Grade 6 adjective content). |
| Persona role "Real Estate Agent" underused | LOW | The persona role is specified but only manifests in 8 lines of the Practice section. The prompt doesn't guide how prominently the persona should appear. | Add guidance: "The persona role should appear in at least one full subsection with 3+ examples in character." |

## 6. Comparison: Previous Build vs Current Build

| Dimension | Previous Build (v4-era) | Current Build (v5) |
|-----------|------------------------|-------------------|
| Pipeline completion | PASS (after 2 fixes) | PASS (0 fixes) |
| Heading match | FAILED initially | PASSED first time |
| Immersion | 25.1% (after fix) | 25.6% (after self-audit) |
| Word count | 2963 (247% of target) | 1822 (152% of target) |
| Activities | 8 | 8 |
| Vocab items | 21 | 20 |
| Callout boxes | 4 | 3 (minimum) |
| Self-audit | N/A | 3 iterations, PASS |
| Validate fixes | 2 | 0 |
| Surviving issues | Imperative "Подивімося", Latin transliteration | Metalanguage "множина" unflagged, "слов" invalid distractor |

## Summary

**Template health: GOOD** -- The v5 template with exact heading instructions and self-audit snippet works well. All placeholders filled correctly. The P1 fix from the previous review (exact heading match) eliminated heading mismatch issues entirely.

**Self-audit effectiveness: HIGH** -- The self-audit feature is the biggest improvement in this build. It caught and fixed issues that previously required 2 validate round-trips. Gemini ran the audit script genuinely (not fabricated) and applied meaningful fixes.

**Remaining risks:**
1. **Dative regex false positive** -- a real audit tooling bug that needs fixing
2. **Immersion target borderline** -- 25.6% is barely passing; verb-free modules will continue to struggle
3. **Textbook examples irrelevance** -- Grade 1 bukvar examples are noise for M11+

**Priority fixes:**
- P1: Fix dative regex in audit_module.sh (tooling bug, affects all modules using "чоловічий")
- P2: Adjust immersion target for verb-free modules (or add more verb-free patterns)
- P3: Filter textbook examples by module topic relevance
