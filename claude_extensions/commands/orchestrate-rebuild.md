# Orchestrated Rebuild: Claude Orchestrates, Gemini Executes

> **Alternative to `/full-rebuild`**: Claude orchestrates phase-by-phase, Gemini executes focused tasks. Claude validates between phases and writes all files. Gemini produces text; Claude handles I/O.

## Usage

```
/orchestrate-rebuild {track} {num}
/orchestrate-rebuild {track} {num} --from={phase}   # Resume from specific phase
```

**Examples:**

```
/orchestrate-rebuild c1-bio 48              # Full orchestrated rebuild
/orchestrate-rebuild b2-hist 5 --from=content  # Resume from content phase
/orchestrate-rebuild a1 5                   # Core track (4-phase pipeline)
```

**Arguments:**

- `{track}` — Any track: seminar (b2-hist, c1-bio, c1-hist, lit, oes, ruth) or core (a1–c2, b2-pro, c1-pro)
- `{num}` — Module number (1-indexed)
- `--from={phase}` — Optional: force start from phase (research, meta, content, activities, audit, review)

---

## Architecture

**Shared filesystem is the data transport layer.** Both Claude and Gemini operate on the same local repo. The SQLite broker carries only short signals (~100-300 chars), not content.

```
Claude writes prompt file to disk
  → Claude sends SHORT broker message: "Phase 2. Prompt: /path/to/prompt.md"
  → Gemini reads prompt file from disk (shared filesystem)
  → Gemini responds with text (captured from Bash stdout by Claude)
  → Claude writes output to disk
  → Broker carries only: "Phase 2 done. Status: pass. 3500 words."
```

**Each phase = fresh Gemini call.** No session continuity between phases. Files on disk are the shared state.

**Prompt file location:**

```
curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-{N}-prompt.md
```

---

## Step 0: Resolve Module

```bash
# Seminar tracks
slug=$(yq ".levels.\"${track}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)

# Core tracks (numbered prefix)
slug=$(ls curriculum/l2-uk-en/${level}/${num_padded}-*.md 2>/dev/null | head -1 | xargs basename | sed 's/^[0-9]*-//' | sed 's/.md$//')
```

### Track Detection

```
SEMINAR_TRACKS: b2-hist, c1-bio, c1-hist, lit, oes, ruth → 6-phase pipeline
CORE_TRACKS: a1, a2, b1, b2, c1, c2, b2-pro, c1-pro → 4-phase pipeline
```

### File Paths

```
plan:           curriculum/l2-uk-en/plans/{track}/{slug}.yaml
research:       curriculum/l2-uk-en/{track}/research/{slug}-research.md
meta:           curriculum/l2-uk-en/{track}/meta/{slug}.yaml
content:        curriculum/l2-uk-en/{track}/{slug}.md  (or {num_padded}-{slug}.md for core)
activities:     curriculum/l2-uk-en/{track}/activities/{slug}.yaml
vocabulary:     curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml
review:         curriculum/l2-uk-en/{track}/review/{slug}-review.md
audit_log:      curriculum/l2-uk-en/{track}/audit/{slug}-audit.log
status:         curriculum/l2-uk-en/{track}/status/{slug}.json
orchestration:  curriculum/l2-uk-en/{track}/orchestration/{slug}/
```

---

## Step 1: Detect State

Same heuristics as `/full-rebuild`. Check which phases are complete:

| Check | Condition | Phase to skip |
|-------|-----------|--------------|
| Research exists with 3+ sources? | `research/{slug}-research.md` exists, has sources section | Skip Phase 0 |
| Meta has content_outline with allocations? | `meta/{slug}.yaml` has `content_outline` with `words` per section | Skip Phase 1 |
| Content meets 95% of word_target? | `.md` exists, `wc -w` >= 95% of `word_target` | Skip Phase 2 |
| Activities + Vocabulary parse? | Both YAML files exist, `yaml.safe_load()` succeeds | Skip Phase 3 |
| Audit passes? | `scripts/audit_module.sh` exit code 0 | Skip Phase 4 |
| Review exists with PASS? | `review/{slug}-review.md` exists, contains "PASS" | Skip Phase 5 |

**Print state report:**

```
📋 /orchestrate-rebuild {track} {num} — State Detection

  Phase 0 (Research):    ✅ DONE — research/{slug}-research.md (5 sources)
  Phase 1 (Meta):        ✅ DONE — meta/{slug}.yaml (7 sections, 4000 words)
  Phase 2 (Content):     ⏳ PENDING — {slug}.md not found
  Phase 3 (Activities):  ⏳ PENDING — activities not found
  Phase 4 (Audit):       ⏳ PENDING — depends on Phase 2-3
  Phase 5 (Review):      ⏳ PENDING — depends on Phase 4

  Mode: Orchestrated (Claude → Gemini)
▶️ Starting from Phase 2 (Content)
```

If `--from={phase}` specified, force start from that phase.

---

## Phase Execution Loop

For each incomplete phase:

### 1. Assemble Prompt

