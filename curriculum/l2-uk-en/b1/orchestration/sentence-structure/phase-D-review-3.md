# Рецензія: Структура речення

**Level:** B1 | **Module:** 4
**Overall Score:** 8.0/10
**Status:** FAIL
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PARTIAL PASS
- Sections: Content follows meta (10 sections) rather than plan (5 sections). All plan topics covered, but "ускладнене речення" and "вставні слова" from plan §4.4.2 requirements are absent.
- Vocabulary: 9/9 required terms covered in content; 4/6 recommended (missing: вставні слова, ускладнене речення). Vocabulary YAML file missing entirely.
- Grammar scope: CLEAN — no scope creep detected.
- Objectives: 3/3 objectives addressed (identify parts, distinguish clauses, name types).
- Activity counts: quiz has 8/10+ items (plan requires 10+); other types meet or exceed plan targets.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Well-structured with engaging throughline (architecture metaphor). Dialogues add life. Cultural hook about underlining ritual is genuinely interesting. However, metaphor density becomes distracting — 10+ distinct metaphors compete for attention rather than reinforcing a single teaching narrative. |
| 2 | Coherence | 9/10 | <7 | Logical progression: Intro → Main parts → Secondary parts → Simple/Complex → Clause hierarchy → Conjunctions → Punctuation → Analysis → Dialogues → Summary. Each section builds cleanly on the previous one. |
| 3 | Relevance | 8/10 | <7 | Directly relevant to B1 curriculum path. Essential metalanguage for upcoming grammar modules. Minor gap: plan-required "вставні слова" (parenthetical words) and "ускладнене речення" (complicated simple sentence) not covered despite being State Standard §4.4.2 items. |
| 4 | Educational | 8/10 | <7 | Step-by-step syntactic analysis walkthrough is excellent. TTT partially implemented — some examples appear before rules, but many subsections lead with definitions. Practice concentrated in activities rather than integrated throughout prose. |
| 5 | Language | 8/10 | <8 | Ukrainian is generally natural and well-written. One clear grammatical error: «Це серце ми називаємо **граматична основа**» uses nominative where instrumental is required after "називати". Minor euphony: «підмета і присудка» should be «підмета й присудка». English bridging sections are clear and appropriate. No Russianisms or calques. |
| 6 | Pedagogy | 8/10 | <7 | Good PPP structure. Cultural hooks effective. The "Візуальна шпаргалка" full parsing example is a strong pedagogical moment. Weakness: explanation-heavy with insufficient mid-lesson practice. Dialogue 2 contains a terminological inaccuracy (labels infinitive complements as "однорідні присудки"). |
| 7 | Immersion | 8/10 | <6 | Estimated ~82% Ukrainian. Two full English paragraphs in the introduction (~140 words), plus extensive parenthetical translations. Within target range (70-85%) for B1.0 bridge module. |
| 8 | Activities | 7/10 | <7 | 7 activity types provide good variety. Error-correction with "false positive" (comma NOT needed) is excellent design. However: quiz has 8 items vs plan's 10+; match-up defines додаток with only «кого? чого?» (genitive) while content correctly lists all oblique cases; vocabulary YAML file missing entirely. |
| 9 | Richness | 8/10 | <6 | Cultural embedding through underlining ritual and school nostalgia dialogues. 9 engagement boxes with varied types. Tables and visual parsing examples. However, sentence examples lean generic (студент, книга, кава, парк) — more culturally specific Ukrainian examples would elevate this. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Content well-paced for B1. English scaffolding provided. Gradual terminology introduction. «Перевірте себе» self-check at end. Warning boxes anticipate common confusions (part of speech vs sentence part, pro-drop panic). |
| 11 | LLM Fingerprint | 7/10 | <7 | Metaphor density test: FAIL. >10 distinct metaphor clusters (map, architecture, chess, engine, heart, anatomy, skeleton, painting, Morse code, detective, cement, apartment/palace). Flagged clichés used: «двигун» and «архітектура» (both explicitly listed). No structural monotony or rhetoric patterns ("це не просто") detected. Example plausibility: PASS. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL TRIGGER.** (1) «називаємо граматична основа» — instrumental case required after "називати" (should be «називаємо граматичною основою»). (2) Dialogue 2: «однорідні присудки» for "піти і купити" is terminologically incorrect — these are infinitive complements within a compound verbal predicate, not standalone predicates. (3) Match-up activity: додаток defined as «кого? чого?» (genitive only) contradicts the content's own correct listing of all oblique cases. |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 8×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 7×1.3 + 8×0.9 + 9×1.3 + 7×1.0 + 8×1.5) / 14.0
= (12.0 + 9.0 + 8.0 + 9.6 + 8.8 + 9.6 + 8.0 + 9.1 + 7.2 + 11.7 + 7.0 + 12.0) / 14.0
= 112.0 / 14.0
= 8.0/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian comparisons found
- Grammar scope: [CLEAN] — no scope creep
- Activity errors: [2 found] — додаток case questions incomplete; quiz item count below plan threshold
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Grammatical Error — Instrumental Case After "називати"
- **Location**: Section "Головні члени речення: Основа", ~line 38
- **Original**: «Це серце ми називаємо **граматична основа** (grammatical basis).»
- **Problem**: The verb "називати" in active voice requires the instrumental case for the complement. Nominative «граматична основа» is grammatically incorrect here. The correct form is «граматичною основою» (instrumental). This error is particularly damaging in a module that teaches syntactic analysis — the lesson itself contains the type of error it should help students avoid.
- **Fix**: «Це серце ми називаємо **граматичною основою** (grammatical basis).»

