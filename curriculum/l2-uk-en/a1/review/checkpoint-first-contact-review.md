<!-- content-hash: 3ea405f2b671 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Language Quality | 7/10 | Colonial framing in `[!cultural]` block (line 140) defines Ukrainian names by contrast with Russian. Ukrainian grammar and vocabulary otherwise correct. English is warm and accessible. |
| 2 | Lesson Quality | 8/10 | Warm, encouraging tutor voice throughout. Good scenario in integration task. Structural monotony (5/5 skills follow identical Модель → Практика → Самоперевірка template) reduces organic feel. |
| 3 | Richness | 8/10 | Good cultural hooks (Lviv coffee, Kulchytsky, syrnyk dialogue), varied callout boxes (tip, warning, cultural, context, myth-buster, note). Could benefit from more named cultural references. |
| 4 | Factual Accuracy | 8/10 | Kulchytsky claim in `[!culture]` block (line 315) diverges from research notes — content says "teaching Viennese society to drink coffee with milk and sugar" while research says "opening one of the first coffee houses." Self-check tests untaught concept ("ніч" gender, line 401). |
| 5 | LLM Fingerprint | 7/10 | All 5 skill sections follow identical `### Модель` → `### Практика` → `### Самоперевірка` structure. No section deviates. This is rigid templating, not organic tutoring flow. |
| 6 | Humanity & Warmth | 8/10 | Has "Don't worry" (line 29), "It's normal to forget" (line 28), "Congratulations" (lines 14, 408), "That is success!" (line 383). Missing "Привіт!" opening and "You can now..." explicit validation. |
| 7 | Activity Quality | 7/10 | 8 activities with 96 items — good quantity and variety. BUT "Question Words" match-up includes 6 untaught items (Який?, Як?, Скільки?, Звідки?, Чий?, Чи?) that never appear in the lesson content — testing before teaching. |
| 8 | Immersion | 9/10 | 20.7% Ukrainian, within A1.1 target of 20-40%. English scaffolding present throughout. Ukrainian used appropriately for examples and practice. |
| 9 | Plan Compliance | 7/10 | Missing required phrase "Дайте, будь ласка..." from plan (§4.3.1 of state standard). Missing "піти на каву" social ritual from integration section. TTT pedagogy not explicitly structured (no pre-test → teach → re-test flow). |

---

## Critical Issues Found

### Issue 1: Colonial Framing — Ukrainian Names Defined by Russian Contrast (CRITICAL)

**Location:** Section «Визначення роду», line 140

**Cited text (verified):** «Notice that Ukrainian male names often end in **-а** or **-о** (Микола, Микита, Петро, Павло). Russian equivalents often end in consonants (Nikolay, Nikita, Petr, Pavel). This is a distinct feature of the Ukrainian language.»

**Problem:** This `[!cultural]` block defines a Ukrainian naming feature by contrasting it with Russian as the baseline ("Russian equivalents often end in consonants"). This is colonial framing — it positions Russian as the norm from which Ukrainian diverges. The Ukrainian naming convention should be presented on its own terms.

**Required fix:** Rewrite to present Ukrainian names independently. For example: "Many common Ukrainian male names end in -а or -о: Микола, Микита, Петро, Павло. Don't let the ending fool you — these are classic male names. If you meet a Микола, that's a man!" Remove all Russian comparisons.

---

### Issue 2: Testing Untaught Content — "ніч" Gender in Self-Check

**Location:** Section «Інтеграційне завдання» (Підсумок), line 401

**Cited text (verified):** «Determine the gender of the words: **вікно**, **ніч**, **Андрій**, **кафе**, **піца**.»

**Problem:** The gender rules taught in section «Визначення роду» cover only: -а/-я → Feminine, consonant → Masculine, -о/-е → Neuter. The word "ніч" (night) is feminine (3rd declension, soft-sign ending), but the lesson provides no rule for soft-sign nouns. A student following the taught algorithm would see a consonant ending and classify it as masculine — and be wrong. This is testing before teaching.

**Required fix:** Replace "ніч" with a word that fits the taught gender rules (e.g., "вулиця", "музика", or "вода"). Alternatively, if "ніч" is pedagogically important, add a brief note about soft-sign feminine nouns in the gender section.

---

### Issue 3: Activity Scope Creep — Untaught Question Words in Match-Up

**Location:** Activities file, "Question Words" match-up, lines 390-403

**Untaught items in activity:** Який? (line 390), Як? (line 394), Скільки? (line 396), Чи? (line 398), Звідки? (line 400), Чий? (line 402)

