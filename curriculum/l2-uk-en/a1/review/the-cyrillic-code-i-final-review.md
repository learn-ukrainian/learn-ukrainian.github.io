Good. Now I have everything I need. Let me conduct the full adversarial review.

---

## Final QA Review: the-cyrillic-code-i (A1 #1)

### Issues Found

**ISSUE 1 — FACTUAL ERROR (Critical): "Uniquely Ukrainian" claim is false**
- **File**: `the-cyrillic-code-i.md`, line 234
- **Text**: `Together with **Ґ**, these four letters are uniquely Ukrainian — they appear in no other language's alphabet.`
- **Problem**: This is linguistically incorrect. **І** appears in Belarusian and Kazakh Cyrillic. **Ї** and **Є** appear in Rusyn. The absolute claim "they appear in no other language's alphabet" is false. Only the full set of four together is distinctive.
- **Fix**: Reframe around the combination being the Ukrainian fingerprint, not individual letters being exclusive.

**ISSUE 2 — PLAN COMPLIANCE GAP (Significant): Missing "Story of Ґ"**
- **File**: `the-cyrillic-code-i.md`, Cultural Context section
- **Plan requires** (line 48-49 of plan): `The Story of Ґ: Brief mention of the 'repressed letter' (removed in 1933, restored in 1990) as a hook for Ukrainian linguistic resilience.`
- **Content**: Ґ is mentioned on line 234 but only as part of the "uniquely Ukrainian" claim. The dramatic historical arc (1933 ban, 1990 restoration) is completely absent.
- **Fix**: Add the Ґ story to the Cultural Context section alongside the factual fix.

**ISSUE 3 — ACTIVITY CATEGORY ERROR (Significant): Б in "True Friends" activity**
- **File**: `activities/the-cyrillic-code-i.yaml`, lines 17-18
- **Text**: Activity 1 "Справжні друзі: Літери та звуки" includes `Б б → b (bank)`.
- **Problem**: Б is categorized as a **New Letter** (Group 3) in the content, NOT a True Friend (Group 1). Including it in the True Friends match-up contradicts the three-group pedagogy. Б already correctly appears in Activity 2.
- **Fix**: Remove Б from Activity 1.

**ISSUE 4 — ANTI-SURZHYK INCOMPLETE (Moderate): Missing ы**
- **File**: `the-cyrillic-code-i.md`, lines 166
- **Plan/Meta require**: "Explicitly state that 'ё', 'ы', 'э' do not exist in Ukrainian." (meta line 25)
- **Content**: Only addresses ё ("e with two dots") and э ("backwards e"). The letter **ы** is not mentioned.
- **Fix**: Add ы to the Anti-Surzhyk Alert.

**ISSUE 5 — MISLEADING ACTIVITY TITLE (Minor): Quiz includes non-False-Friends**
- **File**: `activities/the-cyrillic-code-i.yaml`, line 168
- **Text**: Activity 4 titled "Фальшиві друзі: Перевірка" (False Friends: Check)
- **Problem**: The quiz includes questions about **П** (New Letter, line 156) and **І** (True Friend, line 167) — neither is a False Friend. The title is misleading.
- **Fix**: Rename to "Літери та звуки: Перевірка" (Letters and Sounds: Check).

**ISSUE 6 — DIALECT-SPECIFIC PRONUNCIATION ADVICE (Minor)**
- **File**: `the-cyrillic-code-i.md`, line 275
- **Text**: `*Incorrect*: [pɑhk] (Don't drop the R!)`
- **Problem**: "Don't drop the R" targets non-rhotic speakers (British/Australian). American/Canadian speakers don't drop R — they use the wrong *kind* of R (approximant instead of trill). The advice should be about vibration, not dropping.
- **Fix**: Reframe around trill vs flat R.

**ISSUE 7 — UNTAUGHT LETTER IN DECODING CHALLENGE (Minor)**
- **File**: `the-cyrillic-code-i.md`, line 259
- **Text**: `**Це** [t͡sɛ] (This) — *Standard starter word.*`
- **Problem**: The letter Ц is not among the 19 letters taught in this module. The decoding challenge is the culminating exercise where students apply their skills, yet it begins with an untaught letter. While the IPA is correctly provided, there's no acknowledgment that Ц is a preview.
- **Fix**: Add a brief note flagging this as a preview letter.

---

### Verification Summary

