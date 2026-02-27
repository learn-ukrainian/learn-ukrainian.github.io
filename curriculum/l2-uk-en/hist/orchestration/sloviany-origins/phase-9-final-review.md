---

## Issues Found

### 1. Morphological error — "будь-якіх" (prose, line 33)

**File:** `sloviany-origins.md`
**Quoted text:** `а стосувалося будь-якіх іноземців`
**Problem:** The form "будь-якіх" does not exist in Ukrainian. Genitive plural of "будь-який" is "будь-яких". The ending `-іх` is absent from the Ukrainian adjectival paradigm. This is a genuine morphological error, not a stylistic variant.
**Fix:** `будь-яких іноземців`

---

### 2. Section header inconsistency — "розселення" vs. "переселення" (prose, line 74)

**File:** `sloviany-origins.md`
**Quoted text:** `### Велике розселення народів`
**Problem:** The standard historical term in Ukrainian is **«Велике переселення народів»** (Völkerwanderung). The very next sentence in this section uses the correct term: *«відомі як Велике переселення народів»*. The header contradicts the body.
**Fix:** Change header to match established term and body text.

---

### 3. Preachy prescriptive voice (prose, line 25)

**File:** `sloviany-origins.md`
**Quoted text:** `Ми маємо поважати цей міф як частину нашої інтелектуальної історії, але водночас розуміти реальні, прагматичні корені нашої назви.`
**Problem:** "Ми маємо поважати" (We must respect) is a prescriptive teacher-voice construction. Already flagged by Green Team, not yet fixed.
**Fix:** Rephrase to descriptive mode.

---

### 4. LLM cliché conclusion opener (prose, line 259)

**File:** `sloviany-origins.md`
**Quoted text:** `Ми побачили, що демократія для українців — це не модна забаганка і не новітнє запозичення із Заходу`
**Problem:** "Ми побачили, що..." is a stock AI essay-conclusion pattern. Already flagged by Green Team, not yet fixed.
**Fix:** Replace with a direct assertive claim.

---

### 5. Missing required vocabulary item "топонім" (prose)

**File:** `sloviany-origins.md`
**Problem:** The plan's `vocabulary_hints.required` list explicitly includes **топонім** (toponym). The word does not appear anywhere in the prose text — not as a bolded term, not incidentally. All other required vocabulary items are present. A natural insertion point exists in the Kiy section where Kyiv as a place name is discussed.

---

### 6. Activity instruction misleads learner (activity, line 8)

**File:** `activities/sloviany-origins.yaml`
**Quoted text:** `instruction: Прочитайте уривок з «Війни з готами» Прокопія та дайте відповідь на запитання.`
**Problem:** This reading activity contains no questions. The instruction "дайте відповідь на запитання" (answer the questions) tells the learner to look for questions that don't exist here — they appear in subsequent activities. Already flagged by Green Team, not yet fixed.

---

### 7. `source_reading` mismatch in critical-analysis (activity, lines 54–56)

**File:** `activities/sloviany-origins.yaml`
**Quoted text:** `source_reading: reading-procopius-democracy` (on the Jordanes/Bozh critical-analysis)
**Problem:** This critical-analysis task is about the **Jordanes** quote ("Вінітарій... розп'яв короля антів Божа з синами його і 70 старійшинами...") as stated in `target_text`. The `source_reading` field points to the **Procopius** democracy reading, which contains no Jordanes material. This is a semantic mismatch — students who read the linked source will not find the text they are asked to analyze. Remove the field; the `target_text` is self-contained.

---

### 8. Missing apostrophe in true-false statement (activity, line 92)

**File:** `activities/sloviany-origins.yaml`
**Quoted text:** `- statement: Прокопій Кесарійський писав, що словянами править один цар.`
**Problem:** "словянами" is missing the apostrophe after «слов». Standard orthography requires «слов'янами».

---

Now applying all 8 fixes:

===FIX_START===
FILE: curriculum/l2-uk-en/hist/sloviany-origins.md
---OLD---
а стосувалося будь-якіх іноземців, чиє мовлення нагадувало незв'язне бурмотіння, схоже на звуки природи чи крики тварин.
---NEW---
а стосувалося будь-яких іноземців, чиє мовлення нагадувало незв'язне бурмотіння, схоже на звуки природи чи крики тварин.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/sloviany-origins.md
---OLD---
### Велике розселення народів
---NEW---
### Велике переселення народів
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/sloviany-origins.md
---OLD---
Ми маємо поважати цей міф як частину нашої інтелектуальної історії, але водночас розуміти реальні, прагматичні корені нашої назви.
---NEW---
Цей міф залишається частиною нашої інтелектуальної традиції, але реальні, прагматичні корені нашої назви лежать глибше.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/sloviany-origins.md
---OLD---
Ми побачили, що демократія для українців — це не модна забаганка і не новітнє запозичення із Заходу, а глибока, споконвічна традиція, зафіксована документально ще у VI столітті.
---NEW---
Антська спадщина доводить: демократія для українців — це не модна забаганка і не новітнє запозичення із Заходу, а глибока, споконвічна традиція, зафіксована документально ще у VI столітті.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/sloviany-origins.md
---OLD---
Це робить нашу столицю однією з найдавніших у Східній Європі і безпосередньо, кровно пов'язує її з антською спадщиною. Кий — це місток між антами і Руссю, символ безперервності влади.
---NEW---
Це робить нашу столицю однією з найдавніших у Східній Європі і безпосередньо, кровно пов'язує її з антською спадщиною. Навіть **топонім** «Київ» є живим свідченням тяглості: назва міста зберегла пам'ять про антського вождя крізь тисячоліть. Кий — це місток між антами і Руссю, символ безперервності влади.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/sloviany-origins.yaml
---OLD---
  instruction: Прочитайте уривок з «Війни з готами» Прокопія та дайте відповідь на запитання.
---NEW---
  instruction: Прочитайте уривок з «Війни з готами» Прокопія Кесарійського. Цей текст є основою для наступних аналітичних завдань.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/sloviany-origins.yaml
---OLD---
- type: critical-analysis
  title: Символізм числа 70
  source_reading: reading-procopius-democracy
  instruction: Проаналізуйте повідомлення Йордана про страту князя Божа та 70 старійшин.
---NEW---
- type: critical-analysis
  title: Символізм числа 70
  instruction: Проаналізуйте повідомлення Йордана про страту князя Божа та 70 старійшин.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/sloviany-origins.yaml
---OLD---
  - statement: Прокопій Кесарійський писав, що словянами править один цар.
---NEW---
  - statement: Прокопій Кесарійський писав, що слов'янами править один цар.
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===