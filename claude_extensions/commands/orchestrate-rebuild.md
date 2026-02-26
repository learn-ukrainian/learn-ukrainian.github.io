# Orchestrated Rebuild: Clean Slate Workflow

> **Claude orchestrates. Gemini builds. Human resolves failures.**
> Every module is built fresh from plan + meta. No resume logic. No Claude fallback.

> **Otaman Alternative:** For fully autonomous Gemini-orchestrated rebuilds, use `/otaman {track} {num}` in Gemini interactive mode. The Otaman handles the full Phase 0-7 pipeline autonomously (including Phase 7 adversarial final review in a separate session). Claude spot-checks a random sample only. See `.gemini/skills/otaman/SKILL.md`.

## Usage

```
/orchestrate-rebuild {track} {module_num}
```

**Examples:**

```
/orchestrate-rebuild b1 1      # Build B1 module 1 from scratch
/orchestrate-rebuild a1 3      # Build A1 module 3 from scratch
/orchestrate-rebuild c1-bio 5  # Build C1-BIO module 5 from scratch
```

---

## Bootstrap Order

This is the order for the full curriculum rebuild:

### Wave 1: Prove the workflow
1. **B1 1-5** — Metalanguage gateway (how to talk about grammar)
2. **A1 1-3** — Beginner foundation
3. **A2 1** — Bridge level validation
4. **B1 6** — Transition from metalanguage to main B1

### Wave 2: Complete core tracks (one at a time)
5. **A1** (remaining), **A2**, **B1**, **B2**, **C1**, **C2**

### Wave 3: Seminar + specialization tracks
6. **B2-HIST**, **C1-BIO**, **C1-HIST**, **LIT**, **OES**, **RUTH**
7. **LIT-\***, **B2-PRO**, **C1-PRO**

---

## Track Detection

```
SEMINAR_TRACKS: b2-hist, c1-bio, c1-hist, lit, oes, ruth → 6 phases (0-5)
CORE_TRACKS: a1, a2, b1, b2, c1, c2, b2-pro, c1-pro    → 4 phases (0, 2-4)
```

Core tracks use `phase-0-research-core.md` (lightweight). **Phase 1 (meta rebuild) is mandatory for ALL tracks** — existing meta may be from a weak/outdated prompt and must be regenerated from plan + research.

---

## Immersion Encoding (Bridge Modules)

B1 M01-M05 are **bridge modules** — students just finished A2 and need English scaffolding to learn Ukrainian metalanguage. From M06 onward, it's full Ukrainian immersion.

Each plan file must specify an `immersion` field (percentage). The orchestrator reads this and passes it to Phase 2's content prompt as `{IMMERSION_RULE}`.

| Module | Immersion | English Use |
|--------|-----------|-------------|
| B1 M01 | 70% | English intro + parenthetical equivalents for ALL new terms + English callouts for abstract concepts |
| B1 M02 | 70% | Parenthetical equivalents for new terms only + English in tip/note callouts |
| B1 M03 | 80% | English only in tip/note callouts for tricky concepts |
| B1 M04 | 85% | English only for disambiguation (false friends, confusing pairs) |
| B1 M05 | 85% | Minimal English — disambiguation only, checkpoint readiness |
| B1 M06+ | 95% | Full immersion |

**Scaffolding rules (L1 scaffolding with L2 primacy):**
1. **Ukrainian term first**, English equivalent in parentheses on first introduction only
2. After first introduction — Ukrainian term exclusively, no more English for that term
3. Brief English explanations allowed for abstract concepts — but in clearly marked callouts, not mixed into Ukrainian prose
4. Each module reduces English until M06 where immersion is full

The Phase 2 content template enforces these rules based on the `immersion` value.

---

## File Paths

