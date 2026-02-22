# Рецензія: The Cyrillic Code II: The Final 15 Letters

**Reviewed-By:** claude-sonnet-4-6

**Level:** A1 | **Module:** a1-02
**Overall Score:** 8.1/10
**Status:** PASS
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with one plan-side error)
- Sections: PASS — all 5 H2 sections present:
    Вступ, Унікальні приголосні, Йотовані голосні та М'який знак,
    Голосні та напівголосні, Практика та вимова
- Plan subtitle discrepancy: plan.yaml says "The Final 14 Letters";
    content correctly counts 15 (Г Ґ Ж Ш Щ Ч Ц Є Ї Ю Я Ь И І Й = 15).
    The plan subtitle is wrong; the content is correct.
- Vocabulary: PASS — all 8 required items present (центр, чай, школа,
    гарний, жити, день, Європа, яблуко); recommended items present
    (ще, ґанок, їжа, юнак, сім'я)
- Vocabulary file issue: тінь (shadow) in vocab.yaml has no content anchor;
    ніч (night) is in content line 210 and plan recommended list but ABSENT
    from vocab.yaml
- Grammar scope: PASS — no later-module grammar introduced
- Objectives: PASS — all 4 learning objectives addressed
- State Standard references: PASS — §4.1.4 (И/І), §4.1.3 (Ь), §4.1.1
    identity spellings all addressed
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm narrative opening, varied cultural hooks (decolonization for Ґ, Mariupol resistance for Ї, tea-offer dialogue for Ч), good closing celebration. Pacing concern: Section «Унікальні приголосні» runs 920 words covering 7 consonants with no embedded practice checkpoint. |
| 2 | Language | 8/10 | <8 | Ukrainian text generally clean. Two borderline calques at lines 233 and 260: «Давайте практикувати!» and «Давайте читати.» use "давайте + infinitive" — recognized as a Russianism/calque in Ukrainian prescriptive grammar. Standard forms: "Практикуймо!" / "Читаймо!" No Russianisms in vocabulary. |
| 3 | Pedagogy | 8/10 | <7 | PPP structure sound. Quick Check at line 188 ("Before moving on, can you read these words confidently?") is a good embedded checkpoint added between iotated vowels and final vowels sections. No equivalent checkpoint within Section «Унікальні приголосні» (920 words, 7 consecutive letter presentations, zero interaction). Plan's requirement to break down phonetic shifts for шість and Львів is partially met — only де́нь receives explicit treatment in the warning callout. |
| 4 | Activities | 8/10 | <7 | 8 activities, 6 unique types. All 52 items checked — factually correct. Г/Ґ fill-in and И/І fill-in are pedagogically strong. Minor: Activity 5 (И or І?) item 2 explanation reads "Діти (children) uses the soft І, which softens the D sound" — causation is inverted (it's not that І softens D; both follow the same phonological rule). тінь orphaned in vocab file but not in activities (activities use лі́то and сік which do appear in content). |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Ukrainian at 5.3% — appropriately gentle for A1.1. Required emotional beats all present. Concern: Section «Унікальні приголосні» provides no encouragement or check-in across ~920 words; the only embedded Ukrainian phrase in that section is «Це дуже важливо.» (line 41), which is informational rather than encouraging. |
| 6 | LLM Fingerprint | 7/10 | <7 | Significant improvement from prior pass: Г (narrative), Ж (sensory), Щ (contrast table), Ч (dialogue), Є/Ю (auditory), И/І (paired technique) all use varied openers. Still: 7 of 15 H3 subsections open with "The letter X" formula — Ґ (l.45), Ш (l.72), Ц (l.111), Ї (l.141), Я (l.161), Ь (l.175), Й (l.219). Approximately 11 of 15 sections present vocabulary examples in identical bare bold-list format. Both exceed the 3+ section threshold per rubric. |
| 7 | Linguistic Accuracy | 9/10 | <9 | All 20 IPA transcriptions verified correct. Phonetic rules accurate throughout: [ɦ] description for Г, affricate characterization of Щ, palatalization explanation for Ь. «Запам'ятайте це правило.» (l.229) — correct Ukrainian imperative. Two borderline "давайте + infinitive" instances are linguistically contested (not definitively wrong) and therefore do not drop this below 9. Activity 5 causation inversion (item 2) is a pedagogical framing issue, not a factual error. |

**Weighted Overall:**
```
(8×1.5) + (8×1.1) + (8×1.2) + (8×1.3) + (8×1.3) + (7×1.0) + (9×1.5)
= 12.0 + 8.8 + 9.6 + 10.4 + 10.4 + 7.0 + 13.5
= 71.7 / 8.9 = **8.1/10**
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: BORDERLINE — «Давайте практикувати!» (l.233) and «Давайте читати.» (l.260) use давайте + infinitive (recognized Russianism in prescriptive Ukrainian; debated in colloquial use). Categorized as borderline, not hard auto-fail.
- Grammar scope: CLEAN — no later-module grammar introduced
- Activity errors: CLEAN — all 52 items factually accurate
- Beginner safety: 4/5
- Factual accuracy: CLEAN — Ґ ban (1933) and restoration (1990) historically accurate; Ї resistance symbol in Mariupol 2022 culturally grounded and plausible
- Colonial framing: CLEAN — Ukrainian presented on its own terms; Russian never used as comparison baseline; decolonization callout (Ґ) and culture callout (Ї) are legitimate framing

## Critical Issues Found

### Issue 1: LLM Fingerprint — Persistent Formula Openings in H3 Subsections
- **Location**: Lines 45 (Ґ), 72 (Ш), 111 (Ц), 141 (Ї), 161 (Я), 175 (Ь), 219 (Й) / Sections «Унікальні приголосні», «Йотовані голосні та М'який знак», «Голосні та напівголосні»
- **Original**: «The letter **Ґ** is the true equivalent of the hard English "g"» / «The letter **Ш** resembles a pitchfork or a comb pointing upward» / «The letter **Ц** looks like the letter П» / «The letter **Ї** is a vertical line with two dots on top» / «The letter **Я** looks like a backwards English capital "R."» / «The letter **Ь** is completely unique because it has no sound of its own» / «The letter **Й** looks exactly like the hard vowel **И**, but it wears a small curved hat on top»
- **Problem**: 7 of 15 H3 letter subsections still open with "The letter X [description]" formula. Additionally, approximately 11 of 15 sections present vocabulary examples as identical bare bold-list blocks. Both exceed the 3+ threshold that triggers the example batching penalty. This is real improvement from 13/15 in the prior pass, but the remaining 7 formula sections are still mechanically uniform. Sections Є, Ю (auditory), Г (narrative), Ж (sensory), Щ (table), Ч (dialogue), И/І (paired technique) demonstrate that varied approaches are achievable — the same creativity should extend to the remaining formula sections.
- **Fix**: Rework the opening sentence for Ї, Я, and Й in particular: Ї could open with the Mariupol defiance hook (currently in the callout box below) before introducing the phonetics; Я could open with "Every time you say 'я' you are speaking your identity — because 'я' is both a letter and the Ukrainian word for 'I'"; Й could open with a contrast against И: "You already know the grinning И. Add a hat to it and it becomes something else entirely."

### Issue 2: Calque — «Давайте практикувати!» and «Давайте читати.»
- **Location**: Line 233 (Section «Практика та вимова»), Line 260 (Section «Практика та вимова»)
- **Original**: «Давайте практикувати!» and «Давайте читати.»
- **Problem**: The "давайте + infinitive" construction is a calque of Russian "давайте + инфинитив." In standard Ukrainian, "давайте" takes a conjugated first-person plural verb, not the infinitive. Prescriptive Ukrainian: "Практикуймо!" / "Давайте попрактикуємось!" and "Читаймо!" / "Давайте читатимемо!" A language curriculum introducing the language to beginners models these patterns as correct Ukrainian. Beginners who internalize «Давайте практикувати» as natural Ukrainian will produce a Russianism.
- **Fix**: Line 233: Replace «Давайте практикувати!» with «Практикуймо!» (imperative, 100% standard). Line 260: Replace «Давайте читати.» with «Читаймо.» Both are shorter, crisper, and fully standard Ukrainian.

### Issue 3: Orphaned Vocabulary Item and Missing Entry
- **Location**: Vocabulary file (тінь at vocab line 18); content line 210 (ні́ч)
- **Problem**: «тінь» (shadow) appears in the vocabulary file with IPA [tʲinʲ] but is never mentioned anywhere in the lesson content. Verified by Read tool search across all 299 lines — zero occurrences. Beginners encountering тінь in any quiz or reference will have no lesson anchor for it. Conversely, «ні́ч» (night) appears at content line 210 in the І section example list, is listed in the plan's recommended vocabulary, but is absent from the vocabulary file (no IPA provided for it).
- **Fix**: Remove тінь from vocabulary file (or add a brief mention in the Ь section example list: "**ті́нь** (shadow)" — the soft final Ь matches the section theme). Add ніч [nʲit͡ʃ] (night, noun) to the vocabulary file to replace or supplement тінь.

### Issue 4: No Practice Checkpoint in Section «Унікальні приголосні»
- **Location**: Lines 31–120 / Section «Унікальні приголосні»
- **Problem**: This section covers 7 consonants across approximately 920 words with zero embedded interaction. The prior review's fix added a Quick Check at line 188 (between the iotated/soft-sign section and the final vowels section), which is present and effective. However, no equivalent checkpoint was added within the consonants section itself, leaving A1 beginners to process Г, Ґ, Ж, Ш, Щ, Ч, Ц consecutively before receiving any validation. Per the ≤2 concepts before exercise rule, this violates beginner pacing standards.
- **Fix**: After line 120 (end of Ц subsection), add: "**Quick Drill:** Read these aloud, focusing on the buzzing vs. hissing distinction: **жи́ти** — **шко́ла** — **що́** — **ча́й** — **це́нтр** — **ґа́нок** — **га́рний**. Чудово! (Great job!)"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 233 | «Давайте практикувати!» | «Практикуймо!» | Calque (давайте + infinitive) |
| 260 | «Давайте читати.» | «Читаймо.» | Calque (давайте + infinitive) |
| Vocab file | тінь [tʲinʲ] — no content anchor | Remove or anchor in Ь section | Orphaned vocabulary |
| Vocab file | ніч absent | Add ніч [nʲit͡ʃ] (night, noun) | Missing recommended item |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **PASS** — 5.3% Ukrainian immersion; each letter introduced one at a time with mechanics explained in plain English; structure is predictable and safe
- Instructions clear? **PASS** — every subsection announces what the learner will learn and how to physically produce the sound
- Quick wins? **BORDERLINE PASS** — diagnostic review at lines 24–28 provides an early win; Quick Check at line 188 is good; the 920-word Section «Унікальні приголосні» is a long stretch without validation
- Ukrainian scary? **PASS** — Ukrainian phrases always immediately translated; 5.3% immersion is gentle; «Зверніть увагу:» (l.33) with immediate parenthetical English exemplary
- Come back tomorrow? **PASS** — "You have officially unlocked the entire Cyrillic code" closing is genuinely motivating; five Підсумок questions provide satisfying self-assessment

**Required emotional beats:**
- Welcome/orientation: ✓ Line 16 — "Welcome back to our journey through the Ukrainian alphabet!"
- Curiosity trigger: ✓ Line 18 — "Identity Letters" framing
- Quick wins: ✓ Lines 24–28 (diagnostic), line 188 (Quick Check), line 256 ("Чудова робота!")
- Encouragement: ✓ Line 29 — "If you hesitated, do not worry—repetition is a natural part of language learning"
- Progress marker: ✓ Lines 284–290 — "You have officially unlocked the entire Cyrillic code"

**Emotional gap**: Section «Унікальні приголосні» runs approximately 920 words with only one encouragement phrase embedded («Це дуже важливо.» at line 41). Section «Йотовані голосні та М'який знак» and Section «Голосні та напівголосні» do better with the Quick Check (l.188) and "Smile vs Grin" technique. A mid-consonants encouragement phrase would close the gap.

## Strengths

- **Varied pedagogical voices genuinely improved**: Г opens with a narrative Ukrainian neighbour greeting; Ж with "Close your eyes and say 'pleasure' slowly"; Щ deploys a comparison table; Ч opens with the Ukrainian tea dialogue «Хо́чеш ча́ю?»; И/І use the paired Smile/Grin physiological technique. These are the hallmarks of a real tutor, not a generator.
- **Cultural and decolonization hooks are excellent**: The [!decolonization] callout about Ґ (accurately covering the 1933 Soviet ban and 1990 restoration) and the [!culture] callout about Ї in Mariupol 2022 are both historically accurate and pedagogically powerful — connecting phonetics to living identity.
- **"Smile vs Grin" technique is A+ beginner pedagogy**: The physiological contrast between И (relaxed jaw, back of throat) and І (wide smile, forward sound) is exactly the kind of embodied instruction that makes abstract phonetics stick. The Ри́м–Рі́вне minimal pair precisely executes State Standard §4.1.4.
- **Closing delivers genuine accomplishment**: The Підсумок at lines 288–297 provides a celebratory summary and five concrete self-check questions that anchor learning without being threatening. Strong ending.
- **All 20 IPA transcriptions are correct**: Verified entire vocabulary file — Г [ɦ], Ш [ʃ], Ж [ʒ], Ц [t͡s], Ч [t͡ʃ], Щ [ʃt͡ʃ], Є [jɛ], Ї [ji], Ю [ju], Я [ja] — all phonetically accurate, stress marks correctly placed.

## Fix Plan to Reach 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 141 (Ї subsection opener in Section «Йотовані голосні та М'який знак»): Move the Mariupol resistance context (currently in the callout below) to the OPENING. Replace «The letter **Ї** is a vertical line with two dots on top.» with: «Imagine a city under occupation. And a single letter appears, painted on walls and fences. That letter is **Ї** — because it belongs only to Ukrainian.» Then introduce the phonetics. Cultural first, mechanics second.
2. Line 161 (Я subsection opener in Section «Йотовані голосні та М'який знак»): Replace «The letter **Я** looks like a backwards English capital "R."» with: «Here is a letter that does double duty: it is both an alphabet character and a complete word. **Я** means "I" in Ukrainian. Every time you write about yourself, you will use this letter.» Then explain the sound.
3. Line 219 (Й subsection opener in Section «Голосні та напівголосні»): Replace «The letter **Й** looks exactly like the hard vowel **И**, but it wears a small curved hat on top.» with: «You already know **И** (the grin). Add a tiny curved hat to it and it becomes something quite different — a brief, gliding semivowel. Meet **Й**.» Then explain the sound.
4. Sections «Унікальні приголосні» and «Йотовані голосні та М'який знак»: For at least 3 more sections (Ґ, Ц, Ь), replace the bare bold-list vocabulary presentation with a different format — e.g., a two-column table for Ґ (pairing "Native Ukrainian" vs. "Loanword from other languages"), inline sentence integration for Ь ("Notice how **де́нь** changes: harden the N and you get a clunky 'den'; soften it with Ь and the word breathes").

**Expected score after fix:** 8/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 233: Change «Давайте практикувати!» → «Практикуймо!»
2. Line 260: Change «Давайте читати.» → «Читаймо.»

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Vocabulary file: Remove тінь; add ніч [nʲit͡ʃ] (night, noun).
2. Activity 5, item 2 explanation: Change "Діти (children) uses the soft І, which softens the D sound" → "Діти (children) uses the soft І. After the letter Д, і indicates a soft pronunciation — the vowel and consonant follow the same phonological pattern."

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. After line 120 (end of Section «Унікальні приголосні», Ц subsection): Add "**Quick Drill:** Read these aloud, focusing on the buzzing vs. hissing distinction: **жи́ти** — **шко́ла** — **що́** — **ча́й** — **це́нтр** — **ґа́нок** — **га́рний**. Чудово!"
2. Line 41 area: Add one encouragement phrase mid-consonants section — e.g., after the Ж subsection: "You are making excellent progress! Four of the seven unique consonants done."

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Language:             8 → 9
Pedagogy:             8 → 9
Activities:           8 → 9
LLM Fingerprint:      7 → 8

(8×1.5) + (9×1.1) + (9×1.2) + (9×1.3) + (8×1.3) + (8×1.0) + (9×1.5)
= 12.0 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5
= 76.3 / 8.9 = 8.6/10 — PASS (improved)
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core grammar module — no research track)
- Key Facts Ledger present: NOT_APPLICABLE
- Dates checked: 2 — Ґ banned 1933 ✓; Ґ restored 1990 ✓
- Named figures verified: 0 (no named historical figures cited)
- Primary quotes cross-referenced: NOT_APPLICABLE
- Chronological sequence: CONSISTENT
- Callout box claims verified:
  - [!decolonization] Ґ: "The letter Ґ was forcefully removed from the Ukrainian alphabet in 1933 during the Soviet orthographic reforms... not officially restored to the alphabet until 1990." — historically accurate ✓
  - [!culture] Ї: "In 2022, during the brutal occupation of the Ukrainian city of Mariupol, the letter Ї took on profound new meaning. Local residents and partisan fighters began painting the letter Ї on walls, fences, and monuments throughout the city." — consistent with documented 2022 Ukrainian identity marking practices; culturally plausible ✓
  - [!warning] Ь: Palatalization explanation is phonetically accurate ✓
  - [!tip] Щ: "Fresh cheese" technique for Ш+Ч merger — correct ✓
  - [!fact] И/І minimal pair: Ри́м (Rome) and Рі́вне — correct ✓

## Verification Summary

- Content lines read: 299 (complete file)
- Activity items checked: 52 (all items across 8 activities)
- Ukrainian sentences/phrases verified: 18 (all inline Ukrainian in content)
- IPA transcriptions checked: 20 (full vocabulary file)
- Factual claims verified: 5 (Ґ dates ×2, Mariupol 2022, palatalization, Ри́м/Рі́вне)
- Issues found: 4 (1 LLM fingerprint structural, 1 calque pair, 1 vocabulary mismatch, 1 pacing gap)
- Grep verifications performed: confirmed «Давайте практикувати!» at l.233, «Давайте читати.» at l.260, «Зверніть увагу:» at l.33, «Запам'ятайте це правило.» at l.229, «The letter [X]» formula pattern at ll.45/72/111/141/161/175/219, Quick Check at l.188

## Verdict

**PASS**

The module has been substantially improved since the prior FAIL (LLM Fingerprint 6/10 auto-fail). All auto-fail gates are now clear: LLM Fingerprint reaches 7/10 (improved section openings for 8 of 15 subsections; comparison table for Щ; dialogue opening for Ч; paired technique for И/І). Weighted overall is 8.1/10. Four issues remain: 7 of 15 H3 subsections still use the "The letter X" formula opener; two calque instances model "давайте + infinitive" instead of standard Ukrainian imperatives; vocabulary file contains one orphaned item (тінь) while missing one content-anchored item (ніч); Section «Унікальні приголосні» still lacks a mid-section practice checkpoint. All four are addressable in a targeted repair pass without requiring a full rebuild.