Now I have all files. Let me do the deep adversarial review.

---

## Phase 9 Final QA Review: the-living-verb-ii (A1-08)

### Issues Found

**ISSUE 1 — CRITICAL: Labial L Rule Stated Incorrectly (Content, line 128)**
The text states: `The **Л** appears ONLY in the "I" form (**я**).`
Then 9 lines later (line 137): `**Вони роблять** ... (Wait! The **Л** reappears in "They" for some verbs...)`

This is a **factual grammar error**. The epenthetic Л appears in both 1sg (я) and 3pl (вони) for ALL Type 2 labial-stem verbs: роблю/роблять, люблю/люблять, сплю/сплять. The "ONLY" claim is wrong, and the "Wait!" aside teaches through confusion instead of through clarity.

**ISSUE 2 — CRITICAL: "Wait, incorrect!" Rhetorical Trap (Content, lines 161-163)**
```
*   **Ти сидиш** [sɪˈd͡ʒɪʃ] — You sit (Wait, incorrect! The mutation is ONLY in the "I" form!)
*   **Ти сидиш** [sɪˈdɪʃ] — You sit (Back to **д**)
```
The text deliberately shows a wrong form with wrong IPA, then corrects it. An A1 learner skimming will memorize the wrong form. The wrong IPA `[sɪˈd͡ʒɪʃ]` doesn't even represent a real error anyone would make — it implies someone says *"сиджиш" which is not a natural error. Replace with a clean paradigm.

**ISSUE 3 — CRITICAL: Group-Sort Activity Contradicts Its Own Instruction (Activities, lines 1-25)**
Instruction: "Розподіліть дієслова за групами відповідно до їхнього закінчення в інфінітиві (-ати чи -ити)."
- **спати** ends in **-ати** but is placed in the -ити group. By the instruction's own criterion (infinitive ending), it belongs in -ати.
- **розуміти** ends in **-іти** but is placed in the -ати group. It doesn't match either label.

Both verbs are exceptions that the module explicitly teaches as special cases. They should not appear in a basic sorting exercise that asks students to sort by ending.

**ISSUE 4 — MODERATE: Missing Required Vocabulary "просити" (Plan vs Content)**
Plan `vocabulary_hints.required` lists **просити** (to ask). It appears nowhere in the prose, activities, or vocabulary YAML. The с → ш mutation (просити → прошу) would also strengthen the consonant mutation teaching.

**ISSUE 5 — MODERATE: Missing Plan Point "Hospitality Triad" (Meta vs Content)**
Meta outline for "Культурний контекст" requires: "Hospitality Triad: Mention how їсти, пити, говорити are the core of Ukrainian guest culture." Not addressed in content.

**ISSUE 6 — MODERATE: Quiz Typo "маркерем" (Activities, line 63)**
"Яка літера є маркерем другої дієвідміни у закінченнях?" — Instrumental case of маркер is **маркером**, not "маркерем."

**ISSUE 7 — MODERATE: LLM Artifacts / Purple Prose (Content, multiple locations)**
- Line 53: "the machinery under the hood" — cliché
- Line 24: "the kingdom of the vowel **И/І**" — grandiose
- Line 117: "a fascinating quirk of Slavic phonetics" — academic for A1
- Line 37: "This is a fancy grammatical term" — dismissive/artificial
- Line 316: "Це не просто емоція. Це зв'язок." — classic LLM pattern

**ISSUE 8 — MODERATE: "athematic verb" (Content, line 188)**
"**Їсти** (to eat) is an ancient, athematic verb." — "Athematic" is graduate-level linguistics terminology. An A1 learner will not benefit from this term.

**ISSUE 9 — MINOR: Vocabulary YAML IPA Inconsistency (Vocab, line 74)**
правда transcribed as `[ˈprɑu̯dɑ]` using [u̯] for В, while the entire content file consistently uses [ʋ] for В. Should be `[ˈprɑʋdɑ]` for consistency.

**ISSUE 10 — MINOR: Etymology of любити/люди Stated Too Strongly (Content, line 314)**
"Linguists believe it shares a common ancient root with the word **люди** (people)." — PIE *lewbʰ- (love) and *h₁lewdh- (people) are distinct roots. Some scholars have noted the surface resemblance, but mainstream etymology treats them as separate. Adding "some" before "linguists" would be more accurate.

