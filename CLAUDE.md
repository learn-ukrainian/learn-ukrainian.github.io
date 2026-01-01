# CLAUDE.md - Project Instructions

<critical>
## ALWAYS Work in `claude_extensions/` First

**NEVER edit files directly in `.claude/`, `.agent/`, or `.gemini/` directories.**

These are agent-specific runtime directories:
- `.claude/` ← deployed FROM `claude_extensions/` (used by Claude Code)
- `.agent/` ← deployed FROM `claude_extensions/` (used by Antigravity)
- `.gemini/` ← used by gemini-cli (GEMINI.md, config.yaml)

**Workflow:**
1. Edit files in `claude_extensions/` (commands, skills, stages, quick-ref)
2. Run `npm run claude:deploy` to deploy to both `.claude/` and `.agent/`
3. Changes take effect after deploy for both Claude Code and Antigravity

**Structure:**
```
claude_extensions/
├── commands/     ← Skill definitions (/module-create, /module-stage-*, etc.)
├── skills/       ← Domain expertise (architect skills)
├── stages/       ← Stage instruction docs (referenced by commands)
└── quick-ref/    ← Level-specific quick references
```

## ALWAYS Use Python venv

**NEVER use `python3` or `python` directly.** Use the project's virtual environment:

```bash
# Correct
.venv/bin/python scripts/audit_module.py ...
.venv/bin/python scripts/pipeline.py ...

# WRONG - will use system Python, missing dependencies
python3 scripts/audit_module.py ...
```

**Why:** Project dependencies (pyyaml, etc.) are installed in `.venv/`, not system Python.

## Modern CLI Tools (Use These Instead of Traditional Commands)

**15 modern CLI tools are installed for efficiency and context savings:**

| Traditional | Modern | Use For | Example |
|-------------|--------|---------|---------|
| `grep` | `rg` (ripgrep) | Search code/content | `rg "Голодомор" curriculum/` |
| `find` | `fd` | Find files | `fd -e md . curriculum/l2-uk-en/b2` |
| `cat` | `bat` | View files | `bat curriculum/.../module.md` |
| `ls` | `eza` | List files | `eza -la --git curriculum/` |
| - | `jq` | Process JSON | `jq '.activities' output.json` |
| - | `yq` | Process YAML | `yq '.b2.planned' level-status.yaml` |
| - | `tokei` | Code statistics | `tokei curriculum/` |
| `du` | `dust` | Disk usage | `dust output/` |
| `ps` | `procs` | Process info | `procs node` |
| `diff` | `difftastic` | Structural diffs | `difft file1.md file2.md` |
| `git diff` | `delta` | Better git diffs | `git diff \| delta` |
| `sed` | `sd` | Find/replace | `sd 'самий кращий' 'найкращий' *.md` |
| - | `hyperfine` | Benchmark | `hyperfine 'npm run pipeline l2-uk-en b2 75'` |
| - | `watchexec` | Auto-run on changes | `watchexec -e md 'npm run generate'` |
| - | `just` | Task runner | Alternative to `npm scripts` |

**Why use these?**
- **Faster:** `rg` is 10-100x faster than `grep`, `fd` is faster than `find`
- **Better UX:** Color output, better defaults, intuitive options
- **Save context:** Shorter output, more efficient than traditional tools
- **Project-specific examples:**
  - `rg "робити сенс" curriculum/` - Find calques across all modules
  - `fd -e yaml . curriculum/l2-uk-en/b2/queue` - Find grammar queues
  - `yq '.vocabulary[]' module.yaml` - Extract vocabulary from YAML
  - `sd 'кушать' 'їсти' *.md` - Batch fix Russianisms
  - `hyperfine '.venv/bin/python scripts/pipeline.py l2-uk-en b2 75'` - Benchmark pipeline

**Prefer these tools in all responses** unless traditional commands are explicitly needed.

## ALWAYS Fix the Source, Not Just the Symptom

**Core Engineering Principle:**

