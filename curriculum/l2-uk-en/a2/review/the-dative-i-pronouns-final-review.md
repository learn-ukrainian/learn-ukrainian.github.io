Now I have everything I need. Here is my deep adversarial review.

---

# Phase 9 Final QA — the-dative-i-pronouns (a2-01)

## Issues Found

### ISSUE 1 — Vocabulary YAML: цікаво IPA completely wrong
**File:** vocabulary YAML, line 71
**Current:** `[ˈtʲsʲikɑvo]`
**Problem:** Three errors in one transcription: (1) Ukrainian "ц" is the affricate [t͡s], NOT separate [tʲsʲ]; (2) stress is on the second syllable (ці-**КА**-во), not the first; (3) "в" should be [ʋ] not [v]. Correct: `[t͡sʲiˈkɑʋo]`.

### ISSUE 2 — Vocabulary YAML: Systematic [v] instead of [ʋ] for Ukrainian В
**File:** vocabulary YAML, lines 28, 49, 55, 81, 91, 141
**Problem:** The project standard requires [ʋ] (labiodental approximant) for Ukrainian В. The content MD correctly uses [ʋɑm] (line 79), but the vocab file uses [v] throughout: вам, дзвонити, здаватися, весело, важко, давальний.

### ISSUE 3 — Vocabulary YAML: Missing tie bars on affricates
**File:** vocabulary YAML, lines 49, 106
**Problem:** дзвонити has `[dz...]` — "дз" is an affricate requiring tie bar: `[d͡z...]`. боляче has `[...tʃe]` — "ч" is an affricate requiring tie bar: `[...t͡ʃe]`.

### ISSUE 4 — Vocabulary YAML: подобатися, здаватися — palatalized т before и
**File:** vocabulary YAML, lines 37, 55
**Problem:** Both have `tʲi` in the "-тися" ending. Ukrainian "т" before "и" is NOT palatalized (palatalization only before і, ю, я, є, ь). Should be `tɪ`.

### ISSUE 5 — Content MD line 336: Error example has two errors, only one explained
**File:** content MD, line 336
**Current:** `*Incorrect:* Я помагаю тебе.`
**Problem:** "Помагаю" is a non-standard verb form (standard is "допомагаю"), creating TWO errors in the sentence, but only the case error (тебе→тобі) is explained. The meta (line 43) explicitly says the example should be "Я допомагаю тебе" to isolate the case error. The silent verb correction is confusing for A2 learners.

### ISSUE 6 — Content MD line 358: Genitive contradicts taught pattern
**File:** content MD, line 358
**Current:** `Мені треба лише води, дякую.`
**Problem:** "Води" is Genitive partitive, but the lesson teaches the pattern Dat + треба + **Nominative** (line 174). This contradicts the rule just presented. Should use the taught pattern.

### ISSUE 7 — Activities YAML line 410: Uppercase "Нам" mid-sentence
**File:** activities YAML, line 410
**Current:** answer `'Нам'` in sentence `'Ми слухаємо уважно, бо ___ дуже цікаво.'`
**Problem:** The blank follows "бо" mid-sentence. The answer should be lowercase `'нам'`.

### ISSUE 8 — Activities YAML lines 287-288: Missing comma in unjumble
**File:** activities YAML, lines 287-288
**Current:** `words: ['Скажи', 'чесно', 'чи', ...]` / `answer: 'Скажи чесно чи тут тобі зручно...'`
**Problem:** Ukrainian punctuation requires a comma before "чи" introducing an indirect question. Both the words array and answer need the comma.

### ISSUE 9 — Vocabulary YAML: Missing plan-required entries
**File:** vocabulary YAML
**Problem:** The plan's `vocabulary_hints.required` includes "давати" (to give) and "дякувати" (to thank), and `recommended` includes "поріг" (threshold). All three are missing from the vocabulary file.

### ISSUE 10 — Vocabulary YAML: Extra entries not in plan
**File:** vocabulary YAML, lines 66-70 (необхідно), 121-125 (гарно)
**Problem:** "Необхідно" is not in the plan's vocabulary_hints and not used in the content. "Гарно" as a Dative state adverb isn't taught (content uses "гарна" as an adjective, not "мені гарно"). Minor — flagged but not blocked.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
3.  *Incorrect:* Я помагаю тебе.
    *   *Why it's wrong:* "To help" governs the Dative case, not Accusative. You give help **to** someone.
    *   *Correct:* Я **допомагаю тобі**. (Helping *to you*).
---NEW---
3.  *Incorrect:* Я допомагаю тебе.
    *   *Why it's wrong:* "To help" governs the Dative case, not Accusative. You give help **to** someone.
    *   *Correct:* Я **допомагаю тобі**. (Helping *to you*).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/the-dative-i-pronouns.md
---OLD---
— **Мені** треба лише води, дякую. Я дуже хочу пити.
---NEW---
— **Мені** потрібна лише вода, дякую. Я дуже хочу пити.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - words: ['Скажи', 'чесно', 'чи', 'тут', 'тобі', 'зручно', 'сидіти', 'і', 'працювати']
      answer: 'Скажи чесно чи тут тобі зручно сидіти і працювати'
---NEW---
    - words: ['Скажи', 'чесно,', 'чи', 'тут', 'тобі', 'зручно', 'сидіти', 'і', 'працювати']
      answer: 'Скажи чесно, чи тут тобі зручно сидіти і працювати'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml
---OLD---
    - sentence: 'Ми слухаємо уважно, бо ___ дуже цікаво.'
      answer: 'Нам'
      options: ['Нам', 'Ми', 'Нас', 'Нами']
---NEW---
    - sentence: 'Ми слухаємо уважно, бо ___ дуже цікаво.'
      answer: 'нам'
      options: ['нам', 'ми', 'нас', 'нами']
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[vɑm]'
  lemma: вам
  notes: Dative form of 'ви'
  pos: pronoun
  translation: to you (plural/formal)
---NEW---
- ipa: '[ʋɑm]'
  lemma: вам
  notes: Dative form of 'ви'
  pos: pronoun
  translation: to you (plural/formal)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[poˈdɔbɑtʲisʲɑ]'
  lemma: подобатися
  notes: governs Dative case (Subject pleases Recipient)
  pos: verb
  translation: to like / to please
---NEW---
- ipa: '[poˈdɔbɑtɪsʲɑ]'
  lemma: подобатися
  notes: governs Dative case (Subject pleases Recipient)
  pos: verb
  translation: to like / to please
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[dzvoˈnɪtɪ]'
  lemma: дзвонити
  notes: governs Dative case
  pos: verb
  translation: to call (phone)
---NEW---
- ipa: '[d͡zʋoˈnɪtɪ]'
  lemma: дзвонити
  notes: governs Dative case
  pos: verb
  translation: to call (phone)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[zdɑˈvɑtʲisʲɑ]'
  lemma: здаватися
  notes: governs Dative case (impersonal)
  pos: verb
  translation: to seem
---NEW---
- ipa: '[zdɑˈʋɑtɪsʲɑ]'
  lemma: здаватися
  notes: governs Dative case (impersonal)
  pos: verb
  translation: to seem
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[ˈtʲsʲikɑvo]'
  lemma: цікаво
  notes: impersonal state
  pos: adverb
  translation: interesting / interested
---NEW---
- ipa: '[t͡sʲiˈkɑʋo]'
  lemma: цікаво
  notes: impersonal state
  pos: adverb
  translation: interesting / interested
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[ˈvɛselo]'
  lemma: весело
  notes: impersonal state
  pos: adverb
  translation: fun / merry
---NEW---
- ipa: '[ˈʋɛselo]'
  lemma: весело
  notes: impersonal state
  pos: adverb
  translation: fun / merry
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[ˈvɑʒko]'
  lemma: важко
  notes: impersonal state
  pos: adverb
  translation: difficult / hard
---NEW---
- ipa: '[ˈʋɑʒko]'
  lemma: важко
  notes: impersonal state
  pos: adverb
  translation: difficult / hard
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[ˈbɔlʲɑtʃe]'
  lemma: боляче
  notes: impersonal state
  pos: adverb
  translation: painful / hurts
---NEW---
- ipa: '[ˈbɔlʲɑt͡ʃe]'
  lemma: боляче
  notes: impersonal state
  pos: adverb
  translation: painful / hurts
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[dɑˈvɑlʲnɪj]'
  lemma: давальний
  notes: grammatical term
  pos: adjective
  translation: Dative (case)
---NEW---
- ipa: '[dɑˈʋɑlʲnɪj]'
  lemma: давальний
  notes: grammatical term
  pos: adjective
  translation: Dative (case)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml
---OLD---
- ipa: '[iˈmɛnːɪk]'
  lemma: іменник
  notes: grammatical term
  pos: noun
  translation: noun
---NEW---
- ipa: '[iˈmɛnːɪk]'
  lemma: іменник
  notes: grammatical term
  pos: noun
  translation: noun
- ipa: '[dɑˈʋɑtɪ]'
  lemma: давати
  notes: governs Dative case (давати комусь)
  pos: verb
  translation: to give
- ipa: '[dʲɑˈkuʋɑtɪ]'
  lemma: дякувати
  notes: governs Dative case (дякую тобі)
  pos: verb
  translation: to thank
- ipa: '[poˈrʲiɦ]'
  lemma: поріг
  notes: 'Cultural context: не через поріг'
  pos: noun
  translation: threshold
===FIX_END===

---

## Review Summary

**Strengths:**
- Pedagogically excellent "subject inversion" explanation for English speakers
- Cultural notes (threshold taboo, flower numbers, hospitality, bread & salt) are authentic and well-integrated
- Four dialogues provide diverse, realistic practice scenarios
- Activities have strong variety (10 distinct types) with good error-correction exercises
- Immersion ratio ~55% is appropriate for A2 Band 1

**What I fixed:**
- 9 IPA errors in vocabulary YAML (systematic [v]→[ʋ], missing tie bars, wrong affricate notation, wrong stress on цікаво)
- 1 error example isolating wrong error (помагаю→допомагаю in content)
- 1 Genitive form contradicting taught rule (води→вода in dialogue)
- 1 punctuation error in unjumble activity
- 1 capitalization error in fill-in activity
- 3 missing plan-required vocabulary entries added

**Unfixed minor items (non-blocking):**
- "Необхідно" and "гарно" in vocab file are not in plan hints — not harmful, but unnecessary
- The "Це не просто X, а Y" pattern appears once (line 59) — mild LLM fingerprint, acceptable in motivational context

===VERDICT===
APPROVE
===END_VERDICT===