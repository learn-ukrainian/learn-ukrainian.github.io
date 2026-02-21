Now I have all the data. Let me compile the full adversarial review.

---

# Phase 9: Final QA Review — the-instrumental-i-accompaniment

## Findings

### CRITICAL: Pedagogical Errors (Misplaced Examples)

**Issue 1: "з лікарем" in the -ом section (line 83)**
The section "Чоловічі іменники: Тверді закінчення (-ом)" teaches that hard masculine nouns take -ом. But the example "Батько розмовляє **з лікарем**" uses the ending -ем. In Ukrainian, лікар → лікарем (instrumental takes -ем due to stress/phonetic pattern). A student who just learned "hard stem = add -ом" will be immediately confused by seeing -ем in the very same section with no explanation.

**Issue 2: "з бабусею" in the -ою section (line 126)**
The section "Жіночі іменники: Тверді закінчення (-ою)" teaches feminine nouns ending in -а take -ою. But "бабуся" ends in -я (soft stem), and its instrumental "бабусею" uses the SOFT ending -ею. This example directly contradicts the rule being taught in that section.

### CRITICAL: Activity Defects

**Issue 3: Error-correction item 5 — broken replacement**
Sentence: "Ти будеш каву з я?" — `error: 'я'`, `answer: 'зі мною'`. Replacing 'я' with 'зі мною' produces "Ти будеш каву **з зі мною**?" — double preposition. The error field must be `'з я'` so the replacement yields "Ти будеш каву зі мною?".

**Issue 4: Cloze blanks 2 and 3 violate module scope**
Blank 2: "Ми жили в готелі {{2}} (море)" → answer "над морем". This tests a spatial preposition (над + instrumental), explicitly excluded in the SCOPE comment: "Not covered: Spatial Prepositions (under/behind/above) → a2-07".
Blank 3: "Щовечора ми гуляли {{3}} (пляж)" → answer "пляжем". This is instrumental of means/manner (walking *by way of* the beach), explicitly excluded: "Not covered: Instrumental Case (Means/Tools) → a2-05".

### SIGNIFICANT: Typos (Unfixed from Green Team)

**Issue 5: "ііз" typo (lines 173, 403)**
Line 173: `не «ііз студентом»` — double-і typo.
Line 403: `Я йду ііз студентом.` — same typo. Both were flagged in the Green Team review and remain unfixed.

### SIGNIFICANT: Grammar Error in Ukrainian

**Issue 6: Line 282 — incomplete sentence**
"Стати **другом** потрібен час." — Missing subordinator. Should be "Щоб стати **другом**, потрібен час."

### SIGNIFICANT: Missing Required Vocabulary

**Issue 7: Plan vocabulary_hints.required lists "одружитися" and "подружитися" — both completely absent from content and vocabulary YAML.** These are required items per the plan, not optional. "Познайомитися" (perfective) is also absent from the vocabulary file (only the imperfective "знайомитися" is listed).

### MODERATE: Euphony Example Quality

**Issue 8: "зі зіркою" (line 175)**
Using "зі зіркою" to exemplify the "зі" variant creates an awkward зі+зі stutter. While grammatically defensible, it's a poor teaching example. Replace with a cleaner word starting with a consonant cluster.

### MODERATE: Inconsistent Capitalization in Activity

**Issue 9: Group-sort "з надією" (lowercase)**
All other items in the "-ею / -єю (Feminine Soft)" group are capitalized names (з Марією, з Юлією). "з надією" lowercase suggests the common noun "hope" rather than the name "Надія" used throughout the content. Inconsistent.

### MINOR: LLM Fingerprint / Purple Prose

Pervasive purple prose in English paragraphs:
- Line 68: "Mastering this single ending will allow you to form hundreds of useful sentences"
- Line 111: "one of the most recognizable and musical endings in the entire Ukrainian language"
- Line 162: "The Ukrainian language loves music and smooth sounds"
- Line 193: "You must memorize this specific phrase right now"
- Line 213: "These verbs are the engine of your social vocabulary"
- Lines 243-245: Two full paragraphs of motivational padding about word order

These don't harm students but they inflate word count with filler and carry obvious LLM fingerprints. Not fixing in this pass as the word count (3793) comfortably exceeds the 3000 target.

### MINOR: "Енфонія" — Not a Real Ukrainian Word

Section title "Презентація: Форми та Енфонія" uses "Енфонія" which doesn't exist in Ukrainian. The correct term is "евфонія" (or native "милозвучність"). Cannot fix without also updating the meta file which is not in scope.

### NOTED: "Ігор → з Ігорем" in match-up

