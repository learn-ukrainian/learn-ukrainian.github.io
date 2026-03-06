# Prompt Engineering Review: syllables-and-transfer

**Track:** a1 | **Sequence:** 5
**Pipeline:** v4
**Validate attempts:** 4
**Friction reports:** 1 (NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| No issue | -- | phase-2-prompt.md | Engagement callouts correctly stated as "3+ MANDATORY". Template fix from M3 review working. |
| No issue | -- | phase-2-prompt.md | Word target, immersion range, section budgets all clearly stated. |
| Research note contradicts template | LOW | phase-A-output.md | Research notes say "provide IPA only for the first occurrence" but template correctly bans IPA. Gemini correctly followed the template over the research note. No harm done but research phase should not suggest IPA. |
| Repetitive "Це X" pattern not addressed | MEDIUM | phase-2-prompt.md | Template says "No 3+ sentences starting with the same phrase" but the "Це X. (This is X.)" immersion pattern is NOT sentences — it's parenthetical translations. Gemini interpreted immersion requirements by inserting "Це склад/слово/правило" dozens of times. Template should clarify that immersion variety matters. |

## Context Gaps

| Missing Context | Impact | Fix |
|----------------|--------|-----|
| VESUM false positive on hyphenated syllable words | 54 VESUM "not found" — ALL are syllable breakdowns (а-вто-бус, де-ре-во, мо-ло-ко). Expected for this module but generates noisy validation. | VESUM verifier should strip hyphens before lookup, or syllable-broken words should be allowlisted for phonology modules. |
| M5 uses full alphabet | LOW | M5 charset = full alphabet (same as M4). The UNTRANSLATED_NON_DECODABLE check correctly found that Ґ in ґу-дзик/ґуд-зик needed translation. However, M5 teaches syllables not letters — the full alphabet IS available. The check was correct but the translation requirement still applies since M5 is in the M1-M6 range. |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|---------------|-----------------|---------|--------------|
| Fix1: UNTRANSLATED_NON_DECODABLE on ґу-дзик | **correct detection** | ґу-дзик lacked English translation. Gemini added "(button)" — valid fix. | None needed — check working correctly |
| Fix1: ACTIVITY_VESUM_FAIL on hyphenated words | **tooling limitation** | VESUM doesn't recognize hyphenated syllable breakdowns (У-кра-ї-на, ав-то-бус, etc.). These are pedagogically correct — the module teaches syllable division. | VESUM verifier should strip hyphens and retry: `"ав-то-бус" → "автобус"` → VESUM PASS |
| Fix2: 0 issues in prompt | **tooling bug** | Empty fix prompt — audit failed but no deterministic issues extracted. Gemini received "Fix 0 issues" — impossible to act on. | **FIXED** — ultra-fallback now dumps raw audit tail |
| Fix3: Imperatives (Подивімось, поговорімо, Повторімо) | **model limitation** | Gemini used Ukrainian imperative/hortative forms despite constraint "verb conjugation FORBIDDEN". The constraint text says "FORBIDDEN: verb conjugation, imperatives" but Gemini used 1st-person plural hortatives as natural bridging phrases. | Consider adding explicit examples of banned hortative forms to the constraint block: "Banned: Подивімось, Поговорімо, Давайте розглянемо — use English instead" |
| Fix3: ACTIVITY_VESUM_FAIL (ка, ло, стра) | **tooling limitation** | Syllable fragments used as activity answers. These are correct pedagogically (testing syllable identification) but aren't standalone words. | VESUM check should have an exemption for group-sort/quiz activities in phonology modules where answers are syllable fragments |
| Fix4: Immersion too low (8.8%) | **measurement timing** | Immersion was below 10% after fix3 removed Ukrainian hortatives. Gemini fixed by adding more "Це X" translations throughout. | Not a prompt issue — measurement gate working correctly |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 4 | VESUM false positives on hyphenated words + empty fix prompt + imperatives + low immersion | **Partially** — 1 attempt saved by non-empty fix prompt. VESUM hyphen-stripping would save 1-2 more. |

**Detailed fix loop:**
1. Fix1: 3 issues — untranslated Ґ words + VESUM on hyphenated activity answers. Gemini fixed translations, replaced hyphenated answers.
2. Fix2: 0 issues in prompt (bug) — audit still failed. Wasted iteration.
3. Fix3: 6 issues — imperatives caught by rule engine + VESUM on syllable fragments (ка, ло, стра). Gemini replaced imperatives with English, fixed activity items.
4. Fix4: 1 issue — immersion dropped to 8.8% after removing Ukrainian phrases. Gemini added more "Це X" patterns to boost immersion.

**Cost:** ~20 minutes of Gemini calls + 4 audit runs. Fix2 was entirely wasted (empty prompt bug). Fix3 imperatives could have been caught in fix1 if the rule engine ran all checks in the same pass.

## Content Quality Notes

**Strengths:**
- Clear pedagogical structure: golden rule -> types -> division rules -> summary
- Good example progression: кіт (1 syllable) -> молоко (3) -> Україна (4)
- Textbook reference examples well-chosen for this topic

**Weaknesses:**
- Extremely repetitive "Це X" pattern — nearly every paragraph has 2-3 occurrences of "Це склад/слово/правило/переніс/голосна/приголосна/etc." Used as an immersion crutch.
- "Це правило. (This is a rule.)" appears 6 times — same phrase, same translation
- The pattern became MORE repetitive after fix4 added more to boost immersion from 8.8% to 12.5%

## Suggested Template Fixes

### Fix 1: VESUM hyphen-stripping for syllable modules (Priority: HIGH)
**Prevents:** False VESUM failures on pedagogically correct syllable breakdowns
**Scope:** A1 M5-M6 (phonology modules) + any module with syllable activities
**File:** `scripts/audit/checks/content_quality_pipeline.py` or VESUM verification step

Strip hyphens before VESUM lookup: `"ав-то-бус" → "автобус"`. If the dehyphenated form passes VESUM, the original is valid.

### Fix 2: Immersion variety guidance (Priority: MEDIUM)
**Prevents:** Repetitive "Це X" immersion padding
**Scope:** A1 beginner templates
**File:** `claude_extensions/phases/gemini/beginner-content.md`

Add to writing instructions:
> **Immersion variety**: Don't repeat the same Ukrainian phrase pattern more than twice. Vary between "Це X (This is X)", contextual labels ("Наприклад — For example"), section bridging phrases ("А тепер — And now"), and vocabulary callouts.

### Fix 3: Explicit hortative ban examples (Priority: LOW)
**Prevents:** Gemini using Ukrainian hortative forms (Подивімось, Поговорімо, Давайте)
**Scope:** A1 M1-M14 templates
**File:** Constraint block in placeholders

Add to GRAMMAR STATUS: "Banned Ukrainian phrases: Подивімось, Поговорімо, Давайте розглянемо, Повторімо — always use English equivalents (Let us look at, Let's talk about, etc.)"

## Summary

**Template health:** GOOD (template correctly enforced engagement minimum, IPA ban, engagement count)
**Top 3 fixes by leverage:**
1. **VESUM hyphen-stripping** — prevents false positives unique to syllable/phonology modules
2. **Immersion variety** — prevents "Це X" spam that degrades content quality
3. **Hortative ban examples** — prevents recurring imperative violations in early A1
