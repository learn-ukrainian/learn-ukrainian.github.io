Now I have everything I need. Let me compile the full adversarial review.

---

## Phase 9 Final QA Review — sentence-structure (b1-04)

### Issues Found

**ISSUE 1 — FACTUAL ERROR (CRITICAL): Wrong case label**
- **File:** `sentence-structure.md`, line 132
- **Text:** `Вона думає про **відпустку**. (Думає про що? Про відпустку — Місцевий відмінок).`
- **Problem:** The preposition «про» governs **Знахідний відмінок** (accusative), NOT Місцевий (locative). Місцевий questions are «на/в/у кому? на/в/у чому?» (as correctly stated on line 125). This directly contradicts the module's own teaching. A factual error in a syntax module is catastrophic for trust.
- **Fix:** Replace with a genuine Місцевий example.

**ISSUE 2 — RUSSIANISMS (3 instances, auto-fail territory)**
- **Line 190:** `Давайте розберемо це речення по кісточках:` — «Давайте + 1st person plural» is a Russian calque. Ukrainian uses the synthetic imperative: «Розберімо».
- **Line 353:** `Давайте зробимо повний синтаксичний розбір` — same pattern. Should be «Зробімо».
- **Line 398:** `Давайте подивимося, як ці граматичні терміни працюють` — same. Should be «Подивімося».
- **Note:** The Green Team review caught 2 of 3. The Phase-D (Gemini) review said "Russianisms: CLEAN" — this was a miss.

**ISSUE 3 — CALQUE: "йдемо далі за"**
- **File:** `sentence-structure.md`, line 16
- **Text:** `Сьогодні ми йдемо далі за окремі слова`
- **Problem:** Direct calque from English "go beyond". Natural Ukrainian: «виходимо за межі окремих слів».

**ISSUE 4 — LLM FINGERPRINT: Robotic repetition**
- **Locations:** Lines 34, 56, 96, 120, 142, 159
- **Text:** `Як це працює?` — identical rhetorical question repeated 6 times across consecutive sections.
- **Problem:** Obvious LLM generation pattern. Destroys the illusion of a human teacher's voice.
- **Fix:** Keep the first instance (line 34, establishes the format), vary or remove the rest.

**ISSUE 5 — METAPHOR OVERLOAD (LLM artifact)**
- **File:** `sentence-structure.md`, line 16
- **Text:** `Уявіть, що речення — це живий організм. У нього є скелет, м'язи, шкіра та душа. Щоб вільно володіти мовою на рівні B1 і вище, нам потрібно стати трохи «хірургами» та навчитися бачити цю анатомію.`
- **Problem:** Four metaphors (skeleton, muscles, skin, soul) plus "surgeons" in a single paragraph. This is a textbook LLM purple-prose pattern — the overloaded metaphor cascade.
- **Fix:** Simplify to one clean metaphor thread.

**ISSUE 6 — REGISTER MISMATCH: "бос"**
- **File:** `sentence-structure.md`, line 243
- **Text:** `Головне речення (main clause) — це бос, це лідер.`
- **Problem:** "Бос" is slang (English calque of "boss"). Jarring in a grammar explanation.

**ISSUE 7 — UNJUMBLE ACTIVITY BUG: Missing comma in words array**
- **File:** `activities/sentence-structure.yaml`, item 4 of unjumble
- **Text:** words: `['Я', 'люблю', 'каву', 'а', 'ти', 'чай']` → answer: `'Я люблю каву, а ти чай'`
- **Problem:** Answer contains a comma after «каву», but the words array has no comma token. The learner cannot produce the correct answer from the given tiles.