**Problem:** Section «Питальні речення» teaches exactly 6 question words: Хто?, Що?, Де?, Куди?, Коли?, Чому?. The activity includes 6 additional question words (Який?, Як?, Скільки?, Звідки?, Чий?, Чи?) that are never introduced, explained, or exemplified in the lesson. Students encounter them for the first time in the test. This violates the checkpoint's purpose — it should assess taught material, not introduce new material during assessment.

**Required fix:** Remove the 6 untaught items from the match-up activity, keeping only the 6 question words actually taught in the lesson (Хто?, Що?, Де?, Куди?, Коли?, Чому?).

---

### Issue 4: Self-Check Asks About Untaught "Because" (бо/тому що)

**Location:** Section «Питальні речення», line 288

**Cited text (verified):** «How do you ask "Why?" and answer "Because"?»

**Problem:** The word "because" (бо / тому що) is never taught anywhere in the module. The "Чому?" section at lines 253-255 only shows: «Чому ти тут?» with the answer «Я тут, я турист.» — which doesn't use "because" at all. The self-check question asks students to produce a word they've never seen.

**Required fix:** Either (a) add "бо" / "тому що" to the Чому? examples in section «Питальні речення» (e.g., «Чому ти тут? — Бо я турист.»), or (b) rephrase the self-check question to match what was actually taught (e.g., "How do you ask about the reason for something?").

---

### Issue 5: Missing Required Plan Content — "Дайте, будь ласка..."

**Location:** Section «Замовлення їжі»

**Problem:** The plan explicitly requires the phrase "Дайте, будь ласка..." as an ordering phrase (sourced from §4.3.1 of the State Standard: «спонукальне речення для вираження прохання: Дайте, будь ласка, два квитки»). The content teaches only "Можна...?" and "Я буду..." for ordering. The imperative polite request form is absent.

**Required fix:** Add "Дайте, будь ласка..." as a third ordering phrase in section «Замовлення їжі», under the «Модель: Важливі фрази» subsection. Example: «Дайте, будь ласка, каву.» — Please give me a coffee.

---

### Issue 6: Kulchytsky Claim Diverges from Research Notes

**Location:** Section «Замовлення їжі», line 315

**Cited text (verified):** «He is credited with teaching Viennese society to drink coffee with milk and sugar.»

**Research notes say:** «credited with opening one of the first coffee houses in Vienna (The Blue Bottle) in 1683, originating the Viennese coffee culture»

**Problem:** The content's specific claim about "teaching Viennese society to drink coffee with milk and sugar" is not supported by the research notes, which mention opening a coffee house and popularizing coffee culture generally. The "milk and sugar" detail appears to be embellishment.

**Required fix:** Align the claim with the research notes. Replace with something like: "He is credited with opening one of the first coffee houses in Vienna, helping popularize coffee culture across Europe."

---

## Factual Verification

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Feminine = -а/-я | Line 95-99 | Correct |
| Masculine = consonant | Line 101-105 | Correct (simplified but appropriate for A1) |
| Neuter = -о/-е | Line 107-111 | Correct |
| -й = masculine | Line 105 | Correct |
| тато = masculine exception | Lines 126-130 | Correct |
| First conjugation -ати template | Lines 170-175 | Correct (all forms verified) |
| Second conjugation -ити template | Lines 190-195 | Correct (all forms verified) |
| писати → пишу (с→ш) | Lines 214-217 | Correct |
| "Не" negation position | Lines 278-281 | Correct |

### Callout Box Verification

| Callout | Location | Verdict |
|---------|----------|---------|
| [!tip] "It's normal to forget!" | Lines 27-29 | Factually sound |
| [!warning] "Careful: И vs І" | Lines 52-60 | Phonetically correct; І=[i], И=[ɪ] |
| [!note] "Why does this matter?" (gender-adjective agreement) | Lines 113-119 | Correct: «Добра кава», «Добрий чай» |
| [!cultural] "Mykola vs Nikolay" | Lines 138-140 | Colonial framing issue (see Critical Issue 1), but factual content about Ukrainian names is correct |
| [!warning] "Кава vs Кафе" | Lines 150-154 | Correct: кава = F, кафе = N |
| [!warning] "Common Mistake: Mixing Groups" | Lines 197-203 | Correct: «Вони говорять» not *говорють |
| [!context] "Де vs Куди" | Lines 258-261 | Correct: static vs. dynamic distinction |
| [!culture] "Lviv Coffee" | Lines 313-315 | Diverges from research (see Issue 6) |
| [!myth-buster] "Should you tip?" | Lines 333-335 | Plausible cultural advice, 10% is standard guidance |
| [!note] "Dialogue Analysis" | Lines 373-381 | Correct: verbs identified with correct groups |

