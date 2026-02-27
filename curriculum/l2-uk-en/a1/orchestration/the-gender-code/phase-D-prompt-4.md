# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

---

## Review (from Phase D.1)

# Рецензія: The Gender Code

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 3
**Overall Score:** 8.5/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: PASS — All 5 meta content_outline sections present as H2 headers
  (Вступ, Презентація, Практика, Продукція, Культурний контекст + Підсумок)
- Vocabulary: 19/20 from plan (хліб missing from required; кімната missing from plan examples)
- Grammar scope: PASS — stays within gender system, no scope creep into adjective declension
- Objectives: PASS — all 4 learning objectives addressed
```

The plan (plans/a1/the-gender-code.yaml) specifies in Презентація: "Masculine (consonant: стіл, хліб, дім), Feminine (-а/-я: книга, кімната, земля)." Neither **хліб** nor **кімната** appear anywhere in the content or vocabulary. This is a minor plan compliance gap — the content substitutes other vocabulary (брат, серце) that serves the same pedagogical function, but the specific plan-required items are absent.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | 5/5 on "Would I Continue?" test. Warm opening with «Привіт!», clear objectives at lines 16-19, S.T.A.L.K.E.R. cultural hook in Section «Культурний контекст: Жива мова» adds genuine engagement. Ending with «Молодець!» and self-check questions. |
| 2 | Coherence | 9/10 | <7 | Clean PPP arc: Section «Вступ: Таємний код української мови» establishes mnemonics → Section «Презентація: Три кити роду» teaches rules → Section «Практика: Чотири сім'ї та винятки» drills exceptions → Section «Продукція: Колір і форма» applies algorithm → Section «Культурний контекст: Жива мова» contextualizes → Section «Підсумок» celebrates. One minor coherence issue in the mini-dialogue (line 265). |
| 3 | Relevance | 9/10 | <7 | All content directly serves learning objectives. Family vocabulary (мама, тато, брат, сестра) is maximally relevant for A1 learners. S.T.A.L.K.E.R. hook in Section «Культурний контекст: Жива мова» targets a known gamer demographic for Ukrainian language learners. |
| 4 | Educational | 8/10 | <7 | Strong overall, but Section «Презентація: Три кити роду» line 108 makes an inaccurate semantic generalization about neuter nouns that could build a false mental model. Plan-required vocabulary (хліб, кімната) missing reduces coverage breadth. |
| 5 | Language | 8/10 | <8 | English is warm and accessible throughout. Ukrainian examples are clean. However: IPA discrepancy between content [stʲil] (line 69) and vocabulary file [sʲtʲil] (vocabulary line 11). Line 108's semantic claim about neuter nouns is linguistically inaccurate. Line 265 dialogue has naturalness issue. |
| 6 | Pedagogy | 9/10 | <7 | PPP structure well-executed. "Trap" framing for exceptions is pedagogically excellent — turns potential frustration into detective game. The "Gender Algorithm" at Section «Продукція: Колір і форма» lines 216-222 gives learners a concrete decision procedure. Quick win at line 133-138 before deeper content. |
| 7 | Immersion | 7/10 | <6 | Pre-computed: 11.4%. Target for A1.1: 20-40%. Below lower bound by ~9 percentage points. Justified by grammar-heavy content requiring English explanation, but more Ukrainian instructions, section transitions, and engagement phrases could close the gap. |
| 8 | Activities | 9/10 | <7 | 9 activities, 115 items. Good variety: 2× group-sort, 2× quiz, 2× fill-in, 1× match-up, 1× anagram, 1× true-false. All answers verified correct. Distractors are appropriate (Множина, Універсальний, Спільний test conceptual understanding). |
| 9 | Richness | 8/10 | <6 | S.T.A.L.K.E.R. hook, земля-мати cultural connection, сонце folklore contrast with Romance languages. Good tables and visual organization. Deduction: no audio/listening references, limited authentic text examples, Section «Продукція: Колір і форма» word analysis feels formulaic. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Welcoming opening, clear preview, frequent encouragement, no overwhelming sections. Ukrainian introduced gently. «Спробуйте зараз!» at line 133 provides early success. «Молодець!» at Section «Підсумок» celebrates achievement. |
| 11 | LLM Fingerprint | 8/10 | <7 | No "explore"/"important to note" patterns. No colonial framing. No rhetoric patterns (це не просто). However: Section «Продукція: Колір і форма» word analyses at lines 227-257 follow an identical template (Ending → Category → Gender → Phrase) for all 5 words — formulaic batching pattern. Each gender subsection in Section «Презентація: Три кити роду» follows The Rule → Examples → The Trap → Usage Note — pedagogically intentional but structurally repetitive. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL TRIGGER.** Line 108: «They typically denote abstract concepts, substances, or things that are neither clearly active agents nor passive recipients» — this is linguistically wrong. Neuter includes very concrete nouns (вікно, місто, яйце). IPA mismatch: content has [stʲil] (line 69), vocabulary has [sʲtʲil] (vocab line 11). All gender rules and pronoun agreements are correctly taught. |
| 13 | Factual Accuracy | 9/10 | <8 | Cultural claims verified: French "le soleil" (M) ✓, German "die Sonne" (F) ✓. Собака as masculine per СУМ ✓. Ім'я as neuter ✓. The «земля-мати» concept in Section «Культурний контекст: Жива мова» is well-established in Ukrainian culture. Line 88 "90% likely" claim for -а/-я being feminine is a reasonable pedagogical heuristic. |

**Weighted Overall:**
```
(9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 9×1.2 + 7×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 8×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 9.6 + 8.8 + 10.8 + 7.0 + 11.7 + 7.2 + 11.7 + 8.0 + 12.0 + 13.5) / 15.5
= 131.8 / 15.5
= 8.50/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no кушать, приймати участь, or similar detected
- Calques: [CLEAN] — no робити сенс, брати місце, or similar detected
- Colonial framing: [CLEAN] — no "Unlike Russian" patterns; no Russian comparisons used
- Grammar scope: [CLEAN] — stays within gender identification and мій/моя/моє; adjective agreement correctly deferred to a1-26 per SCOPE comment
- Activity errors: [CLEAN] — all 115 activity items verified correct
- Beginner safety: 5/5
- Factual accuracy: [CLEAN] — all cultural and linguistic claims verified

