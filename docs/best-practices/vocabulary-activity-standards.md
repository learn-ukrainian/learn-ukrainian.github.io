# Vocabulary & Activity Standards

> **Scope:** YAML format, allowed/forbidden types, item counts.
> Full schema reference: `docs/ACTIVITY-YAML-REFERENCE.md`
> Schema files: `schemas/activities-{level}.schema.json`

---

## Activity YAML Format

### Root structure: bare list (CRITICAL)

```yaml
# ✅ CORRECT — bare list at root
- type: quiz
  title: Тест з теми

- type: reading
  title: Читання тексту
```

```yaml
# ❌ WRONG — dictionary wrapper causes schema validation failure
activities:
  - type: quiz
```

### Property names must match schema exactly

| Activity type | Correct property | Wrong property |
|--------------|-----------------|----------------|
| `mark-the-words` | `text` + `answers` array | `passage` + `correct_words` |
| `fill-in` | `sentence` | `text`, `prompt` |
| `unjumble` | `words` array + `answer` | `jumbled`, `scrambled` |
| `cloze` | `passage` | `text` |
| `true-false` | `statement` | `sentence`, `text` |

---

## Allowed Activity Types by Track

### Seminar tracks (b2-hist, c1-bio, c1-hist, lit, oes, ruth)

**Allowed:**
- `reading` — text comprehension (REQUIRED)
- `essay-response` — open-ended written response (REQUIRED)
- `critical-analysis` — evaluate a claim or source (REQUIRED)
- `comparative-study` — compare two topics/periods/figures
- `authorial-intent` — analyze why something was written/created
- `quiz` — factual recall
- `true-false` — statement evaluation

**Forbidden:**
- `match-up`, `fill-in`, `cloze`, `group-sort`, `unjumble`, `anagram`, `mark-the-words`

**Why:** Seminar tracks are CBI (Content-Based Instruction). Activities must require comprehension and analysis, not pattern matching.

### Core tracks (a1, a2, b1, b2, c1, c2, b2-pro, c1-pro)

All activity types allowed. Required types vary by level — check `scripts/audit/config.py`.

---

## Activity Counts by Track

| Track | Min | Max | Required types |
|-------|-----|-----|----------------|
| A1 | 8 | 15 | quiz, mark-the-words |
| A2 | 10 | 15 | quiz, fill-in |
| B1 | 8 | 15 | quiz, fill-in, match-up |
| B2 | 10 | 15 | quiz, match-up, cloze |
| C1 | 12 | 18 | all core types |
| C2 | 16 | 20 | all core types |
| B2-HIST | 3 | 9 | reading, essay-response, critical-analysis |
| C1-BIO | 3 | 9 | reading, essay-response, critical-analysis |
| C1-HIST | 3 | 9 | reading, essay-response, critical-analysis |
| LIT | 3 | 9 | reading, essay-response, critical-analysis |

---

## Activity Quality Standards

### Each activity must have:
- `type` — from allowed list for the track
- `title` — descriptive Ukrainian title
- `instruction` — clear Ukrainian instruction
- Content field (varies by type)

### Seminar activity depth
Activities must require comprehension and critical thinking, not recall:

```yaml
# ✅ Good — requires analysis
- type: critical-analysis
  title: Аналіз джерела
  instruction: Прочитайте цитату і оцініть упередженість автора.
  text: "Поляни суть мудрі і тямущі..." (Нестор Літописець)
  prompts:
    - Чому літописець зображує полян позитивно?
    - Які факти суперечать цьому опису?

# ❌ Bad — only recall
- type: quiz
  title: Хто такі поляни?
  items:
    - question: Де жили поляни?
      answer: Біля Києва
```

---

## YAML Quoting Rules

Strings with colons, quotes, or special characters must be quoted:

```yaml
# ❌ Breaks YAML
- Культурна спадщина: "Дід Панас" як бренд добра

# ✅ Single quotes wrap everything
- 'Культурна спадщина: "Дід Панас" як бренд добра'

# ✅ Or escape inner quotes in double-quoted string
- "Культурна спадщина: \"Дід Панас\" як бренд добра"
```

Apostrophes in Ukrainian (пам'ять) inside single-quoted strings need doubling:
```yaml
- 'Пам''ять народу'  # ✅ doubled apostrophe
- 'Пам'ять народу'   # ❌ breaks string
```

---

## Vocabulary YAML Format

```yaml
# ✅ Correct vocabulary entry
- word: казка
  translation: fairy tale
  pos: noun
  gender: feminine
  example: Дід розповідав казку дітям.
  note: Common in children's literature

# Minimal required fields
- word: телеведучий
  translation: TV presenter
  pos: noun
```

### Vocabulary counts

| Track | Min words | Target |
|-------|-----------|--------|
| A1 | 20 | 25 |
| A2 | 25 | 30 |
| B1+ | 25 | 30 |
| Seminar | 25 | 30-40 |

---

## mark-the-words Format

```yaml
# ✅ Correct — plain text + explicit answers array
- type: mark-the-words
  title: Знайдіть іменники
  instruction: Клацніть на всі іменники.
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце

# ❌ Wrong — asterisk format (deprecated)
- type: mark-the-words
  text: Гарний *день* приніс *радість* у *серце*.
  answers: []
```

---

## Validation

Always validate activity YAML before committing:

```bash
# Validate via audit
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{file}.md

# Schema validation only
.venv/bin/python scripts/validate_activities.py {activities_path}
```

Common errors caught: wrong root structure, wrong property names, forbidden activity types, items below minimum count.
