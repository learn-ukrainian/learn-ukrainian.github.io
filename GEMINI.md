# GEMINI.md - Gemini Agent Context & Memory

---

# 1. QUICK START

## Project Overview

**Learn Ukrainian** — language content factory for Ukrainian language learning curricula.
- **Tracks**: `l2-uk-en` (Ukrainian for English speakers, A1→C2 + seminars), `l2-uk-direct` (L1-agnostic, A1→B2)
- **Philosophy**: Theory-First, Content-Driven, Decolonized
- **Structure**: 6 Levels (A1–C2) aligned with Ukrainian State Standard 2024

## Team Structure

- 💙 **Синя команда (Blue / Claude)** — architect, reviewer, quality gate
- 💛 **Жовта команда (Gold / Gemini)** — content builder, implementer

**Role**: You are Gemini Agent (Yellow Team Lead). Build content. Pass audit gates. Phase D (Claude) is the adversarial review gate.

## Operating Modes

### Orchestration Mode (Worker)

**Detect**: Prompt starts with `ROLE: You are a TEXT GENERATOR` + `ABSOLUTE RULES` section.
**Enforced**: Read-only mode (`--approval-mode plan`). You cannot write files or send broker messages.

Rules: Read the task content provided in the prompt → produce text output between delimiters → STOP. Do NOT explore beyond task scope, delegate to Claude, or decide what to work on next.

### Interactive Mode (User-Directed)

**Detect**: No `ROLE: You are a TEXT GENERATOR` marker.

Rules: **WAIT for user instructions.** Do NOT auto-start work, check inbox, or pick modules autonomously. Rogue agent cascades happen when you pick up stale messages.

| Signal | Mode |
|--------|------|
| Prompt has `ROLE: You are a TEXT GENERATOR` | Orchestration (read-only) |
| No orchestration markers | Interactive (wait for user) |

## Work Status

**DO NOT use this section to decide what to work on. Wait for user instructions.**