## Critical Issues Found

### Issue 1: Inaccurate Linguistic Generalization About Neuter Nouns
- **Location**: Line 108 / Section «Презентація: Три кити роду»
- **Original**: «They typically denote abstract concepts, substances, or things that are neither clearly active agents nor passive recipients.»
- **Problem**: This characterization is linguistically false. Neuter nouns in Ukrainian include highly concrete, everyday objects: вікно (window), місто (city), молоко (milk), яйце (egg). Abstract nouns are distributed across all three genders (любов F, сум M, щастя N). Teaching learners that neuter "typically denotes abstract concepts" builds a false mental model that will cause gender prediction errors.
- **Fix**: Replace with: «Neuter nouns are the "round" ones. They include everyday objects, places, and some abstract ideas — but unlike Masculine and Feminine, you cannot predict Neuter from meaning. The ending (-о/-е) is the only reliable clue.»

### Issue 2: IPA Discrepancy Between Content and Vocabulary File
- **Location**: Content line 69 vs. vocabulary file line 11
- **Original (content)**: «стіл** [stʲil]»
- **Original (vocabulary)**: «ipa: '[sʲtʲil]'»
- **Problem**: The same word has different IPA transcriptions across files. Content has [stʲil] (no palatalization on /s/), vocabulary has [sʲtʲil] (regressive palatalization). For A1 consistency, both files should match.
- **Fix**: Standardize to [stʲil] in the vocabulary file (the more commonly cited transcription in Ukrainian phonology textbooks).

### Issue 3: Unnatural Dialogue Turn at Line 265
- **Location**: Line 265 / Section «Продукція: Колір і форма», subsection «Міні-діалог: Сім'я (The Family)»
- **Original**: «А де **моя** сестра?»
- **Problem**: In context, Андрій is introducing HIS family members. Олена's response «А де моя сестра?» (And where is MY sister?) is a non-sequitur — there's no setup for why Олена is suddenly looking for her own sister in the middle of meeting Андрій's family.
- **Fix**: Change to «А це твоя сестра?» (And is this your sister?) to maintain natural conversational flow, or add a preceding line establishing that Олена and Андрій's families are meeting together.

### Issue 4: Plan Vocabulary Gap — хліб and кімната Missing
- **Location**: Global — plan (plans/a1/the-gender-code.yaml) Презентація section
- **Problem**: The plan specifies "Masculine (consonant: стіл, хліб, дім), Feminine (-а/-я: книга, кімната, земля)" but neither хліб nor кімната appears anywhere in the content or vocabulary file. The content substitutes other words (брат, серце) that serve similar purposes, but plan-specified vocabulary should be included.
- **Fix**: Add хліб [xlʲib] as an additional masculine example in Section «Презентація: Три кити роду» masculine subsection. Add кімната as an additional feminine example in the feminine subsection.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 108 | «They typically denote abstract concepts, substances, or things that are neither clearly active agents nor passive recipients» | Remove semantic characterization; teach only by ending pattern | Linguistic overgeneralization |
| 69 vs vocab:11 | Content: [stʲil] / Vocab: [sʲtʲil] | Standardize to [stʲil] in both files | IPA inconsistency |
| 265 | «А де моя сестра?» | «А це твоя сестра?» | Naturalness |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — pacing is comfortable; new concepts introduced 2-3 at a time before practice
- Instructions clear? **Pass** — clear objectives at lines 16-19; «Спробуйте зараз!» at line 133 gives explicit instructions
- Quick wins? **Pass** — inline quiz at line 133-138 provides immediate success; answer key follows instantly
- Ukrainian scary? **Pass** — Ukrainian introduced gently within English scaffolding; IPA provided for all new words
- Come back tomorrow? **Pass** — S.T.A.L.K.E.R. hook is fun; «Молодець!» ending is warm; self-check questions invite engagement

