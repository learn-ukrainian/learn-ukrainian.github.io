Now I have everything I need. Let me perform the thorough adversarial review.

---

## Adversarial QA Review: my-daily-routine (A1-25)

### Issues Found

**CRITICAL — Activity Bugs (break learner experience)**

**Issue 1: Fill-in missing double negation "не" — broken grammar exercise**
- File: `activities/my-daily-routine.yaml`, line 297
- Text: `"Я ___ спізнююся, бо я не люблю чекати."` with answer `"ніколи"`
- Problem: Inserting "ніколи" yields "Я ніколи спізнююся..." which is **grammatically wrong**. Ukrainian requires double negation: "Я ніколи **не** спізнююся." The "не" is missing from the sentence template. The module itself teaches this rule explicitly at line 207: "You must use **не** with the verb." This activity contradicts its own teaching.

**Issue 2: Quiz item with no blank + untaught vocabulary "готувати"**
- File: `activities/my-daily-routine.yaml`, lines 89-98
- Text: `"Він зараз готує смачний сніданок."` — complete sentence, no `___` blank
- Problem: (a) Every other quiz item in this block has a `___` blank. This one doesn't — the student sees a complete sentence and has nothing to fill in. (b) The verb "готувати" (to cook) is not taught in the module content, not in the vocabulary YAML, and not in the plan's vocabulary_hints. A student cannot solve this.

**Issue 3: Untaught "вчитися" in group-sort**
- File: `activities/my-daily-routine.yaml`, line 27
- Text: `items: ["працювати", "обідати", "йти на роботу", "вчитися"]`
- Problem: "вчитися" (to study) does not appear in the module prose, vocabulary YAML, or plan vocabulary hints. Learner has no basis to categorize it. Green review caught this.

**Issue 4: "цікавий телевізор" — unnatural collocation**
- File: `activities/my-daily-routine.yaml`, line 67
- Text: `"Вона часто ___ цікавий телевізор увечері."`
- Problem: "Цікавий телевізор" (interesting TV set) is semantically wrong. "Телевізор" in "дивитися телевізор" is a fixed collocation — you don't modify the TV set with an adjective. You'd say "цікавий фільм" (interesting film) or "цікаву передачу" (interesting program).

**Issue 5: A2-scope "ходимо" in activity fill-in**
- File: `activities/my-daily-routine.yaml`, line 300
- Text: `"Ми ___ ходимо в парк у неділю."`
- Problem: "ходити" (multidirectional motion verb) is A2 scope, not taught in this module, and not in the vocabulary. Same issue as line 248 in prose but in an activity where the learner must interact with it.

**SIGNIFICANT — IPA Stress Errors**

**Issue 6: потім — wrong stress placement**
- File: `my-daily-routine.md`, line 175
- Text: `[ˈpotʲim]`
- Problem: Stress is on the **second** syllable: потíм → `[poˈtʲim]`

**Issue 7: цього — wrong stress placement**
- File: `my-daily-routine.md`, line 179
- Text: `[ˈpʲislʲɐ ˈt͡sʲɔɦo]`
- Problem: "цього" has stress on the **last** syllable: цьогó → `[t͡sʲɔˈɦo]`

**Issue 8: іноді — wrong stress placement**
- File: `my-daily-routine.md`, line 198
- Text: `[ˈinodʲi]`
- Problem: Stress is on the **second** syllable: інóді → `[iˈnodʲi]`

**Issue 9: сирники — wrong stress placement**
- File: `my-daily-routine.md`, line 79
- Text: `[ˈsɪrnɪkɪ]`
- Problem: Stress is on the **second** syllable: сирникú → `[sɪrˈnɪkɪ]`

**SIGNIFICANT — Grammar and Scope**

**Issue 10: "Ходжу в піжамі" — A2 multidirectional verb in prose**
- File: `my-daily-routine.md`, line 248
- Text: `Одягаюся зручно. Ходжу в піжамі.`
- Problem: "ходити" is an A2 multidirectional motion verb, distinct from "йти" taught in A1. Introduces untaught grammar without explanation. Green review caught this.

**Issue 11: Ukrainian grammar error — "Не треба складна граматика"**
- File: `my-daily-routine.md`, line 273
- Text: `Не треба складна граматика.`
- Problem: "Не треба" requires the **genitive case**: "Не треба складної граматики." Alternatively: "Складна граматика не потрібна." (nominative with "потрібний"). Using nominative after "не треба" is a grammatical error — unacceptable in a teaching module.

