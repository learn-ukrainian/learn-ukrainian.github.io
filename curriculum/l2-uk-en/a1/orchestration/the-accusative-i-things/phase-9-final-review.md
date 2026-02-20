Now let me do a systematic deep review. I'll check IPA accuracy, grammar, plan compliance, activity integrity, and LLM artifacts.

## Deep Adversarial Review: the-accusative-i-things (A1-11)

### Issues Found

**Issue 1: IPA Error — газета uses /h/ instead of /ɦ/ for Ukrainian г**
- **Location**: Content line 155
- **Text**: `**газета** [hɑˈzɛtɑ]`
- **Problem**: Ukrainian г is the voiced glottal fricative /ɦ/, not voiceless /h/. Every other г in the module uses ɦ correctly (книга [ˈknɪɦɑ], магніт [mɑɦˈnʲit], черга [ˈt͡ʃɛrɦu]), making this a clear oversight.
- **Fix**: [hɑˈzɛtɑ] → [ɦɑˈzɛtɑ]

**Issue 2: IPA Error — щітку transcribes щ as /ʃtʲ/ instead of /ʃt͡ʃ/**
- **Location**: Content line 358
- **Text**: `**щітку** [ˈʃtʲitku]`
- **Problem**: Ukrainian щ = /ʃt͡ʃ/ (two-element cluster with affricate), not /ʃtʲ/. The current transcription invents a palatalized /tʲ/ where an affricate /t͡ʃ/ should be.
- **Fix**: [ˈʃtʲitku] → [ˈʃt͡ʃitku]

**Issue 3: Scope Leak — animate noun in self-check for inanimate-only module**
- **Location**: Content line 428
- **Text**: `Why is "Я бачу мама" incorrect? (Hint: Think about the ending for feminine nouns).`
- **Problem**: "Мама" is an animate noun (a person). This module explicitly states: "We are starting with **inanimate objects** (things, not people or animals)." Module a1-12 ("The Accusative II: People") covers animate nouns. Using "мама" in a self-check question here undermines the inanimate scope and could confuse learners about what this lesson covers. While the feminine ending rule happens to be the same for animates, mixing scopes in assessment creates a pedagogical trap.
- **Fix**: Replace "мама" with inanimate feminine noun "лампа"

**Issue 4: Pedagogical Inconsistency — книжку vs книга in warm-up**
- **Location**: Content line 105
- **Text**: `**Я бачу книжку.** (I see a book.)`
- **Problem**: The entire module teaches книга → книгу (10+ occurrences), yet the opening warm-up introduces the diminutive "книжка → книжку" without explanation. A beginner seeing "книжку" first, then "книгу" throughout the lesson, will wonder which is correct or whether these are different words. At A1, this distinction is confusing.
- **Fix**: Change to "книгу" for consistency with the rest of the module.

**Issue 5: Missing IPA on first occurrence of new vocabulary in Cultural section**
- **Location**: Content lines 373-376
- **Text**: "диню", "грушу", "капусту", "сметану" introduced without IPA
- **Problem**: These are new vocabulary items appearing for the first time in the module. Module convention provides IPA on first occurrence (consistently done elsewhere). The Green Team review also flagged this.
- **Fix**: Add IPA for each noun.

**Issue 6 (Minor/Noted): Plan collocations absent from content**
- The plan specifies "мати рацію", "брати участь", "хотіти їсти" as high-frequency collocations to use. None appear in the prose. The module chose concrete physical objects instead, which is arguably better for A1 inanimate scope. Noting but not fixing — this is a defensible pedagogical divergence from the plan hint (not the plan outline).

### Activity Verification

- **group-sort** (16 items): All categorizations correct. ✓
- **match-up "Знайдіть пару"** (8 pairs): All nom→acc transformations correct. ✓
- **quiz "Оберіть правильне закінчення"** (10 items): All correct answers verified. ✓
- **fill-in "Заповніть пропуски"** (8 items): All answers produce grammatical sentences. ✓
- **fill-in "Список покупок"** (8 items): All answers correct. ✓
- **unjumble "Складіть речення"** (8 items): All word arrays match answers exactly. ✓
- **unjumble "У магазині"** (8 items): All word arrays match answers exactly. ✓
- **match-up "Дія і предмет"** (8 pairs): All pairings logical and grammatical. ✓
- **quiz "Знайдіть помилку"** (10 items): All correct answers verified. ✓
- **fill-in "Перевірка"** (8 items): All answers correct. ✓
- **Total**: 92 items across 10 activities. No broken items found.
- **YAML structure**: Bare list at root. ✓
- **No Russian characters** (ы, э, ё, ъ): Clean. ✓
- **No Russianisms**: Clean. ✓
- **No LLM artifacts**: Clean — warm but professional tone, no purple prose. ✓

### Vocabulary file
- 20 entries, all correctly structured with IPA, lemma, pos, translation. ✓
- IPA in vocab file uses ɦ correctly for газета: not present in vocab file (газета is not in vocab). Vocab entries checked: all IPA correct. ✓

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
*   **газета** [hɑˈzɛtɑ] (newspaper) → Я бачу **газету**.
---NEW---
*   **газета** [ɦɑˈzɛtɑ] (newspaper) → Я бачу **газету**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
*   ... **щітку** [ˈʃtʲitku] (toothbrush) — *feminine, change!*
---NEW---
*   ... **щітку** [ˈʃt͡ʃitku] (toothbrush) — *feminine, change!*
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
4.  Why is "Я бачу мама" incorrect? (Hint: Think about the ending for feminine nouns).
---NEW---
4.  Why is "Я бачу лампа" incorrect? (Hint: Think about the ending for feminine nouns).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
**Я бачу книжку.** (I see a book.) **Я бачу вікно.** (I see a window.)
---NEW---
**Я бачу книгу.** (I see a book.) **Я бачу вікно.** (I see a window.)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
At the bazaar, you don't just take things; you ask to see them.
*   **Покажіть, будь ласка, цю диню.** (Please show me this melon.)
*   **Дайте, будь ласка, грушу.** (Give me the pear, please.)
*   **Зважте, будь ласка, капусту.** (Please weigh the cabbage.)
*   **Я хочу спробувати сметану.** (I want to taste the sour cream.)
---NEW---
At the bazaar, you don't just take things; you ask to see them.
*   **Покажіть, будь ласка, цю диню** [ˈdɪnʲu]. (Please show me this melon.)
*   **Дайте, будь ласка, грушу** [ˈɦruʃu]. (Give me the pear, please.)
*   **Зважте, будь ласка, капусту** [kɑˈpustu]. (Please weigh the cabbage.)
*   **Я хочу спробувати сметану** [smɛˈtɑnu]. (I want to taste the sour cream.)
===FIX_END===

===VERDICT===
APPROVE
===END_VERDICT===

**Summary**: Strong module. The "Safe Harbor" metaphor is pedagogically effective, the cultural hooks are authentic, and the 92 activity items provide excellent drilling coverage. Five fixes applied: two IPA errors (г→ɦ for газета, щ→ʃt͡ʃ for щітку), one scope leak (animate "мама" replaced with inanimate "лампа" in self-check), one warm-up consistency fix (книжку→книгу), and missing IPA for four new nouns in the Cultural section. All fixes are surgical — no structural changes needed.