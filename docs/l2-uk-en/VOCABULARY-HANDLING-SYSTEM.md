# Vocabulary Handling System

**Status:** Active
**Created:** 2024-12-14
**Purpose:** Global vocabulary management to prevent recursion and ensure consistency

---

## The Problem

Expanding or adjusting vocabulary at the module level during creation leads to endless recursion:

```
"This module needs more words" → add words
    ↓
"But now cumulative count is wrong" → adjust other modules
    ↓
"But now dependencies break" → adjust again
    ↓
... forever
```

**Root cause:** No separation between planning and creation phases.

---

## The Solution: Phased Vocabulary Workflow

### Phase 1: Planning (Set Targets in Curriculum Plan)

**When:** Before any module creation for a level

**What:**
1. Define minimum vocabulary words per module in curriculum plan
2. Provide explicit vocabulary lists for each module
3. Sum per-module targets to verify level total
4. Include linguistic/grammatical metalanguage vocabulary

**Files to update:**
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`

**Example curriculum plan vocabulary spec:**
```markdown
#### Module 05: Past Tense
**Vocabulary (22 words):**
читав, писав, говорив, слухав, дивився, їв, пив, спав,
учора, позавчора, минулого тижня, минулого місяця,
ранок, вечір, ніч, обід, сніданок, вечеря,
минулий, минула, минуле, минулі
```

---

### Phase 2: Creation (Follow Plan EXACTLY)

**When:** Creating modules

**Rules:**
- Use ONLY vocabulary from the curriculum plan
- NO improvisation or "helpful additions"
- NO expanding vocabulary during module creation
- If vocabulary seems insufficient, STOP and update the plan first

**Workflow:**
```
Read curriculum plan vocabulary list
    ↓
Write module using ONLY those words
    ↓
Run audit to verify compliance
    ↓
If audit fails → Fix module (not the plan)
```

**Critical:** Module vocabulary section must match curriculum plan exactly.

---

### Phase 3: Level Complete (Finalize Vocabulary)

**When:** ALL modules for a level exist

**What:**
1. Run vocabulary audit across entire level
2. Identify any gaps or violations
3. Fix modules to match plan (not vice versa)
4. Rebuild vocabulary database
5. Verify cumulative totals match plan

**Commands:**
```bash
# Audit all modules in a level
for i in {1..34}; do
  python3 scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md
done

# Rebuild vocabulary database
npm run vocab:rebuild

# Verify cumulative count
sqlite3 curriculum/l2-uk-en/vocabulary.db "SELECT level, COUNT(*) FROM lemmas GROUP BY level"
```

---

### Level Dependency Chain

**Critical:** Vocabulary is cumulative. Each level builds on all previous levels.

```
A1 (independent - finalize FIRST)
 ↓
A2 (depends on A1 cumulative vocabulary)
 ↓
B1 (depends on A1 + A2)
 ↓
B2 (depends on A1 + A2 + B1)
 ↓
C1 (depends on all previous)
 ↓