### Issue 2: Terminological Inaccuracy — "Однорідні присудки" in Dialogue 2
- **Location**: Dialogue 2 "Страх перед комами", ~line 442
- **Original**: «Тоді буде **просте речення** з однорідними присудками: «Я хочу піти і купити». Тоді кома не потрібна, бо герой один!»
- **Problem**: In "Я хочу піти і купити", the predicate is "хочу" (compound verbal predicate / складений дієслівний присудок). "Піти" and "купити" are infinitive complements, not standalone predicates. Calling them "однорідні присудки" is terminologically wrong — they are однорідні інфінітиви within a single compound predicate. In a module specifically teaching syntactic terminology, this imprecision undermines the lesson's authority.
- **Fix**: Replace with phrasing that avoids the incorrect label while keeping B1 simplicity.

### Issue 3: Activity Inaccuracy — Додаток Definition Restricted to Genitive
- **Location**: Activities file, match-up activity, pair for "Додаток"
- **Original**: «Другорядний член, що означає об'єкт дії (кого? чого?)»
- **Problem**: «Кого? чого?» are genitive case questions only. The content itself correctly states that додаток answers questions of ALL oblique cases (родовий, давальний, знахідний, орудний, місцевий). Listing only genitive questions in the activity contradicts the lesson and misleads learners into thinking додаток is only genitive.
- **Fix**: «Другорядний член, що означає об'єкт дії (кого? що? кому? чим?)»

### Issue 4: Excessive Metaphor Density
- **Location**: Throughout module
- **Original**: 10+ distinct metaphor clusters (architecture, chess, engine, anatomy, heart, map, skeleton, painting, detective, cement, Morse code, apartment/palace)
- **Problem**: Exceeds the 4-metaphor threshold for LLM Fingerprint detection. Two explicitly flagged clichés used: «двигун» (engine) and «архітектура» (architecture). The sheer density creates cognitive overload — each new concept gets a new metaphor rather than building on a consistent frame.
- **Fix**: Reduce 2-3 of the most forced metaphors. The architecture throughline is the strongest and should be preserved; secondary metaphors like "двигун" and "серце" can be simplified.

### Issue 5: Dialogue 2 — Unexplained Conjunction Switch
- **Location**: Dialogue 2, ~line 438
- **Original**: «Виходить: «Я хочу піти в парк, та я хочу купити морозиво».»
- **Problem**: The student's original sentence used «і» but the tutor's corrected version switches to «та» without explaining why. In a module about conjunctions, silently swapping one for another confuses the lesson about comma placement.
- **Fix**: Keep the original conjunction «і» so the fix focuses on comma placement only.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| ~38 | «називаємо **граматична основа**» | «називаємо **граматичною основою**» | Grammar (instrumental case) |
| ~38 | «підмета і присудка» | «підмета й присудка» | Euphony (і→й after vowel) |
| ~442 | «однорідними присудками» | «однорідними інфінітивами при одному присудку» | Terminology |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Concepts introduced gradually, well-paced sections
- Instructions clear? **Pass** — Terminology explained with both Ukrainian and English
- Quick wins? **Pass** — Simple examples (Студент читає) before complex analysis
- Ukrainian scary? **Pass** — English bridging in introduction, parenthetical translations throughout
- Come back tomorrow? **Pass** — Cultural hooks and dialogues create engagement