### IPA Verification

| Word | Given IPA | Verdict |
|------|-----------|---------|
| Можна | (line 301) | Correct |
| Я буду | (line 305) | Correct |
| Смачного | (line 325) | Correct |
| Суп | [sup] (line 50) | Acceptable simplified IPA for A1 |

---

## Structural & Pedagogical Analysis

### Plan Compliance Detail

| Plan Section | Content Section | Status |
|--------------|-----------------|--------|
| Огляд та мета | «Огляд та мета» | Present but missing "піти на каву" social ritual |
| Навичка 1: Читання кирилиці | «Skill 1: Читання кирилиці» | Present. Missing Standard §4.1.1 words (Олена, олівець) |
| Навичка 2: Визначення роду | «Skill 2: Визначення роду» | Present |
| Навичка 3: Дієвідміна | «Skill 3: Дієвідміна» | Present |
| Навичка 4: Питальні речення | «Skill 4: Питальні речення» | Present. Missing "бо/тому що" |
| Навичка 5: Замовлення їжі | «Skill 5: Замовлення їжі» | Missing "Дайте, будь ласка..." |
| Інтеграційне завдання | «Інтеграційне завдання» | Present. Good café dialogue |

### TTT Pedagogy Assessment

The plan specifies TTT (Test-Teach-Test) pedagogy. The content does NOT follow explicit TTT structure — there is no diagnostic pre-test before review content. The module is structured as Review-Practice (Teach-Test), not Test-Teach-Test. This is a plan deviation, though the current structure is still pedagogically functional.

### "Would I Continue?" Test (Beginner Safety)

| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | No — English support throughout, pacing is comfortable. PASS |
| Were instructions clear? | Mostly — but self-check at line 288 asks about untaught "Because". PARTIAL |
| Did I get quick wins? | Activities are at the end, not embedded within sections. Self-checks are at end of each skill. PASS |
| Was Ukrainian scary? | No — introduced gently with translations. PASS |
| Would I come back tomorrow? | Yes — encouraging tone, practical scenario. PASS |

**Result:** 4/5 → Lesson Quality baseline 9, adjusted to 8 for structural monotony.

### Structural Monotony (LLM Fingerprint)

All 5 skill sections (lines 35-341) follow the identical pattern:

```
## Skill N: [Ukrainian Title]
### Модель: [Subtitle]
### Практика: [Subtitle]
### Самоперевірка
```

Zero deviation across 5 sections. A real tutor would vary their approach — perhaps starting one section with a challenge, another with a story, another with a table. The rigid template is the primary LLM fingerprint signal.

### Vocabulary File Assessment

The vocabulary YAML contains only 5 metalinguistic terms (рід, дієслово, чоловічий, жіночий, середній). The plan lists 15+ required/recommended vocabulary items including high-frequency verbs (читати, писати, говорити, знати) and interrogatives (хто, що, де). These are used extensively in the content but absent from the vocabulary file. This is a vocabulary coverage gap — not critical for the content review but worth flagging for the vocabulary pipeline.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing scan | FOUND: Line 140 — Russian comparison in `[!cultural]` block |
| Russianisms scan | Clean — no Russianisms detected |
| Grammar scope violations | None — all grammar is within A1.1 scope |
| LLM structural monotony | FOUND: 5/5 identical section structure |
| LLM generic rhetoric | Clean — no "it is important to note" etc. |
| Factual accuracy vs. research | DIVERGENCE: Kulchytsky claim embellished beyond research |
| Testing before teaching | FOUND: "ніч" in self-check, "Because" in self-check, 6 untaught question words in activity |
| Immersion range | 20.7% — within A1.1 target (20-40%) |
| Activity correctness | All conjugation forms verified correct; scope creep in Question Words activity |
| Callout diversity | 6 different types used — good variety |
| Encouragement markers | 4+ found — adequate but could be stronger |

---

## Verdict

**PASS WITH REQUIRED FIXES**

The module is a solid A1 checkpoint with warm tutoring voice, correct grammar, good cultural hooks, and a satisfying integration dialogue. The core pedagogical flow works. However, six issues require repair before approval:

1. **Colonial framing** (line 140) — must be removed (Critical)
2. **Untaught "ніч"** in self-check (line 401) — replace with taught word
3. **6 untaught question words** in activity — remove from match-up
4. **Untaught "Because"** in self-check (line 288) — teach it or remove the question
5. **Missing "Дайте, будь ласка..."** from plan — add to café phrases
6. **Kulchytsky claim** (line 315) — align with research notes

Structural monotony (identical section templates) should be addressed in a warmth/polish pass but is not blocking.