```
plan:           curriculum/l2-uk-en/plans/{track}/{slug}.yaml
meta:           curriculum/l2-uk-en/{track}/meta/{slug}.yaml
content:        curriculum/l2-uk-en/{track}/{slug}.md
activities:     curriculum/l2-uk-en/{track}/activities/{slug}.yaml
vocabulary:     curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml
review:         curriculum/l2-uk-en/{track}/review/{slug}-review.md
status:         curriculum/l2-uk-en/{track}/status/{slug}.json
orchestration:  curriculum/l2-uk-en/{track}/orchestration/{slug}/
archive:        _archive/{track}/2026-02-12_22-14/
```

---

## Per-Module Workflow

For each module, Claude executes these steps sequentially:

### 1. Resolve module

```bash
# Get slug from curriculum manifest
slug=$(yq ".levels.\"${track}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
```

Read the plan and meta. Confirm they exist. If either is missing, stop.

### 2. Create orchestration directory

```bash
mkdir -p curriculum/l2-uk-en/{track}/orchestration/{slug}
mkdir -p curriculum/l2-uk-en/{track}/activities
mkdir -p curriculum/l2-uk-en/{track}/vocabulary
mkdir -p curriculum/l2-uk-en/{track}/review
mkdir -p curriculum/l2-uk-en/{track}/status
```

### 3. Execute phases

Run each phase sequentially. Each phase = one Gemini call.

**Artifact versioning:** Every phase prompt, output, audit, review, and friction report is saved in `orchestration/{slug}/`. Only the final passing versions get copied to canonical locations (`audit/`, `review/`, `status/`).

```
orchestration/{slug}/
  phase-0-prompt.md          # What we sent to Gemini
  phase-0-output.md          # Raw extracted output
  phase-2-prompt.md
  phase-2-output.md
  audit-attempt-1.log        # First audit run
  audit-attempt-2.log        # After Gemini fix
  phase-6-review-prompt.md   # Green Team review prompt (NEW session)
  phase-6-review-output.md   # Green Team review extracted
  phase-6b-fixes.md          # Log of which review issues were fixed/skipped
  friction-attempt-1.md      # Gemini's friction report (structured)
```

---

## Module Completion Criteria

**A module is NOT complete until ALL of these are true:**

1. ✅ Phase 1 meta rebuilt from plan + research (not reusing old meta)
2. ✅ Phase 4 audit passes (all strict gates green)
3. ✅ Phase 5 status + MDX generated
4. ✅ Phase 5b archive diff reviewed (regressions flagged)
5. ✅ Phase 6 Green Team review generated (not rubber-stamped)
6. ✅ Phase 6b review fixes applied (every actionable issue addressed)
7. ✅ Final audit re-passes after Phase 6b fixes
8. ✅ Phase 7 final review passes (adversarial QA in separate session) — **Otaman pipeline only**

**Phase 6b is NOT optional. The workflow proceeds automatically from Phase 6 → Phase 6b → Final audit.** Do NOT skip Phase 6/6b. Do NOT report completion after Phase 5. Do NOT stop and wait for human instruction between Phase 6 and Phase 6b. The module is done when the review cycle is complete and the final audit passes.

---

## Phases

### Phase 0: Research

**Template:** `claude_extensions/phases/gemini/phase-0-research-core.md` (core) or `phase-0-research-seminar.md` (seminar)

**What Claude does:**
1. Assemble prompt from template, replacing placeholders with plan/meta data
2. Write prompt to `orchestration/{slug}/phase-0-prompt.md`
3. Send to Gemini via `ask-gemini --stdout-only`
4. Save raw output to `orchestration/{slug}/phase-0-output.md`
5. Extract `===RESEARCH_START===` ... `===RESEARCH_END===`
6. Write to `curriculum/l2-uk-en/{track}/research/{slug}-research.md`
7. Extract `===FRICTION_START===` ... `===FRICTION_END===` → save to `orchestration/{slug}/friction-attempt-1.md`
8. Validate: file exists, has sources section

### Phase 1: Meta Rebuild (ALL tracks — mandatory)

**Template:** `claude_extensions/phases/gemini/phase-1-meta.md`

