# Рецензія: The Dative I — Pronouns

**Level:** A2 | **Module:** 1
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-15

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [Missing specific content points defined in meta.yaml]
- Vocabulary: [14/15 from plan, 1 missing ("легко")]
- Grammar scope: [Minor scope creep: Future Perfective "дам"]
- Objectives: [All covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Tone is warm, engaging, and clear. |
| 2 | Coherence | 9/10 | <7 | Logical flow from pronouns to usage to dialogues. |
| 3 | Relevance | 10/10 | <7 | Highly relevant; covers essential "survival" grammar. |
| 4 | Educational | 9/10 | <7 | Explanations of "subject-object inversion" are excellent. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian examples; colloquial "треба" usage explained well. |
| 6 | Pedagogy | 8/10 | <7 | Good progression, but missed required visual/cultural points from plan. |
| 7 | Immersion | 2/10 | <6 | **CRITICAL FAIL**. 12% is far below the 50-60% target for A2. |
| 8 | Activities | 9/10 | <7 | Well-structured, varied, and accurate. |
| 9 | Richness | 7/10 | <6 | Cultural note on hospitality is good, but plan promised more. |
| 10 | Beginner Safety | 9/10 | <7 | 5/5 on "Would I continue?". Very accessible. |
| 11 | LLM Fingerprint | 9/10 | <7 | Does not feel robotic; good "teacher voice". |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor future tense usage; otherwise accurate. |

**Weighted Overall:** (13.5 + 9 + 10 + 10.8 + 9.9 + 9.6 + 2 + 11.7 + 6.3 + 11.7 + 9 + 13.5) / 14.0 = **8.36/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Minor violation: Future Perfective "дам"]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Severe Lack of Immersion
- **Location**: Entire file
- **Original**: (English instructional text throughout)
- **Problem**: Immersion is at 12%, while the target is 50-60%. For A2, we must start transitioning instructions and headers into Ukrainian or bilingual formats.
- **Fix**: Translate section headers, activity instructions (keep English in parens if needed), and simple transition sentences into Ukrainian.

### Issue 2: Missing Plan Content (Bread & Salt)
- **Location**: Introduction
- **Original**: "Ukrainian culture is deeply rooted in hospitality."
- **Problem**: The plan (`meta.yaml`) explicitly required: "Cultural Hook: 'Bread and Salt' tradition". This is missing.
- **Fix**: Add a specific mention of the "Bread and Salt" (хліб-сіль) tradition in the cultural note or introduction.

### Issue 3: Missing Plan Content (Gift Superstition)
- **Location**: Presentation / Cultural Superstition
- **Original**: (Missing)
- **Problem**: The plan (`meta.yaml`) explicitly required: "Cultural Superstition: Giving gifts (odd numbers for living people)".
- **Fix**: Add a `[!culture]` callout or paragraph explaining that you must give an odd number of flowers to living people.

### Issue 4: Missing Required Vocabulary
- **Location**: Vocabulary / Content
- **Original**: (Missing)
- **Problem**: The word `легко` is listed as **required** in `plans/a2/the-dative-i-pronouns.yaml` and `meta.yaml` but appears nowhere in the content or activities.
- **Fix**: Add a sentence like "Мені легко це робити" or an activity item using "легко".

### Issue 5: Grammar Scope Creep
- **Location**: Activity `mark-the-words` text
- **Original**: "А потім я **дам** їй подарунок."
- **Problem**: "Дам" is the Future Perfective of "дати". Future tense is not typically assumed at the start of A2 (Module 1).
- **Fix**: Change to Present: "А зараз я **даю** їй подарунок" or construction with want: "я хочу дати".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activity `mark-the-words` | "А потім я **дам** їй подарунок." | "А потім я **дам** (future) -> **даю** (present)" | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - "Ultimate survival phrase" section]
- Ukrainian scary? [No]
- Come back tomorrow? [Yes]

Emotional beats: 4 found
- Welcome: "Welcome back! Imagine you are a guest..."
- Curiosity: "The Joy of Giving" title.
- Quick wins: "It is the ultimate survival phrase."
- Encouragement: "Mastering this structure will make you sound much more natural..."
- Progress: "You are ready to stop being just the 'doer'..."

## Strengths
- **Excellent Explanations**: The explanation of "Subject-Object Inversion" for *подобатися* ("The pizza pleases me") is crystal clear and critical for English speakers.
- **Rhythm Check**: The "chanting" tip for pronouns is a great pedagogical tool.
- **Tone**: The "Encouraging Cultural Guide" persona is perfectly maintained.

## Fix Plan to Reach 9/10

### Immersion: 2/10 → 6/10
**What to fix:**
1.  **Headers**: Change "Introduction / Вступ" to "Вступ / Introduction" (prioritize UA).
2.  **Activity Instructions**: Change "Match the Nominative..." to "Знайдіть пару (Match the Nominative...)" in `activities/the-dative-i-pronouns.yaml`.
3.  **Transitions**: Add Ukrainian introductory phrases. E.g., start "Practice" with "Нумо практикуватися!" (Let's practice!).

### Pedagogy: 8/10 → 10/10
**What to fix:**
1.  **Add Missing Cultural Content**: Insert the "Bread and Salt" reference in the Intro and the "Odd number of flowers" rule in the Presentation section (perhaps under "Usage Note").
2.  **Visual Aid**: Add a description or text block that visually maps `[Subject] -> [Verb] -> [Object]` vs `[Object/Subject] -> [Verb] -> [Dative Person]`.

### Richness: 7/10 → 9/10
**What to fix:**
1.  **Add `легко`**: Incorporate the missing vocabulary word `легко` into the "Practice" section or an activity. Example: "Мені легко вивчати українську."

### Linguistic Accuracy: 9/10 → 10/10
**What to fix:**
1.  **Remove Future Tense**: In `activities/the-dative-i-pronouns.yaml` (mark-the-words), change "дам" to "даю".

### Projected Overall After Fixes
(13.5 + 9 + 10 + 10.8 + 9.9 + 12 + 6 + 11.7 + 8.1 + 11.7 + 9 + 15) / 14.0 = **9.05/10**

## Verification Summary
- Content lines read: ~160
- Activity items checked: 36
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: 15
- Issues found: 5
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is structurally sound and pedagogically strong, but it **failed the Immersion gate** (12% vs 50% target) and **missed specific content requirements** from the plan (Bread & Salt, Gift superstitions, Vocabulary "легко"). These must be addressed to meet the A2 standard.