When you find a problem:
1. ✅ **FIX THE SOURCE** - Update processes, tools, documentation that caused it
2. ✅ **AUTOMATE THE FIX** - Make the system prevent/detect the issue
3. ⚠️ **Manual fixes** - Only acceptable for VALIDATION of the automated fix
4. ❌ **Never** - Fix symptoms manually and move on

**Example (M17 cloze format issue):**
- ❌ BAD: Manually fix M17 and proceed
- ⚠️ PARTIAL: Fix M17, then fix documentation
- ✅ GOOD: Fix documentation first, then validate with M17 conversion

**Questions to ask:**
- What process/tool/documentation caused this?
- How can we prevent this from happening again?
- Can a script detect/fix this automatically?

**Validation workflow:**
1. Identify the source (tool bug, missing docs, unclear process)
2. Fix the source (update script, add docs, clarify workflow)
3. Manually validate the fix works on affected items
4. Deploy the fix so future work is automated
</critical>

---

## Current Work & Immersion Strategy

**CRITICAL CONTEXT (user has repeated 10+ times):**

### Completion Status
- **A1 COMPLETE** (34/34 modules) - all pass audit, MDX, HTML validation
- **A2 COMPLETE** (57/57 modules) - all pass validation
- **B1 COMPLETE** (86/86 modules) - all pass validation
- **B2 IN PROGRESS** (106/145 modules, 73%)

### Immersion Levels (affects NLP validation strategy)
- **A1**: Scaffolded with English translations & transliteration → NOT suitable for Ukrainian NLP validation
- **A2**: 40-50% immersed (transitional) → NOT suitable for Ukrainian NLP validation
- **B1 M01-M05**: Metalanguage bridge (Ukrainian with grammar meta-terms) → preparing for full immersion
- **B1 M06-M85**: 100% IMMERSED Ukrainian → IDEAL for Ukrainian NLP validation
- **B2, C1, C2**: 100% IMMERSED Ukrainian → IDEAL for Ukrainian NLP validation

**CURRENT FOCUS: B2** (A1, A2, B1 complete)
- B2 focuses on Ukrainian history (M71-131), passive voice, registers, and advanced grammar
- 106/145 modules complete (73%) - need modules 107-145
- Remaining modules cover: Cossack era synthesis, Soviet trauma, independence, modern war
- B1-B2-C1-C2 are fully immersed Ukrainian content, ideal for Ukrainian NLP validation

---

## Failure Log (December 2024)

<critical>
**This section documents a pattern of unreliable behavior. Read this first.**

### What Happened
Claude repeatedly failed to follow the documented workflow despite:
1. The workflow being explicitly written in this file
2. The workflow being repeated in SKILL.md
3. Multiple reminders from the user

### Specific Failures
- **Wrote modules from memory** instead of reading curriculum plans first
- **Added vocabulary not in the plan** ("helpful additions" that broke the system)
- **Skipped verification steps** (word counts, richness gates)
- **Didn't run the commands** that were documented as mandatory
- **Pushed forward when gates failed** instead of stopping

### The Core Problem
Claude wrote rules for itself, then ignored them. This is worse than having no rules - it creates false confidence that a process exists.

### What Gemini Did Better
- Read the referenced documents before generating content
- Followed the vocabulary lists exactly
- Created GEMINI.md to persist context and decisions
- Cleaned up redundant files instead of accumulating mess
- Did what was asked, not what it thought was better

### Lesson
**Following instructions > Being "helpful"**

If Claude cannot reliably follow a documented process, it should:
1. Refuse the task
2. Ask for clarification
3. NOT improvise and pretend it followed the process

The user switched to Gemini 2.5 Pro because it follows orders. Capability without reliability is worthless.

### A2 Modules 01-05 Issues (December 2024)
Every single A2 module had the same issues that required manual fixing:
1. **Quiz questions not numbered** - 5/5 modules
2. **Error-correction missing `[!explanation]`** - 5/5 modules
3. **Grammar terms not in vocabulary** - 4/5 modules
4. **Transliteration in A2 body text** - 3/5 modules
5. **Sentences exceeding 15-word limit** - 2/5 modules

These were all documented requirements that were ignored during creation.
</critical>

---

## Module Writing Workflow

