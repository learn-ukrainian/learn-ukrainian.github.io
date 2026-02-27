I've read all files. Now I'll compile my adversarial findings.

---

## Adversarial QA Review: at-the-cafe-practical (a1-35)

### Issues Found

**ISSUE 1 — CRITICAL: Activity produces ungrammatical sentence (fill-in)**
File: `activities/at-the-cafe-practical.yaml`, line 169
Sentence: `"— Я буду ___ каву."` with answer `"філіжанку"` produces **"Я буду філіжанку каву"** — two accusative objects stacked, which is grammatically wrong. The content itself (line 260 of .md) correctly uses **"Я буду філіжанку кави"** (Acc. of measure + Gen. of substance). The activity must say `кави` not `каву`.

**ISSUE 2 — CRITICAL: Plan-required construction missing from content**
The plan explicitly requires teaching `«Мені, будь ласка...»` as a key ordering formula (plan line 22: "вивчення фраз «Можна мені...?» та «Мені, будь ласка...»"; meta section 2: "конструкція «Мені, будь ласка...» або «Я буду...»"). The polite construction table (lines 121–127) lists Я хочу, Я буду, Я візьму, Можна, Дайте — but NOT **Мені**. Meanwhile, three activities test it (match-up "Мені, будь ласка...", unjumble "Мені каву будь ласка", fill-in "Мені, будь ___, велику каву"). This is a teach-before-test violation.

**ISSUE 3 — MODERATE: Plan grammar item "Скільки?" not covered**
The plan lists `Questions (Можна...?, Скільки?)` under grammar focus. «Скільки коштує?» (How much does it cost?) never appears in the module content. For a café module with a price menu, this is a natural and necessary phrase.

**ISSUE 4 — MODERATE: "Окремий рахунок" tested but not taught**
The phrase "Окремий рахунок" appears in match-up activity (line 15–16) and unjumble (line 296–297), but is never introduced or explained in the content prose. The plan vocabulary hints include it under `рахунок` collocations. It should appear in the payment section.

**ISSUE 5 — MINOR: IPA for "кав'ярня"**
Line 29: `` — The в in кав'ярня precedes a vowel (я = [jɑ]) across an apostrophe boundary. At this syllable juncture, [ʋ] is more standard than [u̯] in Ukrainian phonological transcription. However, since the apostrophe marks в as syllable-final (кав-'яр-ня), [u̯] is defensible. I will not fix this — it's within acceptable variation for A1.

**ISSUE 6 — MINOR: LLM artifact opener**
Line 19: "Welcome to the world of Ukrainian coffee!" — Generic LLM-style opener. Not critical for A1 practical module.

### Verified Clean

- **Russianisms**: None found. All Ukrainian vocabulary is standard.
- **Russian characters**: No ы, э, ё, ъ detected.
- **IPA tie bars**: Affricates correctly use tie bars: [t͡ʃ] (line 105), [t͡s] (lines 139, 141), В correctly uses [ʋ] throughout.
- **Gender/case agreement**: All checked — велику каву (Acc.F), зелений чай (Acc.M=Nom), середнє/велике лате (neuter agreement, line 293–294), all correct.
- **Green Team fixes already applied**: "Перепрошую!" (line 303), "Зачекайте, будь ласка" (line 297), "Please show me the menu" (line 79), "Enjoy your work!" (line 283) — all confirmed.
- **Kulchytsky claim**: Framed as "Легенда" — historically appropriate hedging.
- **Unjumble word arrays**: All 12 items verified — every word in `words` appears in `answer` and vice versa.
- **All other fill-in items**: 15 of 16 produce grammatical sentences (1 fix needed above).
- **Word target**: Content well exceeds 2000 words. ✅
- **All 4 plan content_outline sections**: Present and covered. ✅
- **All required vocabulary**: кава, чай, меню, рахунок, будь ласка, дякую, готівка, картка — all used in prose. ✅
- **Vocabulary YAML file**: Exists with 20 items covering all required + recommended terms. ✅

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/at-the-cafe-practical.yaml
---OLD---
    - sentence: "— Я буду ___ каву."
      answer: "філіжанку"
      options: ["філіжанку", "філіжанка", "філіжанки", "філіжанкою"]
      explanation: "Accusative case for the object."
---NEW---
    - sentence: "— Я буду ___ кави."
      answer: "філіжанку"
      options: ["філіжанку", "філіжанка", "філіжанки", "філіжанкою"]
      explanation: "Accusative case: філіжанка → філіжанку (a cup of coffee)."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe-practical.md
---OLD---
| Formula | Object (Accusative) | Politeness |
| :--- | :--- | :--- |
| **Я хочу** | **каву**, | будь ласка. |
| **Я буду** | **каву**, | будь ласка. |
| **Я візьму** | **чай**, | дякую. |
| **Можна** | **лате**, | будь ласка? |
| **Дайте** | **меню**, | будь ласка. |
---NEW---
| Formula | Object (Accusative) | Politeness |
| :--- | :--- | :--- |
| **Мені** | **каву**, | будь ласка. |
| **Я хочу** | **каву**, | будь ласка. |
| **Я буду** | **каву**, | будь ласка. |
| **Я візьму** | **чай**, | дякую. |
| **Можна** | **лате**, | будь ласка? |
| **Дайте** | **меню**, | будь ласка. |

The construction **«Мені, будь ласка, каву»** is one of the most natural and polite ways to order. It literally means "To me, please, coffee" — short, soft, and very Ukrainian. You will hear it constantly in cafés.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe-practical.md
---OLD---
Sometimes, you might want a recommendation. This is a great way to practice your speaking!
*   **Що ви порадите?** — What do you recommend?
*   **Яка кава найсмачніша?** — Which coffee is the tastiest?
*   **Що це?** — What is this?
*   **Це смачно?** — Is this tasty?
---NEW---
Sometimes, you might want a recommendation or ask about prices. This is a great way to practice your speaking!
*   **Що ви порадите?** — What do you recommend?
*   **Яка кава найсмачніша?** — Which coffee is the tastiest?
*   **Скільки коштує лате?** — How much does the latte cost?
*   **Що це?** — What is this?
*   **Це смачно?** — Is this tasty?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-cafe-practical.md
---OLD---
To ask for the bill:
*   **Можна рахунок, будь ласка?** — Can I have the bill, please?
*   **Розрахуйте мене, будь ласка.** — Settle the bill, please.
---NEW---
To ask for the bill:
*   **Можна рахунок, будь ласка?** — Can I have the bill, please?
*   **Розрахуйте мене, будь ласка.** — Settle the bill, please.
*   **Можна окремий рахунок?** — Can I have a separate bill? (useful when paying for yourself in a group)
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===