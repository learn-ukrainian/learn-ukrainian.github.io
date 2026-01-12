# A1 Naturalness Scan Report - COMPLETE
**Date:** 2026-01-12
**Protocol:** `claude_extensions/protocols/a1-naturalness-scan.md`
**Scope:** M01-M34 (34 modules)

---

## Executive Summary

**Total modules:** 34
**Prose activities found:** 25 modules (M10-M34)
**Flagged for naturalness issues:** 2 modules (M21, M22)
**Previously fixed:** 1 module (M25 - committed 2026-01-12)
**Checkpoints deferred:** 2 modules (M10, M20, M34 - different standards)

---

## Scan Results by Module

### M01-M09: No Prose Activities ✅
**Status:** PASS
**Activities:** Pure vocabulary drills (match-up, quiz, group-sort)
**Naturalness:** N/A - no connected prose

---

### M10: Checkpoint - First Contact ⏸️
**Status:** DEFERRED
**Activities:** 4× fill-in (demonstratives, conjugation I, conjugation II, negation)
**Sample sentences:**
```
Ця книга цікава.
Цей стіл новий.
Це вікно велике.
...
Я читаю книгу.
Ти читаєш газету.
Він читає журнал.
```
**Score:** 6-7/10
**Issue:** Disconnected drill sentences (expected for checkpoint format?)
**Decision:** Clarify checkpoint naturalness standards before fixing

---

### M11-M20: Single-Sentence Drills ✅
**Status:** PASS
**Activities:** Isolated grammar exercises (1 sentence per item)
**Sample:**
- M11: "Я бачу газету" (accusative drill)
- M12: "Я бачу колегу у магазині" (accusative animate)
- M13: "Я живу в Києві" (locative drill)
- M14: "Це моя книга" (possessive drill)
- M15: "Іди прямо, потім поверни направо" (directions)
- M16: "У мене немає часу" (genitive absence)
- M17: "У мене десять гривень" (numbers)
- M18: "Скільки коштує хліб?" (shopping)
- M19: "Столик на двох, будь ласка" (cafe dialogue)
- M20: Checkpoint (deferred)

**Score:** N/A - isolated sentences, no discourse flow expected
**Naturalness:** Appropriate for single-sentence grammar drills

---

### M21: Yesterday - Past Tense ⚠️ **FLAGGED**
**Status:** NEEDS FIX
**Topic:** Past tense (imperfective, gender agreement)
**Activity:** fill-in "Complete with Past Tense" (lines 45-118)

**Current sentences:**
```
1. Вчора він читав книгу.
2. Вона говорила по телефону вчора.
3. Ми говорили українською вчора.
4. Колись тут була школа.
5. Він слухав музику весь вечір.
6. Вона писала листи весь день.
7. Вони були в Україні минулого року.
8. Я пив каву вранці.
9. Давно він жив тут.
10. Позавчора вона дивилася фільм.
```

**Naturalness Analysis (Ukrainian mode):**
- ❌ **Random subject shifts:** він → вона → ми → (школа) → він → вона → вони → я → він → вона
- ❌ **No discourse connectors:** Missing а, але, потім, тому
- ❌ **Topic jumps:** book → phone → language → school building → music → letters → Ukraine trip → coffee → living → film
- ❌ **No context:** Who are these people? Why these actions?

**Score:** 4/10 - Incoherent, mechanically generated

**Vocabulary constraint:** M01-M21 = 891 words available
**Grammar constraint:** Past tense (M21), gender agreement, time expressions

**Fix approach:** Create family day narrative preserving past tense drill focus

---

### M22: Tomorrow - Future Tense ⚠️ **FLAGGED**
**Status:** NEEDS FIX
**Topic:** Future tense (compound буду + inf, planning expressions)
**Activities:** 2× fill-in

**Activity 1: "Future Tense Forms" (lines 45-104)**
```
1. Я буду читати цю книгу завтра.
2. Вона буде працювати до вечора.
3. Ми будемо вивчати українську разом.
4. Ти будеш готувати вечерю сьогодні?
5. Вони будуть грати у футбол завтра.
6. Ви будете дивитися цей фільм?
7. Він буде писати листа завтра.
8. Ти будеш слухати музику ввечері?
```

**Naturalness Analysis:**
- ❌ **Random subject shifts:** Я → Вона → Ми → Ти → Вони → Ви → Він → Ти
- ❌ **No connectors**
- ❌ **Topic jumps:** book → work → study → cook → football → film → letter → music

**Score:** 5/10

**Activity 2: "Planning Expressions" (lines 105-149)**
```
1. Я планую поїхати в Київ наступного місяця.
2. Вона мріє стати співачкою.
3. Він вирішив купити нову машину.
4. Ми сподіваємося побачити вас скоро.
5. Я постараюся прийти вчасно.
6. Вона обіцяє допомогти нам завтра.
```

**Naturalness Analysis:**
- ❌ **Random subject shifts:** Я → Вона → Він → Ми → Я → Вона
- ❌ **No connectors**
- ❌ **Topic jumps:** Kyiv trip → career dream → car purchase → visit → punctuality → help

**Score:** 6/10

