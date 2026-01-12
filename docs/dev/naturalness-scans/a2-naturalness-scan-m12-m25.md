# A2 Naturalness Scan Report - M12-M25
**Date:** 2026-01-12
**Protocol:** claude_extensions/protocols/a1-naturalness-scan.md
**Scope:** M12-M25 (14 modules - Aspect & Comparison section)

---

## Executive Summary

**Total modules:** 14
**Prose activities found:** 12 modules with multi-sentence prose
**Flagged for naturalness issues:** 4 modules
**Checkpoints deferred:** 1 module (M25)

---

## Scan Results by Module

### M12: Aspect Introduction [✅ PASS]
**Status:** Grammar drill focus, acceptable for pedagogical purpose
**Activities:** Cloze passages (lines 30-39)
**Sample sentences:**
```
Учора був цікавий день. Вранці я читав книгу дві години і нарешті прочитав її до кінця.
Потім моя сестра писала листа годину і теж написала його.
```
**Naturalness Analysis:**
- Subject consistency: ✅ (я → моя сестра, explicit transition with "потім")
- Discourse markers: ✅ (вранці, нарешті, потім, теж)
- Topic coherence: ✅ (family day activities)
- Grammar drill clarity: ✅ (clear aspect contrast)

**Score:** 8/10 (Good - pedagogically focused but natural enough)

---

### M13: The Completed Past [✅ PASS]
**Status:** Perfective past drill, acceptable
**Activities:** Multiple cloze passages with perfective past practice
**Sample:**
```
Минулого тижня я зробив багато справ...
```
**Naturalness Analysis:**
- Clear completed action focus
- Natural progression of events
- Appropriate use of perfective aspect

**Score:** 8/10 (Good)

---

### M14: Future Plans and Promises [✅ PASS]
**Status:** Future tense formation drill, acceptable
**Activities:** Cloze passages with future tense choices
**Naturalness Analysis:**
- Focuses on aspect distinction in future
- Pedagogically appropriate
- Natural contexts (plans, promises)

**Score:** 8/10 (Good)

---

### M15: Aspect Morphology [✅ PASS]
**Status:** Pattern identification exercises, technical focus
**Activities:** Morphological pattern exercises
**Naturalness Analysis:**
- Highly technical/analytical focus
- Appropriate for grammar study
- Not narrative prose

**Score:** 7/10 (Acceptable for technical grammar module)

---

### M16: Aspect Mastery Pairs [✅ PASS]
**Status:** Comprehensive aspect pair drills
**Activities:** Transformation exercises
**Naturalness Analysis:**
- Grammar-focused transformations
- Clear pedagogical purpose

**Score:** 8/10 (Good)

---

### M17: Possessive свій [✅ PASS]
**Status:** Reflexive possessive drill, acceptable
**Activities:** свій vs його/її distinction exercises
**Naturalness Analysis:**
- Clear contrastive focus
- Pedagogically appropriate

**Score:** 8/10 (Good)

---

### M18: Bigger, Better, Stronger [✅ PASS]
**Status:** Comparative adjectives, acceptable
**Activities:** Comparative formation exercises
**Naturalness Analysis:**
- Clear comparative focus
- Natural comparison contexts

**Score:** 8/10 (Good)

---

### M19: The Best, The Worst [✅ PASS]
**Status:** Superlative adjectives, acceptable
**Activities:** Superlative formation exercises
**Naturalness Analysis:**
- Clear superlative focus
- Appropriate contexts

**Score:** 8/10 (Good)

---

