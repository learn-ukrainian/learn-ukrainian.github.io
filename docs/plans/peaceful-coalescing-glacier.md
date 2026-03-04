# Fix Prompt/Audit Friction for A1 and A2 Modules

## Context

Building A1 and A2 modules is slow and expensive because Gemini produces content that can't pass audit gates, triggering fix loops that often exhaust their 2-iteration cap. Root cause: **three layers of config contradictions** between what the prompt tells Gemini to do, what the schema validates, and what the audit expects.

This is NOT a template architecture problem — the parameterized placeholder system works. The problem is that specific config values disagree with each other, and some template rules are hardcoded for B1+ without level-aware alternatives.

---

## Fix 1: Unify Item Count Configs (HIGHEST priority)

**Problem**: Three sources state different minimum items per activity:

| Source | A1 | A2 | Location |
|--------|----|----|----------|
| `LEVEL_CONFIG.min_items_per_activity` | 12 | 8 | `config.py:528,539` |
| `ACTIVITY_CONFIGS.ITEMS_MIN` (→ prompt) | 12 | 12 | `pipeline_lib.py:359,366` |
| `ACTIVITY_COMPLEXITY.min_items` (per-type) | 6-8 | 6-8 | `config.py:236-295` |

Gemini targets 12, audit per-type checks pass at 6-8, but the fallback `min_items_per_activity` rejects types not in `ACTIVITY_COMPLEXITY` at 12. A2 was relaxed to 8 in LEVEL_CONFIG (Feb 2026 comment at line 539) but ACTIVITY_CONFIGS wasn't updated.

**Changes**:

| File | Line | Before | After |
|------|------|--------|-------|
| `scripts/audit/config.py` | 528 | `'min_items_per_activity': 12` | `'min_items_per_activity': 6` |
| `scripts/pipeline_lib.py` | 359 | `"ITEMS_MIN": "12"` | `"ITEMS_MIN": "6"` |
| `scripts/pipeline_lib.py` | 366 | `"ITEMS_MIN": "12"` | `"ITEMS_MIN": "8"` |

**Why 6 for A1**: Early A1 has ~10 decodable words. 8 items of the same 5 words teaches nothing. 6 diverse items > 12 repetitive ones. Per-type `ACTIVITY_COMPLEXITY` already uses 6-8 as floor.

---

## Fix 2: Level-Aware Structural Rules in phase-2 (HIGH priority)

**Problem**: `phase-2-content.md` hardcodes B1+ structural expectations for ALL levels:
- "80-100 words per H3 block" (line 6)
- 4-part structure per concept: definition + how it works + examples + usage note (lines 114-119)
- 5+ format variety for examples (lines 132-139)

Impossible for early A1 (6-letter vocabulary, no grammar) and overkill for A2.

**Changes**:

**`scripts/pipeline_lib.py`** — Add `get_structural_rules(track, module_num) -> str`:

| Level range | H3 words | Structure | Format variety |
|-------------|----------|-----------|----------------|
| A1 M1-M4 | 30-50 | Introduce + show + practice | No minimum (letter-focused) |
| A1 M5-M14 | 40-60 | Introduce + examples + practice tip | 3+ types |
| A1 M15+ | 60-80 | Definition + examples + usage note | 3+ types |
| A2 | 60-80 | Full 4-part but 80 words not 100 | 4+ types |
| B1+ | 80-100+ | Full 4-part (current rules unchanged) | 5+ types |

Add to `write_placeholders`: `"STRUCTURAL_RULES"` and `"H3_WORD_RANGE"`.

**`claude_extensions/phases/gemini/phase-2-content.md`**:
- Line 6: Replace hardcoded "80-100+" with `{H3_WORD_RANGE}`
- Lines 83-139 (Rules 1-4): Replace with `{STRUCTURAL_RULES}` placeholder
- Lines 196-210 (expansion method): Replace with `{EXPANSION_METHOD}` placeholder
- Rules 5-9 (callout variety, anti-robotic, etc.) stay unchanged — they're level-independent

After deploy: `npm run claude:deploy`

---

## Fix 3: Level-Aware English Hints Detection (HIGH priority)

**Problem**: `activity_validation.py:264-335` `check_english_hints_in_activities` flags `(lowercase word)` patterns as English hints. Threshold: >5 = critical. No level parameter usage. But A1/A2 activities are **required** to use English for instructions/explanations (phase-3:198-203).

The function only checks cloze, fill-in, error-correction (not quiz/match-up). It already receives `level` and `module_num` params but never uses them.

**Changes in `scripts/audit/checks/activity_validation.py`**:

1. After line 271 — add level-aware threshold:
```python
base_level = level.split('-')[0].upper() if level else ''
if base_level in ('A1', 'A2'):
    critical_threshold = 15
    severity_floor = 'info'
else:
    critical_threshold = 5
    severity_floor = 'warning'
```