## Strengths

- **Excellent cultural integration**: The underlining ritual (lines, dashes, wavy lines) is a genuine part of Ukrainian school culture, presented with warmth and nostalgia. The school memory dialogue (Dialogue 3) reinforces this authentically.
- **Strong step-by-step analysis**: The full syntactic parsing of «Вчора мій старий друг несподівано подарував мені дуже цікаву книгу» is a pedagogically excellent walkthrough that models the exact skill students need.
- **Outstanding error-correction activity**: The last item (removing an unnecessary comma in «Вона думає, про літню відпустку») is rare and valuable — most activities only test adding commas, not recognizing false positives.
- **Effective engagement boxes**: 9 callouts across 6 different types ([!culture], [!warning], [!myth-buster], [!observe], [!tip], [!context]) provide genuine variety.
- **The "а" vs "але" distinction**: The [!context] box explaining the difference between soft comparison and strong contrast is a genuinely useful insight that most textbooks skip.

## Fix Plan to Reach 9.0/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line ~38: Change «називаємо **граматична основа**» → «називаємо **граматичною основою**» — eliminates grammatical error
2. Dialogue 2 (~line 442): Replace «однорідними присудками» → avoid incorrect terminology — eliminates factual inaccuracy
3. Match-up activity: Change «кого? чого?» → «кого? що? кому? чим?» — aligns activity with content

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Replace «Присудок — це двигун речення, який запускає події» with a non-cliché phrasing — removes one flagged LLM cliché
2. Simplify 1-2 additional forced metaphors (e.g., "азбука Морзе" comparison for dot-dash)

**Expected score after fix:** 8/10 (metaphor count still >4 but below the egregious threshold; full fix would require structural rewrite)

### Activities: 7/10 → 8/10
**What to fix:**
1. Fix додаток case questions (see above)
2. Missing vocabulary file — needs creation (cannot fix via FIND/REPLACE)
3. Quiz needs 2 additional items to meet plan's 10+ requirement (cannot add via FIND/REPLACE)

**Expected score after fix:** 8/10 (vocabulary file and quiz expansion need Phase B rebuild)

### Language: 8/10 → 9/10
**What to fix:**
1. Fix instrumental case error (same as Linguistic Accuracy fix #1)
2. Fix euphony «підмета і присудка» → «підмета й присудка»

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**Requires:** Metaphor reduction (connected to LLM Fingerprint fixes). Structural change — cannot fully fix with targeted replacements.

### Projected Overall After Fixes
```
(8×1.5 + 9×1.0 + 8×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 8×1.0 + 8×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 9×1.5) / 14.0
= (12.0 + 9.0 + 8.0 + 9.6 + 9.9 + 9.6 + 8.0 + 10.4 + 7.2 + 11.7 + 8.0 + 13.5) / 14.0
= 116.9 / 14.0
= 8.35/10
```

Note: Full 9.0 overall requires addressing vocabulary file, quiz count, and metaphor density — these require Phase B/C rebuild, not Phase D fixes.

## Verification Summary

- Content lines read: ~480
- Activity items checked: 58 (12 match-up + 10 mark-the-words + 8 quiz + 6 unjumble + 6 error-correction + 8 fill-in + 8 true-false)
- Ukrainian sentences verified: 68
- IPA transcriptions checked: 0 (none present — syntax module, not pronunciation)
- Issues found: 7 (3 critical, 2 moderate, 2 minor)

## Verdict

**FAIL**

The module fails on **Linguistic Accuracy** (8/10, auto-fail threshold <9). Three factual/grammatical errors undermine a module specifically teaching syntactic terminology: (1) incorrect nominative case after "називати" where instrumental is required, (2) mislabeling infinitive complements as "однорідні присудки", (3) restricting додаток to genitive questions in the match-up activity. The first two issues are fixable with targeted replacements; the third requires an activity edit. Secondary concern: LLM Fingerprint at 7/10 due to excessive metaphor density (>10 clusters, 2 flagged clichés) — this is structural and not fully fixable without prose rewrite.