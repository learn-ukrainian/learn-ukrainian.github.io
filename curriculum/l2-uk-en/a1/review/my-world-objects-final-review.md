Now I have everything. Let me compile the full adversarial review.

---

## Phase 9: Adversarial QA Review — my-world-objects

### Issues Found

---

**Issue 1 (CRITICAL): Anagram activity letters are NOT scrambled**

File: `activities/my-world-objects.yaml`, lines 357-377

All 10 anagram items have the `scrambled` field containing letters in their correct order. Example: `scrambled: с т і л` for answer `стіл`. This makes the exercise trivially solvable by reading left to right — it defeats the entire purpose of an anagram activity. Every single item is affected.

---

**Issue 2 (IPA): Missing tie bar on affricate це**

File: `my-world-objects.md`, line 64

`[tse]` — the affricate ц must always carry a tie bar: `[t͡se]`. All other instances of ц in the file use `t͡s` correctly (цей [t͡sei̯], ця [t͡sʲɑ], ці [t͡sʲi]), making this an inconsistency. Also on line 58: `**Ц** [ts]` should be `[t͡s]`.

---

**Issue 3 (IPA): Missing tie bar on стілець final affricate**

File: `my-world-objects.md`, line 144

`стілець [sʲtʲiˈlɛtʲsʲ]` — the ending -ць is the affricate [t͡sʲ], not two separate sounds [tʲsʲ]. Should be `[sʲtʲiˈlɛt͡sʲ]`. Same error in vocabulary file line 46.

---

**Issue 4 (IPA): Wrong stress on гостях in proverb**

File: `my-world-objects.md`, line 245

`[u ˈɦɔsʲtʲɑx ˈdɔbre̞ ɑ ˈʋdɔmɑ ˈkrɑʃt͡ʃe̞]` — stress on гостях is marked as first syllable `[ˈɦɔsʲtʲɑx]`. Standard Ukrainian: гостя́х, stress on second syllable → `[ɦɔsʲˈtʲɑx]`.

---

**Issue 5 (IPA): Inconsistent vowel reduction in книга**

File: `my-world-objects.md`, lines 45, 70, 156

`книга [ˈknɪɦɐ]` uses [ɐ] for unstressed а, but all other words use [ɑ]: шафа [ˈʃɑfɑ], лампа [ˈlɑmpɑ], кімната [kimˈnɑtɑ]. Ukrainian does not reduce unstressed vowels like Russian. Should be `[ˈknɪɦɑ]` for consistency and accuracy.

---

**Issue 6 (Pedagogical): Neuter ambiguity (Це identification = Це specification) not addressed in prose**

File: `my-world-objects.md`, lines 111-130

The Comparison Table (line 120-123) only contrasts feminine (Це книга vs Ця книга). For neuter nouns, both identification and specification use identical forms: "Це вікно" (This is a window) and "Це вікно" (This window). A beginner seeing the table will expect different forms but find the same word. The warning box (lines 125-130) also omits this. The Green Team review flagged this as Issue #2 — it remains unfixed.

---

**Issue 7 (Scope): Forward-reference grammar in example**

File: `my-world-objects.md`, line 201

`**Де твоя сумка?** (Where is your bag?)` — uses interrogative "де" and possessive "твоя", neither of which are in this module's grammar scope. Every other example in this section uses demonstratives. This one breaks pattern.

---

**Issue 8 (LLM Fingerprint): Repetitive "Let's..." transitions**

File: `my-world-objects.md`, lines 42, 50, 134, 138, 206, 235, 272

Seven instances of "Let's..." as transition phrases. Creates a formulaic cadence. Green Team flagged this.

---

**Issue 9 (Minor): Production section header omits forms**

File: `my-world-objects.md`, line 272

`Specification (**Цей/Ця/Те**)` mixes one near form and one far form while omitting Це (neuter near), Ці/Ті (plural), Той/Та (far m/f). Confusing shorthand.

---

**Issue 10 (IPA): Missing tie bar on Ц letter description**

File: `my-world-objects.md`, line 58

