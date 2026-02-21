Now I have all the evidence I need. Here is my deep adversarial review.

---

# Final QA Review: questions-and-negation (a1-07)

## Issues Found

### Issue 1: FACTUAL ERROR — "сирник" mistranslated as "cheesecake"
**File:** `questions-and-negation.md`, line 279
**Text:** `**Вибачте, чи у вас є сирник?** (Excuse me, do you have cheesecake?)`
**Problem:** Сирник is a cottage cheese pancake/fritter, NOT cheesecake. The vocabulary YAML correctly translates it as "cottage cheese pancake (syrnyk)." The English gloss in the café scenario is factually wrong and would teach learners the wrong meaning for a common Ukrainian food item.

### Issue 2: IPA INCONSISTENCY — скільки palatalization
**File:** `vocabulary/questions-and-negation.yaml`, line 42
**Text:** `ipa: '[ˈsʲkʲilʲ.kɪ]'`
**Problem:** The content file uses [ˈskʲilʲkɪ] (line 140) without palatalizing с. The vocabulary file adds [sʲ] which is phonologically questionable — Ukrainian /с/ does not undergo regressive palatalization before /к/ in standard pronunciation. The content version is more accurate.

### Issue 3: FORWARD REFERENCE — "можемо" in activity
**File:** `activities/questions-and-negation.yaml`, line 252
**Text:** `"___ ми можемо увійти?"` → answer: "Чи"
**Problem:** The verb "могти" (can) is taught in a1-09 (can-must-want-modals), two modules ahead. Grep confirms "можемо" never appears in this module's prose content. Even though the exercise is mechanical (just add "Чи"), encountering unknown vocabulary in exercises creates unnecessary learner anxiety at A1.

### Issue 4: OUT-OF-SCOPE VOCABULARY — "слово" in anagram
**File:** `activities/questions-and-negation.yaml`, line 229-230
**Text:** `scrambled: "с л о в о"` / `answer: "слово"`
**Problem:** "Слово" (word) is not in the module's vocabulary YAML, not in the plan's vocabulary_hints, and only appears in the content as meta-language ("питальне слово" = question word), never as explicitly taught vocabulary. The anagram should use a word the learner has actually studied in this module.

### Issue 5: OUT-OF-SCOPE VOCABULARY — "ідея" in group-sort
**File:** `activities/questions-and-negation.yaml`, line 122
**Text:** `items: ["стіл", "книга", "кава", "телефон", "любов", "ідея"]`
**Problem:** "Ідея" does not appear anywhere in this module's prose or vocabulary. At A1, activities should reinforce taught words. "Ідея" can be replaced with a word that appears in the module.

### Issue 6: ALF QUOTE — minor authenticity note (NOT fixing)
The research confirms the original Ukrainian dub (ICTV, 1996, translator Oleksii Nehrebetskyi) used the formal "Ви" form: "Ви не любите котів? Та ви просто не вмієте їх готувати!" The module uses the "ти" form. However, both versions circulate widely, and the "ти" form is pedagogically better for A1 (learners know ти-conjugations from a1-06). **No fix needed** — this is a justified adaptation.

### Issue 7: MINOR — ALF audience age claim
Line 361: "будь-яким українцем старше 30 років" — In 2026, viewers who were old enough to understand ALF humor in 1996 would be ~38+. "Старше 30" is slightly generous but not egregiously wrong. **No fix needed** — not worth disrupting the text.

---

## Positive Findings (what's working well)

- **IPA quality is excellent throughout.** All affricates have proper tie bars (t͡ʃ, t͡s). В is correctly transcribed as ʋ (not w). Palatalization markers are accurate.
- **No Russianisms detected.** No кушати, получати, приймати участь, слідуючий.
- **No Russian characters** (ы, э, ё, ъ) — clean.
- **All Ukrainian grammar is correct.** Case agreement, verb conjugations, gender agreement all verified.
- **The frequency adverbs section** (lines 169-183) fully addresses the plan objective that the Green Team flagged as missing. завжди, часто, іноді, ніколи are all taught with examples and the double-negation rule for ніколи.
- **All fill-in activities produce grammatical sentences** when the answer is inserted.
- **Match-up pairs are all logically correct.**
- **Cultural claim about ALF is verified** — ICTV 1996 dub, translator Nehrebetskyi, genuinely culturally significant.
- **Word count exceeds 2000 target** — content is rich and thorough.
- **All 4 plan objectives are covered** and mapped to self-check questions.
- **All 15 required+recommended vocabulary items** from the plan are present in both content and vocabulary YAML.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/questions-and-negation.md
---OLD---
**You:** **Вибачте, чи у вас є сирник?** (Excuse me, do you have cheesecake?)
---NEW---
**You:** **Вибачте, чи у вас є сирник?** (Excuse me, do you have syrnyk (cottage cheese pancakes)?)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml
---OLD---
- ipa: '[ˈsʲkʲilʲ.kɪ]'
  lemma: скільки
  pos: adverb
  translation: how much / how many
---NEW---
- ipa: '[ˈskʲilʲkɪ]'
  lemma: скільки
  pos: adverb
  translation: how much / how many
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml
---OLD---
    - sentence: "___ ми можемо увійти?"
      answer: "Чи"
      explanation: "Ввічливе запитання часто починається з частки «Чи»."
      options: ["Чи", "Не", "Ні", "Так"]
---NEW---
    - sentence: "___ це смачно?"
      answer: "Чи"
      explanation: "Ввічливе запитання часто починається з частки «Чи»."
      options: ["Чи", "Не", "Ні", "Так"]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml
---OLD---
    - scrambled: "с л о в о"
      answer: "слово"
---NEW---
    - scrambled: "ч а с т о"
      answer: "часто"
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml
---OLD---
      items: ["стіл", "книга", "кава", "телефон", "любов", "ідея"]
---NEW---
      items: ["стіл", "книга", "кава", "телефон", "любов", "сік"]
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale:** The module is strong — well-structured, pedagogically sound, culturally authentic, and linguistically accurate. The five fixes above address: one factual error (сирник ≠ cheesecake), one IPA inconsistency between files, one forward-reference to untaught grammar in an activity, and two out-of-scope vocabulary items in activities. All are clean, targeted fixes. After applying them, no remaining issues. The content passes all quality gates.