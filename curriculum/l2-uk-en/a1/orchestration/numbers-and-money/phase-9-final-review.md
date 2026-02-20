Good. Files are confirmed. Now let me perform the deep adversarial checks systematically.

---

## Adversarial Review: Numbers & Money (a1-17)

### Issues Found

---

**ISSUE 1 — IPA error: `готівка` transcription**

Line 388: `**готівка** [ɦɔˈtiu̯kɑ]`

The IPA transcription `[ɦɔˈtiu̯kɑ]` is wrong. The vowel in the second syllable of **готівка** is /i/, and the third syllable has /k/ before /a/. Correct IPA: `[ɦɔˈtiu̯kɑ]` — actually this looks like it's trying to render the diphthong, but **готівка** has no diphthong. The word is го-ті-вка: /ɦɔˈtiʋkɑ/. The `u̯` is incorrect — there is no /u/ glide here. This is an LLM IPA hallucination.

**Fix**: `[ɦɔˈtiʋkɑ]`

---

**ISSUE 2 — IPA error: `здача` transcription**

Line 329: `**здача** [ˈzdat͡ʃa]`

The Ukrainian з in **здача** is /z/, and the full word is [ˈzdɑt͡ʃɑ] — the final vowel is /ɑ/ (back), not /a/ (front). More critically, in Ukrainian phonology, before a voiceless consonant, the /z/ in **зд-** assimilates: the /z/ is actually /z/ (voiced stop precedes voiced /d/), but the final -а is /ɑ/. The transcription should be `[ˈzdɑt͡ʃɑ]`.

**Fix**: `[ˈzdɑt͡ʃɑ]`

---

**ISSUE 3 — IPA error: `гроші` transcription**

Line 18: `**гроші** [ˈɦrɔʃi]`

The final vowel in **гроші** — and indeed the /ʃ/ — should be followed by /i/, which is correctly written. But the /ʃ/ in Ukrainian **ш** before **і** softens slightly; standardly rendered [ˈɦrɔʃi] is acceptable. This is fine — not an error. Moving on.

---

**ISSUE 4 — IPA error: `шістнадцять`**

Line 83: `[ʃisˈnɑdt͡sʲɑtʲ]`

The explanation says "the 'т' from 'шість' drops out." But the IPA shows `ʃis` — no /tʲ/ at all. The actual pronunciation in standard Ukrainian is [ʃisʲnɑdˈt͡sʲɑtʲ] — the т drops, but the palatalization of с remains. The transcription `ʃis` (without palatalization marker) is potentially acceptable at A1 level, but the explanation says 'т' drops, which is correct. The /s/ in the transcription should ideally be [ʃisʲ] to reflect the palatalized /sʲ/. However this is within acceptable simplification range for A1.

---

**ISSUE 5 — Factual/pedagogical error: Zone 2 table column header**

Line 234, the visual table:
```
| **2, 3, 4** (22, 33...) | дві | Nominative Pl | **22 гривні** | **2 копійки** |
```

The "Form of One/Two" column says **дві** for Zone 2 (2, 3, 4). But **дві** is only the feminine form of 2. For 3 and 4, there is no gender distinction. The column header is misleading — it lists **дві** as if it applies to 3 and 4 as well. This could confuse learners into thinking all Zone 2 numbers have feminine forms. The column should indicate **два/дві** or note that дві is for 2 only.

**Fix**: Change `дві` to `два/дві` in the table.

---

**ISSUE 6 — Pedagogical error: `два столи` (Zone 2 masculine example)**

Line 196: `*   Masculine/Neuter: **два** (два долари, два столи)`

**два столи** — this is correct Ukrainian, but **столи** is the nominative plural of **стіл**, which is a standard form. This is fine.

---

**ISSUE 7 — Grammar error in activity: `unjumble` missing punctuation**

YAML lines 311-322: The unjumble activity. All six `words` arrays contain no punctuation marks (no question marks, no periods). But the `answer` strings also contain no punctuation. Let me check:

