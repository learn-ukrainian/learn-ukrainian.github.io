# Рецензія: At the Café

**Level:** A1 | **Module:** 35
**Overall Score:** 9.2/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required used, 4/4 recommended used]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent flow, cultural context (Lviv, Kulchytsky) adds depth. |
| 2 | Coherence | 9/10 | <7 | Clear progression, but gender agreement error disrupts logic. |
| 3 | Relevance | 10/10 | <7 | Highly practical "survival" content. |
| 4 | Educational | 9/10 | <7 | Clear explanations of "Я буду" and polite phrases. |
| 5 | Language | 7/10 | <8 | **FAIL**: Gender agreement error in Presentation table; missing stress in IPA. |
| 6 | Pedagogy | 10/10 | <7 | Solid PPP structure; accurate "fixed phrase" handling for Instr/Gen cases. |
| 7 | Immersion | 9/10 | <6 | Narrative is engaging and appropriate for A1. |
| 8 | Activities | 10/10 | <7 | 8 activities, varied types, grammatically correct items. |
| 9 | Richness | 10/10 | <6 | Myth-buster and History-bite add great value. |
| 10 | Beginner Safety | 10/10 | <7 | Encouraging tone, clear instructions. |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural phrasing, avoiding robotic repetition. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **FAIL**: One major grammar error (gender) and one IPA error. |

**Weighted Overall:** 9.2/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Gender Agreement Mismatch
- **Location**: Section "Presentation", Table "Ordering Drinks", Row "Гарячий чи холодний?"
- **Original**: "| **Гарячий чи холодний?** | /ɦɑˈrʲɑt͡ʃɪj t͡ʃɪ xɔˈlɔdnɪj/ | Hot or cold? |"
- **Problem**: The previous row asks "Яку каву ви хочете?" (*Which coffee [fem] do you want?*). The follow-up question uses masculine adjectives (*Гарячий чи холодний?*) to refer to the feminine noun *кава*. This confuses learners about gender agreement rules just established.
- **Fix**: Change to "| **Гаряча чи холодна?** | /ɦɑˈrʲɑt͡ʃɑ t͡ʃɪ xɔˈlɔdnɑ/ | Hot or cold? |"

### Issue 2: IPA Stress Missing
- **Location**: Section "Presentation", Table "Ordering Drinks", Row "Кава і молоко."
- **Original**: "| **Кава і молоко.** | /kɑvɑ i mɔlɔkɔ/ | Coffee and milk. |"
- **Problem**: The IPA transcription lacks stress marks, which are mandatory for learners.
- **Fix**: Change IPA to `/ˈkɑvɑ i mɔlɔˈkɔ/`

### Issue 3: Incorrect POS Tag
- **Location**: `vocabulary.yaml`, Item "Кульчицький"
- **Original**: `pos: adj`
- **Problem**: While surnames ending in -ський decline like adjectives, semantically this is a Proper Noun (Name). Labeling it `adj` in a vocabulary list is confusing.
- **Fix**: Change to `pos: proper noun` (or `noun`).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Table | **Гарячий чи холодний?** | **Гаряча чи холодна?** | Grammar (Gender Agreement) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 4 found
- Welcome: Section "Warm-up"
- Curiosity: Myth-buster (Kulchytsky)
- Quick wins: "Tip" about fixed phrases
- Encouragement: Summary ("Great job!")

## Strengths
- **Cultural Depth**: The inclusion of Yuriy Kulchytsky and the "Lviv Coffee Mine" legend elevates this from a generic language lesson to a culturally immersive experience.
- **Practicality**: Teaching "Я буду..." is the perfect functional equivalent for A1, avoiding complex verb conjugations while enabling immediate communication.
- **Activity Design**: The activities are robust, covering multiple skills (matching, unjumbling, true/false) with no logical errors found.

## Fix Plan to Reach 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Section "Presentation", Table 1: Change "**Гарячий чи холодний?**" to "**Гаряча чи холодна?**" (and update IPA to `/ɦɑˈrʲɑt͡ʃɑ t͡ʃɪ xɔˈlɔdnɑ/`) — Corrects the gender agreement error relative to "каву".
2. Section "Presentation", Table 1: Change IPA for "**Кава і молоко.**" to `/ˈkɑvɑ i mɔlɔˈkɔ/` — Adds mandatory stress marks.

### Linguistic Accuracy: 8/10 → 10/10
**What to fix:**
1. Apply the fixes above.
2. `vocabulary.yaml`: Change `pos` for **Кульчицький** to `proper noun`.

**Expected score after fix:** 10/10

### Projected Overall After Fixes

```
New Overall: ~9.5/10
```

## Verification Summary

- Content lines read: ~140
- Activity items checked: ~65
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: ~15
- Issues found: 3
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is excellent in content, culture, and pedagogy, but fails on **Language** (<8) due to a direct gender agreement error in the presentation table ("Гарячий" referring to "кава") and missing IPA stress. These are objective errors that must be fixed before approval.