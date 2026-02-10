# Seminar Track Full-Rebuild Workflow

> **Alternative:** `/orchestrate-rebuild` — Claude orchestrates phase-by-phase, Gemini executes focused tasks. Use when Gemini skips steps or produces thin content in solo mode.

> **Scope:** Mandatory standard for rebuilding or creating modules in seminar tracks: `b2-hist`, `c1-bio`, `c1-hist`, `lit`, `oes`, and `ruth`. Prioritizes research-driven, decolonized, and linguistically rich content.

## Usage

```
/full-rebuild {track} {module_num}
/full-rebuild {track} {module_num} --from=PHASE   # Resume from specific phase
```

**Examples:**

```
/full-rebuild c1-hist 4               # Runs all phases (resumable)
/full-rebuild c1-hist 4 --from=review # Force start from review phase
/full-rebuild b2-hist 5
```

**Arguments:**

- `{track}` - Seminar track level (b2-hist, c1-bio, c1-hist, lit, oes, ruth)
- `{module_num}` - Module number (1-indexed)
- `--from=PHASE` - Optional: force start from a specific phase (research, meta, content, yaml, audit, review, mdx)

---

## RESUMABLE: Run same command across sessions

**This command is idempotent.** Run it in multiple sessions — it detects completed phases and picks up where it left off.

```
Session 1: /full-rebuild c1-hist 4  → research + meta + content (context fills up)
Session 2: /full-rebuild c1-hist 4  → skips done phases, does audit + review
Session 3: /full-rebuild c1-hist 4  → skips done phases, does MDX
```

---

## Step 0: Resolve Module

```bash
slug=$(yq ".levels.\"${track}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

File paths:

```
research:   curriculum/l2-uk-en/{track}/research/{slug}-research.md
meta:       curriculum/l2-uk-en/{track}/meta/{slug}.yaml
content:    curriculum/l2-uk-en/{track}/{slug}.md
vocab:      curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml
activities: curriculum/l2-uk-en/{track}/activities/{slug}.yaml
review:     curriculum/l2-uk-en/{track}/review/{slug}-review.md
audit_log:  curriculum/l2-uk-en/{track}/audit/{slug}-audit.log (auto-generated)
status:     curriculum/l2-uk-en/{track}/status/{slug}.json
```

## Step 1: Detect State (skip completed phases)

Check which phases are already complete. **Unless `--from` is specified, auto-detect:**

| Check                                           | Condition                                                                          | Phase to skip |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- | ------------- |
| Research file exists and has 3+ sources?        | `research/{slug}-research.md` exists, has `## Використані джерела` with 3+ entries | Skip Phase 0  |
| Meta has content_outline with word allocations? | `meta/{slug}.yaml` has `content_outline` with `words` per section                  | Skip Phase 1  |
| Content meets 95% of word_target?               | `.md` file exists, `wc -w` >= 95% of `word_target`                                 | Skip Phase 2  |
| Vocab + activities YAML exist and parse?        | Both files exist, `yaml.safe_load()` succeeds                                      | Skip Phase 3  |
| Audit passes?                                   | Run `scripts/audit_module.sh`, exit code 0                                         | Skip Phase 4  |
| Review file exists with PASS?                   | `review/{slug}-review.md` exists, contains "PASS"                                  | Skip Phase 5  |
| Status JSON shows PASS?                         | `status/{slug}.json` exists, `overall.status: "pass"`                              | Skip Phase 6  |

**Print state report before starting:**

```
📋 /full-rebuild {track} {num} — State Detection

  Phase 0 (Research):  ✅ DONE — research/{slug}-research.md (5 sources)
  Phase 1 (Meta):      ✅ DONE — meta/{slug}.yaml (7 sections, 4000 words)
  Phase 2 (Content):   ⏳ PENDING — {slug}.md not found
  Phase 3 (YAML):      ⏳ PENDING — activities not found
  Phase 4 (Audit):     ⏳ PENDING — depends on Phase 2-3
  Phase 5 (Review):    ⏳ PENDING — depends on Phase 4
  Phase 6 (MDX):       ⏳ PENDING — depends on Phase 5

▶️ Starting from Phase 2 (Content)
```