**Why mandatory:** Existing meta files may be the product of a weak or outdated prompt. The meta's `content_outline` dictates the entire content structure — if it's wrong, everything downstream is wrong. Always regenerate from plan + research.

**What the orchestrator does:**
1. Archive current meta: `cp meta/{slug}.yaml orchestration/{slug}/meta-old.yaml`
2. Assemble prompt with research notes + plan (NOT the old meta — the plan is source of truth)
3. Include the plan's `immersion` field in the prompt (controls English scaffolding level)
4. Send to Gemini, save output to `orchestration/{slug}/phase-1-output.md`
5. Extract `===META_OUTLINE_START===` ... `===META_OUTLINE_END===`
6. Update `content_outline` in `meta/{slug}.yaml` (preserve other meta fields: module, level, slug, etc.)
7. Extract friction report → `orchestration/{slug}/friction-attempt-{N}.md`
8. Validate: YAML parses, word allocations sum to word_target, section names are Ukrainian
9. Diff old vs new meta: `diff orchestration/{slug}/meta-old.yaml meta/{slug}.yaml` — log changes

### Phase 2: Content

**Template:** `claude_extensions/phases/gemini/phase-2-content.md` (monolithic) or per-section dispatch (see below)

**What Claude does:**
1. Assemble prompt with research + meta + plan + quick-ref
2. Send to Gemini, save output to `orchestration/{slug}/phase-2-output.md`
3. Extract `===CONTENT_START===` ... `===CONTENT_END===`
4. Write to `{slug}.md`
5. Extract friction report → `orchestration/{slug}/friction-attempt-{N}.md`
6. Validate: word count >= 90% of word_target, all H2 sections from outline present

**Word target overshoot strategy:** For monolithic dispatch, ask for `word_target * 1.5`. For section-by-section dispatch, ask for `section_allocation * 1.2` per section. Section dispatch is preferred for modules with word_target >= 4000 — individual sections are small enough that Gemini hits targets reliably without heavy overshoot. Heavy overshoot (2x+) causes bloated, repetitive content.

**For seminar tracks (word_target > 4000):** Content may need a 3a/3b split. If first output is under target, send a continuation prompt for the remaining sections.

#### Section-by-Section Dispatch (for word-count-challenged modules)

When monolithic Phase 2 consistently undershoots word targets (common for modules with word_target >= 4000), the orchestrator may split Phase 2 into per-section dispatches. This sends one Gemini prompt per H2 section, then assembles the results.

**Templates:**
- Section: `claude_extensions/phases/gemini/phase-2-content-section.md`
- Summary: `claude_extensions/phases/gemini/phase-2-summary.md`

**Assembly:** `scripts/assemble_sections.py`

**Workflow:**
1. Read `content_outline` from meta — each entry becomes one dispatch
2. For each section (sequential — coherence requires previous text):
   - Fill `phase-2-content-section.md` with section-specific placeholders
   - Include `{PREVIOUS_CONTENT_SUMMARY}` (condensed key points from prior sections)
   - Include `{CALLOUT_TYPES_USED}` (callout types already used in prior sections)
   - Send to Gemini, extract `===SECTION_CONTENT_START===` / `===SECTION_CONTENT_END===`
   - Save to `orchestration/{slug}/section_{N}.md`
3. After all sections: dispatch summary via `phase-2-summary.md`, save to `orchestration/{slug}/summary.md`
4. Assemble:
   ```bash
   .venv/bin/python scripts/assemble_sections.py \
     --sections-dir curriculum/l2-uk-en/{track}/orchestration/{slug}/ \
     --output curriculum/l2-uk-en/{track}/{slug}.md \
     --word-target {WORD_TARGET} \
     --meta-path curriculum/l2-uk-en/{track}/meta/{slug}.yaml
   ```
5. Validate: assembly script checks word count (>= 80% of target) and H2 header presence