| Check | Result |
|-------|--------|
| IPA accuracy (В = [ʋ], affricates with tie bars) | PASS — [ʋ] on line 79, [t͡sɛ] on line 259 |
| Russianisms (кушати, получати, etc.) | CLEAN |
| Russian characters (ы, э, ё, ъ) | CLEAN in content |
| Gender/case agreement | PASS — мій/кіт (m), моя/мама (f), каву (acc) |
| All plan sections present | PASS (5/5) |
| Required vocabulary in prose | PASS (all 8 required + 4 recommended) |
| Objectives → self-check mapping | PASS |
| Fill-in activities produce grammatical sentences | PASS (all 8 checked) |
| Anagram scrambled arrays match answers | PASS (all 8 checked) |
| Letters in drill words use only taught 19 | PASS (cognate table verified) |
| LLM artifacts (purple prose, grandiose openers) | CLEAN — tone is genuinely warm, not syrupy |
| "Це не просто X, а Y" overuse | NONE found |
| False statistics / invented percentages | NONE found |

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
### Visual Character
Ukrainian has letters you will not find in any other Cyrillic alphabet: **І** (with its familiar vertical stroke), **Ї** (crowned with two dots), and **Є** (a graceful curve). Together with **Ґ**, these four letters are uniquely Ukrainian — they appear in no other language's alphabet. When you see them on a page, you know instantly: this is Ukrainian.

When you write **Україна** (Ukraine), the letter **ї** appears right in the heart of the word — carrying two dots like a quiet signature of the language.
---NEW---
### Visual Character
Ukrainian has a distinctive set of four letters that, taken together, set it apart from its East Slavic neighbors: **І** (with its familiar vertical stroke), **Ї** (crowned with two dots), **Є** (a graceful curve), and **Ґ** (a Г with an upturn). While individual letters like І also appear in Belarusian, the combination of all four is the fingerprint of Ukrainian. When you spot them together on a page, you know instantly: this is Ukrainian.

When you write **Україна** (Ukraine), the letter **ї** appears right in the heart of the word — carrying two dots like a quiet signature of the language.

### The Letter That Came Back
The letter **Ґ** has a dramatic story. In 1933, Soviet authorities removed it from the Ukrainian alphabet, replacing it with **Г**. For almost 60 years, **Ґ** was a "ghost letter" — used only by Ukrainians in the diaspora. When Ukraine moved toward independence, **Ґ** was officially restored in 1990. Today, it lives in words like **ґанок** (porch) and **ґудзик** (button). It is small but mighty — a symbol of linguistic survival.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
> You might see characters in some apps or textbooks that look like an "e" with two dots or a backwards "e". These letters **do not exist** in Ukrainian.
>
> If you spot them in a "Ukrainian" resource, that resource is wrong. Ukrainian has its own elegant system — **Є** for the "ye" sound and **І** for the "ee" sound. Trust the real Ukrainian alphabet.
---NEW---
> You might see characters in some apps or textbooks that look like an "e" with two dots (**ё**), a backwards "e" (**э**), or a "bl" combination (**ы**). These three letters **do not exist** in Ukrainian.
>
> If you spot them in a "Ukrainian" resource, that resource is mixing in Russian. Ukrainian has its own elegant system — **Є** for the "ye" sound, **І** for the "ee" sound, and **И** for the deep vowel. Trust the real Ukrainian alphabet.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
    *   *Incorrect*: [pɑhk] (Don't drop the R!)
---NEW---
    *   *Incorrect*: [pɑɹk] (Don't use the flat English R — make it vibrate!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
1.  **Це** [t͡sɛ] (This) — *Standard starter word.*
---NEW---
1.  **Це** [t͡sɛ] (This) — *A high-frequency starter word. The letter Ц is a sneak preview — you will learn it properly in Module 2.*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  - left: Т т
    right: t (stop)
  - left: Б б
    right: b (bank)
  title: 'Справжні друзі: Літери та звуки'
---NEW---
  - left: Т т
    right: t (stop)
  title: 'Справжні друзі: Літери та звуки'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  title: 'Фальшиві друзі: Перевірка'
  type: quiz
- instruction: Rearrange the letters to form the correct Ukrainian word.
---NEW---
  title: 'Літери та звуки: Перевірка'
  type: quiz
- instruction: Rearrange the letters to form the correct Ukrainian word.
===FIX_END===

---

### Notes (not blocking)

- **Word count**: The Green Team estimated ~1300 words against a 2000 target. The Ґ story addition (~80 words) and Anti-Surzhyk expansion (~20 words) help but don't close the gap. However, for A1 Module 1 (the literal first lesson), conciseness prevents overwhelm. The content is pedagogically dense and every paragraph earns its place. I do not recommend padding.
- **"Це" in decoding challenge**: Uses Ц (not in the 19 letters). Fixed with a preview note above. Pedagogically acceptable as a high-frequency chunk.
- **Activity О vowel**: Content describes О as "dog/off" while Activity 1 says "o (more)". Both are reasonable approximations of [ɔ] for English speakers. Not fixing.

---

===VERDICT===
APPROVE
===END_VERDICT===

All seven issues are addressed by the six fix blocks above. After fixes: the factual error is corrected, the plan compliance gap is filled (Ґ story added), the activity category error is resolved, Anti-Surzhyk covers all three Russian-only letters, the misleading title is fixed, pronunciation advice is dialect-neutral, and the untaught letter gets a preview note. No remaining blockers.