## Strengths

- **Exceptional mnemonic system**: "Hard Stop" (M), "Open A" (F), "Round O" (N) is memorable and pedagogically sound. Presented in Section «Вступ: Таємний код української мови» and reinforced throughout.
- **"Trap" framing for exceptions**: Treating тато, ніч, and ім'я as "traps" to detect turns exception-learning into a game, which is ideal for beginner engagement in Section «Практика: Чотири сім'ї та винятки».
- **S.T.A.L.K.E.R. hook in Section «Культурний контекст: Жива мова»**: Using game vocabulary (артефакт, зона, укриття) as gender classification anchors is a genuinely creative engagement strategy for the target learner demographic.
- **Activity breadth**: 9 activities with 115 items across 6 different activity types provides thorough practice without monotony.
- **Clean PPP arc**: Section «Підсумок» genuinely celebrates progress ("You now possess the three keys") rather than merely restating rules.

## Fix Plan to Reach 9.0/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 108: Remove the semantic characterization. Replace «They typically denote abstract concepts, substances, or things that are neither clearly active agents nor passive recipients» with a description that focuses on the ending pattern without false semantic generalizations.
2. Vocabulary file line 11: Change `'[sʲtʲil]'` → `'[stʲil]'` to match content file.

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 265: Change «А де моя сестра?» → «А це твоя сестра?» or add context for why Олена asks about her own sister.
2. Fix IPA discrepancy (same as Linguistic Accuracy fix #2).

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Add **хліб** and **кімната** to Section «Презентація: Три кити роду» as additional examples per plan specification.
2. Fix the neuter semantic characterization (same as Linguistic Accuracy fix #1).

**Expected score after fix:** 9/10

### Immersion: 7/10 → 8/10
**What to fix:**
1. Convert some English section transitions to Ukrainian with English gloss. E.g., line 60 "Let's break down the rules" → «Розглянемо правила!» (Let's look at the rules!)
2. Add 2-3 more Ukrainian engagement phrases: «Готові?» (Ready?), «Чудово!» (Wonderful!), «Далі!» (Next!)
3. Convert the self-check intro at line 322 from «Перевірте себе:» (already Ukrainian ✓) — look for other English-only transitions that could be bilingual.

**Expected score after fix:** 8/10

### Richness: 8/10 → 9/10
**What to fix:**
1. Add a brief authentic text reference (e.g., a Ukrainian children's rhyme or proverb that demonstrates gender agreement).
2. In Section «Культурний контекст: Жива мова», add one more real-world example beyond S.T.A.L.K.E.R. (e.g., Ukrainian city names as gender examples: Київ M, Одеса F, Запоріжжя N).

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Vary the word analysis template in Section «Продукція: Колір і форма» lines 227-257. Currently all 5 follow: Ending → Category → Gender → Phrase. Mix up the presentation: for at least 2 items, lead with the phrase or the mnemonic before revealing the ending.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 8×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 8.0 + 11.7 + 8.1 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 138.5 / 15.5
= 8.94/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core grammar track, no research file)
- Key Facts Ledger present: NO (not applicable)
- Dates checked: 0 (no historical dates in content)
- Named figures verified: 0 (no historical figures referenced)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: N/A

**Callout box verification (all tracks):**
- Line 34-38: Sun comparison (French masculine, German feminine, Ukrainian neuter) — **VERIFIED CORRECT**
- Line 48-56: "Don't Trust Your English Instincts" tip — pedagogically sound, no factual claims
- Line 171-174: "The Dad Trap" warning — **VERIFIED CORRECT** (тато is masculine)
- Line 209-211: "Is Name Feminine?" myth-buster — **VERIFIED CORRECT** (ім'я is neuter; comparison to сім'я is legitimate)
- Line 298-305: "Nice to Meet You" culture note — **VERIFIED CORRECT** (моє ім'я is correct neuter agreement)

## Verification Summary

- Content lines read: 329
- Activity items checked: 115
- Ukrainian sentences verified: 18 (all example phrases and dialogue lines)
- IPA transcriptions checked: 22 (content + vocabulary; 1 discrepancy found)
- Factual claims verified: 5 (callout boxes)
- Issues found: 4

## Verdict

**FAIL**

Blocking issue: **Linguistic Accuracy 8/10** (auto-fail threshold <9) — the neuter semantic overgeneralization at line 108 teaches learners an inaccurate characterization of neuter nouns as "typically abstract," which contradicts the module's own concrete neuter examples (вікно, місто, серце). Fix is trivial: remove the semantic claim and teach gender by ending only. Secondary issues (IPA discrepancy, dialogue naturalness, plan vocabulary gap) should be addressed in the same fix pass.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
failing gates:
review: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-gender-code-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