C2 (depends on all previous)
```

**Implication:** You CANNOT finalize vocabulary for a level until all prerequisite levels are complete:

| Level | Can Finalize When |
|-------|-------------------|
| A1 | Anytime (no dependencies) |
| A2 | After A1 vocabulary finalized |
| B1 | After A1 + A2 vocabulary finalized |
| B2 | After A1 + A2 + B1 vocabulary finalized |
| C1 | After A1-B2 vocabulary finalized |
| C2 | After A1-C1 vocabulary finalized |

**Why this matters:**
- The audit checks cumulative vocabulary from the database
- If A1 vocabulary isn't in the DB, A2 modules will show false "missing vocabulary" warnings
- The `get_cumulative_vocab()` function in `vocabulary.py` queries all earlier levels

**Current Status:**
- [ ] A1 - 20/34 modules built, needs improvement first
- [ ] A2 - Waiting for A1 finalization
- [ ] B1 - Waiting for A1 + A2
- [ ] B2 - Waiting for A1 + A2 + B1
- [ ] C1 - Waiting for A1-B2
- [ ] C2 - Waiting for A1-C1

**A1 Workflow:**
```
1. Improve A1 curriculum plan (vocabulary targets, grammar scope)
2. Update module creation prompts & audit config
3. Build remaining 14 modules (21-34)
4. Fix existing 20 modules based on audit
5. Finalize A1 vocabulary → rebuild DB
6. THEN A2 can begin
```

---

## Current System Components

### 1. Vocabulary Database

**Location:** `curriculum/l2-uk-en/vocabulary.db`

**Tables:**
- `lemmas` - individual words with level, module, IPA, translation
- `expressions` - multi-word phrases

**Schema:**
```sql
CREATE TABLE lemmas (
    id TEXT PRIMARY KEY,
    uk TEXT NOT NULL,
    ipa TEXT,
    en TEXT,
    notes TEXT,
    level TEXT,
    first_module INTEGER
);
```

### 2. Audit Script

**Location:** `scripts/audit/checks/vocabulary.py`

**Current capabilities:**
- Extract vocabulary from module markdown
- Count vocabulary rows
- Check words used in content vs. vocabulary section
- Sync vocabulary to database during audit
- Get cumulative vocabulary from earlier modules

**Current config (`scripts/audit/config.py`):**
```python
LEVEL_CONFIG = {
    'A1': {'min_vocab': 20, ...},
    'A2': {'min_vocab': 25, ...},
    'B1': {'min_vocab': 25, ...},  # 30 for vocab modules
    'B2': {'min_vocab': 25, ...},  # 30 for vocab modules
    'C1': {'min_vocab': 25, ...},
    'C2': {'min_vocab': 25, ...},
}
```

### 3. Common Words List

**Location:** `scripts/audit/config.py` → `COMMON_WORDS`

Words that don't need to be in vocabulary section:
- Pronouns, conjunctions, prepositions
- Basic verbs (бути, мати, робити, знати, хотіти)
- Particles, adverbs, question words
- Numbers, common adjectives

---

## Audit Enhancements

### ✅ Enhancement 1: Curriculum Plan Vocabulary Check (IMPLEMENTED)

**Purpose:** Verify module vocabulary matches curriculum plan

**Location:** `scripts/audit/checks/vocabulary.py`

**Functions:**
- `parse_plan_vocabulary(plan_path, module_num)` - Extracts vocabulary list from curriculum plan
- `check_vocab_matches_plan(module_path, level, module_num, module_vocab)` - Compares module vs plan

**Violations detected:**
- `VOCAB_PLAN_MISMATCH` - Words in module but not in plan (improvisation)
- `VOCAB_PLAN_MISSING` - Words in plan but not in module

### Enhancement 2: Level Vocabulary Summary (Planned)

**Purpose:** Generate vocabulary report for entire level

**Implementation needed:**
```python
def generate_level_vocab_report(level: str) -> dict:
    """
    Generate vocabulary summary for a level:
    - Total words per module
    - Cumulative total
    - Comparison to plan target
    - Duplicate detection
    """
    # TODO: Implement
    pass
```

### ✅ Enhancement 3: Metalanguage Vocabulary Check (IMPLEMENTED)

**Purpose:** Verify grammatical terms are taught before use

**Location:** `scripts/audit/checks/vocabulary.py`

**Constants:**
```python
METALANGUAGE_BY_LEVEL = {
    'A1': {'іменник', 'дієслово', 'прикметник', 'займенник', ...},
    'A2': {'відмінок', 'називний', 'знахідний', 'вид', ...},
    'B1': {'дієприкметник', 'дієприслівник', 'пасивний', ...},
    'B2': {'стиль', 'регістр', 'синонім', 'антонім', ...},
    'C1': {'персоніфікація', 'алітерація', 'метонімія', ...},
    'C2': {'парцеляція', 'анафора', 'епіфора', ...},
}
```

**Function:**
- `check_metalanguage_scaffolding(content, vocab_words, level)` - Checks if grammar terms are taught

**Violations detected:**
- `METALANGUAGE` - Grammar terms used in content but not in vocabulary section

---

## Commands Reference

```bash
# Audit single module
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md

