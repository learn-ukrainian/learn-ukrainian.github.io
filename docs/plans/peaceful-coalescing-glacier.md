# A1 Pedagogical Constraints Layer

## Context

After rebuilding A1 alphabet modules, we found severe pedagogical errors that no existing gate catches:
1. **Imperatives in lesson 1** — Слухайте!, Читайте!, Повторюйте! appear 46 modules before imperatives are taught (M47)
2. **Undecipherable Ukrainian** — words like Читайте use letters (Ч, Т, Й) that M1 students can't read (only know А, М, Л, У, Н, С)
3. **Untranslated metalanguage** — Ukrainian grammar terms without English equivalents

**Root cause**: `LEVEL_CONSTRAINTS` is per-level (same rules for all 64 A1 modules). `IMMERSION_RULES` is module-aware but only controls language balance %, not what grammar/letters are allowed. Nothing tells Gemini "this student only knows 6 letters and zero grammar."

**Fix**: Add a `PEDAGOGICAL_CONSTRAINTS` placeholder — module-sequence-aware rules that tell Gemini exactly what the student knows at each point. Follows the `IMMERSION_RULES` pattern (dict + selector function).

---

## Design

### Bands (7 bands, A1 only — A2+ uses existing LEVEL_CONSTRAINTS)

| Band | Modules | Key constraint |
|------|---------|----------------|
| `a1-m01` | M1 | 6 letters: А М Л У Н С. No grammar. |
| `a1-m02` | M2 | 14 letters: +К И Р Б В Д І О. No grammar. |
| `a1-m03` | M3 | 23 letters: +П Т Г Ґ Е З Ж Ш Х. No grammar. |
| `a1-m04` | M4 | Full alphabet. No grammar. |
| `a1-m05-10` | M5-10 | Full alphabet. No verbs. Gender/greetings/Це starting M7. |
| `a1-m11-14` | M11-14 | Adjectives, plurals. Still no verbs. |
| `a1-m15+` | M15+ | Verbs start. No imperatives until M47. Existing LEVEL_CONSTRAINTS handles rest. |

### Constraint content per band

Each band is a string containing:
- **DECODABILITY** (M1-3): which letters are known, what words are decodable vs enrichment-only
- **GRAMMAR BAN**: what grammatical forms are forbidden (imperatives, verb conjugation, cases)
- **METALANGUAGE RULE**: all Ukrainian terms need English equivalents

---

## Files Modified

| File | Change |
|------|--------|
| `scripts/pipeline_lib.py` | Add `PEDAGOGICAL_CONSTRAINTS` dict (~line 200), `get_pedagogical_constraints()` function (~line 365), add to `write_placeholders()`, add to `_critical_keys` |
| `claude_extensions/phases/gemini/phase-2-content.md` | Add `{PEDAGOGICAL_CONSTRAINTS}` section |
| Deploy via `npm run claude:deploy` | |

### 1. `scripts/pipeline_lib.py` — Constants and function

**Add after `LEVEL_CONSTRAINTS` (line 199):**