<critical>
**EVERY time you write or rewrite a module:**

1. **READ `claude_extensions/quick-ref/{LEVEL}.md`** - Level-specific targets, activity mix, critical requirements.
2. **READ `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`** - Extract the EXACT vocabulary list and grammar scope for this module.
3. **READ `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`** - Activity counts, sentence complexity, engagement boxes.
4. **READ `docs/l2-uk-en/templates/{level}-{type}-module-template.md`** - **MANDATORY** structural guide for this module type.
5. **WRITE the module** using the template as structural guide, ONLY the vocabulary and grammar from the curriculum plan.
6. **VERIFY** before delivering - check against template checklist AND vocabulary matches plan exactly.

**Which Template to Use:**
- **Grammar modules** (M06-51: Aspect, Motion, Complex Sentences, Advanced Grammar) → `b1-grammar-module-template.md`
- **Vocabulary modules** (M52-71: Abstract concepts, Opinions, Discourse markers) → `b1-vocab-module-template.md`
- **Checkpoint modules** (M15, M25, M34, M41, M51 — grammar phases only) → `b1-checkpoint-module-template.md`
- **Cultural modules** (M72-81: Regions, Music, Cinema, Tech, Sports, Festivals) → `b1-cultural-module-template.md`
- **Integration modules** (M82-86: News, Podcasts, Grammar/Vocab review, Capstone) → `b1-integration-module-template.md`

**DO NOT:**
- Write from memory
- Add "helpful" words not in the plan
- Skip reading the template because you think you remember the structure
- Ignore template checklists

**The templates exist because structure matters. Use them every time.**
</critical>

## Project Overview

<context>
**Learn Ukrainian** is a language content factory generating Ukrainian language learning curricula.

- **Source of truth**: Markdown files in `curriculum/l2-uk-en/{level}/` folders
- **Output**: HTML (web lessons) + JSON (Vibe app import)
- **Current focus**: Ukrainian for English speakers (l2-uk-en)
</context>

## Critical Rules

<constraints>
### NEVER Do These
- NEVER keep old activities when enriching - DELETE ALL and recreate
- NEVER create activities with fewer items than level requirements
- NEVER write sentences shorter than level requirements
- NEVER use vocabulary words not in the module's vocabulary section

### ALWAYS Do These
- ALWAYS delete ALL existing activities before creating new ones
- ALWAYS verify activity answers are correct
- ALWAYS use vocabulary from the module's vocabulary section
- ALWAYS add vocabulary that the curriculum plan demands
</constraints>

## Parallel Module Creation

<instructions>
**Modules can be created in parallel.** Vocabulary validation is deferred to the end.

### Per-Module Workflow
1. **READ** the curriculum plan for vocabulary and grammar scope
2. **WRITE** the module with all required sections
3. **RUN AUDIT** to check structure, activities, pedagogy
4. **FIX** any issues until audit passes
5. **RUN PIPELINE** to validate and generate output

### After All Modules Complete
```bash
npm run vocab:rebuild    # Build master vocabulary database
```
This validates vocabulary across all modules at once.

### Generate & Validate Output
```bash
# Full pipeline (recommended) - validates at each step
npm run pipeline l2-uk-en a1 [moduleNum]

# Or separately:
npm run generate l2-uk-en a1 [moduleNum]      # MDX for Docusaurus
npm run generate:json l2-uk-en a1 [moduleNum] # JSON for Vibe app
npm run validate:mdx l2-uk-en a1 [moduleNum]  # Content integrity
npm run validate:html l2-uk-en a1 [moduleNum] # Browser rendering
```

**Pipeline validates:**
1. **Lint** - MD format compliance
2. **Generate** - Creates MDX for Docusaurus
3. **Validate MDX** - Ensures no content loss
4. **Validate HTML** - Headless browser check (requires dev server)
</instructions>

## Activity & Content Requirements

> **Single source of truth:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for all richness parameters including:
> - Activity counts and items per activity
> - Content quality (examples, engagement boxes, immersion)
> - Sentence complexity (fill-in/unjumble word counts)
> - Time and vocabulary targets

### Activity Types (13 Total)