# Audit all modules in level
for f in curriculum/l2-uk-en/a1/*.md; do
  python3 scripts/audit_module.py "$f"
done

# Rebuild vocabulary database from all modules
npm run vocab:rebuild

# Query vocabulary database
sqlite3 curriculum/l2-uk-en/vocabulary.db "SELECT level, COUNT(*) FROM lemmas GROUP BY level"

# Check for duplicates across levels
sqlite3 curriculum/l2-uk-en/vocabulary.db "
  SELECT uk, GROUP_CONCAT(level) as levels, COUNT(*) as cnt
  FROM lemmas
  GROUP BY uk
  HAVING cnt > 1
"
```

---

## Vocabulary Targets by Level

| Level | New Words | Cumulative | Min per Module |
|-------|-----------|------------|----------------|
| A1 | ~750 | ~750 | 20 |
| A2 | ~1,050 | ~1,800 | 25 |
| B1 | ~1,500 | ~3,300 | 25-30 |
| B2 | ~2,900 | ~6,200 | 25-30 |
| C1 | ~2,800 | ~9,000 | 25 |
| C2 | ~2,000 | ~11,000 | 25 |

**Note:** These are targets from curriculum plans. Reconcile any discrepancies in improvement plans before module creation.

---

## Metalanguage Vocabulary (Must Teach Before Use)

### A1 - Basic Grammar Terms
| Ukrainian | English | Introduce In |
|-----------|---------|--------------|
| іменник | noun | M03 |
| дієслово | verb | M05 |
| прикметник | adjective | M26 |
| він/вона/воно | he/she/it (gender markers) | M03 |
| однина | singular | M07 |
| множина | plural | M07 |

### A2 - Case and Aspect Terms
| Ukrainian | English | Introduce In |
|-----------|---------|--------------|
| відмінок | case | M01 |
| називний | nominative | M01 |
| знахідний | accusative | M01 |
| родовий | genitive | M01 |
| давальний | dative | M01 |
| орудний | instrumental | M01 |
| місцевий | locative | M01 |
| кличний | vocative | M01 |
| вид | aspect | M06 |
| доконаний | perfective | M06 |
| недоконаний | imperfective | M06 |
| час | tense | M08 |

### B1 - Advanced Grammar Terms
| Ukrainian | English | Introduce In |
|-----------|---------|--------------|
| дієприкметник | participle | Before participle module |
| дієприслівник | adverbial participle | Before gerund module |
| пасивний стан | passive voice | Before passive module |
| активний стан | active voice | Before passive module |
| умовний спосіб | conditional mood | Before conditional module |
| дієслова руху | motion verbs | Before motion verb module |

### B2+ - Academic/Literary Terms
| Ukrainian | English | Level |
|-----------|---------|-------|
| стиль | style | B2 |
| регістр | register | B2 |
| синонім | synonym | B2 |
| антонім | antonym | B2 |
| фразеологізм | idiom/phraseology | B2 |
| метафора | metaphor | C1 |
| персоніфікація | personification | C1 |

---

## Anti-Patterns (DO NOT DO)

### 1. Vocabulary Improvisation
```
❌ "This sentence needs the word X, let me add it to vocabulary"
✅ "This sentence needs word X which isn't in the plan. STOP. Update plan first."
```

### 2. Mid-Level Vocabulary Changes
```
❌ "Module 15 needs more words, let me add 10 more"
✅ "Module 15 has insufficient vocabulary. Flag for plan review at level completion."
```

### 3. Recursive Fixes
```
❌ Module A needs word from Module B → Add to A → But A teaches it first → Change B → ...
✅ All vocabulary defined in plan BEFORE creation. No cross-module vocabulary changes.
```

### 4. Database-First Changes
```
❌ Add word to database, then update module to match
✅ Module is source of truth. Database rebuilt from modules.
```

---

## Success Criteria

Vocabulary system is working correctly when:

1. [ ] All curriculum plans have explicit per-module vocabulary lists
2. [ ] Module vocabulary sections match curriculum plans exactly
3. [ ] Audit script can detect vocabulary improvisation
4. [ ] Audit script can verify metalanguage scaffolding
5. [ ] `npm run vocab:rebuild` produces consistent results
6. [ ] Cumulative vocabulary totals match plan targets
7. [ ] No vocabulary changes happen during module creation phase

---

## References

- Improvement Plans: `docs/l2-uk-en/{LEVEL}-IMPROVEMENT-PLAN.md`
- Curriculum Plans: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- Audit Config: `scripts/audit/config.py`
- Vocabulary Audit: `scripts/audit/checks/vocabulary.py`