```python
PEDAGOGICAL_CONSTRAINTS: dict[str, str] = {
    "a1-m01": (
        "DECODABILITY (M1 — 6 known letters: А, М, Л, У, Н, С):\n"
        "- Words in reading drills MUST use ONLY these 6 letters (e.g., мама, сума, луна, мул, нам)\n"
        "- Words with unknown letters (кіт, вода, привіт) may appear ONLY as labelled vocabulary "
        "with immediate English translation: «Привіт!» (Hello!)\n"
        "- Video example words for the letter being taught (ананас for А) are fine — they are heard, not read\n\n"
        "GRAMMAR BAN (no verbs exist yet in the student's knowledge):\n"
        "- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED\n"
        "- NO verb conjugation of any kind (present, past, future)\n"
        "- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat after the video'\n"
        "- Allowed Ukrainian structures: bare nouns only (мама, сума, луна)\n\n"
        "METALANGUAGE:\n"
        "- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)', 'consonants (приголосні)'\n"
        "- Section headings may be bilingual: '## Голосні — Vowels'\n"
        "- NEVER write Ukrainian-only explanatory prose — the student cannot read it yet"
    ),
    "a1-m02": (
        "DECODABILITY (M2 — 14 known letters: А М Л У Н С + К И Р Б В Д І О):\n"
        "- Reading drills MUST use ONLY these 14 letters (e.g., банан, вода, молоко, кіно, рука, дім, бік, він)\n"
        "- Still unknown: П, Т, Г, Ґ, Е, З, Ж, Ш, Х, Й, Ч, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф\n"
        "- Words needing unknown letters require immediate English translation\n\n"
        "GRAMMAR BAN (no verbs exist yet):\n"
        "- NO imperative forms — ALL BANNED. Use English for instructions.\n"
        "- NO verb conjugation of any kind\n"
        "- Allowed: bare nouns, noun phrases using known letters\n\n"
        "METALANGUAGE:\n"
        "- All terminology English-first with Ukrainian in parentheses"
    ),
    "a1-m03": (
        "DECODABILITY (M3 — 23 known letters: previous 14 + П Т Г Ґ Е З Ж Ш Х):\n"
        "- Nearly all common text is readable now. Reading drills use these 23 letters.\n"
        "- Still unknown: Й, Ч, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф + digraphs ДЖ, ДЗ\n"
        "- Words needing unknown letters require English translation\n\n"
        "GRAMMAR BAN (no verbs exist yet):\n"
        "- NO imperative forms — BANNED. English for instructions.\n"
        "- NO verb conjugation\n"
        "- Allowed: bare nouns, noun phrases\n\n"
        "METALANGUAGE: English-first, Ukrainian in parentheses"
    ),
    "a1-m04": (
        "DECODABILITY (M4 — full 33-letter alphabet now complete):\n"
        "- No letter restrictions — all Ukrainian words are decodable after this module.\n\n"
        "GRAMMAR BAN (no verbs exist yet):\n"
        "- NO imperative forms — BANNED. English for instructions.\n"
        "- NO verb conjugation\n"
        "- Allowed: bare nouns, noun phrases, Це + noun (preview)\n\n"
        "METALANGUAGE: English-first, Ukrainian in parentheses"
    ),
    "a1-m05-10": (
        "SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):\n"
        "Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), "
        "greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).\n\n"
        "GRAMMAR STATUS:\n"
        "- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, "
        "memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)\n"
        "- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative\n"
        "- Use English for all classroom instructions\n\n"
        "METALANGUAGE: English-first, Ukrainian term in parentheses on first use"
    ),
    "a1-m11-14": (
        "SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):\n"
        "Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.\n"
        "Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).\n\n"
        "GRAMMAR STATUS:\n"
        "- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), "
        "Це/Я sentences, memorized phrases\n"
        "- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), "
        "cases beyond nominative (accusative starts M25)\n"
        "- Use English for classroom instructions\n\n"
        "METALANGUAGE: English-first, Ukrainian in parentheses"
    ),
    "a1-m15+": (
        "SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):\n"
        "Present tense verbs start at M15. Past tense at M36. Future at M37.\n\n"
        "KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) "
        "are NOT taught until M47 (imperative-and-requests). "
        "Before M47, use indirect requests or English for instructions.\n\n"
        "The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) "
        "apply in addition to this constraint."
    ),
}


def get_pedagogical_constraints(track: str, module_num: int) -> str:
    """Module-sequence-aware pedagogical constraints for A1."""
    base = track.split("-")[0]
    if base != "a1":
        return ""
    if module_num == 1:
        return PEDAGOGICAL_CONSTRAINTS["a1-m01"]
    elif module_num == 2:
        return PEDAGOGICAL_CONSTRAINTS["a1-m02"]
    elif module_num == 3:
        return PEDAGOGICAL_CONSTRAINTS["a1-m03"]
    elif module_num == 4:
        return PEDAGOGICAL_CONSTRAINTS["a1-m04"]
    elif module_num <= 10:
        return PEDAGOGICAL_CONSTRAINTS["a1-m05-10"]
    elif module_num <= 14:
        return PEDAGOGICAL_CONSTRAINTS["a1-m11-14"]
    else:
        return PEDAGOGICAL_CONSTRAINTS["a1-m15+"]
```

### 2. `scripts/pipeline_lib.py` — `write_placeholders()` changes

**Add to `_critical_keys` (line 1620):**
```python
_critical_keys = {"ITEM_MINIMUMS_TABLE", "ACTIVITY_MAX", "ACTIVITY_MIN",
                  "PRONUNCIATION_VIDEOS", "PEDAGOGICAL_CONSTRAINTS"}
```

**Add to placeholders dict (after `LEVEL_CONSTRAINTS` line ~1651):**
```python
"PEDAGOGICAL_CONSTRAINTS": get_pedagogical_constraints(ctx.track, ctx.module_num),
```

### 3. `claude_extensions/phases/gemini/phase-2-content.md` — Template

**Add after the `{PRONUNCIATION_VIDEOS}` line (line ~38), before the `---` separator:**

```markdown
## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints enforce what the student has actually learned so far.** Using letters, grammar forms, or vocabulary from future modules is a pedagogical error — the student literally cannot parse text with letters they haven't been taught. Violations will be caught in review.
```

When `{PEDAGOGICAL_CONSTRAINTS}` is empty (A2+), the section appears with no constraint text — harmless.

### 4. Deploy: `npm run claude:deploy`

---

## Verification

```bash
# 1. Unit check — selector returns correct band
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from pipeline_lib import get_pedagogical_constraints
for m in [1, 2, 3, 4, 5, 10, 11, 14, 15, 47, 64]:
    c = get_pedagogical_constraints('a1', m)
    print(f'M{m:02d}: {c[:60]}...' if c else f'M{m:02d}: (empty)')
# A2 should return empty
print(f'A2: {repr(get_pedagogical_constraints(\"a2\", 1))}')
"

# 2. Run existing tests
.venv/bin/python -m pytest tests/test_pipeline_v4.py -x -q

# 3. Verify placeholder in YAML for M1
.venv/bin/python -c "
import sys, yaml; sys.path.insert(0, 'scripts')
from pipeline_lib import get_pedagogical_constraints
text = get_pedagogical_constraints('a1', 1)
assert 'А, М, Л, У, Н, С' in text
assert 'Слухайте' in text
assert 'BANNED' in text
print('M1 constraints OK')
"

# 4. After rebuild: verify no imperatives in M1 output
# grep -i 'Слухайте\|Читайте\|Повторюйте\|Пишіть' curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
```
