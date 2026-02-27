# Euphony Engine — Implementation Plan

**Issue:** #593
**Status:** APPROVED — ready for implementation
**Proposed by:** Gemini (Yellow Team), scoped by Claude (Blue Team)

---

## Decisions

| # | Question | Decision |
|---|----------|----------|
| Q1 | Severity | `warning` for all rules (non-blocking) |
| Q2 | Scope | Prose `.md` files only — no activity YAML |
| Q3 | Auto-fix | No auto-fix. Violations surface in audit report and fix prompt; Gemini corrects on next loop. Plugs into existing fix loop for free. |
| Q4 | Prompt update | Yes — add euphony rules to `phase-2-content.md` so Gemini produces euphonic prose from the start (prevention, not just detection). |

---

## What We're Building

A deterministic audit check (`scripts/audit/checks/euphony.py`) that scans Ukrainian prose and flags violations of милозвучність (euphony) rules. These are the sound-smoothing alternations that make Ukrainian melodic — rules LLMs know grammatically but routinely violate in practice.

**It fits exactly here in the audit pipeline:**
```
content_purity → imperial_terminology → euphony → prose_quality
```

---

## Ukrainian Euphony Rules in Scope

### Rule 1: Conjunction і/й

**Core principle:** `й` can ONLY appear between two vowels. In all other positions, use `і`.

| Context | Rule | Example (bad → good) |
|---------|------|----------------------|
| Between vowels (vowel + і + vowel) | і → й | `вона і Олена` → `вона й Олена` |
| After consonant (consonant + й + anything) | й → і | `він й Олена` → `він і Олена` |
| Before consonant (vowel + й + consonant) | й → і | `вона й працює` → `вона і працює` |
| After consonant, before vowel | і stays і | `він і Олена` ✓ (correct as-is) |
| After consonant, before consonant | і stays і | `він і працює` ✓ (correct as-is) |

**Detection targets:**
- `[vowel-ending word] і [vowel-starting word]` → should be `й` (flag і)
- `[consonant-ending word] й [any word]` → should be `і` (flag й)
- `[any word] й [consonant-starting word]` → should be `і` (flag й)

### Rule 2: Preposition у/в

| Context | Rule | Example (bad → good) |
|---------|------|----------------------|
| Before vowel-starting word | у → в | `у Одесі` → `в Одесі` |
| Before consonant cluster (2+ consonants) | в → у | `в зграї` → `у зграї` |
| Before word starting with в or ф | в → у | `в вікні` → `у вікні` |

**Detection targets:**
- `у [vowel-word]` → `в [vowel-word]`
- `в [consonant-cluster-word]` → `у [consonant-cluster-word]`
- `в в[...]` / `в ф[...]` → `у в[...]` / `у ф[...]`

### Rule 3: Preposition з/із/зі

| Context | Rule | Example (bad → good) |
|---------|------|----------------------|
| Before word starting with з or с | з → із | `з Сонцем` → `із Сонцем` |
| Before consonant cluster starting with зб, зд, зг, зм, зн, зр, зв, зл | з → із or зі | `з зброєю` → `із зброєю` |
| Otherwise | з (standard) | `з книгою` ✓ |

### Rule 4: Conjunction та/й variety

| Context | Rule | Example (bad → good) |
|---------|------|----------------------|
| Same conjunction (`і` or `й`) used 2+ times in one sentence without `та` | suggest `та` for second+ occurrence | `він і вона і Іван` → `він і вона та Іван` |

**Detection target:** Two or more occurrences of `і`/`й` within the same sentence (split on `.!?`) without any `та` appearing between them.

**Why it's detectable:** Simple sentence-level count. If a sentence contains `і` (or `й`) twice or more and zero `та`, flag the second occurrence and suggest substituting `та`.

**Why it matters:** LLMs default to repeating the same conjunction. Ukrainian stylistic convention rotates `і → й → та` to avoid monotony — exactly the kind of "phonetically lazy" output this check targets.

---

## What We Will NOT Detect (by design)

These require morphological parsing or have too many valid exceptions:

- Word-internal euphony (suffixes, prefixes)
- `на/над`, `під/піді` alternation (extremely rare in modern prose)
- `та` before vowels (та is always acceptable before any sound — no rule violation possible)
- Cases where the alternation is optional/dialectal

---

## Implementation Design

### File: `scripts/audit/checks/euphony.py`

```python
"""
Euphony (Милозвучність) Checker

Detects violations of Ukrainian euphony rules in prose:
  Rule 1: Conjunction і/й alternation (phonetic position)
  Rule 2: Preposition у/в alternation (phonetic position)
  Rule 3: Preposition з/із/зі alternation (consonant clusters)
  Rule 4: Conjunction та/й variety (stylistic — no repeated і/й)

Severity: WARNING (non-blocking — edge cases exist in poetry,
quoted speech, and stylistic usage).

Track exemptions: OES, RUTH (historical Ruthenian texts).
"""
```

