# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Track Calibration

# Track Calibration: B2

## Bilingual Scope
B2 is fully immersed (100% Ukrainian). Flag ANY English in prose as
LANGUAGE_BLENDER. Only vocabulary tables and frontmatter may contain English.

## Russicism Lookup (B2)
Zero tolerance. All previous Russicisms plus:
- якщо → коли (when 'if' is better expressed with 'when' — context-dependent, don't over-flag)
- обов'язково → конче (insistently — register choice, both acceptable)
- любий (meaning "будь-який") — flag as Russian "любой"
- приходити до висновку → доходити висновку (to come to a conclusion)

## LLM Filler Sensitivity
Very strict. Flag ALL generic AI patterns in Ukrainian. No tolerance for:
- Meta-commentary about the lesson structure
- Generic transitions between sections
- Stacked abstract nouns or AI-typical metaphors

## Content Focus
Advanced grammar, cultural content, professional communication.
Focus on: register accuracy, coherent argumentation, natural flow between
paragraphs, absence of AI artifacts.


---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-medical-ukrainian.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/activities/register-medical-ukrainian.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/vocabulary/register-medical-ukrainian.yaml`

---

## Review (from Phase D.1)

# Рецензія: Медична українська: спілкування у сфері охорони здоров'я

**Level:** B2 | **Module:** b2-20
**Overall Score:** 8.5/10
**Status:** PASS
**Reviewed-By:** claude-opus-4-6
**Reviewed:** 2026-02-27

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 6 plan sections present as H2 headers. Minor title variations:
  Plan "Медична документація та цифровізація" → Content adds "суспільства";
  Plan "Культура мовлення та корекція русизмів" → Content "Культура мовлення: корекція суржику та русизмів"
- Vocabulary: 30/20 from plan (10 required + 10 recommended). All 10 required present, all 10 recommended present, 10 extra.
- Grammar scope: CLEAN — no scope creep detected. Grammar focuses on: біль gender, лікувати/лікуватися, відділ/відділення. All within medical register B2 scope.
- Objectives: Both objectives addressed:
  (1) "Understand and apply медична українська" — covered across all sections
  (2) "Analyze and evaluate медичний регістр" — covered through register comparison (formal vs colloquial, section "Культура мовлення: корекція суржику та русизмів")
- Activity hints: quiz 15/15+ ✅, fill-in 12/12+ ✅, match-up 15/16+ ❌ (1 short), reading 4/4 ✅, error-correction 12/12+ ✅, essay-response ✅. Extra types: unjumble, true-false, translate, select, group-sort, cloze.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong opening hook with "Чому це важливо?" frame. Pharmacy culture and Helsi.me are highly practical hooks. TTT boxes (lines 57-63, 150-156, 252-259) engage before explaining. However, some sections are quite long without breaks — section "Опис симптомів та відчуттів" runs heavily with 5 identical-format clinical example blocks. |
| 2 | Coherence | 9/10 | <7 | Clear narrative arc: pharmacy → symptoms → consultation → instructions/Amosov → documentation → anti-surzhik. Each section builds on vocabulary and concepts from the previous one. Transitions are natural and motivated. |
| 3 | Relevance | 9/10 | <7 | Directly covers B2 State Standard §3.9 health domain. Helsi.me, e-prescriptions, pharmacy culture — all immediately practical for anyone living in Ukraine. Amosov provides cultural depth. |
| 4 | Educational | 9/10 | <7 | Key grammar points (біль gender, лікувати/лікуватися, відділ/відділення) explained thoroughly with multiple examples. Medical collocations (поставити діагноз, приймати ліки, здати аналізи) are systematically introduced. Pain vocabulary taxonomy is clinically accurate and pedagogically useful. |
| 5 | Language | 8/10 | <8 | Ukrainian is high-quality, natural, and register-appropriate. No Russianisms in the teaching prose. However: 12+ English parenthetical translations appear in the body text (lines 129, 137, 143-146, 160, 167, 226, 263, 278, 279) — LANGUAGE_BLENDER for a B2 module that should be 100% Ukrainian. Line 80: awkward compound "маркер-помилка" (should be "помилка-маркер"). |
| 6 | Pedagogy | 8/10 | <7 | Excellent TTT structure: practice boxes before theory at three key grammar points. Strong scaffolding from concrete pharmacy scenarios to abstract grammatical analysis. Section "Консультація: Діалог лікар-пацієнт" models real clinical dialogue structure well. Deduction: pain-type examples (lines 94-107) use identical format ×5, reducing pedagogical variety. |
| 7 | Immersion | 8/10 | <6 | 98.7% Ukrainian (audit metric). Plan specifies 100%. English parenthetical glosses appear 12+ times in prose body — these should be in vocabulary tables only, not inline. Track calibration: "Flag ANY English in prose as LANGUAGE_BLENDER." |
| 8 | Activities | 9/10 | <7 | 15 activities across 12 types — excellent variety. Error-correction activities directly target module's key errors (біль gender, відділ/відділення, лікувати/лікуватися, осмотр→огляд). Reading activities include 4 authentic-style texts (Amosov, drug leaflet, Helsi notification, hospital discharge). Match-up has 15/16 pairs (1 short of plan). |
| 9 | Richness | 9/10 | <6 | 99% richness, 11 engagement boxes. Good variety: [!culture], [!decolonization], [!practice], [!warning], [!tip], [!quote], [!note]. Register comparison table (lines 327-334). Pharmacy culture, Helsi.me digital system, Amosov philosophy — all provide authentic cultural embedding. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 5/5. Strong scaffolding for B2 learners. Practice boxes before theory build confidence. However, some paragraphs run very long (section "Вступ: Медичний регістр та культура аптеки" has dense paragraphs without visual breaks between lines 22-34). Summary section with self-check questions closes well. |
| 11 | LLM Fingerprint | 8/10 | <7 | Section openings are varied (no 3+ identical starts ✅). No "це не просто"/"це не лише" patterns found ✅. Callout titles vary ✅. However: 5 consecutive pain-type descriptions (lines 94-107) use identical format (bold term → description → italic "*Клінічний приклад:*" → quoted speech) — this structural uniformity across the subsection reads as LLM-generated. |
| 12 | Linguistic Accuracy | 9/10 | <9 | All grammar explanations verified: біль = masculine ✅, лікувати = transitive ✅, лікуватися = reflexive/intransitive ✅, відділ ≠ відділення ✅, приймати ліки (not пити) ✅, брати участь (not приймати) ✅, ліки = plurale tantum ✅. No overgeneralizations or inaccurate rules found. |
| 13 | Factual Accuracy | 8/10 | <8 | Amosov facts correct: кардіохірург, "система обмежень і навантажень", комплекс "1000 рухів", "Роздуми про здоров'я" ✅. Helsi.me description accurate ✅. E-prescription process accurate ✅. Issue: Reading activity 1 (activities line 740) attributes mixed content to Amosov's book — the first 3 sentences are a real quote, but remaining sentences are paraphrased module prose presented as Amosov's primary text. This is fabricated sourcing. |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 9×1.3 + 9×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 8×1.5) / 15.5
= (12.0 + 9.0 + 9.0 + 10.8 + 8.8 + 9.6 + 8.0 + 11.7 + 8.1 + 10.4 + 8.0 + 13.5 + 12.0) / 15.5
= 130.9 / 15.5
= **8.4/10**
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — No Russianisms in teaching prose. Russian terms appear only in error examples (lines 311, 318) and [!decolonization] callout (line 72), which are legitimate pedagogical uses.
- Calques: [CLEAN] — Calques appear only as teaching examples in section "Культура мовлення: корекція суржику та русизмів" (lines 309-319).
- Colonial framing: [CLEAN] — Line 69 uses "інших слов'янських мов" (euphemism for Russian) which is appropriate decolonization framing. Line 72 names Russian within a [!decolonization] block (legitimate exception). Line 302 provides historical context about Russification (legitimate exception).
- Grammar scope: [CLEAN] — All grammar points (біль gender, лікувати/лікуватися, відділ/відділення) are within B2 medical register scope.
- Activity errors: Match-up has 15/16 pairs (plan requires 16+). Minor shortfall.
- Beginner safety: 5/5
- Factual accuracy: Reading activity 1 fabricates primary source attribution (see Issue 3 below).

## Critical Issues Found

### Issue 1: LANGUAGE_BLENDER — English in B2 prose body
- **Location**: Lines 129, 137, 143-146, 160, 167, 226, 263, 278, 279
- **Original**: Line 226: 「слово ліки в українській граматиці завжди і без винятків вживається у формі множини (подібно до слів "scissors", "trousers" чи "glasses" в англійській мові)」
- **Problem**: B2 track calibration requires 100% Ukrainian immersion. English parenthetical translations and comparisons appear 12+ times throughout the prose body, not in vocabulary tables or frontmatter.
- **Fix**: Remove all English parenthetical translations from prose. Replace English comparisons with Ukrainian metalinguistic explanations. E.g., line 226: remove the "(подібно до слів...)" comparison entirely — the Ukrainian explanation is self-sufficient. For lines 143-146 (doctor questions), remove the English translations — by B2, learners should understand from context.

### Issue 2: Example format monotony in section "Опис симптомів та відчуттів"
- **Location**: Lines 94-107 (pain types: ниючий, ріжучий, пульсуючий, розпираючий, тупий)
- **Original**: Each block follows identical structure: `**Term**: Description paragraph. → *Клінічний приклад:* «Quoted speech»`
- **Problem**: 5 consecutive identical-format blocks. LLM-typical structural uniformity. A real textbook would vary presentation: some as table cells, some as dialogues, some as fill-in exercises.
- **Fix**: Vary the format. Present ниючий and ріжучий in the current format, present пульсуючий and тупий as a comparison table, present розпираючий within a patient dialogue. This maintains content while breaking monotony.

### Issue 3: Fabricated primary source in Reading Activity 1
- **Location**: Activities YAML, lines 740-741 (reading type, id: reading-1)
- **Original**: Source attributed to "Микола Амосов, Роздуми про здоров'я" — but only the first 3 sentences match the actual Amosov quote (line 210 of content). Sentences 4-7 ("Медицина може врятувати вас лише у критичний момент...") are paraphrased from the module author's prose (line 213).
- **Problem**: Presenting module-authored paraphrase as a primary source quote from Amosov's book is factual misattribution.
- **Fix**: Either (a) limit the reading text to the verified Amosov quote only ("Лікарі лікують хвороби... усієї нашої фізіології") and label the rest as "за мотивами / adapted", or (b) change the source attribution to "Адаптовано за: Микола Амосов" and adjust the reading tasks accordingly.

### Issue 4: Awkward compound "маркер-помилка"
- **Location**: Line 80, section "Опис симптомів та відчуттів"
- **Original**: Callout title 「Увага: Критична мовна маркер-помилка!」 (from line 80 callout header)
- **Problem**: "маркер-помилка" is semantically reversed — the intended meaning is "a mistake that serves as a marker" = "помилка-маркер". The compound as written means "a marker that is a mistake", which is nonsensical.
- **Fix**: Change to "Увага: Критична мовна помилка-маркер!" or simply "Увага: Помилка, яка видає рівень мовця!"

### Issue 5: Match-up activity short of plan requirement
- **Location**: Activities YAML, lines 699-735 (match-up type)
- **Problem**: 15 pairs provided, plan activity_hints specify 16+. One pair short.
- **Fix**: Add one more pair. Suggestion: "Лікарняний лист" ↔ "Офіційний документ для підтвердження тимчасової непрацездатності".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 80 | 「Критична мовна маркер-помилка」 | 「Критична помилка-маркер」 | Compound word order |
| 129 | "(patient's complaints)" | Remove English | LANGUAGE_BLENDER |
| 137 | "(doctor's consultation)" | Remove English | LANGUAGE_BLENDER |
| 143 | "(What is bothering you?)" | Remove English | LANGUAGE_BLENDER |
| 144 | "(How long ago did this start?)" | Remove English | LANGUAGE_BLENDER |
| 145 | "(Do you have an allergy to any medications?)" | Remove English | LANGUAGE_BLENDER |
| 146 | "(Have you taken any medicine independently before visiting me?)" | Remove English | LANGUAGE_BLENDER |
| 160 | "(Transitive verb)" | Remove or replace: "(перехідне)" | LANGUAGE_BLENDER |
| 167 | "(Reflexive verb)" | Remove or replace: "(зворотне)" | LANGUAGE_BLENDER |
| 226 | "(подібно до слів "scissors", "trousers" чи "glasses" в англійській мові)" | Remove comparison entirely | LANGUAGE_BLENDER |
| 263 | "одним і тим самим словом "department"" | Remove English or rephrase | LANGUAGE_BLENDER |
| 278 | "sick leave certificate" | Remove English | LANGUAGE_BLENDER |
| 279 | "(patient's medical history)" | Remove English | LANGUAGE_BLENDER |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — Module scaffolds from familiar pharmacy scenario to formal medical terminology
- Instructions clear? Pass — Practice boxes set expectations before each grammar explanation
- Quick wins? Pass — Lines 57-63 give an immediate self-test that creates curiosity
- Ukrainian scary? Pass — Strong teacher voice with encouragement and anticipation of errors
- Come back tomorrow? Pass — Practical relevance (health, pharmacy, digital tools) motivates continued study

## Strengths
- **Excellent cultural embedding**: The pharmacy culture section (lines 22-37) is genuinely informative and gives learners real practical knowledge about Ukrainian medical culture, not just vocabulary.
- **Strong TTT pedagogy**: Three well-placed practice boxes (lines 57-63, 150-156, 252-259) create discovery moments before grammar rules are stated.
- **Amosov as cultural hook**: The Amosov section (lines 196-218) naturally extends medical vocabulary into health philosophy while introducing an important Ukrainian cultural figure.
- **Anti-surzhik section**: Section "Культура мовлення: корекція суржику та русизмів" (lines 300-339) directly addresses real learner errors with clear incorrect/correct pairs and linguistic reasoning.
- **Activity variety**: 12 distinct activity types covering grammar, vocabulary, pragmatic skills, reading comprehension, and production.
- **Register comparison table**: Lines 327-334 provide a clear, useful comparison of colloquial vs. formal medical terminology.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 8/10 → 9/10
**What to fix:**
1. Lines 129, 137, 143-146, 160, 167, 226, 263, 278, 279: Remove all 12 English parenthetical translations from the prose body. For grammatical terms (lines 160, 167), replace with Ukrainian equivalents in parentheses: "(перехідне дієслово)" and "(зворотне дієслово)".
2. Line 80: Change 「Критична мовна маркер-помилка」→ "Критична помилка-маркер" or "Помилка, яка видає рівень мовця".

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 94-107 (section "Опис симптомів та відчуттів"): Vary the format of pain-type examples. Present 2 as current format, 2 in a comparison table, 1 in a patient dialogue. This breaks monotony and adds pedagogical variety.

**Expected score after fix:** 9/10

### Immersion: 8/10 → 9/10
**What to fix:**
Same as Language fixes above — removing English from prose body will raise immersion to ~100%.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
Same as Experience Quality — varying pain-type presentation formats.

**Expected score after fix:** 9/10

### Beginner Safety: 8/10 → 9/10
**What to fix:**
1. Lines 22-34 (section "Вступ: Медичний регістр та культура аптеки"): Break the long pharmacy paragraph into 2 shorter paragraphs with a visual break after line 27 (after the pharmacist question examples).

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Activities lines 740-741: Change source attribution for reading-1 from "Микола Амосов, Роздуми про здоров'я" to "Адаптовано за мотивами: Микола Амосов, Роздуми про здоров'я" — or limit the text to the verified quote only.
2. Activities line 702 (match-up): Add 1 more pair to meet 16+ plan requirement.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
Same as Experience Quality — varying pain-type example formats breaks the most visible structural monotony.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 9×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9 + 9 + 10.8 + 9.9 + 10.8 + 9 + 11.7 + 8.1 + 11.7 + 9 + 13.5 + 13.5) / 15.5
= 139.5 / 15.5
= 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (this is B2 core, not a seminar track — research notes are brief but present)
- Dates checked: N/A — no specific historical dates claimed beyond "ще десять років тому" (approximate)
- Named figures verified: 1 — Микола Амосов: кардіохірург, "система обмежень і навантажень", "1000 рухів", "Роздуми про здоров'я" — all confirmed in research notes
- Primary quotes cross-referenced: 1/1 — Amosov quote at line 210 matches research notes cultural hooks section
- Chronological sequence: N/A
- Claims without research grounding: 1 — Reading activity 1 extends the verified Amosov quote with module prose attributed to his book

## Verification Summary

- Content lines read: 357
- Activity items checked: 112 (15 quiz + 12 fill-in + 8 unjumble + 12 error-correction + 10 true-false + 8 translate + 8 select + 15 match-up + 4 reading + 1 essay + 1 group-sort + 16 cloze blanks + 2 schema checks)
- Ukrainian sentences verified: 40+
- Citations in bank: 16
- Issues found: 5

## Verdict

**PASS**

This is a strong B2 medical register module with effective TTT pedagogy, rich cultural embedding (pharmacy culture, Helsi.me, Amosov), and accurate grammar teaching. The five issues found are fixable: remove English parenthetical translations from prose (LANGUAGE_BLENDER), vary pain-type example formatting, fix the fabricated Amosov source attribution in reading activity 1, correct the "маркер-помилка" compound, and add 1 match-up pair. None trigger auto-fail thresholds.

---

## Audit Failures (from automated re-audit)

```
Gates:   6 pass, 1 info
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues
5. For Russianisms: replace with the standard Ukrainian form from the calibration table

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-medical-ukrainian.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/activities/register-medical-ukrainian.yaml
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
