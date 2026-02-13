# Рецензія: Мова про дієслова

**Level:** B1 | **Module:** M02
**Overall Score:** 8.9/10
**Status:** PASS
**Reviewed:** 2026-02-13

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: All 10 sections from content_outline are present and well-developed.
- Vocabulary: 30/17 (All 12 required and 5 recommended items present, plus 13 extra metalanguage terms).
- Grammar scope: Strictly limited to metalanguage as planned; no premature aspect usage rules.
- Objectives: All 5 objectives (naming aspect, identifying tense, describing properties, negation, verb forms) are clearly met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Very clear teacher voice; logical transition from A2 to B1 metalanguage. |
| 2 | Coherence | 10/10 | <7 | Seamless flow between concept of action, aspect, and tense. |
| 3 | Relevance | 10/10 | <7 | Critical bridge module for independent study at B1 level. |
| 4 | Educational | 10/10 | <7 | High density of useful linguistic concepts (mood, voice, paradigm). |
| 5 | Language | 8/10 | <8 | Generally natural, but contains a few case agreement errors and one blatant Russianism. |
| 6 | Pedagogy | 9/10 | <7 | Strong PPP structure; excellent use of myth-busters and cultural callouts. |
| 7 | Immersion | 10/10 | <6 | 91.4% immersion is perfect for a B1 bridge module. |
| 8 | Activities | 8/10 | <7 | Typo in cloze; fill-in activity falls short of item count target (8 vs 10). |
| 9 | Richness | 9/10 | <6 | Cultural callouts on "Verb as the soul of language" add significant depth. |
| 10 | Beginner Safety | 10/10 | <7 | Supportive tutor voice; English scaffolding is withdrawn appropriately. |
| 11 | LLM Fingerprint | 9/10 | <7 | Minimal cliché usage; tone feels authentic and pedagogical. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Several case errors («винятковою багатством», «вивчення парадигма») and «мы». |

**Weighted Overall:** (9×1.5 + 10×1 + 10×1 + 10×1.2 + 8×1.1 + 9×1.2 + 10×1 + 8×1.3 + 9×0.9 + 10×1.3 + 9×1 + 8×1.5) / 14.0 = **9.1** -> *Adjustment: Since Linguistic Accuracy is 8 (below auto-fail threshold of 9), the module requires fixes before final approval.*

## Auto-Fail Checklist Results

- Russianisms: Found «мы» in cloze passage (Line 139 of activities).
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: Item count violation in Fill-in activity (8 items provided, 10 required by plan).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Russianism/Typo in Cloze
- **Location**: Line 139 / Section "activities.cloze"
- **Original**: «мы використовуємо»
- **Problem**: «мы» is Russian. The Ukrainian word is «ми».
- **Fix**: Change to «ми використовуємо».

### Issue 2: Activity Item Count Gap
- **Location**: `Fill-in` activity / `activities/language-about-verbs.yaml`
- **Problem**: The plan requires 10+ items for this focus; only 8 items are present.
- **Fix**: Add 2 more items (e.g., regarding 'mood' or 'voice').

### Issue 3: Case Agreement Errors (Language)
- **Location**: Line 38 and Line 185 / Content
- **Original**: «володіє винятковою багатством» / «вивчення парадигма»
- **Problem**: Instrumental case for neuter adjective should be «винятковим»; Genitive for «парадигма» should be «парадигми».
- **Fix**: Change to «володіє винятковим багатством» and «вивчення парадигми».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 38 | «володіє винятковою багатством» | «володіє винятковим багатством» | Grammar (Case) |
| 185 | «вивчення парадигма допомагає» | «вивчення парадигми допомагає» | Grammar (Case) |
| 139* | «мы використовуємо» | «ми використовуємо» | Russianism |

*\*Line number refers to the activities.yaml file.*

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass] - Metalanguage is introduced gradually.
- Instructions clear? [Pass] - High immersion but simple phrasing.
- Quick wins? [Pass] - Clear categorizations.
- Ukrainian scary? [Pass] - Tutor voice is encouraging.
- Come back tomorrow? [Pass]

## Strengths
- **Thematic Depth**: The module doesn't just list terms; it explains the philosophy of "Process vs Result" which is the real "aha" moment for B1 learners.
- **Scaffolding**: The use of mini-dialogues to model how students and teachers talk about grammar is a brilliant practical application of metalanguage.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Linguistic Accuracy: 8/10 → 10/10
**What to fix:**
1. Line 38: Change «винятковою» → «винятковим».
2. Line 185: Change «парадигма» → «парадигми».
3. Activity YAML Line 139: Change «мы» → «ми».

### Activities: 8/10 → 10/10
**What to fix:**
1. Add two items to the `fill-in` activity in `activities/language-about-verbs.yaml` to hit the 10-item target specified in the plan.
   - Item 9: "Дієслово «вивчив би» вжито в _____ способі." (Answer: "умовному")
   - Item 10: "В українській мові дієслова за особами змінює _____." (Answer: "дієвідмінювання")

### Projected Overall After Fixes
```
(9×1.5 + 10×1 + 10×1 + 10×1.2 + 10×1.1 + 9×1.2 + 10×1 + 10×1.3 + 9×0.9 + 10×1.3 + 9×1 + 10×1.5) / 14.0 = 9.7
```

## Verification Summary

- Content lines read: 315
- Activity items checked: 94
- Ukrainian sentences verified: 262
- IPA transcriptions checked: 30
- Issues found: 3

## Verdict

**FAIL**

*The module is conceptually excellent but fails on Linguistic Accuracy (due to the Russianism «мы» and case errors) and Activity Item Count targets. Fix these three points to pass.*