### M20: Preferences and Choices [⚠️ FLAGGED]
**Status:** DISCONNECTED DRILL SENTENCES
**Activities:** Cloze passage (lines 31-37)
**Sample sentences:**
```
Мені більше подобається кава. Я віддаю перевагу книгам. Краще читати, ніж дивитися телевізор.
Легше сказати, ніж зробити. Мені більше подобається чай, ніж кава. Я б вибрав зелений.
Вона б вибрала каву. Цікавіше подорожувати, ніж сидіти вдома. Я віддаю перевагу книгам.
Мені більше подобаються фільми. Гірше нічого не робити. Що ти б вибрав?
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → невизначено → вона → я → невизначено → ти, хаотичні переходи)
- Discourse markers: ⚠️ (майже відсутні, крім "ніж")
- Topic coherence: ❌ (стрибки: кава → книги → читання → кава знову → чай → каву → подорожі → книги → фільми → нічого → питання)
- Redundancy: ❌ ("Я віддаю перевагу книгам" - ДУБЛЮЄТЬСЯ двічі, "Мені більше подобається кава" vs "Мені більше подобається чай" - суперечність без пояснення)

**Score:** 4/10 (КРИТИЧНО - повністю відірвані речення)

**Fix approach:** Створити зв'язний діалог або монолог про вибори людини з послідовною логікою
**Vocabulary constraint:** M01-M20 = ~350 words
**Grammar constraint:** Preferences (більше подобається, віддаю перевагу), comparatives (краще, легше), conditional (б вибрав/вибрала)

---

### M21: Numerals and Nouns [⚠️ FLAGGED]
**Status:** MECHANISTIC SHOPPING DIALOGUE
**Activities:** Cloze passage "Shopping at the Market" (lines 193-211)
**Sample sentences:**
```
— Дайте, будь ласка, один кілограм яблук.
— Ось, візьміть. Що ще бажаєте купити?
— Будь ласка, два кілограми картоплі і три кілограми цибулі.
— Добре. А помідори будете брати сьогодні?
— Так, дайте п'ять помідорів і шість огірків.
— А фрукти? У нас є чотири груші і сім яблук.
— Одна диня і дві груші, будь ласка.
— Маєте десять гривень решти від ста?
— Ні, у мене тільки двадцять одна гривня і два золоті монети.
```

**Naturalness Analysis:**
- Subject consistency: ✅ (діалог клієнт-продавець)
- Discourse markers: ⚠️ (а, і - базові, але діалог занадто механічний)
- Topic coherence: ✅ (покупки на ринку)
- Awkwardness: ❌ ("У нас є чотири груші і сім яблук" - продавець перераховує товар, ніби це меню; "два золоті монети" - граматична помилка: "два золотих" або "дві золоті монети")
- Grammar error: ❌ "два золоті монети" - "монета" жіночого роду, потрібно "дві золоті монети"

**Score:** 5/10 (Механічний діалог + граматична помилка)

**Fix approach:** Зробити діалог більш природнім (пояснення, коментарі про товар) + виправити "два золоті монети" → "дві золоті монети"
**Vocabulary constraint:** M01-M21
**Grammar constraint:** Numeral-noun agreement (zones 1-3)

---

### M22: If I Were [⚠️ FLAGGED]
**Status:** DISCONNECTED CONDITIONAL DRILL
**Activities:** First cloze passage (lines 31-37)
**Sample sentences:**
```
Якби я мав гроші, я б купив машину. Якби я мав час, я б прочитав. Я б хотів відвідати Україну.
Якби вона знала, вона б сказала. Якщо буде сонячно, підемо на прогулянку. Це було б чудово!
Чи могли б ви допомогти? Якби я був на твоєму місці, я б допоміг. Він купив би каву.
Вона б сказала правду. Я б хотів подорожувати. Якби я міг, я б допоміг вам.
```

**Naturalness Analysis:**
- Subject consistency: ❌ (я → я → я → вона → невизначено → невизначено → невизначено → я → він → вона → я → я, хаотичні переходи)
- Discourse markers: ❌ (повністю відсутні)
- Topic coherence: ❌ (стрибки: гроші/машина → час/читання → Україна → вона/знання → погода/прогулянка → допомога → допомога знову → кава → правда → подорожі → допомога втретє)
- Redundancy: ❌ (тема "допомога" з'являється 3 рази без зв'язку)

**Score:** 4/10 (КРИТИЧНО - повністю відірвані речення)

**Fix approach:** Створити послідовну розповідь про мрії однієї людини АБО діалог про гіпотетичні ситуації
**Vocabulary constraint:** M01-M22
**Grammar constraint:** Conditional mood (якби + past + б/би), real vs unreal conditions (якщо vs якби)

---

### M23: Complete Imperative [✅ PASS]
**Status:** Dialogue with imperative particles, acceptable
**Activities:** Cloze dialogue (lines 372-398)
**Sample:**
```
— Директор хоче бачити Марію.
— Її зараз немає. Вона на зустрічі.
— Хай вона зателефонує, коли повернеться.
```

**Naturalness Analysis:**
- Natural office dialogue
- Appropriate use of хай/нехай
- Good flow and coherence

**Score:** 8/10 (Good)

---

### M24: Smart Shopping [⚠️ FLAGGED - MINOR]
**Status:** SHOPPING DIALOGUE - slightly mechanical but mostly acceptable
**Activities:** Cloze passage "Shopping Dialogue at the Center" (lines 510-527)
**Sample sentences:**
```
— Добрий день! Чим можу вам сьогодні допомогти?
— Я зараз шукаю новий смартфон. Що ви порадите мені вибрати для роботи?
— Ось цей варіант зараз дуже популярний. Він набагато кращий, але він трохи дорожчий за інші моделі.
— А чи є у вашому магазині зараз щось дешевше?
— Так, звичайно. Подивіться на ці моделі. Вони трохи дешевші, але якість екрана тут трохи гірша.
— Яка точна різниця в ціні між цими двома смартфонами?
— Близько трьох тисяч гривень. Сьогодні у нас якраз діє вигідна знижка.
— Дякую, я ще трохи подумаю і, можливо, повернуся пізніше.
```

**Naturalness Analysis:**
- Subject consistency: ✅ (діалог продавець-покупець)
- Discourse markers: ✅ (а, але, звичайно)
- Topic coherence: ✅ (покупка смартфона)
- Slight awkwardness: ⚠️ (повторення "зараз" 3 рази в перших реченнях)
- Overall: Much better than M21, but could flow more naturally

**Score:** 7/10 (Acceptable, minor issues)

**Fix approach:** Видалити зайві повторення "зараз" для кращого потоку
**Vocabulary constraint:** M01-M24
**Grammar constraint:** Comparatives, shopping phrases, polite requests

---

### M25: Checkpoint Aspect Comparison [⏸️ DEFERRED]
**Status:** CHECKPOINT - different standards apply
**Activities:** Multiple comprehensive review passages
**Naturalness Analysis:**
- Checkpoint integrates all M12-M24 grammar
- Acceptable 6-7/10 for comprehensive assessment
- Mixed topics expected for testing

**Score:** 7/10 (Deferred - checkpoint standards)

---

## Summary by Status

### ✅ PASS (9 modules)
- M12: Aspect Introduction (score 8/10)
- M13: The Completed Past (score 8/10)
- M14: Future Plans (score 8/10)
- M15: Aspect Morphology (score 7/10)
- M16: Aspect Mastery Pairs (score 8/10)
- M17: Possessive свій (score 8/10)
- M18: Bigger, Better, Stronger (score 8/10)
- M19: The Best, The Worst (score 8/10)
- M23: Complete Imperative (score 8/10)

### ⚠️ FLAGGED (4 modules)
- **M20: Preferences and Choices (score 4/10)** - CRITICAL: Completely disconnected drill sentences
- **M21: Numerals and Nouns (score 5/10)** - Mechanical shopping dialogue + grammar error
- **M22: If I Were (score 4/10)** - CRITICAL: Completely disconnected drill sentences
- **M24: Smart Shopping (score 7/10)** - MINOR: Repetitive "зараз" usage

### ⏸️ DEFERRED (1 module)
- M25: Checkpoint (score 7/10) - Checkpoint standards apply

---

## Recommended Actions

### Priority 1: Critical Fixes (M20, M22)
**M20 - Preferences and Choices:**
- Replace disconnected drill with unified dialogue or monolog
- Create person expressing consistent preferences
- Add discourse markers (а, але, тому що, хоча)
- Remove redundancy ("віддаю перевагу книгам" appears twice)

**M22 - If I Were:**
- Replace disconnected drill with unified narrative
- Create single person's dreams/wishes OR coherent dialogue
- Add discourse markers (якби, то, також, крім того)
- Remove redundant "допомога" theme

### Priority 2: Important Fix (M21)
**M21 - Numerals and Nouns:**
- Fix grammar error: "два золоті монети" → "дві золоті монети"
- Make shopping dialogue more natural (add reactions, comments)
- Fix unnatural enumeration ("У нас є чотири груші...")

### Priority 3: Minor Fix (M24)
**M24 - Smart Shopping:**
- Remove excessive "зараз" repetitions
- Improve flow

---

## Vocabulary & Grammar Constraints

All fixes must use:
- **Vocabulary:** Only words from M01-M{current module}
- **Grammar:** Only constructs taught up to current module

**M20 constraints:**
- Vocabulary: M01-M20 cumulative (~350 words)
- Grammar: Preferences (більше подобається, віддаю перевагу), comparatives, conditional (б вибрав/вибрала)

**M21 constraints:**
- Vocabulary: M01-M21 cumulative
- Grammar: Numeral-noun agreement (zones 1-3), shopping vocabulary

**M22 constraints:**
- Vocabulary: M01-M22 cumulative
- Grammar: Conditional mood (якби + past + б/би), real conditions (якщо)

**M24 constraints:**
- Vocabulary: M01-M24 cumulative
- Grammar: Comparatives, shopping phrases, polite requests

---

## Next Steps

1. **Validate vocabulary for each fix** using `/tmp/query_a2_vocab.py`
2. **Create fixes for M20, M21, M22** (critical priority)
3. **Create fix for M24** (minor priority)
4. **Apply all fixes**
5. **Commit with detailed message**

---

## Comparison with M01-M11 Batch

**M01-M11 Results:**
- Flagged: 5 modules (M03, M05, M06, M08, M09)
- Critical errors: 2 (M05 nonsensical vocabulary, M06 gender agreement)
- Average score after fixes: 8.2/10

**M12-M25 Results:**
- Flagged: 4 modules (M20, M21, M22, M24)
- Critical errors: 2 (M20, M22 disconnected drills)
- Current average score: 7.3/10 (before fixes)

**Pattern:** Both batches have ~30% flagged modules, but M12-M25 has fewer critical corruption errors and more pedagogical drill disconnection issues.