**Issue 12: English word order "(I never am late.)"**
- File: `my-daily-routine.md`, line 208
- Text: `(I never am late.)`
- Problem: Unnatural English. Should be "(I am never late.)" Green review caught this.

**Issue 13: Confusing meta-talk about conjugation tables**
- File: `my-daily-routine.md`, line 136
- Text: `Standard conjugation tables usually simplify this to **-ся** for almost all forms except sometimes the "I" form.`
- Problem: A1 learners don't know what "standard conjugation tables" are or what they "usually" do. This is linguistics meta-talk that confuses beginners. Green review caught this.

**MINOR — Punctuation/Format**

**Issue 14: Unjumble missing comma before "а"**
- File: `activities/my-daily-routine.yaml`, lines 314-315
- Text: `answer: "Спочатку я вмиваюся а потім одягаюся"`
- Problem: Ukrainian orthography requires a comma before "а" connecting clauses. Missing comma + missing comma token in words array.

**Issue 15: Vocabulary YAML uses `items:` wrapper instead of bare list**
- File: `vocabulary/my-daily-routine.yaml`, line 1
- Text: `items:` with 2-space-indented entries
- Problem: All other A1 vocabulary files (e.g., `this-is-i-am.yaml`) use bare list format at root. This file uses a dictionary wrapper, inconsistent with project convention.

**NOTED (not fixing — enrichment scope):**
- Vocabulary YAML is missing entries for дивитися, іноді, нарешті, щодня, після цього — all taught in module
- Meta hook "жайворонки і сови" (morning person/night owl) from plan not implemented in content
- Vocabulary entries lack IPA fields (unlike other A1 vocab files)

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
**сирники** [ˈsɪrnɪkɪ] (cottage cheese pancakes)
---NEW---
**сирники** [sɪrˈnɪkɪ] (cottage cheese pancakes)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
**Потім** [ˈpotʲim] (Then / Later)
---NEW---
**Потім** [poˈtʲim] (Then / Later)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
**Після цього** [ˈpʲislʲɐ ˈt͡sʲɔɦo] (After that)
---NEW---
**Після цього** [ˈpʲislʲɐ t͡sʲɔˈɦo] (After that)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
**Іноді** [ˈinodʲi] (Sometimes)
---NEW---
**Іноді** [iˈnodʲi] (Sometimes)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
*   Я **ніколи не** спізнююся. (I never am late.) - literally "never not am late".
---NEW---
*   Я **ніколи не** спізнююся. (I am never late.) — literally "never not am late".
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
*   *Note:* Standard conjugation tables usually simplify this to **-ся** for almost all forms except sometimes the "I" form. For A1, sticking to **-ся** is always correct and safe.
---NEW---
*   *Note:* At A1 level, using **-ся** is always correct and safe. You may hear **-сь** in everyday speech (вмиваюсь instead of вмиваюся), but both forms are accepted.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
| **Одяг** | Одягаюся швидко. Одягаю костюм. | Одягаюся зручно. Ходжу в піжамі. |
---NEW---
| **Одяг** | Одягаюся швидко. Одягаю костюм. | Одягаюся зручно. Я у піжамі. |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-daily-routine.md
---OLD---
Не треба складна граматика. Розкажіть про свій день.
---NEW---
Складна граматика не потрібна. Розкажіть про свій день.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
      items: ["працювати", "обідати", "йти на роботу", "вчитися"]