- `"Скільки коштує цей сувенір"` — missing `?` (it's a question)
- `"Яка ціна цього магніта"` — missing `?`
- `"Дайте той за тридцять"` — missing `.` (imperative sentence)
- `"З вас сорок гривень"` — missing `.`
- `"Ні дякую я зі своїм"` — missing punctuation, also missing comma after «Ні» and «дякую»
- `"Ваша здача десять гривень"` — missing `.`

Per the activity format spec: unjumble `words` array should contain all words AND punctuation tokens in the answer. Since the answers lack terminal punctuation, the words arrays also lack it — this is internally consistent. However, the answers being punctuation-free sentences is a minor quality issue (learner sees unpunctuated sentences), but not a format breakage. 

More critically: `"Яка ціна цього магніта"` — the genitive of **магніт** is **магніта**, which is correct. Fine.

---

**ISSUE 8 — Grammar error in match-up activity: untaught phrase**

YAML lines 340-351 (match-up "Корисні фрази"):
```yaml
- left: "Дайте, будь ласка"
  right: "Give me, please"
- left: "Ось, тримайте"
  right: "Here you go"
- left: "Маєте решту?"
  right: "Do you have change?"
- left: "Я візьму це"
  right: "I will take this"
```

These four phrases (**Дайте, будь ласка**, **Ось, тримайте**, **Маєте решту?**, **Я візьму це**) do NOT appear in the lesson prose or dialogues (except **Дайте** appears in dialogue 3). They are introduced for the first time in the activity without any prior teaching. This violates the principle that activities test what was taught, not introduce new content.

**Маєте решту?** is particularly problematic — it uses **решту** (accusative of **решта**) which means "change/remainder." The module teaches **здача** for "change." Having **Маєте решту?** in an activity alongside **здача** creates confusion: which word means "change"? Both do, but they're not explained as synonyms in the lesson.

**Ось, тримайте** — never appears in the prose at all.

**Я візьму це** — appears in the Final Quiz as a translation question but not taught in the prose.

This is a real pedagogical flaw: activity tests vocabulary never introduced in the lesson.

---

**ISSUE 9 — LLM artifact: "99% of daily retail interactions"**

Line 38: `"This covers 99% of daily retail interactions."`

Invented statistic. Classic LLM padding. There is no basis for this claim.

**Fix**: Remove or rephrase to "covers the vast majority of daily retail interactions."

---

**ISSUE 10 — `сорок` folk etymology claim**

Line 114: `(The odd one out! It has a unique history related to counting fur skins)`

This is the "40 skins in a bundle" etymology — it IS a widely accepted folk etymology for **сорок** in Ukrainian/Russian. It is documented in etymological dictionaries. However it is disputed — some linguists trace it to Turkic or other origins. Presenting it as definitive fact to A1 learners is misleading. The current phrasing "It has a unique history related to counting fur skins" is stated as fact without hedging.

**Fix**: Add hedging: "Some linguists trace it to ancient fur trade counting" or "possibly related to fur trade counting."

---

**ISSUE 11 — `дев'яносто` description**

Line 119: `(Another unique one, sounds like "nine-hundred-ish")`

This is inaccurate and pedagogically harmful. **дев'яносто** does NOT sound like "nine-hundred-ish." It comes from an old Slavic formation, but telling learners it "sounds like nine-hundred" will actively confuse them when they encounter **дев'ятсот** (900). This LLM parenthetical remark is wrong and should be removed.

**Fix**: Replace with a neutral note: "(Another unique form — just memorize it!)"

---

**ISSUE 12 — Grammar note error: Zone 2 explanation for `два столи`**

Line 196: `Masculine/Neuter: **два** (два долари, два столи)`

The claim that **два** applies to both masculine AND neuter is incorrect. The neuter form of "two" is also **два** — so technically correct. But **два столи** and **два долари** are masculine. A neuter example would be **два вікна**, **два яблука**. The text doesn't actually provide a neuter example, which is fine, but labeling the category as "Masculine/Neuter" without a neuter example is incomplete teaching. Not a hard error, but worth noting.

---

**ISSUE 13 — Phrase translation error in match-up activity**

YAML line 332-333: `"Скільки з мене?"` → `"How much do I owe?"`

The prose on line 277-278 correctly explains this as "How much do I owe you?" / "What is the total?" The match-up shortens it to "How much do I owe?" — acceptable.

---

**ISSUE 14 — `готівка` pronunciation note**

Line 388: `[ɦɔˈtiu̯kɑ]`

As noted in Issue 1, the diphthong `u̯` is wrong. **готівка**: г-о-ті-вка. The /v/ (which is [ʋ] in Ukrainian) should be transcribed as [ʋ], giving [ɦɔˈtiʋkɑ].

---

**ISSUE 15 — Plan compliance: `Давайте практикувати`**

Line 154: `Давайте практикувати.`

This is grammatically incorrect Ukrainian. **Давайте** used as "Let's" requires either an imperfective infinitive or a 1st person plural form. **Давайте практикуємо** (Let's practice) or **Давайте попрактикуємо** are correct. **Давайте практикувати** — the infinitive after **давайте** is used colloquially but is grammatically non-standard and should not be taught in a prescriptive A1 module.

**Fix**: `Давайте попрактикуємо.` or `Потренуємося.`

---

**ISSUE 16 — `мінус` IPA**

Line 156: `**мінус** [ˈminus]`

The IPA uses /u/ but Ukrainian **у** in **мінус** is indeed /u/. The word stress falls on first syllable: [ˈminus]. But the /i/ should be Ukrainian /i/ — this is fine as written. However, notice the vowel is not [ɪ] (as in **числа** [ˈt͡ʃɪslɑ]). In **мінус**, the /i/ is long/tense [i] (borrowed word). Acceptable.

---

**ISSUE 17 — `плюс` IPA**

Line 155: `**плюс** [plʲus]`

The palatalized /lʲ/ is correct for **плюс** in Ukrainian. Fine.

---

**ISSUE 18 — Zone description inconsistency in the table**

Line 235: `| **5, 6... 9, 0** (also 11-19) | п'ять, шість... | Genitive Pl | **25 гривень** | **5 копійок** |`

The table says "5, 6... 9, 0 (also 11-19)" — this description correctly handles the case where 10 ends in 0 (Zone 3) and 11-19 are exceptions. But the description "5, 6... 9, 0" could be misread as "numbers ending in 5 through 9 or 0 excluding 10." The number 10 is not a compound number ending in a digit — it ends in 0. This is handled correctly. However, 20, 30, 40 etc. also end in 0 and need Zone 3, but 20 is not in the teens range. This is handled correctly by the rule "ending in 5,6,7,8,9,0." The table is pedagogically sound.

---

### Summary of Real Issues Requiring Fixes

**Critical:**
1. IPA: `[ɦɔˈtiu̯kɑ]` → `[ɦɔˈtiʋkɑ]` (wrong diphthong for готівка) — line 388
2. IPA: `[ˈzdat͡ʃa]` → `[ˈzdɑt͡ʃɑ]` (wrong final vowel for здача) — line 329
3. Grammar: `Давайте практикувати` → `Давайте попрактикуємо` — line 154
4. Factual error: `sounds like "nine-hundred-ish"` for дев'яносто — line 119
5. Activity flaw: untaught phrases in match-up activity (решту/тримайте/візьму)

**Moderate:**
6. Table: `дві` in Zone 2 column should be `два/дві`
7. Statistics: `"99% of daily retail interactions"` — invented figure
8. Etymology: `сорок` claim presented as certain fact

Now applying fixes:

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
> The word **здача** [ˈzdat͡ʃa] means "change" (the money you get back). You will hear this constantly.
---NEW---
> The word **здача** [ˈzdɑt͡ʃɑ] means "change" (the money you get back). You will hear this constantly.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
Давайте практикувати.
---NEW---
Давайте попрактикуємо.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
*   **90 — дев'яносто** [dɛʋjɑˈnɔstɔ] (Another unique one, sounds like "nine-hundred-ish")
---NEW---
*   **90 — дев'яносто** [dɛʋjɑˈnɔstɔ] (Another unique form — just memorize it!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
*   **40 — сорок** [ˈsɔrɔk] (The odd one out! It has a unique history related to counting fur skins)
---NEW---
*   **40 — сорок** [ˈsɔrɔk] (The odd one out — some linguists trace it to ancient fur trade counting, but just remember it as a special case)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
This covers 99% of daily retail interactions.
---NEW---
This covers the vast majority of daily retail interactions.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
**готівка** [ɦɔˈtiu̯kɑ] (cash)
---NEW---
**готівка** [ɦɔˈtiʋkɑ] (cash)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
| **2, 3, 4** (22, 33...) | дві | Nominative Pl | **22 гривні** | **2 копійки** |
---NEW---
| **2, 3, 4** (22, 33...) | два/дві | Nominative Pl | **22 гривні** | **2 копійки** |
===FIX_END===

Now fix the activity: remove the untaught phrases from the match-up "Корисні фрази" — specifically **Ось, тримайте**, **Маєте решту?**, and **Я візьму це** which never appear in the lesson prose. **Дайте, будь ласка** does appear in dialogue 3 so it can stay. **Я візьму це** also appears in the final quiz so it needs to either be taught in the prose OR removed from the activity. Since the quiz asks for its translation, it should at minimum be introduced somewhere in the lesson. The cleanest fix is to add **Я візьму це** to the shopping phrases section in the prose and remove **Маєте решту?** (which conflicts with **здача** already taught) and **Ось, тримайте** (never introduced).

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/numbers-and-money.yaml
---OLD---
    - left: "Дайте, будь ласка"
      right: "Give me, please"
    - left: "Ось, тримайте"
      right: "Here you go"
    - left: "Маєте решту?"
      right: "Do you have change?"
    - left: "Це дорого"
      right: "It is expensive"
    - left: "Це дешево"
      right: "It is cheap"
    - left: "Я візьму це"
      right: "I will take this"
---NEW---
    - left: "Дайте, будь ласка"
      right: "Give me, please"
    - left: "Ось п'ятдесят"
      right: "Here is fifty"
    - left: "Це дорого"
      right: "It is expensive"
    - left: "Це дешево"
      right: "It is cheap"
    - left: "Я візьму це"
      right: "I will take this"
===FIX_END===

And add **Я візьму це** to the lesson prose so it is taught before being tested. It fits naturally in the "Дорого чи дешево?" section:

===FIX_START===
FILE: curriculum/l2-uk-en/a1/numbers-and-money.md
---OLD---
Приклад:
— Скільки коштує вода?
— Сто гривень.
— Ого! Це дуже дорого!
---NEW---
Приклад:
— Скільки коштує вода?
— Сто гривень.
— Ого! Це дуже дорого!

Коли ціна вас влаштовує:
— Добре. **Я візьму це.** (I'll take this.)
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===

**Summary of fixes applied (9 total):**

1. IPA fix: `здача [ˈzdat͡ʃa]` → `[ˈzdɑt͡ʃɑ]` (wrong vowels in IPA)
2. IPA fix: `готівка [ɦɔˈtiu̯kɑ]` → `[ɦɔˈtiʋkɑ]` (false diphthong, wrong consonant)
3. Grammar fix: `Давайте практикувати` → `Давайте попрактикуємо` (non-standard infinitive construction)
4. Factual fix: дев'яносто "sounds like nine-hundred-ish" → neutral note (pedagogically dangerous misinformation)
5. Etymology hedge: `сорок` folk etymology stated as fact → hedged with "some linguists trace"
6. Statistic removal: `99% of daily retail interactions` → `vast majority` (invented figure)
7. Table fix: Zone 2 column `дві` → `два/дві` (дві is feminine-only; 3 and 4 have no gender form listed)
8. Activity fix: Removed untaught phrases `Ось, тримайте` and `Маєте решту?` from match-up (never introduced in prose; **решту** conflicts with **здача** as synonyms without explanation)
9. Prose addition: Added `Я візьму це` to the lesson body so the Final Quiz translation question tests what was taught

The Green Team review missed issues 1–4 (IPA errors, the дев'яносто misinformation, the grammar of `Давайте практикувати`) and issue 8 (activity testing untaught vocabulary). These are real problems, not cosmetic. After these fixes, the module is sound.