**Key design decisions** (from #577):
- **Sequential dispatch** — each section needs previous text for coherence (no parallel)
- **First section** gets +200 words budget (carries the module intro), not a separate dispatch
- **Callout tracking** — `{CALLOUT_TYPES_USED}` prevents type repetition across sections
- **Seam prevention** — template instructs "continue seamlessly, no re-introductions"

**The Otaman** (`.gemini/skills/otaman/SKILL.md`) implements its own inline assembly for this pattern. This script is for the Claude-orchestrated path only.

### Phase 3: Activities + Vocabulary

**Template:** `claude_extensions/phases/gemini/phase-3-activities.md`

**What Claude does:**
1. Assemble prompt with content + plan + meta + schema
2. Send to Gemini, save output to `orchestration/{slug}/phase-3-output.md`
3. Extract `===ACTIVITIES_START===` / `===VOCABULARY_START===`
4. Write to `activities/{slug}.yaml` and `vocabulary/{slug}.yaml`
5. Extract friction report → `orchestration/{slug}/friction-attempt-{N}.md`
6. Validate: YAML parses, bare list at root, no unknown fields

### Phase 4: Audit (Claude-only)

**No Gemini call.** Claude runs:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

Save audit log to `orchestration/{slug}/audit-attempt-{N}.log` (increment N for each attempt).

**If audit passes:** Copy final audit to `audit/{slug}-audit.md`, continue to Phase 5.

**If audit fails:**
1. Read audit log for specific errors
2. Assemble fix prompt using `phase-fix.md` / `phase-fix-content.md` / `phase-fix-activities.md`
3. Send to Gemini, save fix output to `orchestration/{slug}/fix-attempt-{N}-output.md`
4. Extract friction report from fix output → `orchestration/{slug}/friction-attempt-{N}.md`
5. Apply fixes, re-audit (save as `audit-attempt-{N+1}.log`)
6. Loop max 3 iterations
7. **If still failing after 3 retries: STOP. Report to human.** Do NOT attempt to fix it as Claude.

> **CONTEXT ALIGNMENT RULE**: After all Phase 4 fixes are applied and audit passes, verify the **canonical content file** (`curriculum/l2-uk-en/{track}/{slug}.md`) is the final version. All subsequent phases (5, 6, 6b) must reference files at their canonical paths — never intermediate orchestration artifacts. If content was patched during fix iterations, the canonical `.md`, `activities/*.yaml`, and `vocabulary/*.yaml` files must reflect all applied fixes before proceeding.

### Phase 5: Archive Comparison + Status

**After audit passes:**

1. Compare new module against archived version:

```bash
# Word count comparison
old_words=$(wc -w < _archive/{track}/2026-02-12_22-14/{slug}.md 2>/dev/null || echo "0")
new_words=$(wc -w < curriculum/l2-uk-en/{track}/{slug}.md)
echo "Words: ${old_words} → ${new_words}"
```

2. Run MDX generation:

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en {track} {module_num}
```

3. Update status cache:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

4. Print completion report.

### Phase 5b: Archive Diff (orchestrator-only)

**No Gemini call.** The orchestrator compares the new module against the archived version to catch content regression.

**What the orchestrator does:**
1. If archive exists (`_archive/{track}/.../{slug}.md`), diff old vs new:

```bash
# Extract key elements from old version
rg -c '###' _archive/{track}/*/{slug}.md         # heading count
rg -ic 'мнемон|пам.ятка|формула' _archive/{track}/*/{slug}.md  # mnemonics
rg -ic 'шевченк|франк|українк|смотрицьк' _archive/{track}/*/{slug}.md  # cultural refs
wc -w < _archive/{track}/*/{slug}.md              # word count
```

2. Compare against new version:

```bash
rg -c '###' curriculum/l2-uk-en/{track}/{slug}.md
rg -ic 'мнемон|пам.ятка|формула' curriculum/l2-uk-en/{track}/{slug}.md
rg -ic 'шевченк|франк|українк|смотрицьк' curriculum/l2-uk-en/{track}/{slug}.md
wc -w < curriculum/l2-uk-en/{track}/{slug}.md
```

3. **Flag regressions:**
   - Heading count dropped >20% → "Structural flattening — review H3 density"
   - Mnemonic/formula present in old but missing in new → "Cultural anchor lost — consider restoring"
   - Cultural references dropped → "Cultural reference regression"
   - Activity total items dropped >15% → "Practice volume regression"

4. Save diff report to `orchestration/{slug}/archive-diff.md`
5. If critical regressions found: add them to the Phase 6 review prompt so the Green Team reviewer is aware

**If no archive exists:** Skip this phase (first-time build).

---

### Phase 6: Green Team Review (Gemini — NEW session)

**Anti-self-review architecture.** Gemini built the content in Phases 2-3. To avoid self-review bias, Phase 6 sends the review to Gemini in a **completely new session** (different task-id) where it has no memory of building the content. We frame it as "Green Team" — an independent quality reviewer.

**Why this works:** Session isolation means Gemini genuinely doesn't know it authored the content. Combined with adversarial prompting, this produces honest reviews instead of rubber-stamps.

**What Claude does:**

1. Write adversarial review prompt to `orchestration/{slug}/phase-6-review-prompt.md`
2. The prompt must include:
   - Green Team framing (independent reviewer, no prior relationship)
   - Anti-gaming rules (automated detection will reject rubber-stamps)
   - Minimum requirements: ≥3 real issues, ≥2 dimensions below 9, specific «» quotes
   - The 14-dimension scoring protocol from `review-content-v4.md`
   - Tier-specific guidance from `review-tiers/tier-{N}-{tier}.md`
   - Specific areas to scrutinize (historical claims, etymologies)
   - References to content files at their canonical paths (NOT orchestration/)
3. Send to Gemini with a **NEW task-id** (e.g., `green-review-{slug}`, NOT `orchestrate-{slug}`):

```bash
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Read and execute the review at $(pwd)/curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-6-review-prompt.md" \
  --task-id green-review-{slug} \
  --stdout-only \
  --model {model} \
  > /tmp/gemini-output-green-review-{slug}.txt 2>&1
```

4. Extract `===REVIEW_START===` ... `===REVIEW_END===` (use LAST block — template echo pattern)
5. Validate review against anti-gaming checks:
   - Not all dimensions ≥ 9/10
   - At least 1 real issue with «» quoted Ukrainian
   - No gaming language ("ensuring a high score", etc.)
   - **If rubber-stamp detected: retry with stronger adversarial prompt (max 2 retries)**
6. Write passing review to `review/{slug}-review.md`
7. Re-run audit to verify review gate passes:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

**Team identity:**
- 💙 Blue = Claude (architect, quality gate)
- 💛 Yellow/Gold = Gemini builder session (Phases 0-3)
- 💚 Green = Gemini reviewer session (Phase 6 — NEW session, no memory of building)

**Key rules:**
- NEVER use the same task-id as the build phases
- The review prompt must NOT reference orchestration artifacts or mention that Gemini built it
- If review is rubber-stamped after 2 retries: save as-is and flag for human review
- Extract friction report → `orchestration/{slug}/friction-attempt-{N}.md`

### Phase 6b: Fix Review Findings (Claude) — AUTO-PROCEEDS FROM PHASE 6

> **After Phase 6 review is saved, IMMEDIATELY proceed to Phase 6b. Do NOT stop and wait for human instruction.**

**After Phase 6 review passes, Claude fixes actionable issues found by the Green Team.**

This step ensures review findings don't just sit in a report — they get applied to the content.

**What Claude does:**

1. Read the review file at `review/{slug}-review.md`
2. For each issue in the "Issues Found" section, classify:
   - **Quick fix** (single word/sentence change): Fix directly in the content file
   - **Gemini fix** (needs new content, >50 words): Send to Gemini as a fix prompt
   - **Skip** (requires major structural rewrite): Document why and skip
3. Apply all quick fixes directly to `.md` and/or activities `.yaml`
4. For Gemini fixes: assemble a fix prompt, send to Gemini (use builder task-id), apply changes
5. Re-run audit to verify all gates still pass after fixes:

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{slug}.md
```

6. **Regenerate MDX** (Phase 6b changes content files, so Phase 5 MDX is stale):

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en {track} {module_num}
```

7. Update the review file's "Issues fixed" count
8. If audit fails after fixes: revert and report to human

**Classification guidelines:**
- Word substitutions, added sentences, expanded examples → Quick fix (Claude)
- New paragraphs, alternative explanations, structural changes → Gemini fix
- "Vary the presentation style across sections" → Skip (too broad)

**Key rule:** Fixing review findings is NOT optional. Every actionable issue must be addressed before the module is marked complete. Only "Skip" items (requiring major rewrites) can be deferred.

---

## Sending to Gemini

**CRITICAL — Protect Claude's context window:**

Gemini streams 10-100K chars of thinking tokens. Never read raw output.

```bash
# 1. Send to Gemini via stdin pipe, capture to temp file
cat curriculum/l2-uk-en/{track}/orchestration/{slug}/phase-{N}-prompt.md \
  | .venv/bin/python scripts/ai_agent_bridge.py ask-gemini - \
  --task-id orchestrate-{slug} \
  --stdout-only \
  --model {model} \
  > /tmp/gemini-output-{slug}-phase-{N}.txt 2>&1

# 2. Extract all delimited content for this phase (uses LAST match — handles template echo)
.venv/bin/python scripts/extract_phase.py \
  /tmp/gemini-output-{slug}-phase-{N}.txt \
  --phase {N} \
  --output-dir curriculum/l2-uk-en/{track}/orchestration/{slug}/ \
  --attempt 1

# 3. Read the extracted file(s) from orchestration dir
# Output files: phase-{N}-{tag}.md (e.g., phase-2-content.md)
# Friction report: friction-attempt-1.md (if present)
```

> **Fallback (if extract_phase.py is unavailable):**
> ```bash
> sed -n '/===TAG_START===/,/===TAG_END===/p' /tmp/gemini-output-{slug}-phase-{N}.txt \
>   > /tmp/gemini-extracted-{slug}-phase-{N}.txt
> wc -l /tmp/gemini-extracted-{slug}-phase-{N}.txt
> ```

**Model selection:**
- ALL tracks: `gemini-3-pro-preview`
- Flash is NOT used — it underproduces content and hallucinates word counts

**Rules:**
- `--stdout-only` is mandatory (Gemini runs read-only, can't write files)
- No broker messages during orchestration — prompt file on disk is the only channel
- Never fix Gemini's output yourself — send retry/fix prompts back to Gemini
- Max 3 retries per phase. After that → stop, report to human.
- **Canonical path rule:** Phases 3, 6, and 6b must always reference the **final validated** content files at their canonical paths (`{track}/{slug}.md`, `activities/{slug}.yaml`, `vocabulary/{slug}.yaml`) — never intermediate orchestration artifacts. This ensures Gemini reads the current state, not stale snapshots.

---

## Friction Report Format

Every Gemini phase output must include a friction report block:

```
===FRICTION_START===
**Phase**: Phase {N}: {name}
**Step**: {what was being done}
**Friction Type**: YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | NONE
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what Gemini changed, or "N/A"}
**Proposed Tooling Fix**: {if friction is a script/design issue, or "N/A"}
===FRICTION_END===
```

If no friction occurred, Gemini still outputs the block with `Friction Type: NONE`.

Claude extracts this and saves to `orchestration/{slug}/friction-attempt-{N}.md`.

---

## Retention Policy

- **During rebuild**: Keep all `orchestration/` dirs on disk. Don't delete until the full track is done. **`**/orchestration/` must NOT be in `.gitignore` during active rebuilds** — Gemini cannot read gitignored files. The pattern is commented out in `.gitignore` by default.
- **After track completion**: Uncomment `**/orchestration/` in `.gitignore`, summarize unique frictions into `docs/rebuild-friction-log.md`, then purge `orchestration/` dirs.
- **Failed/abandoned modules**: Keep `orchestration/` dir for debugging.
- **Staging prompt files**: Write all prompt files to `orchestration/{slug}/` — Gemini reads them from there directly. Do NOT use system `/tmp/` (outside Gemini's sandbox) or gitignored directories.

---

## Failure Protocol

**There is no Claude fallback.** When something fails:

1. Print what failed and why (specific errors, audit log excerpt)
2. Save the failed state in `orchestration/{slug}/`
3. Report to human: "Module {slug} failed at Phase {N}. Errors: ..."
4. Move on to the next module (or stop if human wants to investigate)

The human decides whether to:
- Retry with modified prompts
- Fix manually
- Skip the module for now

---

## Completion Report

After each module:

```
✅ /orchestrate-rebuild {track} {num} — COMPLETE

  Module:  {slug}
  Track:   {track}

  Phase 0 (Research):    ✅ {sources} sources
  Phase 1 (Meta):        ✅ Rebuilt from plan + research ({sections} sections, {word_target} words)
  Phase 2 (Content):     ✅ {new_words} words (was: {old_words} in archive)
  Phase 3 (Activities):  ✅ {activity_count} activities, {vocab_count} vocab items
  Phase 4 (Audit):       ✅ All gates PASS
  Phase 5 (MDX):         ✅ Generated
  Phase 5b (Diff):       ✅ Archive comparison — {regressions} regressions flagged
  Phase 6 (Review):      ✅ Green Team review — {overall_score}/10 ({issue_count} issues found)
  Phase 6b (Fixes):      ✅ {fixed_count}/{fixable_count} review issues fixed ({skipped_count} skipped)
  Phase 7 (Final Review): ✅ Adversarial QA — {verdict} ({fix_count} fixes applied)

  Archive comparison:
    Words:     {old_words} → {new_words} ({delta})
    Activities: {old_act_count} → {activity_count}
