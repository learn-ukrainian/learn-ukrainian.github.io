# Рецензія: Reflexive Verbs (-ся)

**Level:** A1 | **Module:** 17
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: 4/4 H2 sections present ✅
- Vocabulary: 8/8 required present in prose ✅, 4/4 recommended present ✅
- Grammar scope: CLEAN — no scope creep
- Objectives: 4/4 addressed ✅
- Past tense forms: MISSING (plan point for Презентація section)
- Yoga Instructor persona: NOT INTEGRATED
```

### Plan Adherence Checklist (content_outline.points)

**Section "Вступ: Дзеркало дії (Introduction: Mirroring Action)":**
- ✅ COVERED: Suffix -ся turns action back onto subject — mirror analogy used throughout (line 5)
- ✅ COVERED: -ся is short for 'себе' — bound morpheme explanation (line 9)
- ✅ COVERED: Cultural Hook: Вибачаюсь vs Вибачте (lines 11-15)
- ✅ COVERED: Learner error: "Myself" Redundancy (lines 17-27)

**Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)":**
- ✅ COVERED: Phonetic Rule: -ся after consonants, -сь after vowels (lines 36-42)
- ✅ COVERED: State Standard §4.2.4.1 — дивитися conjugation (lines 44-57)
- ❌ MISSING: Past tense forms (сміявся, сміялася, сміялося, сміялися) — plan explicitly requires mentioning these "to show the suffix persists across tenses." Section "Morphological Note: The Mirror Persists" (lines 59-68) only shows additional present tense forms of сміятися, not past tense. This is a direct plan violation.
- ✅ COVERED: Shibboleth Pronunciation of -ться (lines 70-81)

**Section "Семантичні групи (Semantic Groups)":**
- ✅ COVERED: Type 1 — True Reflexive with daily routine verbs (lines 88-101)
- ✅ COVERED: Type 2 — Reciprocal (lines 103-112)
- ✅ COVERED: Type 3 — Lexicalized with сміятися з/над nuance (lines 114-126)
- ✅ COVERED: Agent Confusion: називати vs називатися (lines 127-136)

**Section "Практика та застосування (Practice and Application)":**
- ✅ COVERED: Transitive ↔ Reflexive Contrast drill (lines 142-154)
- ✅ COVERED: Daily Routine Integration (lines 156-165)
- ✅ COVERED: Conjugation Drills for дивитися and вчитися (lines 167-183)
- ✅ COVERED: Social Interaction dialogues (lines 185-196)

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good lesson arc but missing persona integration and only 1 engagement box. Warm opening and closing but the middle sections are heavy on lists without interstitial encouragement. |
| 2 | Language | 7/10 | <8 | Colonial framing in [!tip] box (line 76): 「In Russian, a similar spelling is pronounced as a hard, short sound.」 Ukrainian pronunciation defined by contrast with Russian in a non-decolonization context. Also, incomplete transitive sentences at lines 147/153. |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP structure. Mirror analogy is excellent. Missing past tense forms (plan point). "bound morpheme" (line 9) is overly technical for A1 — a nervous beginner doesn't need linguistics jargon. |
| 4 | Activities | 6/10 | <7 | Activity 2 has fundamental design flaw: 3rd-person stems can't take suffix-only answers (сміє+ся≠сміється, вмиває+ся≠вмивається). "шся" answer is not a valid suffix choice. 3 broken items. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Content is approachable and well-paced, but "bound morpheme" in line 9 is intimidating. No explicit "don't worry" moments. |
| 6 | LLM Fingerprint | 8/10 | <7 | Structural monotony: sections 3 sub-headers all follow "Type N: Name (Description)" pattern. Example presentation is varied (bullet lists, dialogues, conjugation tables). No generic AI clichés detected. |
| 7 | Linguistic Accuracy | 8/10 | <9 | Activity 2 items produce invalid word forms. Incomplete sentences 「**Я мию.**」(line 147) and 「**Мама одягає.**」(line 153) are unnatural without objects. VESUM verification: core vocabulary all valid. |

**Weighted Overall:** (8×1.5 + 7×1.1 + 8×1.2 + 6×1.3 + 8×1.3 + 8×1.0 + 8×1.5) / 8.9 = (12 + 7.7 + 9.6 + 7.8 + 10.4 + 8.0 + 12.0) / 8.9 = 67.5 / 8.9 = **7.6/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [CLEAN]
- Colonial framing: [FOUND] Line 76 — Russian pronunciation comparison in [!tip] box (not a [!myth-buster] or [!decolonization] block)
- Grammar scope: [CLEAN] — no future grammar introduced prematurely
- Activity errors: [FOUND] Activity 2 has 3 broken items (lines 154-169 in YAML)
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — grammar rules are correct, cultural hook about Вибачаюсь is well-documented

## Critical Issues Found

### Issue 1: Activity Design Flaw — Broken Suffix Fill-In Items (HIGH)
- **Location**: Activities YAML, Activity 2, items at lines 154-169
- **Original (line 154)**: `"Він сміє___."` with answer `"ся"` and (line 162): `"Ти сміє___."` with answer `"шся"` and (line 166): `"Вона вмиває___."` with answer `"ся"`
- **Problem**: Activity 2 is titled "Choose the Correct Suffix: -ся or -сь" but three items don't work with this paradigm:
  - "Він сміє" + "ся" = "смієся" — NOT a valid form. Correct is "сміється" (with -ть-).
  - "Вона вмиває" + "ся" = "вмиваєся" — NOT a valid form. Correct is "вмивається" (with -ть-).
  - "Ти сміє" + "шся" = "смієшся" — orthographically works, but "шся" is NOT a suffix choice between -ся/-сь. The "ш" is a conjugation ending, not part of the reflexive suffix. This answer is categorically wrong for an activity about suffix selection.
- **Fix**: Remove these 3 items entirely and replace with stems that cleanly take -ся or -сь (e.g., "Ми сміємо___." → "сь", "Ти одягаєш___." → "ся", "Вони займають___." → "ся").

### Issue 2: Colonial Framing in [!tip] Box (HIGH)
- **Location**: Line 76, Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)"
- **Original**: 「In Russian, a similar spelling is pronounced as a hard, short sound. By mastering this long, soft sound, you are embracing the true melody of Ukrainian and distinguishing your pronunciation.」
- **Problem**: This defines Ukrainian pronunciation through contrast with Russian. The block is a [!tip], not a [!myth-buster] or [!decolonization] block. Per review protocol, this is colonial framing — Ukrainian features must be presented on their own terms.
- **Fix**: Remove the Russian comparison entirely. Present the [ц'а] pronunciation as an intrinsic feature of Ukrainian: "This long, soft sound is a hallmark of authentic Ukrainian pronunciation. Practice making it soft and drawn out — it's one of the beautiful sounds that defines the melody of Ukrainian."

### Issue 3: Missing Plan Point — Past Tense Forms (MEDIUM)
- **Location**: Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)", subsection "Morphological Note" (lines 59-68)
- **Problem**: Plan explicitly requires: "Mention past tense forms per Standard examples (сміявся, сміялася, сміялося, сміялися) to show the suffix persists across tenses." The content only shows present tense forms of сміятися. This is a direct plan violation.
- **Fix**: Add a brief note after line 67 showing past tense forms in a small table or list: сміявся, сміялася, сміялося, сміялися — with a note that past tense will be taught at M36, this is just pattern recognition.

### Issue 4: Incomplete Transitive Sentences (MEDIUM)
- **Location**: Lines 147, 153 in Section "Практика та застосування (Practice and Application)"
- **Original**: 「**Я мию.** (I wash something.)」 and 「**Мама одягає.** (Mom dresses someone.)」
- **Problem**: Transitive verbs мити and одягати require objects in Ukrainian. "Я мию." and "Мама одягає." sound truncated and unnatural. The plan itself says "мити тарілку" — the object was in the plan but dropped in content.
- **Fix**: Change to "**Я мию тарілку.** (I wash a plate.)" and "**Мама одягає дитину.** (Mom dresses the child.)" — consistent with the plan's "мити тарілку" phrasing.

### Issue 5: No Yoga Instructor Persona Integration (MEDIUM)
- **Location**: Entire module — Section "Практика та застосування (Practice and Application)" is the most natural fit
- **Problem**: Plan specifies `persona: { voice: Patient Supportive Tutor, role: Yoga Instructor }`. Research notes explicitly suggest "A yoga class also works well — займатися йогою, розминатися (warm up), розслаблятися (relax)." Zero yoga references appear in the module. The persona is completely absent.
- **Fix**: Add a yoga-themed example cluster in Section "Практика та застосування (Practice and Application)", e.g., a short dialogue at a yoga class using займатися йогою, розминатися, розслаблятися.

### Issue 6: Low Immersion & Missing Engagement Elements (LOW-MEDIUM)
- **Location**: Entire module
- **Problem**: Immersion at 12.3% is below the 15-25% audit target and well below the 25-45% band for A1 modules 11-20. Only 1 engagement box ([!tip] at line 70) vs. 2 required. Zero video embeds vs. 2 richness target. Research notes found a relevant YouTube video (ULP Ep 109) that is not embedded.
- **Fix**: Add at least 1 more engagement callout (e.g., a [!did-you-know] about Ukrainian morning routines using the proverb from research notes: "Хто рано встає, тому Бог дає"). Embed the ULP video. Both will also boost immersion.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 147 | 「**Я мию.** (I wash something.)」 | 「**Я мию тарілку.** (I wash a plate.)」 | Grammar — missing object |
| 153 | 「**Мама одягає.** (Mom dresses someone.)」 | 「**Мама одягає дитину.** (Mom dresses the child.)」 | Grammar — missing object |
| 174 | 「**Вона вчиться грати.** (She studies playing.)」 | 「**Вона вчиться грати на гітарі.** (She is learning to play guitar.)」 | Naturalness — incomplete thought |
| Act.154 | "Він сміє___." answer: "ся" | Remove item — "смієся" is invalid | Activity error |
| Act.162 | "Ти сміє___." answer: "шся" | Replace with "Ти одягаєш___." answer: "ся" | Activity error |
| Act.166 | "Вона вмиває___." answer: "ся" | Replace with "Вони займають___." answer: "ся" | Activity error |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, new concepts introduced gradually
- Instructions clear? **Pass** — always clear what's being taught
- Quick wins? **Pass** — early mirror analogy gives conceptual "aha" moment, conjugation tables are manageable
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations
- Come back tomorrow? **Borderline Pass** — "bound morpheme" (line 9) is intimidating jargon for A1; no explicit "don't worry" encouragement moments in the middle sections; closing is warm but the journey there could be warmer

## Strengths
- **Mirror analogy** is genuinely excellent pedagogy — it's intuitive, memorable, and used consistently throughout the module as a unifying thread
- **Вибачаюсь vs Вибачте cultural hook** is engaging, culturally accurate, and demonstrates -ся semantics in a way that sticks
- **Transitive ↔ Reflexive contrast** in Section "Практика та застосування (Practice and Application)" effectively reinforces the core concept
- **Activity 1 (Conjugation fill-in)** is well-designed with 25 items covering all persons across multiple verbs — excellent drill variety
- **Activity 3 (Match-up)** covers 12 pairs including all three semantic types — comprehensive
- **Semantic grouping** in Section "Семантичні групи (Semantic Groups)" is pedagogically sound — true reflexive, reciprocal, lexicalized is the standard Ukrainian textbook taxonomy

## Fix Plan to Reach 9.0/10

### Language: 7/10 → 9/10
**What to fix:**
1. Line 76: Remove Russian comparison from [!tip] box — present [ц'а] as intrinsic Ukrainian feature
2. Line 147: Change 「**Я мию.**」 → 「**Я мию тарілку.**」
3. Line 153: Change 「**Мама одягає.**」 → 「**Мама одягає дитину.**」

**Expected score after fix:** 9/10

### Activities: 6/10 → 9/10
**What to fix:**
1. Remove/replace 3 broken items in Activity 2 (lines 154, 162-165, 166-169 in YAML): replace with stems that cleanly take -ся or -сь
2. Remove "шся" as an answer option entirely — it's not a suffix

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Fix Activity 2 broken items (same as above)
2. Line 147, 153: Add objects to transitive sentences
3. Line 174: Expand 「**Вона вчиться грати.**」 to include instrument

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add past tense forms (сміявся, сміялася, сміялося, сміялися) to Section "Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)" subsection "Morphological Note"
2. Replace "bound morpheme" with simpler phrasing in Section "Вступ: Дзеркало дії (Introduction: Mirroring Action)"
3. Integrate yoga instructor persona into Section "Практика та застосування (Practice and Application)"

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 1+ engagement callout (e.g., [!did-you-know] with morning routine proverb from research)
2. Embed ULP Ep 109 video
3. Add 1-2 encouragement beats in middle sections

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9 = 77.8 / 8.9 = **8.7/10**

## Verification Summary

- Content lines read: 206
- Activity items checked: 68 (25 + 15 + 12 + 6 across 4 activities, all items individually inspected)
- Ukrainian sentences verified: 32
- Citations in bank: 19
- Issues found: 6

## Verdict

**FAIL**

Three blocking issues: (1) Activity 2 has 3 broken items that produce invalid Ukrainian word forms — students would practice non-existent forms; (2) Colonial framing in [!tip] box defines Ukrainian pronunciation via Russian comparison; (3) Missing plan-required past tense forms. Fix these before shipping.