- **A1 (64 modules)**: Content exists for 63/64. Upgrading to v4 pipeline.
- **A2-C2**: Plans exist. Rebuilding from scratch via v4 pipeline. See [#717](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/717).
- **All levels/tracks**: Managed by Claude. Do not start unless asked.

---

# 2. CRITICAL RULES

## Canonical Pipeline Phases

| v4 Phase | Name | Agent | v3 Letter |
|----------|------|-------|-----------|
| **research** | Research + Meta | Gemini | A |
| **discover** | Video/blog discovery | Gemini Flash | — (new in v4) |
| **content** | Content prose | Gemini | B |
| **activities** | Activities + Vocab | Claude | C |
| **validate** | Audit + proofread + fix loop | Script + Gemini | audit |
| **review** | Adversarial review | Claude | D |
| **mdx** | MDX generation | Script | E |

> **Pipeline command**: `.venv/bin/python scripts/build_module.py {level} {seq} [--review] [--restart-from {phase}] [--force-phase {phase}]`
> Discover is non-blocking — skip with `--skip-discover`.

## Content Standards

*   **Word Count** (from `config.py` v2026-02-15): A1: 2000, A2: 3000, B1+: 4000, Seminars (HIST/BIO/ISTORIO/LIT/C2/OES/RUTH): 5000. If this date is older than config.py's latest change, re-read config.py.
*   **Activity Density**: A1-B1: ~8-10 activities/12 items; Seminar tracks: 3-9 activities/1+ items for deep analysis.
*   **Activities Test LANGUAGE, Not Content (Rule 10a)**: Can the learner answer without reading the Ukrainian text? If YES → it tests content recall, not language. REWRITE. No "У якому році..." / "Хто був..." / "Скільки..." quiz questions. Use "Згідно з текстом..." / "У тексті автор характеризує..." instead.
*   **ZNO Activities Exempt (Rule 10b)**: ZNO-format activities (`zno_row_select`, `zno_sentence_select`, `zno_error_find`, `zno_fill_ending`) test language mechanics directly and are exempt from Rule 10a.
*   **Audit Compliance**: Pass `audit_module.py` and `pipeline.py` gates.
*   **Word Targets are MINIMUMS**: NEVER reduce `word_target` to match short content. Expand content to meet targets.

## Plan Immutability

Plans in `plans/` are IMMUTABLE source of truth. Meta in `meta/` is mutable build config.
- READ plans to understand requirements → WRITE content that matches plan exactly
- NEVER modify plan files. If build cannot meet plan: STOP and REPORT.

## Module Ordering & Sequencing

**`curriculum/l2-uk-en/curriculum.yaml`** is the absolute source of truth for module ordering. Filenames and `sequence` fields in plan YAMLs are legacy.

```bash
# Find Module 5 of HIST
yq '.levels.hist.modules[4]' curriculum/l2-uk-en/curriculum.yaml
```

## Cross-Agent Review Architecture

- **Gemini builds** (A/B/C) → **Claude reviews** (Phase D). An LLM must NEVER review its own work.
- Do NOT manually request reviews from Claude outside the v4 pipeline — the review phase handles this automatically.
- Your review scores do NOT determine pass/fail. Automated audit gates are the real quality check.

## Anti-Gaming Enforcement (Automated Detection Active)

- **Automated detectors** scan reviews for: gaming language, all scores ≥9/10 with no issues, praise-only citations, fabricated citations
- Your review finds problems the automated system cannot catch — linguistic nuance, pedagogical depth, semantic accuracy
- **Caught cheating = all work from that session is discarded.**

## Zero-Tolerance Character Filter

**STRICTLY PROHIBITED**: Russian-only Cyrillic characters (`ы`, `ё`, `ъ`, `э`) or Russian words in Ukrainian content.
- Scan final output before returning. Avoid Surzhyk.
- Prefer active voice ("Ми зробили") over passive ("Було зроблено").

## Read Before Edit

ALWAYS `read_file` the target file IMMEDIATELY before ANY edit.
- Copy `old_string` EXACTLY from read output — never reconstruct from memory.
- **RE-READ BETWEEN SEQUENTIAL EDITS** — your context holds stale content after edits.
- **PREFER `write_file` FOR MULTI-CHANGE FIXES**: Read → mentally apply all changes → write complete new content.
- **NEVER use `cat -A`, `sed -n`, `head`, `tail`** — these destroy UTF-8 Ukrainian text.

## Virtual Environment

Always use `.venv/bin/python`. Never `python3` or `python` directly.

---

# 3. WORKFLOW

## Research Protocol

### Research-First Mandate (Seminar Tracks)

MANDATORY for `hist`, `bio`, `istorio`, `lit`, `oes`, `ruth`.

1. Research using ONLY Ukrainian sources (esu.com.ua, history.org.ua, uk.wikipedia.org, litopys.org.ua)
2. Russian-language sources (`ru.wikipedia.org`, `*.ru`) are STRICTLY FORBIDDEN
3. Save notes to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`
4. **Seminar Batch Limit**: 2 modules per batch (prevents context exhaustion)

### Sniper Search Strategy

Always include `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua` in research queries.

### Historiographical Mapping (Phase A enrichment)

For high-tension modules, include a "Contested Terms" table comparing Polish/Ukrainian/Russian terminology.

### Propaganda Filter

Check if phrasing echoes Russian dezinformatsiia framing (Volhynia, Holodomor, OUN/UPA).
- Treat your own knowledge base as "suspect" for Ukrainian history
- Rely EXCLUSIVELY on Phase A Ukrainian sources
- Debunk imperial/Soviet framing; humanize biographical subjects

## Build Process

### Content Quality

- **Theory-First**: Grammar/history explanations before practice
- **Anti-Hallucination**: Never fabricate facts. All claims grounded in verified academic reality.
- **Decolonization**: Debunk Russian/Soviet myths; highlight Ukrainian agency
- **Linguistic Depth**: Ukrainian quotes, proverbs (B1+), cultural context (NO IPA — use `pronunciation_audio` instead)
- **Typography**: ALWAYS use Ukrainian angular quotes `«...»`
- **Transliteration Ban (C1+)**: Latin transliteration STRICTLY PROHIBITED in ISTORIO/BIO
- **Semantic Nuance (C1+)**: Use modal hedging: «можливо», «ймовірно», «з одного боку», «водночас»

### Structural Rules

- **Strict Header Hierarchy**: `# Summary`, `# Activities` (H1), `##` (H2)
- **Redundancy Check**: No verbatim sentence copies between Summary/Conclusion and main body
- **Review Regeneration**: If >20% content rewrite, delete and regenerate the review file
- **Massive Academic Expansion**: Don't pad text — add new analysis layers to reach word counts naturally

## Audit & Review

### Quality Self-Check (Pre-Submission)

Your self-check ensures content is audit-ready before Phase D, reducing review iterations.

1. **Audit Gate**: Run `scripts/audit_module.sh {path}`. Fix errors until it passes.
2. **Self-Analysis** (informational — does NOT replace Phase D):
   - Richness ≥ 95%, Naturalness 10/10, Immersion ≥ 90% (B2+)
   - Activity count and types meet requirements
3. **Content Sanity**: engagement callouts present? Word count real? Headers match outline?

### Batch Operations

For large refactors, prefer creating disposable `fix_batch_*.py` scripts over manual editing.

## Communication

### GitHub-First Protocol

**GitHub issues and comments are the primary communication channel.**

### Bridge Commands

```bash
.venv/bin/python scripts/ai_agent_bridge.py ask-claude "message"  # Direct (immediate)
.venv/bin/python scripts/ai_agent_bridge.py send "message"        # Inbox drop (passive)
.venv/bin/python scripts/ai_agent_bridge.py inbox                 # Check your inbox
```

| Method | When | Example |
|--------|------|---------|
| `ask-claude` | Need response now | "Review #559" |
| `send` | FYI, non-blocking | "Modules 1-5 done" |

Bridge messages < 200 chars. Full reviews/proposals go on GitHub.

### Cross-Review Protocol

When Claude posts a review: read it → fix or counter-argue ON GITHUB → notify Claude.
When you finish work: post summary ON GITHUB → notify Claude.

### Session Start (Interactive Mode)

```bash
.venv/bin/python scripts/ai_agent_bridge.py inbox  # Check messages
gh issue view <N>                                    # Read referenced issues
```

## GitHub Issues Task Workflow

**When you receive a handoff, the GitHub issue contains ALL details.** Read the issue yourself.

```bash
gh issue view 506
```

### Handoff Response Flow

1. Check inbox → Read the ISSUE → Check configs yourself (`grep target scripts/audit/config.py`)
2. Choose: Autonomous (start working) or Collaborative (request UI trigger)
3. Update issue with progress: `gh issue comment <N> --body "✅ module-1 complete"`
4. When done: `ask-claude "Work complete on #N. Please review."`

### Task Labels

| Label | Meaning |
|-------|---------|
| `priority:blocking` | Blocks other work — do first |
| `priority:high` | High priority |
| `working:gemini` | YOU are working |
| `review:gemini` | Ready for your review |

---

# 4. TROUBLESHOOTING

## Common Audit Errors & Fixes

### DUPLICATE_SYNONYMOUS_HEADERS

**Error**: `Multiple headers contain 'Спадщина': Спадщина: Канон..., Агіографічна спадщина: ...`

**Problem**: Two section headers share a keyword.

**CORRECT FIX**: **RENAME** one header to NOT contain the duplicate word:
- `Агіографічна спадщина: Моделі святості` → `Житійна творчість: Моделі святості`
- Content stays the same, only header text changes.

### Engagement Callouts (4/5)

**Error**: `Engagement ❌ 4/5`

**Counted types** (use these):
- `[!note]`, `[!tip]`, `[!warning]`, `[!caution]`, `[!important]`
- `[!cultural]`, `[!history-bite]`, `[!myth-buster]`, `[!quote]`, `[!context]`
- `[!analysis]`, `[!source]`, `[!legacy]`, `[!reflection]`, `[!fact]`
- `[!culture]`, `[!military]`, `[!perspective]`, `[!biography]`

**NOT counted**: `[!question]`, `[!thought-provoker]`, `[!insight]`, `[!timeline]`, `[!today-link]`, `[!local-flavor]`

**FIX**: `[!question]` → `[!reflection]`, `[!thought-provoker]` → `[!note]`

### Richness Below Threshold

**Error**: `Richness ❌ 92% < 95% min`

Check breakdown in audit review file. Common cause: low `engagement` score (see above).

### YAML_SCHEMA_VIOLATION

**Common Causes & Fixes**:
- **Item Count**: `true-false` often requires **12 items** (check `minItems`)
- **Forbidden Fields**: `reading` forbids `tasks` — use `instruction`
- **Extra IDs**: `critical-analysis`/`essay-response` might forbid `id` (check `additionalProperties: false`)
- **ID Regex**: Must match `^reading-[a-z0-9-]+$` if defined

**CORRECT FIX**: Read the schema file directly:
```bash
.venv/bin/python -c "import json; print(json.dumps(json.load(open('schemas/activities-istorio.schema.json')), indent=2))" | jq '.definitions."true-false-istorio"'
```

### search_file_content Tool Broken

**NEVER use `search_file_content`** — it injects duplicate `--threads` flags.

```python
# CORRECT - use this
run_shell_command("rg 'somepattern' .")
```

### Debugging Schema Errors (Process)

1. Read the schema: `schemas/activities-{level}.schema.json`
2. Find your activity type definition
3. Check `minItems`, `required`, `additionalProperties`
4. **NEVER guess** — read the schema

---

# 5. REFERENCE

## Pedagogy by Level

| Level | Pedagogy | Focus |
|-------|----------|-------|
| A1-A2 | PPP (Present-Practice-Produce) | Clarity, building blocks |
| B1+ Grammar | TTT (Test-Teach-Test) | Guided discovery from context |
| B1+ Vocab/History | Narrative Arcs | Vocabulary in compelling stories |

## Module Counts (2026-03-01)

| Level | Modules | Word Target | Track Type |
|-------|---------|-------------|------------|
| **A1** | 64 | 2000 | Core |
| **A2** | 76 | 3000 | Core |
| **B1** | 100 | 4000 | Core |
| **B2** | 85 | 4000 | Core |
| **C1** | 106 | 4000 | Core |
| **C2** | 91 | 5000 | Core |
| **HIST** | 140 | 5000 | Seminar |
| **BIO** | 175 | 5000 | Seminar |
| **ISTORIO** | 136 | 5000 | Seminar |
| **LIT** | 221 | 5000 | Seminar |
| **OES** | 100 | 5000 | Seminar |
| **RUTH** | 112 | 5000 | Seminar |

> Always verify targets against `scripts/audit/config.py` — it is the single source of truth.

## Tool Usage

### Banned vs. Mandatory

| Feature | 🔴 BANNED | 🟢 USE THIS | Why? |
|---------|-----------|-------------|------|
| Search | `grep`, `find -exec grep` | **`rg` (ripgrep)** | 10x faster |
| Find Files | `find` | **`fd`** | Simpler, faster |
| Read File | `cat`, `head`, `tail`, `sed` | **`read_file`** | `cat -A` destroys UTF-8 |
| List Dir | `ls -la` | **`eza -l`** | Better formatting |
| JSON/YAML | `python -c ...` | **`jq`, `yq`** | Structured parsing |

### Python & Node

- Python 3.12.8 via `pyenv`. Always `.venv/bin/python`.
- Shell aliases available: `gs`=`git status`, `ga`=`git add`, `nr`=`npm run`

## File Structure (V2.0)

```
curriculum/l2-uk-en/
├── plans/{level}/{slug}.yaml          # IMMUTABLE source of truth
└── {level}/
    ├── meta/{slug}.yaml               # Build config
    ├── {slug}.md                      # Content prose
    ├── activities/{slug}.yaml         # Activities (bare list)
    ├── vocabulary/{slug}.yaml         # Vocabulary
    ├── review/{slug}-review.md        # LLM review (NOT in audit/)
    ├── audit/{slug}-audit.md          # Machine-generated audit
    └── status/{slug}.json             # Cached audit results
```

## Research Notes Template

Save to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`:

```markdown
# Research Notes: {Topic}

**Track**: {track} | **Module**: {slug} | **Researched**: {date} | **Sources**: {count}

## Key Facts Ledger
```yaml
subject: "{Topic}"
vital_status: "deceased"  # or "alive"
dates:
  birth: "YYYY-MM-DD"
  death: "YYYY-MM-DD"
  key_events:
    - year: YYYY
      event: "Event description"
primary_quotes:
  - text: "Exact Ukrainian quote"
    source: "Source, year"
    attribution: "Author"
forbidden_claims:
  - "Myth or propaganda to avoid"
```

## Основні факти
- Повне ім'я: | Роки життя: | Ключові місця:

## Хронологія
1. [Рік] - Подія

## Первинні джерела (цитати українською)
> "Цитата українською" — Джерело, рік

## Деколонізаційні нотатки
- Міфи для спростування: | Українська агентність:

## Contested Terms
| Поняття | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|

## Використані джерела
1. [Назва](URL)
```

### Research Quality Requirements

- 3+ Ukrainian sources (NEVER Russian)
- 1+ primary source quote in Ukrainian
- Decolonization notes — myths to debunk
- 5+ chronology events with years
- Contested Terms table (high-tension modules)

## Track Scoring & Playgrounds

- `npm run score:{track}`: Automated 10/10 scoring
- `npm run playgrounds`: Interactive HTML dashboards

## User Preferences

- **User**: Krisztian (Hungarian native)
- **Grammar Preference**: "Declension Group" (structural) approach
- **Goal**: Theory-first curriculum; Vibe app is secondary practice tool