---NEW---
      items: ["працювати", "обідати", "йти на роботу", "читати"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
    - question: "Вона часто ___ цікавий телевізор увечері."
      explanation: "Дієслово «дивитися» належить до II групи, тому закінчення -ить."
---NEW---
    - question: "Вона часто ___ цікавий фільм увечері."
      explanation: "Дієслово «дивитися» належить до II групи, тому закінчення -ить."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
    - question: "Він зараз готує смачний сніданок."
      explanation: "Займенник «він» вимагає закінчення -є."
      options:
        - text: "готує"
          correct: true
        - text: "готуєш"
          correct: false
        - text: "готую"
          correct: false
        - text: "готують"
          correct: false
---NEW---
    - question: "Він зазвичай ___ о першій годині."
      explanation: "Займенник «він» вимагає закінчення -є."
      options:
        - text: "обідає"
          correct: true
        - text: "обідаєш"
          correct: false
        - text: "обідаю"
          correct: false
        - text: "обідають"
          correct: false
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
    - sentence: "Я ___ спізнююся, бо я не люблю чекати."
      answer: "ніколи"
      options: ["ніколи", "завжди", "іноді", "рідко"]
---NEW---
    - sentence: "Я ___ не спізнююся, бо я не люблю чекати."
      answer: "ніколи"
      options: ["ніколи", "завжди", "іноді", "рідко"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
    - sentence: "Ми ___ ходимо в парк у неділю."
      answer: "зазвичай"
      options: ["зазвичай", "ніколи", "рідко", "іноді"]
---NEW---
    - sentence: "Ми ___ відпочиваємо вдома у вихідні."
      answer: "зазвичай"
      options: ["зазвичай", "ніколи", "рідко", "іноді"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-daily-routine.yaml
---OLD---
    - words: ["Спочатку", "я", "вмиваюся", "а", "потім", "одягаюся"]
      answer: "Спочатку я вмиваюся а потім одягаюся"
---NEW---
    - words: ["Спочатку", "я", "вмиваюся,", "а", "потім", "одягаюся"]
      answer: "Спочатку я вмиваюся, а потім одягаюся"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/my-daily-routine.yaml
---OLD---
items:
  - lemma: "прокидатися"
    translation: "to wake up"
    pos: "verb"
    aspect: "imperfective"
    notes: "reflexive verb"
    usage: "Я прокидаюся о сьомій."
  - lemma: "вставати"
    translation: "to get up"
    pos: "verb"
    aspect: "imperfective"
    usage: "Він встає рано."
  - lemma: "вмиватися"
    translation: "to wash oneself (face)"
    pos: "verb"
    aspect: "imperfective"
    notes: "reflexive verb"
    usage: "Ти вмиваєшся холодною водою."
  - lemma: "чистити"
    translation: "to clean (to brush)"
    pos: "verb"
    aspect: "imperfective"
    example: "чистити зуби"
    usage: "Ми чистимо зуби щоранку."
  - lemma: "одягатися"
    translation: "to get dressed"
    pos: "verb"
    aspect: "imperfective"
    notes: "reflexive verb"
    usage: "Я швидко одягаюся."
  - lemma: "снідати"
    translation: "to have breakfast"
    pos: "verb"
    aspect: "imperfective"
    usage: "Вони снідають на кухні."
  - lemma: "йти"
    translation: "to go (on foot)"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я йду на роботу."
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
    usage: "Ми працюємо в офісі."
  - lemma: "обідати"
    translation: "to have lunch"
    pos: "verb"
    aspect: "imperfective"
    usage: "Коли ти обідаєш?"
  - lemma: "повертатися"
    translation: "to return"
    pos: "verb"
    aspect: "imperfective"
    notes: "reflexive verb"
    usage: "Я повертаюся додому."
  - lemma: "вечеряти"
    translation: "to have dinner"
    pos: "verb"
    aspect: "imperfective"
    usage: "Ми вечеряємо о сьомій."
  - lemma: "відпочивати"
    translation: "to rest"
    pos: "verb"
    aspect: "imperfective"
    usage: "Увечері я відпочиваю."
  - lemma: "лягати"
    translation: "to lie down"
    pos: "verb"
    aspect: "imperfective"
    example: "лягати спати"
    usage: "Діти лягають спати."
  - lemma: "спати"
    translation: "to sleep"
    pos: "verb"
    aspect: "imperfective"
    usage: "Я люблю спати."
  - lemma: "спочатку"
    translation: "first / at first"
    pos: "adverb"
    usage: "Спочатку я снідаю."
  - lemma: "потім"
    translation: "then"
    pos: "adverb"
    usage: "Потім я йду на роботу."
  - lemma: "зазвичай"
    translation: "usually"
    pos: "adverb"
    usage: "Я зазвичай встаю рано."
  - lemma: "завжди"
    translation: "always"
    pos: "adverb"
    usage: "Він завжди спізнюється."
  - lemma: "рідко"
    translation: "rarely"
    pos: "adverb"
    usage: "Ми рідко ходимо в кіно."
  - lemma: "ніколи"
    translation: "never"
    pos: "adverb"
    notes: "requires 'не' before the verb"
    usage: "Я ніколи не курю."
  - lemma: "дієслово"
    translation: "verb"
    pos: "noun"
    gender: "neuter"
    usage: "Це дієслово має закінчення -ся."
---NEW---
- lemma: "прокидатися"
  translation: "to wake up"
  pos: "verb"
  aspect: "imperfective"
  notes: "reflexive verb"
  usage: "Я прокидаюся о сьомій."
- lemma: "вставати"
  translation: "to get up"
  pos: "verb"
  aspect: "imperfective"
  usage: "Він встає рано."
- lemma: "вмиватися"
  translation: "to wash oneself (face)"
  pos: "verb"
  aspect: "imperfective"
  notes: "reflexive verb"
  usage: "Ти вмиваєшся холодною водою."
- lemma: "чистити"
  translation: "to clean (to brush)"
  pos: "verb"
  aspect: "imperfective"
  example: "чистити зуби"
  usage: "Ми чистимо зуби щоранку."
- lemma: "одягатися"
  translation: "to get dressed"
  pos: "verb"
  aspect: "imperfective"
  notes: "reflexive verb"
  usage: "Я швидко одягаюся."
- lemma: "снідати"
  translation: "to have breakfast"
  pos: "verb"
  aspect: "imperfective"
  usage: "Вони снідають на кухні."
- lemma: "йти"
  translation: "to go (on foot)"
  pos: "verb"
  aspect: "imperfective"
  usage: "Я йду на роботу."
- lemma: "працювати"
  translation: "to work"
  pos: "verb"
  aspect: "imperfective"
  usage: "Ми працюємо в офісі."
- lemma: "обідати"
  translation: "to have lunch"
  pos: "verb"
  aspect: "imperfective"
  usage: "Коли ти обідаєш?"
- lemma: "повертатися"
  translation: "to return"
  pos: "verb"
  aspect: "imperfective"
  notes: "reflexive verb"
  usage: "Я повертаюся додому."
- lemma: "вечеряти"
  translation: "to have dinner"
  pos: "verb"
  aspect: "imperfective"
  usage: "Ми вечеряємо о сьомій."
- lemma: "відпочивати"
  translation: "to rest"
  pos: "verb"
  aspect: "imperfective"
  usage: "Увечері я відпочиваю."
- lemma: "лягати"
  translation: "to lie down"
  pos: "verb"
  aspect: "imperfective"
  example: "лягати спати"
  usage: "Діти лягають спати."
- lemma: "спати"
  translation: "to sleep"
  pos: "verb"
  aspect: "imperfective"
  usage: "Я люблю спати."
- lemma: "спочатку"
  translation: "first / at first"
  pos: "adverb"
  usage: "Спочатку я снідаю."
- lemma: "потім"
  translation: "then"
  pos: "adverb"
  usage: "Потім я йду на роботу."
- lemma: "зазвичай"
  translation: "usually"
  pos: "adverb"
  usage: "Я зазвичай встаю рано."
- lemma: "завжди"
  translation: "always"
  pos: "adverb"
  usage: "Він завжди спізнюється."
- lemma: "рідко"
  translation: "rarely"
  pos: "adverb"
  usage: "Ми рідко ходимо в кіно."
- lemma: "ніколи"
  translation: "never"
  pos: "adverb"
  notes: "requires 'не' before the verb"
  usage: "Я ніколи не курю."
- lemma: "дієслово"
  translation: "verb"
  pos: "noun"
  gender: "neuter"
  usage: "Це дієслово має закінчення -ся."
===FIX_END===

---

## Review Summary

| Category | Issues | Fixed |
|----------|--------|-------|
| Activity bugs (broken exercises) | 5 | 5 |
| IPA stress errors | 4 | 4 |
| Ukrainian grammar error in prose | 1 | 1 |
| A2 scope leak (prose + activity) | 2 | 2 |
| English translation error | 1 | 1 |
| Beginner-unfriendly meta-talk | 1 | 1 |
| Punctuation (unjumble) | 1 | 1 |
| Vocabulary YAML format | 1 | 1 |
| **Total** | **16** | **16** |

**Green Team missed:** 11 of 16 issues (caught 4: ходжу, вчитися, English word order, meta-talk; partially caught "готує" item). Critically missed: the double-negation bug in the "ніколи" fill-in, the broken quiz item without a blank, the grammar error "Не треба складна граматика", all 4 IPA stress errors, the "цікавий телевізор" collocation, and the A2 "ходимо" in activities.

**Remaining unfixed (enrichment scope, not blocking):** Vocabulary YAML missing entries for дивитися, іноді, нарешті, щодня, після цього. Vocabulary entries lack IPA fields. Meta hook "жайворонки і сови" not implemented.

**Strengths the module does well:**
- Excellent cultural context (обід as main meal, traditional breakfast)
- Clear вмиватися vs мити distinction with memorable "washing your hands' face" joke
- Well-structured progression morning → day → evening
- Good dialogue variety (workday vs weekend contrast)
- Meets word target

===VERDICT===
APPROVE
===END_VERDICT===