The form is correct (Ігор → Ігорем in standard Ukrainian). However, "Ігор" ends in a hard consonant but takes -ем, contradicting the module's "hard masculine = -ом" rule. This could confuse students. The activity includes it alongside properly-taught soft stems without explanation. Noted but not critical enough to fix.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
*   Батько розмовляє **з лікарем**.
---NEW---
*   Батько розмовляє **з сусідом**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
*   Дівчинка малює **з бабусею**.
---NEW---
*   Дівчинка малює **з подругою**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
*   **зі** студентом (не «ііз студентом» — занадто багато приголосних)
---NEW---
*   **зі** студентом (не «із студентом» — занадто багато приголосних)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
*   **зі** зіркою (with a star)
---NEW---
*   **зі** Славою (with Slava)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
**Друг** — це людина, якій ви довіряєте своє життя, гроші та секрети. Стати **другом** потрібен час.
*   Я буду святкувати **з другом**.
*   Вона ділиться секретами **з подругою**.
*   Він завжди радиться **з найкращим другом**.
---NEW---
**Друг** — це людина, якій ви довіряєте своє життя, гроші та секрети. Щоб стати **другом**, потрібен час.
*   Я буду святкувати **з другом**.
*   Вона ділиться секретами **з подругою**.
*   Він завжди радиться **з найкращим другом**.

Важливі дієслова:
*   **Подружитися з кимось** — стати друзями. Ми **подружилися з Оленою** минулого року.
*   **Одружитися з кимось** — створити сім'ю. Він **одружився з Наталією** влітку.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-instrumental-i-accompaniment.md
---OLD---
*   ❌ Я йду ііз студентом. (збіг приголосних «із ст-» — важко вимовити)
---NEW---
*   ❌ Я йду із студентом. (збіг приголосних «із ст-» — важко вимовити)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-instrumental-i-accompaniment.yaml
---OLD---
    - sentence: 'Ти будеш каву з я?'
      error: 'я'
      answer: 'зі мною'
---NEW---
    - sentence: 'Ти будеш каву з я?'
      error: 'з я'
      answer: 'зі мною'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-instrumental-i-accompaniment.yaml
---OLD---
  passage: 'Минулого літа я їздив на море. Я їздив не сам, а {{1}} (друг). Його звати Іван. Ми жили в готелі {{2}} (море). Щовечора ми гуляли {{3}} (пляж). Одного разу ми познайомилися {{4}} (дівчина).
---NEW---
  passage: 'Минулого літа я їздив на море. Я їздив не сам, а {{1}} (друг). Його звати Іван. Ми жили в готелі разом {{2}} (Іван). Щовечора ми гуляли {{3}} (хлопці) біля моря. Одного разу ми познайомилися {{4}} (дівчина).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-instrumental-i-accompaniment.yaml
---OLD---
    - id: 2
      answer: 'над морем'
      options: ['над морем', 'з морем', 'під морем', 'за морем']
    - id: 3
      answer: 'пляжем'
      options: ['пляжем', 'з пляжем', 'пляжу', 'на пляжі']
---NEW---
    - id: 2
      answer: 'з Іваном'
      options: ['з Іваном', 'з Івана', 'з Івану', 'з Іване']
    - id: 3
      answer: 'з хлопцями'
      options: ['з хлопцями', 'з хлопців', 'з хлопцям', 'з хлопці']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-instrumental-i-accompaniment.yaml
---OLD---
      items: ['з Марією', 'з надією', 'з доцею', 'з Юлією', 'з мрією']
---NEW---
      items: ['з Марією', 'з Надією', 'з доцею', 'з Юлією', 'з мрією']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-instrumental-i-accompaniment.yaml
---OLD---
  - lemma: 'займенник'
    translation: 'pronoun (grammar term)'
    pos: 'noun'
    gender: 'm'
    notes: 'Metalanguage term used in grammar explanations'
---NEW---
  - lemma: 'займенник'
    translation: 'pronoun (grammar term)'
    pos: 'noun'
    gender: 'm'
    notes: 'Metalanguage term used in grammar explanations'
  - lemma: 'одружитися'
    translation: 'to get married'
    pos: 'verb'
    aspect: 'perf'
    usage: 'одружитися з кимось (to marry someone)'
  - lemma: 'подружитися'
    translation: 'to become friends'
    pos: 'verb'
    aspect: 'perf'
    usage: 'подружитися з кимось (to become friends with someone)'
  - lemma: 'познайомитися'
    translation: 'to get acquainted / to meet'
    pos: 'verb'
    aspect: 'perf'
    usage: 'познайомитися з кимось (to meet someone new)'
===FIX_END===

---

## Remaining Issues After Fixes

1. **"Енфонія" in section title** — requires meta file update (out of scope)
2. **LLM purple prose** in English paragraphs — pervasive but not student-harmful; would need prose rewrite
3. **"Ігор → з Ігорем"** in match-up — correct form but potentially confusing given taught rules
4. **Quiz item count** — 9 items vs plan's 12+ (select activity partially compensates)
5. **"зі школою"** (line 174) — grammatically correct euphony example but semantically odd for an accompaniment module

None of these are blocking. The critical pedagogical and activity defects are addressed by the fixes above.

===VERDICT===
NEEDS_WORK
===END_VERDICT===