**Core approach:**
1. Skip non-prose lines (headers, tables, blockquotes, code, frontmatter)
2. For Rules 1–3: tokenize each line into words; for each trigger word (`і`, `у`, `з`, `в`, `й`) examine the surrounding words
3. For Rule 4: split content into sentences; count `і`/`й` per sentence; flag if ≥ 2 with no `та`
4. Apply rule table → emit warning with location and suggested fix

**Helper functions:**
- `_ends_with_vowel(word)` — word ends in Ukrainian vowel (а е є и і ї о у ю я)
- `_starts_with_vowel(word)` — word starts with Ukrainian vowel
- `_starts_with_cluster(word)` — starts with 2+ consonants (зб, зд, зм, зн, зр, зв, зл, зг, сп, ст, тр, etc.)
- `_starts_with_v_or_f(word)` — starts with в or ф
- `_skip_line(line)` — True for headers (`#`), tables (`|`), blockquotes (`>`), code fences, frontmatter

**Lines to skip:**
- `#` headers
- `|` table rows
- `>` blockquotes (may contain quoted speech)
- Lines starting with ` ``` `
- Lines between `---` frontmatter delimiters

### Violation format

```python
{
    "type": "EUPHONY",
    "severity": "warning",
    "issue": "Line 47: «вона і Олена» — і між голосними; має бути «й Олена»",
    "fix": "Replace «і» with «й» (between vowels)",
    "line": 47,
}
```

### Registration

```python
# __init__.py
from .euphony import check_euphony_violations

# core.py (after imperial_terminology block)
euphony_violations = check_euphony_violations(content, file_path)
if euphony_violations:
    print(f"  🎵 Euphony violations: {len(euphony_violations)}")
    for v in euphony_violations:
        print(f"     ⚠️  [{v['type']}] {v['issue']}")
    content_quality_violations.extend(euphony_violations)
```

### Prompt update: `phase-2-content.md`

Add euphony rules to the "Language Quality Rules" section (after "Russianisms", before "Pronunciation: IPA Only") so Gemini produces euphonic prose from the start:

```markdown
### Euphony / Милозвучність (WARNING if violated)

Ukrainian prose must follow euphony rules. Scan your output:

| Rule | Bad | Good |
|------|-----|------|
| і → й between vowels | вона і Олена | вона й Олена |
| й → і after consonant | він й Олена | він і Олена |
| й → і before consonant | вона й працює | вона і працює |
| у → в before vowel | у Одесі | в Одесі |
| в → у before в/ф | в вікні | у вікні |
| в → у before consonant cluster | в зграї | у зграї |
| з → із before з/с/consonant cluster | з зброєю | із зброєю |
| Vary conjunctions | він і вона і Іван | він і вона та Іван |
```

This prevents violations at generation time rather than catching them only in the audit loop.

---

## Testing Plan

### Smoke test cases

```python
# Rule 1 — should flag:
"вона і Олена прийшли"   # і between vowels (vowel-і-vowel) → й Олена
"вона і Іван говорили"   # і between vowels (vowel-і-vowel) → й Іван
"він й Олена"            # й after consonant → і Олена
"він й працює"           # й after consonant → і працює
"вона й працює"          # й before consonant → і працює

# Rule 1 — should NOT flag:
"він і Олена"            # і after consonant, before vowel — correct (й not allowed after consonant)
"він і працює"           # і after consonant, before consonant — correct
"вона й Оля"             # й between vowels — correct
"сонце і місяць"         # і before consonant — correct

# Rule 2 — should flag:
"у Одесі"                # у before vowel → в Одесі
"в вікні"                # в before в → у вікні
"в зграї"                # в before consonant cluster → у зграї

# Rule 2 — should NOT flag:
"в парку"                # в before consonant — correct
"у зборах"               # у before cluster — correct

# Rule 3 — should flag:
"з зброєю"               # з before consonant cluster → із зброєю
"з Сонцем"               # з before с → із Сонцем

# Rule 3 — should NOT flag:
"з книгою"               # з before к — correct
"із зброєю"              # already correct

# Rule 4 — should flag:
"він і вона і Іван"      # two і without та → він і вона та Іван

# Rule 4 — should NOT flag:
"він і вона та Іван"     # та already present
"він і вона"             # only one і
```

### False positive scan

Run against all built `.md` files in a1, a2, b1, b2, c1, hist, c1-hist, c1-bio before declaring done.
Target: zero errors on clearly correct existing content.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| False positives in quoted speech | Medium | Blockquotes (`>`) skipped entirely |
| Tokenization breaks on punctuation | Low | Strip trailing punctuation before checking word boundaries |
| у/в before numbers (`у 1648 році`) | Low | Digit-starting words treated as consonant-initial (correct: `в 1648 році`) |
| Abbreviations (`ЄС`, `США`) before в/у | Low | Capital vowel → apply rule normally (`в ЄС` → `у ЄС`) |
| Rule 4 false positive in sentence with deliberate та absent | Low | Only flag if ≥ 2 `і`/`й` — single use is always fine |

---

## Effort Estimate

- Core implementation (Rules 1–4): ~3 hours
- False positive tuning: ~1 hour
- Registration + smoke test: ~30 minutes

**Total: ~4.5 hours**