a. Read the phase template from `claude_extensions/phases/gemini/phase-{N}-{name}.md`
b. Read module-specific data (plan, meta, research, quick-ref)
c. Replace all `{PLACEHOLDER}` tokens with actual values
d. Write assembled prompt to `curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-{N}-prompt.md`

```bash
# Ensure orchestration directory exists
mkdir -p curriculum/l2-uk-en/{track}/orchestration/{slug}
```

### 2. Send to Gemini

Use `ask-gemini` with a SHORT message referencing the prompt file.

**Model preference**: Use `gemini-3-pro-preview` (more reliable for complex tasks). Fall back to `gemini-3-flash-preview` if Pro is unavailable or rate-limited.

**CRITICAL — Protect Claude's context window:**
Gemini streams thinking tokens mixed with actual content. A single call can produce 100K+ chars of "Wait, let me check..." thinking that pollutes Claude's context. **Never read raw Gemini output directly.** Instead:
1. Redirect stdout to a temp file
2. Extract only the delimited content with `sed`
3. Read only the extracted file

```bash
# Step 1: Send to Gemini, capture to temp file (NOT Claude's context)
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Read and execute the instructions at $(pwd)/curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-{N}-prompt.md. Return your output as text." \
  --task-id orchestrate-{slug} \
  --stdout-only \
  --model gemini-3-pro-preview \
  > /tmp/gemini-output-{slug}-phase-{N}.txt 2>&1

# Step 2: Extract ONLY delimited content (discard thinking tokens)
sed -n '/===REVIEW_START===/,/===REVIEW_END===/p' /tmp/gemini-output-{slug}-phase-{N}.txt \
  > /tmp/gemini-extracted-{slug}-phase-{N}.txt

# Step 3: Check if extraction succeeded
wc -l /tmp/gemini-extracted-{slug}-phase-{N}.txt
# If 0 lines: Gemini didn't produce delimited output → retry

# Step 4: Read ONLY the extracted file (small, clean)
```

**`--stdout-only` is CRITICAL** for four reasons:
1. **Read-only mode**: Gemini CLI runs with `--approval-mode plan` (NOT `-y` YOLO). This is enforced at the CLI level — Gemini literally cannot write files, edit files, send broker messages, or run modifying shell commands.
2. **Restrictive prompt**: Gemini gets an ultra-restrictive "TEXT GENERATOR" prompt with explicit prohibitions on file writing, message sending, and tool usage.
3. **Lean broker**: The broker only gets a short summary (~100 chars), not full output.
4. **Pre-acknowledged**: Message is marked as read immediately, preventing inbox leakage.

**IMPORTANT — No extra broker messages during orchestration:**
- Do NOT send status updates, acknowledgments, or progress messages TO Gemini via `mcp__message-broker__send_message`
- All communication flows through: prompt file on disk → `ask-gemini --stdout-only` → temp file → sed extraction
- The broker is a signal layer for Claude to track progress, NOT a chat channel with Gemini

**IMPORTANT — Never fix Gemini's output yourself:**
- If Gemini's output is bad (empty delimiters, wrong format, incomplete), send a retry prompt
- If Gemini produces content with issues (wrong Ukrainian, bad scaffolding), send a fix prompt TO GEMINI
- Claude is the orchestrator — validate, route, retry. NOT the worker.
- Max 3 retries per phase. If still failing, report to user.

### 3. Parse Output

Extract content between delimiters (using sed on the temp file, NOT reading raw output):
- `===RESEARCH_START===` ... `===RESEARCH_END===` → Phase 0
- `===META_OUTLINE_START===` ... `===META_OUTLINE_END===` → Phase 1
- `===CONTENT_START===` ... `===CONTENT_END===` → Phase 2
- `===ACTIVITIES_START===` ... `===ACTIVITIES_END===` → Phase 3 (activities)
- `===VOCABULARY_START===` ... `===VOCABULARY_END===` → Phase 3 (vocabulary)
- `===REVIEW_START===` ... `===REVIEW_END===` → Phase 5

### 4. Write to Disk

Claude writes the parsed output to the appropriate file:
- Phase 0 → `research/{slug}-research.md`
- Phase 1 → Update `content_outline` in `meta/{slug}.yaml`
- Phase 2 → `{slug}.md` (or `{num_padded}-{slug}.md`)
- Phase 3 → `activities/{slug}.yaml` and `vocabulary/{slug}.yaml`
- Phase 5 → `review/{slug}-review.md`

### 5. Validate

Run phase-specific validation gate:

| Phase | Validation |
|-------|-----------|
| 0 (Research) | File exists, has "Використані джерела" with 3+ entries, 5+ timeline items |
| 1 (Meta) | YAML parses, word allocations sum to word_target |
| 2 (Content) | `wc -w` >= word_target, all content_outline sections present as H2 |
| 3 (Activities) | Both YAML files parse, bare list at root, no unknown fields |
| 4 (Audit) | `scripts/audit_module.sh` exit code 0 |
| 5 (Review) | All 14 dimensions scored, average >= 6.0, verdict present |

### 6. Handle Failures

**On validation failure (max 3 retries per phase):**

1. Append specific errors to the prompt file:

```markdown
---

## Validation Errors (Attempt {N})

The following issues were found in your output:

{list of specific errors}

Fix these issues and return the COMPLETE output again (same format with delimiters).
```

2. Re-send to Gemini with the updated prompt file

**On `NEEDS_HELP:` marker:**

1. Read the `HELP_TYPE` from Gemini's output
2. Follow the protocol in `claude_extensions/phases/gemini/help-response.md`
3. Append reference material to the prompt file
4. Re-send to Gemini

**On delegation attempt** (Gemini says "please run /review-content" or "Claude should..."):

- Ignore the delegation request
- Re-send the original task prompt unchanged
- Gemini executes; Claude orchestrates

### 7. Next Phase

On validation pass: move to next incomplete phase.

---

## Phase 4: Audit (Claude-Only)

Phase 4 is NOT sent to Gemini. Claude runs audit directly:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

**If audit fails:**

1. Read the audit log
2. Assemble a fix prompt for Gemini with specific errors:
   - Missing sections from outline
   - Word count shortfalls per section
   - YAML schema violations
   - Activity field errors
3. Send fix prompt to Gemini (references content file path for Gemini to read)
4. Gemini returns fixes; Claude applies them
5. Re-run audit
6. Loop max 3 iterations

**If audit passes:** Continue to Phase 5 (Review).

---

## Phase 6: Build Pipeline (Claude-Only, Seminar Tracks)

After review passes, run the build pipeline:

```bash
.venv/bin/python scripts/pipeline.py l2-uk-en {track} {num} --steps generate
```

Verify status:

```bash
jq '.overall.status' curriculum/l2-uk-en/{track}/status/{slug}.json
# Must be "pass"
```

---

## Placeholder Reference

When assembling prompts, replace these tokens:

| Placeholder | Value Source |
|-------------|-------------|
| `{PLAN_PATH}` | Absolute path to plan YAML |
| `{META_PATH}` | Absolute path to meta YAML |
| `{RESEARCH_PATH}` | Absolute path to research notes |
| `{CONTENT_PATH}` | Absolute path to content .md |
| `{ACTIVITIES_PATH}` | Absolute path to activities YAML |
| `{VOCAB_PATH}` | Absolute path to vocabulary YAML |
| `{QUICK_REF_PATH}` | `claude_extensions/quick-ref/{LEVEL}.md` |
| `{SCHEMA_PATH}` | `schemas/activities-{track}.schema.json` |
| `{TOPIC_TITLE}` | Title from plan/meta |
| `{TRACK}` | Track identifier |
| `{LEVEL}` | Uppercase level for quick-ref (e.g., B2-HIST) |
| `{SLUG}` | Module slug |
| `{WORD_TARGET}` | From plan `word_target` |
| `{OVERSHOOT_TARGET}` | `word_target * 1.5` |
| `{ENGAGEMENT_MIN}` | From MODULE-RICHNESS-GUIDELINES-v2.md |
| `{EXAMPLE_MIN}` | From MODULE-RICHNESS-GUIDELINES-v2.md |
| `{IMMERSION_RULE}` | From quick-ref (e.g., "100% Ukrainian") |
| `{ACTIVITY_COUNT_TARGET}` | From meta or richness guidelines |
| `{VOCAB_COUNT_TARGET}` | From plan vocabulary count |
| `{AUDIT_WORD_COUNT}` | From audit_module.sh output |
| `{WORD_PERCENT}` | Computed: `(audit_words / word_target) * 100` |
| `{SECTIONS_PRESENT}` | Comma-separated list from audit |
| `{SECTIONS_MISSING}` | Comma-separated list from audit |
| `{ACTIVITY_COUNT}` | Count of activities in YAML |
| `{VOCAB_COUNT}` | Count of vocabulary items |
| `{ENGAGEMENT_COUNT}` | Count of engagement boxes in content |
| `{AUDIT_STATUS}` | "PASS" or "FAIL" from audit |

---

## Completion Report

```
✅ /orchestrate-rebuild {track} {num} — COMPLETE

  Phase 0 (Research):    ✅ {sources} sources, {quotes} quotes
  Phase 1 (Meta):        ✅ {sections} sections, {word_target} word target
  Phase 2 (Content):     ✅ {raw_words} raw words ({audit_words} audit)
  Phase 3 (Activities):  ✅ {vocab_count} vocab, {activity_count} activities
  Phase 4 (Audit):       ✅ All gates PASS
  Phase 5 (Review):      ✅ {score}/10
  Phase 6 (Pipeline):    ✅ Status PASS

  Mode: Orchestrated (Claude → Gemini)
  Broker messages: ~{msg_count} messages, all <300 chars
```

---

## When to Use This vs Solo `/full-rebuild`

| Scenario | Use |
|----------|-----|
| Gemini skips steps in solo mode | `/orchestrate-rebuild` (forces step-by-step) |
| Gemini produces thin content | `/orchestrate-rebuild` (Claude validates per phase) |
| Simple module, Gemini handles well solo | `/full-rebuild` (less overhead) |
| Need maximum control over each phase | `/orchestrate-rebuild` |
| Claude context is tight | `/full-rebuild` (delegates entirely) |