`the letter **Ц** [ts]` — should be `[t͡s]` with tie bar since it's describing the affricate phoneme.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
The "Near" words start with the letter **Ц** [ts]. Think of the "ts" sound in "cats."
---NEW---
The "Near" words start with the letter **Ц** [t͡s]. Think of the "ts" sound in "cats."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
| **Neuter** | **це** | [tse] | This | **це вікно** (this window) |
---NEW---
| **Neuter** | **це** | [t͡se] | This | **це вікно** (this window) |
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
2.  **стілець** [sʲtʲiˈlɛtʲsʲ] — chair
---NEW---
2.  **стілець** [sʲtʲiˈlɛt͡sʲ] — chair
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
2.  **Feminine (Вона):** Usually ends in **-а** or **-я** (like **книга** [ˈknɪɦɐ] — book).
---NEW---
2.  **Feminine (Вона):** Usually ends in **-а** or **-я** (like **книга** [ˈknɪɦɑ] — book).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
*   **Ця книга** [t͡sʲɑ ˈknɪɦɐ] (this book) — right in front of you.
---NEW---
*   **Ця книга** [t͡sʲɑ ˈknɪɦɑ] (this book) — right in front of you.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
2.  **книга** [ˈknɪɦɐ] — book
---NEW---
2.  **книга** [ˈknɪɦɑ] — book
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
[u ˈɦɔsʲtʲɑx ˈdɔbre̞ ɑ ˈʋdɔmɑ ˈkrɑʃt͡ʃe̞]
---NEW---
[u ɦɔsʲˈtʲɑx ˈdɔbre̞ ɑ ˈʋdɔmɑ ˈkrɑʃt͡ʃe̞]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
> [!warning]
> **Don't Mix Them Up!**
> *   WRONG: **Цей** книга. (Masculine "this" with feminine "book" — Gender Mismatch).
> *   WRONG: **Ця** є книга. (English structure translated word-for-word).
> *   CORRECT: **Це** книга. (This is a book).
> *   CORRECT: **Ця** книга... (This book...).
---NEW---
> [!warning]
> **Don't Mix Them Up!**
> *   WRONG: **Цей** книга. (Masculine "this" with feminine "book" — Gender Mismatch).
> *   WRONG: **Ця** є книга. (English structure translated word-for-word).
> *   CORRECT: **Це** книга. (This is a book).
> *   CORRECT: **Ця** книга... (This book...).
>
> **Neuter trap:** For neuter nouns, identification and specification look identical: **Це вікно.** can mean "This is a window" (naming it) OR "This window" (pointing to it). Context tells you which is which. If a sentence follows (e.g., **Це вікно велике** — "This window is big"), it is specification. If it stands alone as an answer to **Що це?**, it is identification.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
*   **Де твоя сумка?** (Where is your bag?)
---NEW---
*   **Ця сумка нова.** (This bag is new.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Before we learn the new words, let's quickly remember *why* we need them. Remember the endings from the last lesson?
---NEW---
Before we learn the new words, we need to quickly remember *why* we need them. Remember the endings from the last lesson?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Let's explore how to point correctly.
---NEW---
Time to point correctly.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Now that we have the grammar, let's fill our room with objects. We will learn common items you find in a Ukrainian home, from the living room to the kitchen.

### Меблі (Furniture)

Let's learn these words by their gender so we know which "pointer" to use.
---NEW---
Now that we have the grammar, we can fill our room with objects. Here are common items you find in a Ukrainian home, from the living room to the kitchen.

### Меблі (Furniture)

We will group these words by their gender so we know which "pointer" to use.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Let's see how a conversation works when we combine these concepts. Imagine you are asking about things in a furniture store.
---NEW---
Here is how a conversation works when we combine these concepts. You are in a furniture store, asking about things.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Language reflects how people live. Let's look at the Ukrainian concept of "home."
---NEW---
Language reflects how people live. The Ukrainian concept of "home" reveals this beautifully.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/my-world-objects.md
---OLD---
Let's bring everything together. We are going to describe a room using our new tools: Identification (**Це**) and Specification (**Цей/Ця/Те**).
---NEW---
Now we bring everything together. We are going to describe a room using our two tools: Identification (**Це...**) and Specification (**Цей/Ця/Це** for near, **Той/Та/Те** for far).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/my-world-objects.yaml
---OLD---
  - answer: стіл
    scrambled: с т і л
  - answer: шафа
    scrambled: ш а ф а
  - answer: вікно
    scrambled: в і к н о
  - answer: книга
    scrambled: к н и г а
  - answer: лампа
    scrambled: л а м п а
  - answer: диван
    scrambled: д и в а н
  - answer: стілець
    scrambled: с т і л е ц ь
  - answer: телефон
    scrambled: т е л е ф о н
  - answer: крісло
    scrambled: к р і с л о
  - answer: ліжко
    scrambled: л і ж к о
---NEW---
  - answer: стіл
    scrambled: л і с т
  - answer: шафа
    scrambled: ф а ш а
  - answer: вікно
    scrambled: к н о в і
  - answer: книга
    scrambled: г и к н а
  - answer: лампа
    scrambled: п а л м а
  - answer: диван
    scrambled: в а н д и
  - answer: стілець
    scrambled: ц і л е с т ь
  - answer: телефон
    scrambled: ф е н о л е т
  - answer: крісло
    scrambled: с л о к р і
  - answer: ліжко
    scrambled: к о ж л і
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml
---OLD---
- ipa: '[tse]'
  lemma: це
---NEW---
- ipa: '[t͡se]'
  lemma: це
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml
---OLD---
- ipa: '[sʲtʲiˈlɛtʲsʲ]'
  lemma: стілець
---NEW---
- ipa: '[sʲtʲiˈlɛt͡sʲ]'
  lemma: стілець
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml
---OLD---
- ipa: '[ˈknɪɦɐ]'
  lemma: книга
---NEW---
- ipa: '[ˈknɪɦɑ]'
  lemma: книга
===FIX_END===

---

### Review Summary

| Category | Issues | Severity |
|----------|--------|----------|
| Broken activity (anagram not scrambled) | 1 | CRITICAL — fixed |
| IPA errors (tie bars, stress, vowel) | 5 | Medium — all fixed |
| Pedagogical gap (neuter ambiguity) | 1 | Medium — fixed |
| Forward-reference grammar | 1 | Minor — fixed |
| LLM fingerprint | 6 transitions | Minor — fixed |
| Russianisms | 0 | Clean |
| Russian characters | 0 | Clean |
| Gender/case agreement | 0 errors | Clean |
| Factual/cultural accuracy | 0 errors | Clean |
| Plan compliance | Full | All sections present |

**Strengths:**
- Excellent "laser pointer" analogy and Ц/Т mnemonic
- Cultural section (Покуття, хата vs квартира vs дім) is genuinely rich
- Activity variety is strong (9 activities across 5 types)
- The Identification vs Specification distinction is well-presented
- All activities are grammatically correct (answers produce valid Ukrainian sentences)
- No Russianisms, no scope creep beyond demonstratives + gender agreement

**Post-fix state:** All 10 issues resolved. Module is pedagogically sound, linguistically accurate, and plan-compliant.

===VERDICT===
APPROVE
===END_VERDICT===