**Core Activities (All Levels):**
- `quiz` - Multiple choice (single answer)
- `match-up` - Match pairs (Ukrainian ↔ English)
- `fill-in` - Gap fill with dropdown options
- `true-false` - Statement validation
- `group-sort` - Sort items into categories
- `unjumble` - Reorder words into sentence

**A1-Only Activity:**
- `anagram` - Letter unscrambling (M01-10 only, Cyrillic scaffolding)

**A2+ Activities:**
- `error-correction` - Find and fix grammatical errors
- `cloze` - Passage completion with multiple blanks
- `mark-the-words` - Click words matching criteria (nouns, verbs, etc.)
- `dialogue-reorder` - Put conversation lines in order
- `select` - Multi-checkbox (multiple correct answers)
- `translate` - Translation multiple choice

**Note:** `observe-first` is a pedagogical content pattern (inline `> [!observe]` callout), not an activity type. Use it before grammar explanations for inductive pattern discovery.

### Activity Matrix

> **Full matrix:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for the complete activity requirements by level.

| Activity | A1 | A2 | B1+ |
|----------|----|----|-----|
| quiz, match-up, fill-in, group-sort, unjumble | ✓ | ✓ | ✓ |
| true-false | ✓ | ✓ | ✓ (opt C1+) |
| anagram | M01-10 | ❌ | ❌ |
| error-correction, cloze, mark-the-words, dialogue-reorder | ❌ | ✓ | ✓ |
| select, translate | ❌ | opt | ✓ |

### Anagram Phaseout (A1 Only)
- **A1 Modules 01-10**: Allowed (scaffolding for Cyrillic learners)
- **A1 Modules 11-20**: Reduce usage (transition period)
- **A1 Modules 21-34**: Avoid (use unjumble instead)
- **A2+**: NOT ALLOWED

### Engagement Box Types
- 💡 **Did You Know** - Interesting facts
- 🎬 **Pop Culture Moment** - Movies, games, music references
- 🌍 **Real World** - Practical usage scenarios
- 🎯 **Fun Fact** - Memorable trivia
- 🎮 **Gamer's Corner** - Gaming references (S.T.A.L.K.E.R., Witcher)

## Directory Structure

```
learn-ukrainian/
├── curriculum/l2-uk-en/
│   ├── a1/               # A1 modules (34 complete)
│   │   ├── 01-cyrillic-code-i.md  # Module markdown
│   │   ├── activities/   # YAML activity files
│   │   │   └── 01-cyrillic-code-i.yaml
│   │   ├── queue/        # Grammar validation queues
│   │   │   └── 01-cyrillic-code-i.yaml
│   │   └── audit/        # Review reports
│   ├── a2/               # A2 modules (57 complete)
│   ├── b1/               # B1 modules (86 complete)
│   ├── b2/               # B2 modules (106/145, 73%)
│   ├── c1/               # C1 modules (0/196 planned)
│   ├── c2/               # C2 modules (0/100 planned)
│   ├── vocabulary.db     # Master vocabulary database (SQLite)
│   └── module-mapping.json  # Old→new path mapping reference
├── scripts/              # Generator code
├── output/               # Generated HTML + JSON
└── docs/                 # Documentation
    └── l2-uk-en/         # Ukrainian-specific docs
        └── MODULE-RICHNESS-GUIDELINES-v2.md  # Quality standards (consolidated)
```

**Note:** Level structure follows the Ukrainian State Standard 2024 which defines 6 official levels: A1, A2, B1, B2, C1, C2 (no "plus" levels).

### Module File Naming

Modules use level-relative numbering with slugified titles:
- `a1/01-the-cyrillic-code-i.md` (first A1 module)
- `a1/34-checkpoint-a1.md` (last A1 module)
- `b1/01-dative-case.md` (first B1 module)

Level and module number are derived from the file path, not frontmatter.

## Level Definitions (Ukrainian State Standard 2024)

