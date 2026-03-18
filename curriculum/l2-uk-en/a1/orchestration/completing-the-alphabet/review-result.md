# Рецензія: Completing the Alphabet

**Level:** A1 | **Module:** 4
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 7 H2 sections present and match plan content_outline ✅
- Vocabulary: 11/11 required from plan, 10/10 recommended, 21 total in vocab YAML
- Grammar scope: PARTIAL — verbs Дякую, Будь appear in pre-verb module (see issues)
- Objectives: All 5 objectives addressed ✅
```

**Plan Adherence Checklist (content_outline.points):**

Section "Вступ — Introduction":
- Review M1-M3 progress: COVERED — lines 5-8 list each module's contribution
- Final pieces overview: COVERED — line 10 lists Ь, apostrophe, affricates, digraphs, Ф

Section "М'який знак — The Soft Sign":
- Ь has no sound, softens consonant: COVERED — line 17
- Words сіль, день, Львів, мідь, осінь: COVERED — lines 22-26
- Pattern (end of word, before consonant, never at start/after vowel): COVERED — line 19
- Minimal pair кінь vs кін: COVERED — lines 30-32

Section "Апостроф — The Apostrophe":
- Apostrophe separates consonant from iotated vowel: COVERED — line 36
- Words м'ясо, п'ять, сім'я, м'яч, об'єкт: COVERED — lines 43-47
- Rule: after Б, П, В, М, Ф, Р before Я, Ю, Є, Ї: COVERED — line 38
- Compare with/without apostrophe: COVERED — line 40

Section "Африкати, Щ та Ф — Affricates, Щ, and Ф":
- Ц as Т+С affricate, words цукор, цибуля, -ець/-иця endings: COVERED — lines 57-60
- Ч as affricate, words час, черепаха, чай: COVERED — lines 65-68
- Щ as Ш+Ч cluster (NOT affricate), words що, ще, щастя: COVERED — lines 73-76
- Ф as rare letter in borrowings, факт, фото, voiceless partner of В: COVERED — lines 81-83

Section "Диграфи ДЖ, ДЗ — Digraphs":
- Two letters = one sound, single phonemes: COVERED — line 97
- ДЖ like English 'j', джерело, бджола, voiced partner of Ч: COVERED — lines 99-101
- ДЗ no English equivalent, voiced partner of Ц, дзвін, дзеркало: COVERED — lines 103-105
- Plan says "Uniquely Ukrainian — absent from Russian": Content says 「This sound is distinctly Ukrainian — a hallmark of authentic Ukrainian phonology.」 (line 103) — positive framing without colonial comparison ✅

Section "Весь алфавіт! — The Full Alphabet Mastered":
- Complete 33-letter alphabet listed: COVERED — line 112
- Full-alphabet reading challenge: COVERED — lines 116-117
- Survival phrases: COVERED — lines 120-126
- Celebration: COVERED — line 128

Section "Підсумок — Summary":
- Recap all concepts: COVERED — lines 133-138
- Self-check questions: COVERED — lines 141-144
- Next module preview: COVERED — line 146

**Activity Hints Check:**
- watch-and-repeat (10 items): COVERED ✅
- classify — soft sign (8 items): COVERED (8 items) — but contains error (see issues)
- image-to-letter (8 items): COVERED ✅
- quiz — apostrophe (10 items): COVERED (10 items) ✅
- classify — affricate identification (8 items): COVERED as broader "Sort by Sound Type" (8 items) ✅
- fill-in (6 items): COVERED (8 items, exceeds target) ✅
- match-up (6 items): COVERED (10 pairs, exceeds target) ✅

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Warm tutor voice, clear progression M1→M4, celebratory ending. Slight issue: survival phrases section feels like a vocabulary dump rather than integrated practice. |
| 2 | Language | 8/10 | <8 | English prose is clear and accessible. Ukrainian examples are well-glossed. Minor: 「**М'Я** means "hard **М** + **Й** + **А**"」 (line 40) uses isolated letter fragments that could confuse beginners. |
| 3 | Pedagogy | 8/10 | <7 | PPP structure solid. Good minimal pair кінь/кін. But verb forms (Дякую, Будь) introduced in pre-verb module M4 — research notes explicitly warned against this. |
| 4 | Activities | 6/10 | <7 | **AUTO-FAIL.** тінь miscategorized as "Soft Т" (it's soft Н). ДЖ/ДЗ/Apostrophe watch-and-repeat items link to wrong YouTube videos. Fill-in uses verb forms as answers. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5 — pacing comfortable, instructions clear, quick wins present, Ukrainian introduced gently, encouraging closing. |
| 6 | LLM Fingerprint | 8/10 | <7 | Example formatting is uniform across all sections (「**word** (translation) — note」 bullet pattern in 6+ sections). No rhetorical filler. Section openings are varied. |
| 7 | Linguistic Accuracy | 7/10 | <9 | **AUTO-FAIL.** тінь classification error in activities is a factual phonological mistake. Verb forms in pre-verb module violates morphological scope. Activity VESUM distractors are intentional wrong spellings (pedagogically valid, but audit-flagged). |

**Weighted Overall:**
(9×1.5 + 8×1.1 + 8×1.2 + 6×1.3 + 9×1.3 + 8×1.0 + 7×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 7.8 + 11.7 + 8.0 + 10.5) / 8.9
= 69.9 / 8.9
= **7.9/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russianisms detected
- Calques: CLEAN
- Colonial framing: CLEAN — ДЗ described positively on its own terms (line 103), no Russian comparisons
- Grammar scope: **VIOLATION** — verb forms Дякую (line 122) and imperative Будь (line 123) used in pre-verb module M4. Verbs not introduced until M15.
- Activity errors: **FAIL** — тінь miscategorized; wrong video URLs for ДЖ, ДЗ, Apostrophe
- Beginner safety: 5/5
- Factual accuracy: CLEAN for core grammar claims; apostrophe rule matches textbook (Avramenko Grade 5 §57-58)

## Critical Issues Found

### Issue 1: Activity Classification Error — тінь in Wrong Category (HIGH)
- **Location**: Activities file, line 59-61 / Activity "Which Consonant Is Softened?"
- **Original**: 「- label: "Soft Т" ... items: ["мить", "тінь"]」
- **Problem**: тінь (Т-І-Н-Ь) has the soft sign after Н, not Т. The Ь softens Н. мить (М-И-Т-Ь) correctly has soft Т, but тінь belongs in the "Soft Н" category alongside день, кінь, осінь.
- **Fix**: Move тінь from "Soft Т" to "Soft Н". Add a different word with soft Т to replace it (e.g., "сміть" or keep "Soft Т" with just "мить" and add another Soft Т word).

### Issue 2: Wrong Video URLs in Watch-and-Repeat Activity (MEDIUM)
- **Location**: Activities file, lines 33-40 / Activity "Watch and Repeat"
- **Original**: ДЖ item uses 「video: "https://www.youtube.com/watch?v=UsJkbdsY2RA"」 (this is the Ч video). ДЗ item uses video u44eCjR2Oz8 (the Ц video). Apostrophe item uses cJlal8XKBxo (the Ь video).
- **Problem**: Students clicking these videos will see lessons for completely different sounds (Ч instead of ДЖ, Ц instead of ДЗ, Ь instead of apostrophe). No dedicated videos exist in the plan for these sounds.
- **Fix**: Either use the overview video (ksXIXj7CXwc) for ДЖ, ДЗ, and Apostrophe items, or remove these items from the watch-and-repeat activity and add a note explaining these sounds lack dedicated videos.

### Issue 3: Verb Forms in Pre-Verb Module (HIGH — Morphological Scope Violation)
- **Location**: Content lines 122-123, Activities lines 263-270 / Section "Весь алфавіт! — The Full Alphabet Mastered"
- **Original**: 「**Дя́кую!** (Thank you!)」 (line 122) and 「**Будь ла́ска!** (Please!)」 (line 123)
- **Problem**: Дякую is a 1st person singular verb (VESUM: verb:imperf:pres:s:1). Будь is an imperative (VESUM: verb:imperf:impr:s:2). Module M4 is pre-verbal — verbs are introduced at M15. The research notes explicitly warn: "present them as read-aloud labels, not as communicative structures." The content introduces them as survival phrases but the fill-in activity (line 263-270) uses them as production targets, which contradicts this guidance.
- **Fix**: In the prose, add a framing sentence: "These are fixed phrases — you don't need to understand the grammar yet, just recognize and read them." In activities, restructure the fill-in items for Дякую and Будь ласка to be match-up or recognition tasks rather than production tasks.

### Issue 4: Activity VESUM Failures on Distractors (LOW — Intentional but Audit-Blocking)
- **Location**: Activities file, lines 108-158 / Activity "Apostrophe Rules"
- **Original**: Distractors include мясо, мьясо, пять, пьять, сімя, сімья, обєкт, обьєкт
- **Problem**: These are deliberately misspelled forms used as wrong answer options in the apostrophe quiz. Pedagogically this is sound — the quiz tests apostrophe knowledge. However, the VESUM audit pipeline flags them as "non-existent forms" causing ACTIVITY_VESUM_FAIL. The audit status is FAIL partly because of this.
- **Fix**: This requires a pipeline/tooling fix — the VESUM checker should exempt explicitly-marked distractors in spelling quizzes. As a content-level workaround, add a `vesum_exempt: true` flag (if schema supports it) or document in activity notes that these are intentional misspellings.

### Issue 5: Words мить and тінь Not in Prose or Vocabulary (LOW)
- **Location**: Activities file, lines 52-61 / Activity "Which Consonant Is Softened?"
- **Original**: мить and тінь appear only in the classify activity, never in the lesson prose or vocabulary YAML.
- **Problem**: Learners encounter unfamiliar words for the first time in an activity without prior exposure. At A1, this violates the PPP "Present before Practice" principle.
- **Fix**: Either add мить to the prose (e.g., in the Ь section as another example: "мить (moment) — soft Т") and add it to vocabulary YAML, OR replace мить/тінь with words already in the lesson.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act. 59-61 | тінь categorized as "Soft Т" | тінь → "Soft Н" category | Grammar error |
| 122 | 「**Дя́кую!** (Thank you!)」 — verb form | Add framing: "fixed phrase — no grammar analysis needed yet" | Scope violation |
| 123 | 「**Будь ла́ска!** (Please!)」 — imperative | Add framing: "fixed phrase — no grammar analysis needed yet" | Scope violation |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — pacing is comfortable, 3-5 new words per section
- Instructions clear? **Pass** — English explanations are clean and direct
- Quick wins? **Pass** — reading practice dialogue (lines 85-93) gives early success
- Ukrainian scary? **Pass** — all Ukrainian glossed, introduced gently
- Come back tomorrow? **Pass** — celebratory ending, clear progress marker

## Strengths
- **Excellent plan adherence**: Every content_outline point is covered with evidence
- **Strong pedagogical structure**: M1-M4 review at the top provides context and safety; the reading challenge (line 116) 「«Ту́т м'я́со, ри́ба, цу́кор і ча́й. Моя́ сім'я́ — це вели́ке ща́стя!»」 is a great full-alphabet integration exercise
- **Good decolonization**: ДЗ described as 「This sound is distinctly Ukrainian — a hallmark of authentic Ukrainian phonology.」 — positive framing, no Russian baseline
- **Clean minimal pair**: кінь vs кін (line 30-31) is textbook-quality
- **Thorough apostrophe teaching**: The 「Without the apostrophe, a combination like **М** + **Я** would mean "soft **М** + **А**". But with the apostrophe, **М'Я** means "hard **М** + **Й** + **А**"」 explanation (line 40) is precise and clear
- **Rich activity set**: 7 activities with good variety (watch-and-repeat, classify, image-to-letter, quiz, fill-in, match-up)

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Activities: 6/10 → 9/10
**What to fix:**
1. Activities line 61: Move тінь from "Soft Т" to "Soft Н" category — corrects phonological error
2. Activities lines 33-40: Replace ДЖ, ДЗ, and Apostrophe video URLs with overview video (ksXIXj7CXwc) — prevents misleading video experience
3. Activities lines 263-270: Reframe Дякую and Будь ласка fill-in items as recognition (match-up) rather than production — aligns with research guidance

**Expected score after fix:** 9/10

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Fix тінь classification (same as Activities fix #1 above)
2. Content lines 119-123: Add framing sentence before survival phrases: "These are fixed phrases you'll learn as whole units — don't worry about the grammar yet, just practice reading them aloud."
3. Resolve VESUM distractor issue (tooling fix or schema exemption)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 76.8 / 8.9 = 8.6/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not seminar track — N/A)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Grammar rule verification: Apostrophe rule (line 38) confirmed against Avramenko Grade 5 §57-58 (губний + Р before iotated vowels). Щ = Ш+Ч confirmed. кін verified in VESUM as noun:inanim:m.

## Verification Summary

- Content lines read: 146
- Activity items checked: 7 activities, all items individually reviewed
- Ukrainian sentences verified: 21 (all vocabulary + key examples)
- Citations in bank: 15
- Issues found: 5 (1 HIGH classification error, 1 MEDIUM video mismatch, 1 HIGH scope violation, 1 LOW audit-blocking distractors, 1 LOW vocabulary gap)

## Verdict

**FAIL**

Blocking issues: (1) тінь miscategorized as "Soft Т" — this is a phonological error in an activity that teaches soft sign placement; students would learn the wrong classification. (2) Wrong video URLs in watch-and-repeat send students to unrelated sound lessons. (3) Verb forms in pre-verb module without adequate framing violate morphological scope gates. All three are fixable in one pass.