**If `--from=PHASE` is specified, force start from that phase regardless of state.**

### Monitor Integration

Report progress to the batch monitor so it shows up in the playground:

```bash
# At start of module processing:
.venv/bin/python scripts/batch_report.py {track} {slug} running --mode manual

# When module passes all gates:
.venv/bin/python scripts/batch_report.py {track} {slug} pass --mode manual

# If module fails and you're moving on:
.venv/bin/python scripts/batch_report.py {track} {slug} fail --mode manual
```

---

## Phase 0: Research-First Mandate

> **CRITICAL: Research is a BLOCKING dependency.**
> Phase 0 MUST fully complete before ANY work on Phases 1-5 begins.
> Do NOT launch research in background and continue — that defeats the entire purpose.
> The research exists to prevent writing from memory. If you don't wait for it, you ARE writing from memory.

**Before researching, load content_outline from meta** to structure notes by section:

```bash
yq '.content_outline' curriculum/l2-uk-en/{track}/meta/{slug}.yaml
```

- **Sniper Search**: Use `google_web_search` with `site:esu.com.ua OR site:history.org.ua OR site:elib.nlu.org.ua` for academic accuracy.
- **Source Filter**: STRICTLY Ukrainian-language sources only; Russian sources are prohibited.
- **Notes**: Capture chronology, primary quotes, and decolonization angles. Save to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`.
- **Section-mapped content**: Structure research notes with headings that match `content_outline` sections. This makes Phase 2 mechanical: read section research → write section.
- **Engagement Mapping**: Identify at least 6 engagement hooks (`[!myth-buster]`, `[!history-bite]`, `[!context]`, `[!quote]`, `[!decolonization]`) from research data. Assign each to a specific section.
- **Completion Gate**: Research notes file must exist and contain verified facts BEFORE proceeding to Phase 1.

### Phase 0.5: Historiographical Mapping (High-Tension Modules)

> **WHEN:** Any module where the same events are described differently by Ukrainian, Polish, Russian, or Soviet historiographies.
> Examples: Polish-Ukrainian relations, Volyn 1943, Soviet repressions, Crimea, Donbas, Cossack-era conflicts.
> **SKIP** for modules with no contested narratives (e.g., pure linguistics, cultural practices).

**Before writing content**, create a **Contested Terms Table** in the research notes:

```markdown
## Contested Terms / Historiographical Mapping

