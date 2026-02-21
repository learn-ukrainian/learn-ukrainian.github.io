Good. Status confirms 2529 words (above 2000 target) and an IPA warning flagged by the linter. Let me now write the full adversarial review.

---

## Adversarial QA Review: checkpoint-navigation (a1-20)

### Issues Found

**Issue 1: Pragmatically bizarre example — "на подрузі" (CRITICAL)**
- **File:** `checkpoint-navigation.md`, line 109
- **Text:** `*   **г → з**: подруга → **на подрузі**.`
- **Problem:** "На подрузі" literally means "on top of the female friend." Grammatically valid for demonstrating г→з, but semantically absurd for A1 learners. The meta outline explicitly specifies "дорога → на дорозі" as the example. This also fits the navigation theme perfectly.
- Green Team flagged this. Confirmed — must fix.

**Issue 2: Missing formal possessive "Ваш" (MODERATE)**
- **File:** `checkpoint-navigation.md`, Навичка 4 (lines 193-239)
- **Problem:** The module teaches polite navigation phrases (Вибачте, Скажіть будь ласка) but only covers informal possessive "Твій." In real navigation scenarios, a learner addressing a stranger would need "Ваш квиток" not "Твій квиток." A brief note after the "Your" section is needed.

**Issue 3: IPA wrong for "її" (MODERATE)**
- **File:** `checkpoint-navigation.md`, line 212
- **Text:** `**її** [jiˈji]`
- **Problem:** "Її" is і + ї = [iˈji]. The transcription [jiˈji] adds a spurious [j] before the initial "і", making it sound like "її" (two ї letters). Standard citation form is [iˈji].

**Issue 4: IPA garbled for "гривні" (MODERATE)**
- **File:** `checkpoint-navigation.md`, line 156
- **Text:** `**Три гривні** [ɦrɪu̯n⁽ʲ⁾i]`
- **Problem:** Missing stress mark. Palatalization of н before і is mandatory, not optional (⁽ʲ⁾). Should be [ˈɦrɪu̯nʲi].

**Issue 5: IPA wrong vowel + missing stress for "прямо" (MINOR)**
- **File:** `checkpoint-navigation.md`, line 260
- **Text:** `**Прямо** [prʲɑmɔ]`
- **Problem:** After palatalized р, the vowel represented by "я" is [a] not [ɑ]. Also missing stress mark. Should be [ˈprʲamɔ].

**Issue 6: IPA missing stress for "часу" (MINOR)**
- **File:** `checkpoint-navigation.md`, line 140
- **Text:** `**Немає часу** [t͡ʃɑsu]`
- **Problem:** Missing stress mark. Should be [t͡ʃɑˈsu].

**Issue 7: IPA optional palatalization on mandatory contexts (MINOR)**
- **File:** `checkpoint-navigation.md`, lines 121-122
- **Text:** `**у школі** [ʃkɔl⁽ʲ⁾i]` and `**у місті** [m⁽ʲ⁾isʲt⁽ʲ⁾i]`
- **Problem:** л before і and м before і are mandatory palatalizations in Ukrainian, not optional. Also missing stress marks. Should be [ʃkɔˈlʲi] and [ˈmʲistʲi].

**Issue 8: Quiz explanation contradicts itself (MODERATE)**
- **File:** `checkpoint-navigation.yaml`, line 68
- **Text:** `'Більшість іменників у Місцевому відмінку мають закінчення -і (у парку, у школі).'`
- **Problem:** The explanation says the ending is -і and cites "у парку" as an example — but "парку" ends in -у, not -і. This directly contradicts the point. Should use examples that actually demonstrate -і (e.g., "у школі, у місті").

**Issue 9: "поїзд" in activity not in plan vocabulary or prose (MINOR)**
- **File:** `checkpoint-navigation.yaml`, line 38-39
- **Text:** `left: 'поїзд'` / `right: 'train'`
- **Problem:** "Поїзд" doesn't appear in the plan's vocabulary_hints or in the prose content. The prose lists автобус, трамвай, метро, таксі. Not a blocker since it's a common A1 word, but it's scope creep.