**Vocabulary constraint:** M01-M22 = includes обіцяти, планувати, мріяти (introduced M22)
**Grammar constraint:** Future tense (compound), planning verbs

**Fix approach:** Create family plans narrative preserving future tense + planning verb drills

---

### M23-M24: Single-Sentence Drills ✅
**Status:** PASS
**Activities:** Time expressions, modal verbs (isolated sentences)
**Naturalness:** Appropriate for single-sentence format

---

### M25: My Daily Routine ✅ **PREVIOUSLY FIXED**
**Status:** FIXED (committed 2026-01-12)
**Commit:** `37c22336`
**Activities:** 2× fill-in (reflexive verbs, sequence words)
**Fix:** Added family context, discourse connectors (спочатку, потім, а)
**Score:** 4/10 → 8/10
**Validation:** ✅ Vocabulary compliant, ✅ Grammar preserved, ✅ Naturalness improved

---

### M26-M33: Single-Sentence Drills ✅
**Status:** PASS
**Activities:** Adjectives, colors, adverbs, weather, prepositions, health, family, holidays
**Sample:**
- M26: "Це новий будинок" (adjective agreement)
- M27: "У мене біла сорочка" (colors + clothing)
- M28: "Вона співає дуже гарно" (adverbs)
- M29: "Сьогодні світить сонце. Тепло." (weather)
- M30: "Де ти зараз? Я йду до магазину." (prepositions)
- M31: "У мене болить голова" (health)
- M32: "Моя мама дуже добра" (family)
- M33: "Ми святкуємо Новий рік вдома" (holidays)

**Naturalness:** Appropriate for single-sentence/dialogue format

---

### M34: Checkpoint - Final Review ⏸️
**Status:** DEFERRED
**Activities:** Comprehensive grammar review (all topics M01-33)
**Format:** Single-sentence drills across all topics
**Decision:** Clarify checkpoint standards

---

## Summary by Status

### ✅ PASS (30 modules)
- M01-M09: No prose activities
- M11-M20: Single-sentence drills (appropriate format)
- M23-M24: Single-sentence drills
- M25: Previously fixed and committed
- M26-M33: Single-sentence drills

### ⚠️ FLAGGED (2 modules)
- **M21:** Yesterday - Past Tense (score 4/10)
- **M22:** Tomorrow - Future Tense (score 5-6/10)

### ⏸️ DEFERRED (2 modules)
- M10: Checkpoint - First Contact
- M34: Checkpoint - Final Review

---

## Recommended Actions

### Immediate: Fix Flagged Modules (M21, M22)

**M21 Fix Strategy:**
- Create family day narrative using past tense
- Unify subjects: family members (я, брат, сестра, мама, тато)
- Add connectors: вчора ввечері, а, потім, увечері
- Preserve grammar focus: past tense conjugation drill
- Vocabulary: Validate all words against M01-M21 (891 words)

**M22 Fix Strategy:**
- Create family plans narrative using future tense
- Unify subjects: family context
- Add connectors: завтра, а, також, потім
- Preserve grammar focus: future tense + planning verbs
- Vocabulary: Validate against M01-M22 (includes new planning verbs)

### Later: Clarify Checkpoint Standards

**Questions:**
1. Should checkpoints have same naturalness standards as regular modules?
2. Are disconnected drill sentences acceptable for comprehensive grammar review?
3. Target score for checkpoints: 6/10 or 8/10?

---

## Constraint Validation

### Grammar Progression (A1 Curriculum Plan)

| Module Range | Allowed Grammar |
|--------------|-----------------|
| M01-M10 | Present tense, Nominative, basic Accusative |
| M11-M15 | + Accusative (full), Locative |
| M16-M20 | + Genitive (basic) |
| M21-M25 | + Past tense, Future tense |
| M26-M34 | + All A1 constructs |

**M21 constraint:** ✅ Past tense introduced
**M22 constraint:** ✅ Future tense introduced
**M25 constraint:** ✅ Reflexive verbs (M09), daily routine vocab

### Vocabulary Database

**Tool:** `/tmp/query_a1_vocab.py` (queries YAML files)
**Usage:**
```bash
.venv/bin/python /tmp/query_a1_vocab.py 21        # Get M01-M21 vocab
.venv/bin/python /tmp/query_a1_vocab.py check сестра  # Check word module
```

**Validation status:**
- M21: 891 words available (M01-M21 cumulative)
- M22: Adds planning verbs (обіцяти, планувати, мріяти)
- M25: ✅ Previously validated (committed)

---

## Next Steps

1. **Validate M21 fix** against M01-M21 vocabulary
2. **Validate M22 fix** against M01-M22 vocabulary
3. **Apply fixes** to flagged modules
4. **Decide on checkpoints** (M10, M34)
5. **Commit fixes** with detailed message
6. **Update protocol** if needed based on findings

---

## Scan Metadata

**Protocol used:** `claude_extensions/protocols/a1-naturalness-scan.md`
**Vocabulary tool:** `/tmp/query_a1_vocab.py`
**Grammar reference:** `docs/l2-uk-en/A1-CURRICULUM-PLAN.md` (Ukrainian State Standard 2024)
**Previously fixed:** M25 (commit `37c22336`)
**Token usage:** ~100k (full systematic scan)