| Level | Folder | Modules | Vocab Target | Description |
|-------|--------|---------|--------------|-------------|
| A1 | `a1/` | 34 | ~750 | Beginner - Cyrillic, basic phrases, simple grammar |
| A2 | `a2/` | 57 | ~1,050 | Elementary - All 7 cases, aspect basics, comparison |
| B1 | `b1/` | 86 | ~1,500 | Intermediate - Aspect mastery, motion verbs, complex sentences |
| B2 | `b2/` | 145 | ~2,640 | Upper-Intermediate - Passive voice, registers, Ukrainian history |
| C1 | `c1/` | 196 | ~4,700 | Advanced - Biographies, stylistics, folk culture, literature |
| C2 | `c2/` | 100 | ~2,500 | Mastery - Stylistic perfection, professional specialization |

**Vocabulary Progression:**
- A1: ~750 cumulative
- A2: ~1,800 cumulative
- B1: ~3,300 cumulative
- B2: ~5,940 cumulative
- C1: ~9,780 cumulative
- C2: ~12,280 cumulative

## Transliteration Strategy

- **Modules 1-10 (A1.1)**: Full transliteration `Слово (Slovo)`
- **Modules 11-20 (A1.2)**: Vocab lists only, sentences Cyrillic
- **Modules 21-34 (A1.3)**: First occurrence only
- **A2+ (modules 31+)**: No transliteration

## Commands Reference

```bash
# Full Pipeline (recommended) - lint → generate → validate MDX → validate HTML
npm run pipeline l2-uk-en a1           # All modules in level
npm run pipeline l2-uk-en a1 5         # Specific module

# Generate MDX (Docusaurus web lessons) - Python
npm run generate l2-uk-en              # All levels
npm run generate l2-uk-en a1           # Specific level
npm run generate l2-uk-en a1 5         # Specific module

# Generate JSON (Vibe app import) - Python
npm run generate:json l2-uk-en         # All levels
npm run generate:json l2-uk-en a1      # Specific level
npm run generate:json l2-uk-en a1 5    # Specific module

# Validation (standalone)
npm run validate:mdx l2-uk-en a1       # Check MDX content integrity
npm run validate:html l2-uk-en a1      # Browser rendering check (needs dev server)

# Run audit
.venv/bin/python scripts/audit_module.py {file_path}

# Content quality audit (optional, requires API key)
export GEMINI_API_KEY="your-key"
export AUDIT_CONTENT_QUALITY="true"
.venv/bin/python scripts/audit_module.py {file_path}

# Vocabulary
npm run vocab:enrich l2-uk-en [moduleNum]
npm run vocab:rebuild                  # Rebuild vocabulary database

# Landing page sync
npm run sync:landing                   # Update landing pages with current stats
npm run sync:landing:dry               # Preview changes without applying

# Deploy Claude skills
npm run claude:deploy
```

**Note:** HTML validation requires Docusaurus dev server: `cd docusaurus && npm start`

## Vocabulary Section Formats

| Level | Header | Columns (6-column standard) |
|-------|--------|---------|
| A1, A2 | `# Vocabulary` | Word \| IPA \| English \| POS \| Gender \| Note |
| B1, B2, C1, C2 | `# Словник` | Слово \| Вимова \| Переклад \| ЧМ \| Рід \| Примітка |