**ISSUE 8 — DIALOGUE INCONSISTENCY (minor)**
- **File:** `sentence-structure.md`, line 419
- **Text:** Іра corrects Марк's sentence, but switches «і» (from his original, line 416) to «та» without explanation. While synonymous, this unmotivated switch in a teaching dialogue about punctuation could confuse learners.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
*   Вона думає про **відпустку**. (Думає про що? Про відпустку — Місцевий відмінок).
---NEW---
*   Я граю **на гітарі**. (Граю на чому? На гітарі — Місцевий відмінок).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Ласкаво просимо до архітектурного бюро української мови! Сьогодні ми йдемо далі за окремі слова — ми дивимося на креслення, за якими будується кожна думка. Уявіть, що речення — це живий організм. У нього є скелет, м'язи, шкіра та душа. Щоб вільно володіти мовою на рівні B1 і вище, нам потрібно стати трохи «хірургами» та навчитися бачити цю анатомію. Ми переходимо від простого копіювання фраз до їхнього глибокого розуміння та конструювання.
---NEW---
Ласкаво просимо до архітектурного бюро української мови! Сьогодні ми виходимо за межі окремих слів і дивимося на креслення, за якими будується кожна думка. Кожне речення має свою внутрішню логіку, свій порядок і свої правила. Щоб вільно володіти мовою на рівні B1 і вище, нам потрібно навчитися бачити цю внутрішню будову — анатомію речення. Ми переходимо від простого копіювання фраз до їхнього глибокого розуміння та конструювання.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Як це працює? Присудок відповідає на питання:
---NEW---
Присудок відповідає на питання:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Як це працює? Особові закінчення дієслів в українській мові настільки унікальні
---NEW---
Річ у тому, що особові закінчення дієслів в українській мові настільки унікальні
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Як це працює? Додаток відповідає на питання непрямих відмінків
---NEW---
Додаток відповідає на питання непрямих відмінків
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Як це працює? Означення відповідає на питання прикметника:
---NEW---
Означення відповідає на питання прикметника:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Як це працює? Обставина відповідає на питання прислівника:
---NEW---
Обставина відповідає на питання прислівника:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Давайте розберемо це речення по кісточках:
---NEW---
Розберімо це речення по кісточках:
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Тепер найцікавіше. Давайте зробимо повний **синтаксичний розбір**
---NEW---
Тепер найцікавіше. Зробімо повний **синтаксичний розбір**
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Давайте подивимося, як ці граматичні терміни працюють у реальному житті
---NEW---
Подивімося, як ці граматичні терміни працюють у реальному житті
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
**Головне речення** (main clause) — це бос, це лідер.
---NEW---
**Головне речення** (main clause) — це основа, це лідер.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/sentence-structure.md
---OLD---
Виходить: «Я хочу піти в парк, та я хочу купити морозиво».
---NEW---
Виходить: «Я хочу піти в парк, і я хочу купити морозиво».
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/b1/activities/sentence-structure.yaml
---OLD---
    - words:
        - 'Я'
        - 'люблю'
        - 'каву'
        - 'а'
        - 'ти'
        - 'чай'
      answer: 'Я люблю каву, а ти чай'
---NEW---
    - words:
        - 'Я'
        - 'люблю'
        - 'каву,'
        - 'а'
        - 'ти'
        - 'чай'
      answer: 'Я люблю каву, а ти чай'
===FIX_END===

---

### Review Summary

| Check | Result |
|-------|--------|
| Russian characters (ы, э, ё, ъ) | CLEAN |
| Russianisms | 3 found → fixed |
| Calques | 2 found → fixed |
| Case/gender agreement | 1 factual error in case labeling → fixed |
| Grammar scope within level | CLEAN |
| IPA accuracy | N/A (syntax theory module) |
| Forward references | CLEAN (passive voice mention is a preview, not a teaching point) |
| Unjumble words↔answer match | 1 bug → fixed |
| Fill-in grammaticality | CLEAN (all 8 items verified) |
| Factual accuracy | 1 wrong case label → fixed |
| LLM artifacts | Metaphor overload + robotic repetition → fixed |
| Plan compliance (sections) | All 10 meta sections present |
| Required vocabulary coverage | All 9 required + 6 recommended terms used in prose |
| Objectives → self-check mapping | All 3 objectives map to self-check questions |
| Activity YAML format | CLEAN (bare list at root) |
| Vocabulary file | Present, 24 items, `items:` wrapper (standard for vocab) |
| Word target (4000) | Content ~4200 words — MEETS target |

**Phase-D review (Gemini) missed:** 3x "Давайте" Russianisms, the case error on line 132, and the unjumble comma bug. The Phase-D review's "Russianisms: CLEAN" was wrong.

**Green Team review missed:** 3rd "Давайте" instance (line 353), the case factual error (line 132), and the unjumble activity bug.

**Automated audit says PASS** — activity count (7 types) meets the configured threshold. The Green Team's "8+ required" claim doesn't match the audit config.

===VERDICT===
APPROVE
===END_VERDICT===