2. Line 323 — use level-aware threshold instead of hardcoded 5

3. Expand scaffolding allowlist for A1/A2: `(example)`, `(hint)`, `(listen)`, `(repeat)`, `(choose)`, etc.

---

## Fix 4: Decodable Vocabulary Injection (HIGH priority)

**Problem**: Gemini gets `PEDAGOGICAL_CONSTRAINTS` saying "only use 6 letters" but no actual word list. It invents words that violate the charset constraint, fails audit, enters fix loop.

**Changes**:

**`scripts/pipeline_lib.py`** — Add `get_decodable_vocabulary(track, module_num, plan) -> str`:

- M1-M4: Returns curated word list (VESUM-verified, charset-validated using `rule_engine._DECODABILITY_SPECS`)
- M5+, A2+: Returns empty string

Word lists curated per module:
- **M1** (АМЛУНС): мама, сума, луна, мул, нам, нас, сам, ум, масла, мала
- **M2** (+ТОКИВРЕІ): банан, вода, молоко, кіно, рука, дім, він, вона, бік, рис, сир, дорога, робота, добро
- **M3** (+ДПЗБГХЖШЧ): Full alphabet nearly complete — large word set, inject top-30 from plan's vocab_hints
- **M4**: Full alphabet — no restriction, empty placeholder

Each word verified with `mcp__rag__verify_word` and charset-checked against `rule_engine._DECODABILITY_SPECS[module].allowed` before inclusion.

**`claude_extensions/phases/gemini/phase-2-content.md`** — Add `{DECODABLE_VOCABULARY}` after `{PEDAGOGICAL_CONSTRAINTS}`

**`claude_extensions/phases/gemini/phase-3-activities.md`** — Add `{DECODABLE_VOCABULARY}` after line 25

---

## Implementation Order

1. **Fix 1** (item counts) — 3 single-line changes, highest impact, zero risk
2. **Fix 3** (English hints) — contained to one function, prevents false audit failures
3. **Fix 4** (vocabulary injection) — new function + placeholder, prevents constraint guessing
4. **Fix 2** (structural rules) — template change + new function, most complex; deploy via `npm run claude:deploy`

Fixes 1+3 can be one commit. Fixes 4+2 can be a second commit.

---

## Files Modified

| File | Fix | Change |
|------|-----|--------|
| `scripts/audit/config.py` | 1 | A1 `min_items_per_activity`: 12→6 |
| `scripts/pipeline_lib.py` | 1,2,4 | ITEMS_MIN alignment, `get_structural_rules()`, `get_decodable_vocabulary()`, `write_placeholders` |
| `scripts/audit/checks/activity_validation.py` | 3 | Level-aware thresholds in `check_english_hints_in_activities` |
| `claude_extensions/phases/gemini/phase-2-content.md` | 2,4 | `{STRUCTURAL_RULES}`, `{H3_WORD_RANGE}`, `{EXPANSION_METHOD}`, `{DECODABLE_VOCABULARY}` |
| `claude_extensions/phases/gemini/phase-3-activities.md` | 4 | `{DECODABLE_VOCABULARY}` |

---

## Verification

```bash
# 1. Confirm item count alignment
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from audit.config import LEVEL_CONFIG
from pipeline_lib import ACTIVITY_CONFIGS
for lvl in ['A1', 'A2']:
    lc = LEVEL_CONFIG[lvl]['min_items_per_activity']
    ac = ACTIVITY_CONFIGS[lvl.lower()]['ITEMS_MIN']
    match = '✅' if str(lc) == ac else '❌'
    print(f'{lvl}: LEVEL_CONFIG={lc}, ACTIVITY_CONFIGS={ac} {match}')
"

# 2. Verify structural rules vary by level
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from pipeline_lib import get_structural_rules
for track, mod in [('a1', 1), ('a1', 10), ('a1', 20), ('a2', 1), ('b1-grammar', 1)]:
    rules = get_structural_rules(track, mod)
    print(f'{track} M{mod}: {rules[:60]}...')
"

# 3. Verify decodable vocabulary
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from pipeline_lib import get_decodable_vocabulary
for mod in [1, 2, 3, 5]:
    vocab = get_decodable_vocabulary('a1', mod, {})
    print(f'M{mod}: {\"words found\" if vocab else \"empty (correct)\"}')
"

# 4. Existing tests pass
.venv/bin/python -m pytest tests/test_pipeline_v4.py tests/test_rule_engine.py -x -q

# 5. Deploy template changes
npm run claude:deploy

# 6. Rebuild M1 or M2 and compare fix-loop iterations (should be fewer)
```
