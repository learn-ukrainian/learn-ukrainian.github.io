## Deep Adversarial QA Review: prepositions-direction-origin (A1-30)

---

### Ukrainian Language Quality

**IPA Accuracy** — All transcriptions verified:
- `[dɛ]`, `[kuˈdɪ]`, `[ˈzʋʲidkɪ]`, `[ɪˈtɪ]`, `[ˈjixɐtɪ]`, `[u̯ˈdɔmɐ]` — correct. Uses ʋ for В (not w). No tie-bar issues (no affricates in this module). **PASS**

**Russianisms** — No кушати, получати, приймати участь, слідуючий, являється, зустрінути, or other Russianisms found. **CLEAN**

**Russian Characters** — No ы, э, ё, ъ found. **CLEAN**

**Gender/Case Agreement** — Systematically verified all ~60 declined forms in prose:
- All locative forms correct (магазині, школі, кімнаті, банку, сумці, Києві, Україні, столі, стіні, вікні, концерті, уроці, роботі, вулиці, пошті, вокзалі, аеропорті, готелі, лікарні, центрі, ринку, площі)
- All accusative forms correct (магазин, парк, школу, роботу, Україну, кімнату, бібліотеку, вулицю, лікарню, площу)
- All genitive forms correct (парку, магазину, Києва, школи, України, кімнати, офісу, роботи, пошти, вулиці, концерту, столу, вокзалу, лікаря, мами, друга, Америки, Англії, Канади, Лондона, Польщі, аеропорту, готелю, лікарні, театру, ресторану, центру, ринку, площі)
- **PASS**

---

### Issues Found

#### Issue 1 (CRITICAL): Wrong verb form as distractor — "їдять" instead of "їдуть"

**File:** `activities/prepositions-direction-origin.yaml`, line 305
**Text:** `- text: "їдять"`

**Problem:** "їдять" is the 3rd person plural of **їсти** (to eat), NOT їхати (to go by transport). The correct 3pl of їхати is **їдуть**. In a quiz titled "Йти чи Їхати?", this distractor implies "їдять" is a conjugation of їхати, which could teach learners a wrong paradigm. Every other item in this quiz uses correctly conjugated forms (їдемо, їде, їдеш), making this one stand out as a bug.

**Fix:** Change to "їдуть" (actual 3pl of їхати) so the distractor tests the intended verb-choice distinction.

#### Issue 2 (MINOR): Plan compliance gap — "Slipper Culture" absent

**File:** Content prose
**Plan reference:** Plan section 1, point 2: *"Slipper Culture: Exploring the linguistic and physical boundary between the outside world (shoes on) and the home «вдома» (shoes off)."*

The content covers **вдома** (lines 159-166) but omits the slipper culture cultural hook entirely. The meta file also references it: *"'Вдома' (At home) implies safety and comfort (slippers on)"*. The concept of home-as-location is present; the cultural texture around it is not. This is a gap but doesn't affect the module's core pedagogical function. Not blocking.

#### Issue 3 (COSMETIC): Prefixed motion verbs beyond stated scope

The SCOPE comment (line 4) says *"just basic йти/їхати"* but the prose uses **виходжу** (line 278, 386, 392), **заходжу** (line 202), **приїхав** (line 277), and **сідає** (line 410). These verbs appear in example sentences where the pedagogical focus is on the preposition, not the verb. At A1.3 (Consolidation), passive exposure to common prefixed verbs is standard and expected. **повертатися**, **приходити**, and **дістатися** ARE in the vocabulary file. Not blocking.

---

### Pedagogical Correctness

- **Vocabulary used in activities**: All activity vocabulary traces to the prose content and plan vocabulary_hints. "Університет" appears once in a fill-in (line 162) — not in vocab file but is a transparent cognate. Acceptable. **PASS**
- **Grammar scope**: No grammar beyond A1 scope taught. Cases are within plan.grammar. Aspect is not explicitly taught (appropriate for A1). **PASS**
- **Forward references**: None found. Module references a1-13 (prerequisite) and a1-34/a1-35 (future) in SCOPE comments only, not in teachable content. **PASS**
- **Unjumble words**: All 6 items verified — every word in `words` array appears exactly in the `answer`. **PASS**
- **Fill-in answers**: All 16 fill-in items verified — each answer produces a grammatical Ukrainian sentence when inserted. **PASS**
- **Quiz answers**: All items correct except Issue 1 above. **PASS (after fix)**

---

### Plan Compliance

| Plan Section | Present? | Notes |
|---|---|---|
| Вступ / Укрзалізниця hook | ✅ | Lines 14-33 |
| Slipper Culture | ❌ | Missing (Issue 2) |
| Three Questions intro | ✅ | Lines 20-27 |
| Де? — Locative with в/у, на | ✅ | Lines 117-179 |
| Euphony у/в | ✅ | Line 134 |
| Вдома concept | ✅ | Lines 159-166 |
| Куди? — Accusative with в/у, на | ✅ | Lines 181-250 |
| Static vs Dynamic error | ✅ | Lines 89-99 |
| До + Genitive | ✅ | Lines 225-237 |
| Звідки? — Genitive with з/від | ✅ | Lines 252-325 |
| з/із/зі euphony §4.1.7 | ✅ | Lines 256-262 |
| з vs від distinction | ✅ | Lines 264-300 |
| City route synthesis | ✅ | Lines 380-432 |
| Decision table | ✅ | Lines 67-71 |

Required vocabulary all present in prose: де, куди, звідки, в/у, на, до, з/із/зі, від, йти, їхати, вдома, центр, робота. **PASS**

---

### Factual Accuracy

- Ukrzaliznytsia train culture description — accurate. **PASS**
- Ринок vs Супермаркет distinction — accurate. **PASS**
- All case forms verified against standard Ukrainian grammar. **PASS**

---

### LLM Artifacts

- No purple prose, no grandiose openers. **CLEAN**
- No "Це не просто X, а Y" pattern. **CLEAN**
- No folk etymology presented as fact. **CLEAN**
- No invented statistics or percentages. **CLEAN**
- Tone is clear, direct, and instructional throughout. **CLEAN**

---

### Word Count

Content is ~460 lines of prose with extensive examples, tables, and dialogues. Comfortably exceeds the 2000-word target. **PASS**

---

### Activity Count & Quality

86 items across 10 activity blocks. Excellent variety: group-sort (2), match-up (2), quiz (2), fill-in (2), unjumble (1), true-false (1). All Ukrainian in activities is grammatically correct. Feedback explanations are pedagogically useful. **PASS**

---

## Fix

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/prepositions-direction-origin.yaml
---OLD---
        - text: "їдять"
          correct: false
        - text: "читають"
          correct: false
        - text: "пишуть"
---NEW---
        - text: "їдуть"
          correct: false
        - text: "читають"
          correct: false
        - text: "пишуть"
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Summary:** Solid module with strong pedagogical structure, accurate Ukrainian, and excellent activity coverage (86 items). One critical fix applied: "їдять" (3pl of їсти/to eat) → "їдуть" (3pl of їхати/to go by transport) in the verb-choice quiz. The "Slipper Culture" plan point is absent but non-blocking — вдома is covered functionally. All other gates pass clean.