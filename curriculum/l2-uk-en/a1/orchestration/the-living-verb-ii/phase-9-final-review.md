Good — the Herder quote is real (from "Journal meiner Reise im Jahr 1769") but the module's version is significantly reworded. Let me now compile my full adversarial review.

---

## Adversarial QA Review: the-living-verb-ii (a1-08)

### Issues Found

**Issue 1 (CRITICAL): Anagram activity completely broken**
- **File**: `activities/the-living-verb-ii.yaml`, lines 393-416
- **Problem**: Every single `scrambled` field has the letters in the CORRECT order, not scrambled. E.g., `scrambled: г о в о р и т и` for answer `говорити`. This makes the activity trivial and useless — it's copy-paste, not unscrambling.
- **All 10 items** are affected.

**Issue 2 (MODERATE): Forward reference to Accusative Case**
- **File**: `the-living-verb-ii.md`, line 237
- **Text**: `**каву** (Accusative case! We learned this!)`
- **Problem**: This module is sequence 8. The Accusative I (Things) is sequence 11. The accusative case has NOT been taught yet. Claiming "We learned this!" is a pedagogical sequencing error that will confuse learners who follow the curriculum order.
- **Also line 356**: `(Hint: Don't forget the Accusative case for coffee!)` — same problem.

**Issue 3 (MODERATE): Herder quote misquoted**
- **File**: `the-living-verb-ii.md`, line 333
- **Text**: `«Хто не любить своєї рідної мови? Хто забуває солодкі звуки свого дитинства? Така людина не заслуговує на ім'я людини.»`
- **Problem**: The actual Herder quote (from "Journal meiner Reise im Jahr 1769") is: «Хто не любить своєї рідної мови, солодких святих звуків свого дитинства, не заслуговує на ім'я людини.» The module restructures it into three separate sentences, adds "Хто забуває" (which is not in the original), and drops "святих" (sacred). Presenting a rewrite in quotation marks as a direct quote is factually dishonest.

**Issue 4 (MINOR): Inaccurate parenthetical on line 137**
- **File**: `the-living-verb-ii.md`, line 137
- **Text**: `(The **-лю-** returns here too!)`
- **Problem**: The form is "роб**ля**ть" not "роб**лю**ть". The epenthetic Л returns, but the vowel is -я-, not -ю-. Saying "-лю- returns" is misleading.

**Issue 5 (MINOR): Reflexive verb in activity context**
- **File**: `activities/the-living-verb-ii.yaml`, line 217
- **Text**: `Ми ___ вдома і дивимось фільм.`
- **Problem**: "дивимось" is a reflexive verb form. The module SCOPE explicitly says "Not covered: Reflexive verbs → a1-09". Using an untaught verb form in an activity sentence is a pedagogical leak.

**Issue 6 (MINOR): Recommended vocabulary "стояти" entirely absent**
- **Location**: Plan vocabulary_hints.recommended includes `стояти (to stand)`, but it appears in neither the content, vocabulary YAML, nor activities. Low priority since "recommended" not "required".

---

### IPA Verification

Checked all IPA transcriptions in the content. All use correct ɦ (not h) for Г, ʋ (not w) for В, t͡ʃ with tie bar for Ч, d͡ʒ with tie bar for ДЖ. Stress markings consistent. No issues found.

### Russianisms / Russian Characters

None detected. Clean.

### Activity Grammar Verification

All fill-in sentences produce grammatical Ukrainian when the answer is inserted. All match-up pairs are correct. All quiz answers verified. All true-false statements have correct truth values. Group-sort categories are accurate.

### Plan Compliance

- All 5 meta content_outline sections present in content
- All 8 required vocabulary items appear in prose and vocabulary YAML
- All 4 objectives map to self-check questions
- `просити` (required vocab) present in content (line 229) and vocab YAML

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
*   Object: **кава** (coffee) → **каву** (Accusative case! We learned this!)
---NEW---
*   Object: **кава** (coffee) → **каву** (The ending changes — you will learn why in a later lesson!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
4.  Перекладіть: "Ми любимо каву." (Hint: Don't forget the Accusative case for coffee!)
---NEW---
4.  Перекладіть: "We love coffee." (Hint: **Я люблю**, **Ми люби...?** And coffee is **каву** in this form.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
*   **Вони роблять** — They do (The **-лю-** returns here too!)
---NEW---
*   **Вони роблять** — They do (The **Л** returns here too!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
> «Хто не любить своєї рідної мови? Хто забуває солодкі звуки свого дитинства? Така людина не заслуговує на ім'я людини.» — Йоганн Готфрід Гердер
>
> ("He who does not love his native language? Who forgets the sweet sounds of his childhood? Such a person does not deserve the name of a human.")
---NEW---
> «Хто не любить своєї рідної мови, солодких святих звуків свого дитинства, не заслуговує на ім'я людини.» — Йоганн Готфрід Гердер
>
> ("He who does not love his native language, the sweet, sacred sounds of his childhood, does not deserve the name of a human being.")
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml
---OLD---
    sentence: Ми ___ вдома і дивимось фільм.
---NEW---
    sentence: Ми ___ вдома і п'ємо чай.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml
---OLD---
  - answer: говорити
    scrambled: г о в о р и т и
  - answer: робити
    scrambled: р о б и т и
  - answer: бачити
    scrambled: б а ч и т и
  - answer: любити
    scrambled: л ю б и т и
  - answer: ходити
    scrambled: х о д и т и
  - answer: сидіти
    scrambled: с и д і т и
  - answer: спати
    scrambled: с п а т и
  - answer: вчити
    scrambled: в ч и т и
  - answer: платити
    scrambled: п л а т и т и
  - answer: їсти
    scrambled: ї с т и
---NEW---
  - answer: говорити
    scrambled: р и т о в г о и
  - answer: робити
    scrambled: т и б о р и
  - answer: бачити
    scrambled: ч и т а б и
  - answer: любити
    scrambled: т и б ю л и
  - answer: ходити
    scrambled: д и т о х и
  - answer: сидіти
    scrambled: т і д и с и
  - answer: спати
    scrambled: т и а п с
  - answer: вчити
    scrambled: т и ч в и
  - answer: платити
    scrambled: т и л а т п и
  - answer: їсти
    scrambled: т и с ї
===FIX_END===

---

### Verdict

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale**: The module is pedagogically solid with good structure, accurate Ukrainian grammar, correct IPA, and no Russianisms. The six issues found are all fixable: a broken anagram activity (critical but mechanical fix), two forward references to the Accusative case, a misquoted Herder citation, a misleading parenthetical, and a reflexive verb leak in an activity. After applying the fixes above, the module passes all gates. Content meets word target (~2400 words). Activities are numerous, varied (10 activities), and grammatically sound. Vocabulary coverage is complete for all required items.