```

---

## Placeholder Reference

| Placeholder | Source |
|-------------|--------|
| `{PLAN_PATH}` | `curriculum/l2-uk-en/plans/{track}/{slug}.yaml` |
| `{META_PATH}` | `curriculum/l2-uk-en/{track}/meta/{slug}.yaml` |
| `{RESEARCH_PATH}` | `curriculum/l2-uk-en/{track}/research/{slug}-research.md` |
| `{CONTENT_PATH}` | `curriculum/l2-uk-en/{track}/{slug}.md` |
| `{ACTIVITIES_PATH}` | `curriculum/l2-uk-en/{track}/activities/{slug}.yaml` |
| `{VOCAB_PATH}` | `curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml` |
| `{QUICK_REF_PATH}` | `claude_extensions/quick-ref/{LEVEL}.md` |
| `{SCHEMA_PATH}` | `schemas/activities-{track}.schema.json` |
| `{TOPIC_TITLE}` | From plan title |
| `{TRACK}` | Track identifier |
| `{LEVEL}` | Uppercase level for quick-ref |
| `{SLUG}` | Module slug |
| `{WORD_TARGET}` | From level config (`scripts/audit/config.py`) |
| `{OVERSHOOT_TARGET}` | `word_target * 1.5` (monolithic) or `section_allocation * 1.2` (section dispatch) |
| `{ENGAGEMENT_MIN}` | From MODULE-RICHNESS-GUIDELINES-v2.md |
| `{EXAMPLE_MIN}` | From MODULE-RICHNESS-GUIDELINES-v2.md |
| `{IMMERSION_RULE}` | From quick-ref |
| `{SKILL_IDENTITY}` | From `.gemini/skills/full-rebuild-{skill}/SKILL.md` opening line (e.g., "Senior Biographer and Historian") |
| `{PERSONA_FLAVOR}` | From skill's Persona Registry (e.g., "Investigative Journalist", "The Ethnographer") |
| `{PERSONA_VOICE}` | From plan `persona.voice` |
| `{PERSONA_ROLE}` | From plan `persona.role` |