| Concept              | Enemy framing                          | Neighbor framing                       | Ukrainian (decolonized)                                      |
| -------------------- | -------------------------------------- | -------------------------------------- | ------------------------------------------------------------ |
| Волинські події 1943 | "Wołyń massacre" (одностороння жертва) | "tragedia wołyńska" (спільна трагедія) | Волинська трагедія (взаємне насильство в контексті окупації) |
| Переяславська угода  | "воссоединение" (возз'єднання)         | —                                      | Переяславська рада (військовий союз, не злиття)              |
```

**Rules:**

- Minimum 3 rows for high-tension modules, 1-2 for moderate tension
- The "Ukrainian (decolonized)" column is the ONLY framing used in content
- Enemy/neighbor columns exist to show what the module must NOT echo
- If any phrase in final content matches "Enemy framing" column → **auto-fail**

## Phase 1: Metadata Alignment (`meta/{slug}.yaml`)

- **Plan Sync**: Match the immutable `word_target` from `plans/`.
- **Granular Outline**: Refactor `content_outline` into H2 sections with word allocations summing to the target.
- **Vital Status**: Verify subject's status to ensure correct section naming (e.g., "Legacy" vs. "Impact").

## Phase 2: Content Hydration (`{slug}.md`)

> **OVERSHOOT RULE: Write to 1.5× the word_target on first draft.**
> For a 4000-word target, write 5500–6000 words. Trimming is cheap; expanding is expensive.
> Expanding burns 30%+ of context window in iterative audit-fix cycles. Overshoot eliminates this.

**Before writing:**

1. Read research notes (`research/{slug}-research.md`)
2. Read meta content_outline (`meta/{slug}.yaml`)
3. Read template (`docs/l2-uk-en/templates/`) and quick-ref (`claude_extensions/quick-ref/`)
4. **Pre-plan callouts**: List where each of the 6+ engagement callouts will go (which section, which type). Write this list FIRST.

**While writing:**

- Write section-by-section following content_outline, using research notes for each section
- Target 1.5× word allocation per section
- Use research notes exhaustively — every fact, quote, and date should appear
- Typography: Ukrainian angular quotes `«...»`

> **SECTION WORD BUFFER: Audit counts ~100-150 fewer words than `wc -w`.**
> The audit excludes blockquote text, callout markup, and some formatting from word counts.
> For a section with a 600-word allocation, write 700-750 raw words to safely clear the audit threshold.
> This gap is consistent — plan for it rather than discovering it during audit-fix cycles.

> **FACT ALLOCATION RULE (Duplicate Prevention):**
> Every unique date, statistic, primary source quote, or named figure introduction MUST appear in exactly ONE H2 section.
>
> - Before writing each section, check: "Has this fact already been introduced in an earlier section?"
> - If yes: reference it briefly (e.g., "Як зазначалося вище...") but do NOT re-present the full data
> - If no: introduce it fully with context
> - **Treat sections as thematic silos**: Section A = "What happened", Section B = "Why it matters", Section C = "How historians debated it"
> - This prevents the #1 content quality issue: identical statistics or quotes appearing in multiple sections

## Phase 3: Atomic YAML Generation

> **SCHEMA-FIRST: Read the activity schema BEFORE writing any activities.**
>
> ```
> schemas/activities-{track}.schema.json
> ```
>
> Note which fields each activity type supports. `additionalProperties: false` means unlisted fields cause audit failure. Only `reading` type has `id` field in seminar tracks.
> `essay-response` rubric: `criteria`/`description`/`points` (NOT `criterion`/`weight`).
>
> **YAML FORMAT: Activities must be a BARE LIST at root level.**
>
> ```yaml
> # ✅ CORRECT — bare list at root
> - type: reading
>   title: ...
>
> # ❌ WRONG — dictionary wrapper (causes audit failure)
> activities:
>   - type: reading
>     title: ...
>
> # ❌ WRONG — metadata headers (not part of schema)
> module: some-slug
> level: c1-hist
> activities:
>   - type: reading
> ```
>
> Do NOT add `module:`, `level:`, `id:` (except on `reading`), or any wrapper keys.

- **Enriched Vocabulary**: Create `vocabulary/{slug}.yaml` matching the count target defined in the plan/meta. Include IPA and English translations.
- **Pedagogical Activities**: Create `activities/{slug}.yaml` following track-specific schemas (Seminar style: **Reading Input -> Analytical Output**).

> **ACTIVITY TYPE CONSTRAINTS: Check allowed/forbidden types BEFORE writing activities.**
>
> ```bash
> .venv/bin/python -c "
> import sys; sys.path.insert(0, 'scripts')
> from audit.config import get_level_config
> cfg = get_level_config('{LEVEL}', '{FOCUS}')
> print('ALLOWED:', sorted(cfg.get('priority_types', set())))
> print('FORBIDDEN:', sorted(cfg.get('forbidden_types', set())))
> "
> ```
>
> Using a forbidden type wastes the entire activity phase — audit will auto-FAIL.
> Seminar tracks typically allow: `reading`, `essay-response`, `critical-analysis`, `comparative-study`.
> Seminar tracks typically forbid: `quiz`, `fill-in`, `cloze`, `match-up`, `unjumble`, `anagram`, etc.

## Phase 4: Technical Audit (`scripts/audit_module.py`)

> **BATCH FIX: Run audit ONCE, collect ALL errors, fix ALL at once, re-audit ONCE.**
> Never fix one error at a time. The iterative fix→audit→fix→audit cycle wastes context.
> Read the full audit log, list every failure, apply all fixes in one pass, then re-audit.

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

- **Strict Gates**: All must pass:
  - **Outline Compliance**: Headers must match the metadata outline exactly.
  - **Word Density**: Every section must meet its allocated target. (With 1.5× overshoot, this should pass first try.)
  - **Schema Integrity**: Validate activity IDs and field names against `schemas/`.
  - **Richness Score**: Ensure 95%+ richness through vocabulary density and engagement.

## Phase 5: Review-Content-v4 (Deep Quality & Scoring)

> **CRITICAL: YOU (Gemini) are the reviewer.**
> Do NOT ask Claude. Do NOT skip this step.
> You must rigorously apply the V4 Deep Review standard yourself by reading `claude_extensions/commands/review-content-v4.md` and executing it step-by-step.
> **BE BRUTALLY HONEST AND CRITICAL.** Do not sugarcoat. If it's trash, say it's trash and fix it.

- **Linguistic Sophistication**: Verify the Ukrainian register (e.g., Academic for C1). Check for high-level connectors and specialized terminology.
- **IPA Stress Verification**: Check every IPA transcription in vocabulary for correct stress placement.
- **Narrative Logic**: Ensure the decolonized argument is coherent and builds toward the production task.
- **Scoring**: Perform a granular 0-10 scoring on the following 14 dimensions:
- **Re-audit after fixes**: Run audit again to confirm PASS after applying review fixes.

### Review Dimensions (14)

Score each 0-10 in the review file (`review/{slug}-review.md`):

| #   | Dimension           | What to evaluate                                                    |
| --- | ------------------- | ------------------------------------------------------------------- |
| 1   | Experience Quality  | Engagement, intellectual depth, narrative momentum                  |
| 2   | Coherence           | Logical section flow, smooth transitions, building argument         |
| 3   | Relevance           | Plan alignment: sections match outline, vocabulary from plan used   |
| 4   | Educational         | Scaffolding quality, concept explanation, analytical frameworks     |
| 5   | Language            | Ukrainian naturalness, register correctness, no Russianisms/calques |
| 6   | Pedagogy            | Activity types match track style, no forbidden drill types          |
| 7   | Immersion           | % Ukrainian, non-Ukrainian elements contextually justified          |
| 8   | Activities          | Count, type variety, rubric quality, model answer depth             |
| 9   | Richness            | Engagement boxes, cultural references, primary source density       |
| 10  | Humanity            | Teacher voice, warmth vs. robotic tone, rhetorical questions        |
| 11  | LLM Fingerprint     | Absence of AI cliches, authentic writing style                      |
| 12  | Linguistic Accuracy | Historical facts verified, no fabricated quotes, dates correct      |
| 13  | Propaganda Filter   | Decolonized narrative, empire named, no imperial euphemisms         |
| 14  | Semantic Nuance     | Hedging markers (5+ per 1000 words for C1+), epistemic modality     |

**Review file format:** Follow the template in `curriculum/l2-uk-en/lit/review/01-introduction-to-kotliarevsky-review.md` — includes scores table, issues found/fixed, verification summary, post-fix audit results, and PASS/FAIL recommendation.

## Phase 6: Build Pipeline

- **MDX Generation**: Run `.venv/bin/python scripts/pipeline.py l2-uk-en {track} {num} --steps generate`
- **Status Check**: Confirm that `status/{slug}.json` has `overall.status: "pass"` (NOT `audit_passed` — that field doesn't exist).

---

## Completion Report

```
✅ /full-rebuild {track} {num} — COMPLETE

  Phase 0 (Research):  ✅ {sources} sources, {quotes} quotes
  Phase 1 (Meta):      ✅ {sections} sections, {word_target} word target
  Phase 2 (Content):   ✅ {raw_words} raw words ({audit_words} audit)
  Phase 3 (YAML):      ✅ {vocab_count} vocab, {activity_count} activities
  Phase 4 (Audit):     ✅ All gates PASS
  Phase 5 (Review):    ✅ {score}/10
  Phase 6 (MDX):       ✅ Pipeline PASS
```