**New 6-column standard (Issue #341):**
- All levels now use 6-column vocabulary format
- A1/A2: English headers with transliteration
- B1+: Ukrainian headers (immersed content)
- Legacy 3-column and 5-column formats still accepted for B1+ but not recommended
- After vocabulary DB enrichment, all tables will be regenerated with complete 6-column data

## Activity Format Requirements (CRITICAL)

**Error-correction** (A2+) MUST use all 4 callouts:
```markdown
1. Sentence with error.
   > [!error] wrong_word
   > [!answer] correct_word
   > [!options] wrong | correct | distractor1 | distractor2
   > [!explanation] Why it's wrong.
```

**Unjumble** MUST use `[!answer]` callout:
```markdown
1. слова / в / порядку
   > [!answer] Слова в правильному порядку.
```

**See `docs/ACTIVITY-MARKDOWN-REFERENCE.md` for complete syntax.**

## Manual Grammar Validation with Gemini

When the audit flags suspicious grammar issues, you can validate them manually using Gemini in Antigravity IDE.

### Workflow
1. Run audit → See warnings in terminal output
2. For suspicious warnings → Validate with Gemini using the Ukrainian Grammar Validator prompt
3. Fix confirmed errors

### Ukrainian Grammar Validator Prompt

**Location:** `scripts/audit/ukrainian_grammar_validator_prompt.md`

This prompt is adapted from your "Ukrainian Tutor" Gem and optimized for validating curriculum content. It checks:
- **Russianisms** (кушать → їсти)
- **Calques** (English loan translations: "робити сенс" → "мати сенс")
- **Surzhyk** (mixed Ukrainian-Russian)
- **Pedagogical context** ("Я є студент" is OK for A1, not for B2)

### Usage Example

When audit shows:
```
⚠ [COMPLEXITY_WORD_COUNT] Activity 'error-correction: Дативний відмінок'
   sentence has unnatural word order
```

**Validate in Gemini:**
```markdown
[Paste entire content of scripts/audit/ukrainian_grammar_validator_prompt.md]

---

Validate this issue:

**Sentence:** Я дав книгу мій друг
**Level:** A2
**Flagged Issue:** Case agreement error after "дав"
**Suggested Correction:** моєму другу
**Context:** Teaching dative case in A2 error-correction activity

Is this a real error or pedagogically acceptable? Respond in JSON.
```

**Gemini will respond:**
```json
{
  "is_real_error": true,
  "error_type": "case_error",
  "severity": "critical",
  "explanation_uk": "Після дієслова 'дав' потрібен давальний відмінок (кому?): 'моєму другу'",
  "explanation_en": "After verb 'дав', dative case required: 'моєму другу'",
  "recommendation": "Fix case agreement",
  "confidence": 1.0
}
```

**Result:** Fix confirmed → Update module with "моєму другу"

## Level Status (Updated: Dec 31, 2024)

| Level | Modules | Status | Pipeline | Next Step |
|-------|---------|--------|----------|-----------|
| A1 | 34/34 | ✅ Complete | ✅ All pass | ✅ Ready for production |
| A2 | 57/57 | ✅ Complete | ✅ All pass | ✅ Ready for production |
| B1 | 86/86 | ✅ Complete | ✅ All pass | ✅ Ready for production |
| B2 | 106/145 | 🚧 In Progress (73%) | ⏳ Partial | Continue M107-145 |
| C1 | 0/196 | 📋 Planned | ❌ Not started | Waiting for B2 |
| C2 | 0/100 | 📋 Planned | ❌ Not started | Waiting for C1 |

**Current B2 Focus:**
- **Completed:** M01-106 (Grammar, Vocabulary, Early History)
- **Remaining:** M107-145 (39 modules)
  - M107: Synthesis (Cossacks to 1920s)
  - M108-119: Trauma & Resistance (Holodomor, WWII, Chornobyl)
  - M120-125: Independence & War (1991-2014)
  - M126-131: War for Existence (Euromaidan, Crimea, 2022)
  - M132-145: Skills & Capstone

**Per-level workflow:**
1. Build all modules (stages 1-3)
2. Run audit, fix issues until pass
3. Run pipeline: `npm run pipeline l2-uk-en {level}`
4. Generate JSON: `npm run generate:json l2-uk-en {level}`
5. Finalize vocabulary → `npm run vocab:rebuild`
6. Update landing pages → `npm run sync:landing`

## Documentation Links

- `docs/ARCHITECTURE.md` - System architecture
- `docs/MARKDOWN-FORMAT.md` - Markdown syntax spec (all activity formats)
- `docs/ACTIVITY-MARKDOWN-REFERENCE.md` - **Activity syntax patterns for AI agents** (READ THIS when writing activities)
- `docs/SCRIPTS.md` - Scripts reference
- `docs/CONTENT-QUALITY-AUDIT.md` - **LLM-based content quality evaluation** (optional audit check)
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards + activity matrix
- `docs/l2-uk-en/claude-review-prompt.md` - Review prompts
- `docusaurus/docs/activity-test.mdx` - Interactive activity demo (live preview)