**ISSUE 11 — MINOR: Herder Quote Potentially Apocryphal (Content, line 329)**
The quote attributed to Herder cannot be verified to a specific work. It may be a paraphrase or folk attribution. Not blocking, but should be flagged.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
Now, let's look at the machinery under the hood. How do we change these verbs to fit the person doing the action? If you remember the pattern for **читати**, you are halfway there—but you need to tune your ear to a slightly different frequency.
---NEW---
Now, let's look at how these verbs work. How do we change them to fit the person doing the action? If you remember the pattern for **читати**, you are halfway there—but you need to tune your ear to a slightly different sound.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
The Second Conjugation is primarily made up of verbs that end in **-ити** in their dictionary form (the infinitive). While the First Conjugation is often associated with the vowel **Е/Є** in its endings, the Second Conjugation is the kingdom of the vowel **И/І**.

Think of these verbs as the "Action Family." While **читати** (to read) and **слухати** (to listen) help you receive information, the core verbs of the Second Conjugation often describe fundamental human interactions and movements.
---NEW---
The Second Conjugation is primarily made up of verbs that end in **-ити** in their dictionary form (the infinitive). While the First Conjugation is associated with the vowel **Е/Є** in its endings, the Second Conjugation uses the vowel **И/І**.

Think of these verbs as the "Action Family." While **читати** (to read) and **слухати** (to listen) help you receive information, the core Second Conjugation verbs describe fundamental human interactions and movements.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
Just like the verbs you already know, these new verbs are **imperfective** (недоконаний вид). This is a fancy grammatical term, but the concept is simple: these verbs describe actions that are **ongoing**, **habitual**, or **incomplete**.
---NEW---
Just like the verbs you already know, these new verbs are **imperfective** (недоконаний вид). This simply means these verbs describe actions that are **ongoing**, **habitual**, or **incomplete**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
Now we meet a fascinating quirk of Slavic phonetics. Some verbs have stems that end in "labial" consonants—sounds made with the lips: **Б, П, В, М, Ф**.
---NEW---
Now let's look at a special sound change. Some verbs have stems that end in "labial" consonants—sounds made with the lips: **Б, П, В, М, Ф**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
**Правило просте:** The **Л** appears ONLY in the "I" form (**я**).

Let's look at **робити** (to do):

*   **Я роблю** [rɔˈblʲu] — I do (See the **-лю**?)
*   **Ти робиш** [rɔˈbɪʃ] — You do (No **л** here!)
*   **Він робить** [rɔˈbɪtʲ] — He does
*   **Ми робимо** [rɔˈbɪmɔ] — We do
*   **Ви робите** [rɔˈbɪtɛ] — You do
*   **Вони роблять** [rɔˈblʲɑtʲ] — They do (Wait! The **Л** reappears in "They" for some verbs, but the "I" form is the most important one to remember right now).
---NEW---
**Правило просте:** The **Л** appears in the forms for **"I"** (**я**) and **"They"** (**вони**).

Let's look at **робити** (to do):

