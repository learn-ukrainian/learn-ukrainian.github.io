## Phase 9: Final Adversarial QA Review — the-accusative-ii-people

---

### Issues Found

**Issue 1 — CRITICAL: Собака gender error (content + activity)**

Content line 146: `Dog is feminine (**-а** → **-у**).`
Activity YAML line 390: `Собака - жіночий рід, -а змінюється на -у.`

`Собака` in Ukrainian is grammatically **masculine** (чоловічий рід) per СУМ-11, despite following I declension (-а ending). Calling it "feminine" will cause learners to produce wrong adjective/pronoun agreement later (e.g., `*моя собака` instead of `мій собака`). The accusative form `собаку` is correct — the explanation is wrong.

**Issue 2 — CRITICAL: Батько in "Vowel Magic" table (content line 138)**

`| **Батько** | Я бачу **батька** | **-о** drops → **+а** |`

`Батько → батька` is standard II declension ending replacement (-о → -а), NOT a fleeting vowel or root alternation like кіт→кота (і→о) or пес→пса (е disappears). Grouping it here teaches learners that regular declension = "magic" irregularity. Must remove.

**Issue 3 — MODERATE: "Zombie Rule" undefined reference (content line 225)**

`The "Zombie Rule" was ignored here!`

This term appears exactly once and is never defined anywhere in the module. The module's established metaphors are "Heart Box" / "Stone Box" / "Greedy Masculine." This is a leftover from a different draft.

**Issue 4 — MODERATE: "it sounds okay" for кіта (content line 131)**

`If we say "Кіта", it sounds okay. But historically, it changed to **Кота**.`

Telling an A1 learner that the wrong form "sounds okay" undermines their confidence in the correct form. The form `кіта` is simply incorrect — don't validate it even hypothetically.

**Issue 5 — MODERATE: Червона Рута factual embellishment (content line 407)**

`The song is full of people — a perfect theme for today's lesson.`

Червона Рута is a love song about a rare flower. It is NOT "full of people." This is an LLM-generated false connection.

**Issue 6 — MINOR: "Джессіку" double с (content line 394)**

`Я бачу **Джессіку**.`

Standard Ukrainian transliteration does not double consonants from English. The correct form is **Джесіка** → **Джесіку**.

**Issue 7 — MODERATE: подруга IPA stress error (vocabulary line 21)**

`ipa: '[ˈpɔdruɦɑ]'`

подру́га has stress on the second syllable. The stress marker `ˈ` is before `[pɔ]`, wrongly indicating first-syllable stress. Should be `[pɔˈdruɦɑ]`.

---

### Strengths (confirmed)

- "Heart Box" vs "Stone Box" metaphor is excellent A1 pedagogy
- IPA in the content body (бачити, знати, любити, чекати) uses correct tie bars on affricates
- No Russianisms, no Russian characters anywhere
- All unjumble activities have correct word arrays matching answers
- All fill-in sentences are grammatical with answers inserted
- Plan compliance: all 5 sections present, all required vocabulary used
- Activity variety is strong: group-sort, match-up, quiz, fill-in, unjumble
- Dialogues are natural and contextually rich

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
| **Я люблю собака.** | **Я люблю собаку.** | Dog is feminine (**-а** → **-у**). |
---NEW---
| **Я люблю собака.** | **Я люблю собаку.** | Собака ends in **-а**, so it changes to **-у** (like **мама**). |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
| **Кіт** | Я бачу **кота** | **і** → **о** |
| **Пес** | Я бачу **пса** | **е** disappears |
| **Батько** | Я бачу **батька** | **-о** drops → **+а** |
---NEW---
| **Кіт** | Я бачу **кота** | **і** → **о** |
| **Пес** | Я бачу **пса** | **е** disappears |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
These sentences have errors. Can you fix them? The "Zombie Rule" was ignored here!
---NEW---
These sentences have errors. Can you fix them? The "Heart Box Rule" was ignored here!
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
*   **Кіт** (cat): If we say "Кіта", it sounds okay. But historically, it changed to **Кота**.
---NEW---
*   **Кіт** (cat): You might expect "Кіта", but the vowel changes — the correct form is **Кота**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
The song is full of people — a perfect theme for today's lesson.
---NEW---
The song is about love and longing — a perfect emotional connection to today's lesson about the people we love.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-ii-people.md
---OLD---
*   **Jessica** (ends in -a) acts like Olena: Я бачу **Джессіку**.
---NEW---
*   **Jessica** (ends in -a) acts like Olena: Я бачу **Джесіку**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-accusative-ii-people.yaml
---OLD---
    explanation: Собака - жіночий рід, -а змінюється на -у.
---NEW---
    explanation: Собака закінчується на -а, тому -а змінюється на -у.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/the-accusative-ii-people.yaml
---OLD---
- ipa: '[ˈpɔdruɦɑ]'
  lemma: подруга
---NEW---
- ipa: '[pɔˈdruɦɑ]'
  lemma: подруга
===FIX_END===

---

### Issues the Green Team review MISSED

The existing review (8.8/10) caught issues 1 and 2 above but missed:
- Issue 3 (undefined "Zombie Rule" term)
- Issue 4 (validating wrong form "кіта sounds okay")
- Issue 5 (false claim about Червона Рута)
- Issue 6 (non-standard transliteration Джессіку)
- Issue 7 (IPA stress error in vocabulary file)

---

===VERDICT===
APPROVE
===END_VERDICT===

All issues are fixable with the patches above. After applying fixes: content is accurate, activities are well-formed, Ukrainian is clean (no Russianisms, correct morphology), word count exceeds 2000-word target, and all plan sections are covered. Module is strong.