**Issue 10: Non-IPA transcription "[park]" (COSMETIC)**
- **File:** `checkpoint-navigation.md`, line 70
- **Text:** `**Я бачу парк** [park].`
- **Problem:** "[park]" is English romanization, not IPA. Either remove (unnecessary for a word already taught) or use proper [pɑrk]. Low priority.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
*   **г → з**: подруга → **на подрузі**.
---NEW---
*   **г → з**: дорога → **на дорозі**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
### Your (Твій, Твоя, Твоє)
This works exactly the same way as "my". Use this with friends, family, and children (informal "you").
*   **Де твій квиток?** (Where is your ticket?)
*   **Де твої речі?** (Where are your things?)
---NEW---
### Your (Твій, Твоя, Твоє)
This works exactly the same way as "my". Use this with friends, family, and children (informal "you").
*   **Де твій квиток?** (Where is your ticket?)
*   **Де твої речі?** (Where are your things?)

### Formal "Your" (Ваш, Ваша, Ваше)
When speaking to strangers or in polite situations (which is most of navigation!), use **Ваш** instead of **Твій**. It follows the same gender pattern.
*   **Вибачте, це Ваш квиток?** (Excuse me, is this your ticket?)
*   **Це Ваша валіза?** (Is this your suitcase?)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
**його** [jɔˈɦɔ] (his) and **її** [jiˈji] (her) **do not change**.
---NEW---
**його** [jɔˈɦɔ] (his) and **її** [iˈji] (her) **do not change**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
*   **Три гривні** [ɦrɪu̯n⁽ʲ⁾i].
---NEW---
*   **Три гривні** [ˈɦrɪu̯nʲi].
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
*   **Прямо** [prʲɑmɔ] — Straight. Go straight ahead.
---NEW---
*   **Прямо** [ˈprʲamɔ] — Straight. Go straight ahead.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
**Немає часу** [t͡ʃɑsu]. (There is no time.)
---NEW---
**Немає часу** [t͡ʃɑˈsu]. (There is no time.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/checkpoint-navigation.md
---OLD---
*   школа → **у школі** [ʃkɔl⁽ʲ⁾i].
*   місто → **у місті** [m⁽ʲ⁾isʲt⁽ʲ⁾i].
---NEW---
*   школа → **у школі** [ʃkɔˈlʲi].
*   місто → **у місті** [ˈmʲistʲi].
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-navigation.yaml
---OLD---
      explanation: 'Більшість іменників у Місцевому відмінку мають закінчення -і (у парку, у школі).'
---NEW---
      explanation: 'Більшість іменників у Місцевому відмінку мають закінчення -і (у школі, у місті). Але є винятки: у парку (-у).'
===FIX_END===

---

### Issues NOT fixed (minor, non-blocking)

- **"поїзд" in match-up activity:** Common A1 word, not harmful. Replacing it would reduce activity richness for no real gain.
- **"[park]" on line 70:** Cosmetic inconsistency. Harmless for learners.
- **Meta deviation on integration scenario:** Meta says "Арсенальна → парк Вічної Слави" but content follows the plan (source of truth) with "Золоті Ворота → кав'ярня." Plan takes precedence — no fix needed.
- **Missing х → с alternation example:** Meta lists all three (г→з, к→ц, х→с) but finding a natural navigation-themed х→с example is forced. The two shown are sufficient for a checkpoint review.

---

### Verification Summary

| Check | Result |
|-------|--------|
| Word count (target 2000) | 2529 — PASS |
| Plan sections covered | All 4 plan sections present |
| Meta sections covered | All 7 meta sections present |
| Required vocabulary in prose | All 8 required items used |
| Russianisms | CLEAN |
| Russian characters (ы, э, ё, ъ) | CLEAN |
| Grammar scope (no beyond-level forms) | CLEAN |
| Activity YAML format (bare list) | CLEAN |
| Unjumble words↔answer match | All 6 verified ✅ |
| Fill-in answers produce grammatical sentences | All 24 verified ✅ |
| Quiz correct answers verified | All 16 verified ✅ |
| Group-sort classifications | All 3 sorts verified ✅ |
| Match-up translations | All 16 pairs verified ✅ |
| Factual claims (Arsenalna depth, Zoloti Vorota) | Accurate |
| LLM artifacts | None detected |
| Beginner safety | Excellent — supportive tone, clear scaffolding |
| IPA tie bars on affricates (t͡ʃ, t͡s) | Present where needed ✅ |
| В transcribed as ʋ (not w) | ✅ |

---

===VERDICT===
APPROVE
===END_VERDICT===