*   **Я роблю** [rɔˈblʲu] — I do (See the **-лю**?)
*   **Ти робиш** [rɔˈbɪʃ] — You do (No **л** here!)
*   **Він робить** [rɔˈbɪtʲ] — He does
*   **Ми робимо** [rɔˈbɪmɔ] — We do
*   **Ви робите** [rɔˈbɪtɛ] — You do
*   **Вони роблять** [rɔˈblʲɑtʲ] — They do (The **-лю-** returns here too!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
**сидіти** (to sit) → stem **сид-**
*   **Я сиджу** [sɪˈd͡ʒu] — I sit (The **д** became **дж**)
*   **Ти сидиш** [sɪˈd͡ʒɪʃ] — You sit (Wait, incorrect! The mutation is ONLY in the "I" form!)
*   **Ти сидиш** [sɪˈdɪʃ] — You sit (Back to **д**)
*   **Він сидить** [sɪˈdɪtʲ] — He sits
---NEW---
**сидіти** (to sit) → stem **сид-**
*   **Я сиджу** [sɪˈd͡ʒu] — I sit (The **д** became **дж**!)
*   **Ти сидиш** [sɪˈdɪʃ] — You sit (Back to normal **д**)
*   **Він сидить** [sɪˈdɪtʲ] — He sits
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
**Їсти** (to eat) is an ancient, athematic verb. It doesn't follow the rules of Type 1 OR Type 2 perfectly. It has its own unique set of endings that are very old. You just have to memorize it.
---NEW---
**Їсти** (to eat) is an ancient, irregular verb. It doesn't follow the rules of Type 1 OR Type 2 perfectly. It has its own unique set of endings that are very old. You just have to memorize it.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
*   **платити** (dental **т**) → **Я плачу** (change to **ч** — yes, **т** becomes **ч**!)
---NEW---
*   **платити** (dental **т**) → **Я плачу** (change to **ч** — yes, **т** becomes **ч**!)
*   **просити** (dental **с**) → **Я прошу** (change to **ш** — **с** becomes **ш**!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
The verb **любити** (to love) is very special. Linguists believe it shares a common ancient root with the word **люди** (people).
---NEW---
The verb **любити** (to love) is very special. Some linguists note it may share a common ancient root with the word **люди** (people).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
Подумайте про цей зв'язок. In the ancient Slavic worldview, to love was intimately connected to being part of the tribe, part of the people. To love is to be human. Це не просто емоція. Це зв'язок.
---NEW---
Подумайте про цей зв'язок. In the ancient Slavic worldview, to love was connected to being part of the community. To love is to be human. Любити — це зв'язок з людьми.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-living-verb-ii.md
---OLD---
Ви вивчаєте давню мову. Ця мова жила століттями. When you conjugate these verbs, you are stepping into a river of history that has been flowing for a millennium.
---NEW---
Ви вивчаєте давню мову. Ця мова жила століттями. When you conjugate these verbs, you are using forms that Ukrainians have used for over a thousand years.

### Тріада гостинності

In Ukrainian culture, three actions form the heart of hospitality: **їсти, пити, говорити** — to eat, to drink, to speak. When a guest arrives, these three verbs activate immediately. Гість прийшов? Сідай, їж, пий, говори! This is the rhythm of Ukrainian hospitality, and now you know all three verbs.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml
---OLD---
  - items:
    - читати
    - слухати
    - думати
    - знати
    - мати
    - розуміти
    - питати
    name: Перша дієвідміна (-ати)
  - items:
    - говорити
    - робити
    - любити
    - ходити
    - бачити
    - вчити
    - платити
    - сидіти
    - спати
    name: Друга дієвідміна (-ити)
---NEW---
  - items:
    - читати
    - слухати
    - думати
    - знати
    - мати
    - питати
    name: Перша дієвідміна (-ати)
  - items:
    - говорити
    - робити
    - любити
    - ходити
    - бачити
    - вчити
    - платити
    - сидіти
    name: Друга дієвідміна (-ити)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-living-verb-ii.yaml
---OLD---
    question: Яка літера є маркерем другої дієвідміни у закінченнях?
---NEW---
    question: Яка літера є маркером другої дієвідміни у закінченнях?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-living-verb-ii.yaml
---OLD---
- ipa: '[ˈprɑu̯dɑ]'
  lemma: правда
  pos: noun
  translation: truth
---NEW---
- ipa: '[ˈprɑʋdɑ]'
  lemma: правда
  pos: noun
  translation: truth
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-living-verb-ii.yaml
---OLD---
- ipa: '[sʲurˈprɪz]'
  lemma: сюрприз
  pos: noun
  translation: surprise
- ipa: '[ʃt͡ʃɔˈdnʲɑ]'
  lemma: щодня
  pos: adverb
  translation: every day
---NEW---
- ipa: '[sʲurˈprɪz]'
  lemma: сюрприз
  pos: noun
  translation: surprise
- ipa: '[ʃt͡ʃɔˈdnʲɑ]'
  lemma: щодня
  pos: adverb
  translation: every day
- ipa: '[prɔˈsɪtɪ]'
  lemma: просити
  notes: Type 2 (-ити); Mutation s→sh (я прошу)
  pos: verb
  translation: to ask / to request
===FIX_END===

---

### Unfixed Items (noted, not blocking)

1. **Herder quote (line 329)** — Potentially apocryphal or a loose paraphrase. Cannot verify to a specific Herder work. Recommend adding "adapted from" or replacing with a verified Shevchenko quote in a future pass.
2. **розуміти in practice section (line 218)** — "розуміти → Ends in -іти. This is usually Type 1!" Teaching the exception then saying "ignore it for now" adds cognitive noise. Not fixing because it's in the free-form practice section, not an activity answer.
3. **Vocabulary file missing просити** — Added via fix above.
4. **стояти (to stand)** — Listed as recommended in plan, absent from content. Not required, so not blocking.

### Verification Summary

- Content lines read: 356 (full file)
- Activity items verified: 100+ (all 10 activities, all items)
- Ukrainian forms checked: all paradigms (говорити, робити, любити, сидіти, ходити, бачити, платити, вчити, спати, їсти, пити)
- IPA transcriptions checked: all (content + vocabulary YAML)
- Russianisms: CLEAN
- Russian characters: CLEAN
- Case/gender agreement: CLEAN (all activity sentences grammatical)
- Fill-in answers: ALL produce grammatical sentences when inserted
- Plan compliance: all 5 sections present, 7/8 required vocab covered (просити added via fix), hospitality triad added via fix

===VERDICT===
APPROVE
===END_VERDICT===