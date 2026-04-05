# Plan Review: checkpoint-foundations

**Track:** a2 | **Sequence:** 7 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1500, Config: 1500 (checkpoint) |
| section_budgets | PASS | Sum = 1500 (400+500+600) vs target 1500 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | version: '1.0' |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Aspect recognition (доконаний/недоконаний) | YES | A2 verbs (lines 1341-1359) | A2 | PASS |
| Genitive singular/plural production | YES | A2 cases (lines 1265-1285) | A2 | PASS |
| Aspect selection in context | YES | A2 verbs (lines 1341-1359) | A2 | PASS |

Review/checkpoint modules consolidate previously taught grammar. All topics are within A2 scope.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Aspect recognition exercise | Авраменко Gr7 p54, Litvinova Gr7 p35 | YES | Textbooks use similar exercise types: "Визначте вид запропонованих дієслів" |
| Genitive form production | Заболотний Gr6, Litvinova Gr6 | YES | "У мене немає (брат) -> У мене немає брата" — standard drill format |
| Aspect pair matching | Заболотний Gr7, Litvinova Gr7 p35 | YES | "Утворіть, де можливо, видові пари" — standard exercise type |

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| вправа | OK | |
| перевірка | OK | |
| контрольна точка | NOT FOUND | "контрольна точка" as a compound is not in VESUM. "контрольна" (adj) and "точка" (noun) exist separately. |
| завдання | OK | |
| текст | OK | |
| речення | OK | |
| відповідь | OK | |
| правильний | OK | |
| варіант | OK | |
| обрати | OK | |
| написати | OK | |

## Issues Found

### CRITICAL (must fix before build)
1. **Missing required fields**: Plan lacks `persona`, `grammar`, and `register` fields.

### HIGH (should fix before build)
1. **Dialogue situation is artificial**: A tutor quizzing a student ("Утвори родовий від 'книга'. Книги!") is essentially a grammar exam scenario. The MEMORY.md and Tier 1 guidelines explicitly warn against artificial interrogation dialogues. A checkpoint can still have a natural scenario — e.g., friends helping each other study, or a student reviewing notes before a test where the conversation naturally involves using genitive and aspect.
2. **References are weak**: Same issue as M06 — only "Заболотний Grade 5-6, Повторення вивченого" with no section numbers. A checkpoint reviewing aspect and genitive should reference the specific textbook sections being consolidated.

### MEDIUM (fix if possible)
1. **"контрольна точка" is a calque**: While "контрольна точка" is understood in Ukrainian, it may be a calque from English "checkpoint." Consider using "перевірка знань" or simply "контрольна" (which is the standard Ukrainian school term for a test/assessment). The subtitle already uses "Перевірка знань" which is more natural.
2. **Content outline reads like an exercise list, not a module plan**: Sections 1-3 are literally "Exercise 1, Exercise 2..." This is a checkpoint, so exercises are expected, but the plan should indicate what connective prose/explanation surrounds these exercises. Even checkpoints need warm-up text, transitions, and celebration of progress (per Tier 1 guidelines).
3. **Activity hint type "match-up" with focus "Short written response"**: This is a mismatch — a match-up activity shouldn't be "short written response." Written production should be a different activity type.

### LOW (informational)
1. **Error-correction activity is a good addition**: This type is excellent for checkpoints and tests real understanding (not just recognition). Well chosen.
2. **Writing prompt (Exercise 7) is appropriate**: "Напишіть про свої плани на вихідні" naturally requires both aspect and genitive usage.

## Suggested Fixes

**Fix 1 — Add missing fields:**
```yaml
persona: friendly-tutor
grammar:
  - aspect_recognition
  - aspect_selection
  - genitive_singular_production
  - genitive_plural_production
register: informal-educational
```

**Fix 2 — Replace artificial dialogue:**
```yaml
# OLD
dialogue_situations:
  - setting: 'Language test preparation — a tutor quizzes the student...'
    speakers:
      - Репетитор (tutor)
      - Студент
# NEW
dialogue_situations:
  - setting: 'Friends studying together before a Ukrainian class — quizzing each
      other from notes, one struggles with genitive plural, the other explains.
      Скільки у тебе братів? Двох братів... ні, два брати! Ох, я завжди плутаю.'
    speakers:
      - Олена (студентка)
      - Марко (студент)
    motivation: 'Natural peer study scenario — genitive and aspect review through
      friendly conversation, not interrogation'
```

**Fix 3 — Improve references:**
```yaml
references:
  - title: Заболотний Grade 6, §30-31
    notes: Родовий відмінок іменників
  - title: Заболотний Grade 7, §25-26
    notes: Вид дієслова
  - title: Авраменко Grade 7, §25
    notes: Вид дієслова
```

**Fix 4 — Fix activity type mismatch:**
```yaml
# OLD
- type: match-up
  focus: Short written response
  items: 8
# NEW
- type: fill-in
  focus: Short written responses using genitive and aspect
  items: 6
```
