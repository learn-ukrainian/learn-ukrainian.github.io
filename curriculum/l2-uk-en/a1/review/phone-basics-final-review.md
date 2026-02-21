Good, I have all the source files. Now let me conduct the deep adversarial review.

---

## Phase 9 Final QA Review: phone-basics (a1-41)

### Issues Found

**Issue 1: IPA — [w] used instead of [ʋ] for Ukrainian В (3 instances)**

Ukrainian В before a vowel is the labiodental approximant [ʋ], not the bilabial [w]. This is a systematic error across three transcriptions:

- **Line 60**: `[d͡zʋoˈnɪtɪ]` for дзвонити — should be `[d͡zʋoˈnɪtɪ]`
- **Line 134**: `[xʋɪˈlɪnkɐ]` for хвилинку — should be `[xʋɪˈlɪnkɐ]`
- **Line 217**: `[pɛrɛd͡zʋoˈnɪtɪ]` for передзвонити — should be `[pɛrɛd͡zʋoˈnɪtɪ]`

Note: the module correctly uses [ʋ] for телефонувати `[tɛlɛfonuˈʋɑtɪ]` on the same line 60, and for До зв'язку `[do zʋjɐzˈku]` on line 148 — so this is inconsistency, not ignorance.

**Issue 2: Pedagogically dangerous phrase taught as polite (Line 50)**

«Що Ви хотіли?» is presented as "Formal - to a service worker or stranger." This is terrible advice. In contemporary Ukrainian, this phrase sounds impatient, dismissive, and carries Soviet-era bureaucratic connotations. Teaching an A1 learner to say this to a stranger or service worker will make them sound rude. The correct polite formal alternative is «Чим можу допомогти?» (How can I help?).

**Issue 3: Plan-required phrase missing from content (Line 107)**

Both the plan (line 26: "Using simple phrases like «Чи можу я поговорити з...?»") and the meta (line 20: "Introduce polite contact phrases like «Чи можу я поговорити з...?»") explicitly require this phrase. The content at line 107 instead has «Чи є Анна?» — a different, simpler phrase.

Meanwhile, activity fill-in (activities line 52) tests `Чи ___ я поговорити з Анною?` (answer: можу), and true-false (activities line 259) asserts this phrase is correct. This breaks the PPP cycle: activities test a phrase the content never teaches.

**Issue 4: Header hierarchy error (Line 234)**

`# Підсумок` is an H1 header with a non-matching name. The meta outline specifies section 4 as "Продукція та підсумок" at H2 level, consistent with the other three sections (`## Вступ та етикет`, `## Презентація: Основні структури`, `## Практика: Життєві ситуації`). This will cause outline compliance audit failures.

**Issue 5: Dialogue short of meta requirement (Lines 116-118)**

The meta point 2 for section 2 requires "a short 4-line bilingual mini-dialogue." The existing dialogue has only 3 lines. Expanding it to 4 lines while incorporating the required «Чи можу я поговорити з...?» phrase fixes both issues simultaneously.

**Issue 6: Group-sort activity endorses removed phrase (Activities line 189)**

The group-sort categorizes «Що Ви хотіли?» under "Офіційний стиль (Formal)." After removing this phrase from the content (Issue 2), the activity would test untaught material AND implicitly endorse a rude phrase as appropriate formal speech. Must replace with the new phrase.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
**дзвонити** [d͡zʋoˈnɪtɪ]
---NEW---
**дзвонити** [d͡zʋoˈnɪtɪ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
**Зачекайте одну хвилинку.** [xʋɪˈlɪnkɐ]
---NEW---
**Зачекайте одну хвилинку.** [xʋɪˈlɪnkɐ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
**передзвонити** [pɛrɛd͡zʋoˈnɪtɪ]
---NEW---
**передзвонити** [pɛrɛd͡zʋoˈnɪtɪ]
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
*   **Що Ви хотіли?**
    *   What did you want? (Formal - to a service worker or stranger)
---NEW---
*   **Чим можу допомогти?**
    *   How can I help? (Formal/Professional - to a caller)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
*   **Чи є Анна?**
    *   Is Anna there?
---NEW---
*   **Чи можу я поговорити з Анною?**
    *   May I speak with Anna?
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
— **Добрий день, слухаю.** (Good afternoon, I am listening.)
— **Добрий день. Покличте директора.** (Good afternoon. Call the director.)
— **Так, зачекайте.** (Yes, wait.)
---NEW---
— **Добрий день, слухаю.** (Good afternoon, I am listening.)
— **Добрий день. Чи можу я поговорити з директором?** (Good afternoon. May I speak with the director?)
— **Так, зачекайте хвилинку.** (Yes, wait a moment.)
— **Дякую.** (Thank you.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/phone-basics.md
---OLD---
# Підсумок
---NEW---
## Продукція та підсумок
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/phone-basics.yaml
---OLD---
      items: ["Слухаю вас", "Зачекайте, будь ласка", "Вибачте, Ви хто?", "Повторіть, будь ласка", "До побачення", "Що Ви хотіли?"]
---NEW---
      items: ["Слухаю вас", "Зачекайте, будь ласка", "Вибачте, Ви хто?", "Повторіть, будь ласка", "До побачення", "Чим можу допомогти?"]
===FIX_END===

---

### Items Verified Clean

- **Russianisms**: None found (no кушати, получати, приймати участь, слідуючий)
- **Russian characters**: No ы, э, ё, ъ detected
- **Case agreement**: All checked — дативе (другу, мамі, Анні, Олегу), генітів (Анни, Олега, дверей, будинку), інструменталь (номером, директором) — all correct
- **Verb aspect**: Appropriate throughout; передзвонити (pf.) for single future acts, дзвонити (impf.) for habitual/ongoing
- **Other IPA**: [ɑˈlɔ], [ˈsluxɐju], [zɐt͡ʃɛˈkɑi̯te], [tɛlɛfonuˈʋɑtɪ], [do zʋjɐzˈku], [pomɪˈlɪtɪsʲ], [ˈzɑi̯nʲɐtɪi̯], [poʋʲiˈdɔmlennʲɐ], [pɛrɛˈdɑtɪ], [ˈnɔmɛr tɛlɛˈfɔnu] — all correct, tie bars present on affricates
- **Activity fill-in answers**: All produce grammatical sentences when inserted
- **Activity unjumble**: Words arrays contain all tokens in answers (punctuation omitted by convention — consistent)
- **True-false answers**: All factually correct
- **Quiz answers**: All correct options are genuinely correct; all distractors are genuinely wrong
- **Vocabulary file**: 20 items covering all plan-required (8) and plan-recommended (7) plus 5 contextual additions — no gaps
- **Factual claims**: No invented dates, statistics, or contested historical claims
- **LLM artifacts**: "incredibly" appears 3× in English scaffolding — minor fingerprint, not actionable at A1 where encouraging tone is expected
- **Plan compliance**: All 4 sections present (after header fix); all outline points covered (after phrase fix); all vocabulary hints used in prose; all 4 objectives map to self-check questions (lines 266-270)

---

### Verification Summary

| Check | Count |
|-------|-------|
| Content lines read | 272 |
| Activity items checked | 78 (8 match-up pairs + 16 T/F + 16 fill-in + 16 quiz + 6 unjumble + 12 group-sort + 8 match-up) |
| Ukrainian sentences verified | 45+ |
| IPA transcriptions checked | 13 |
| Issues found | 6 (all fixable) |
| Fixes applied | 8 blocks |

===VERDICT===
APPROVE
===END_VERDICT===