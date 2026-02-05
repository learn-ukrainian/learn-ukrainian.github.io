# /module

Unified entry point for building modules using the 7-phase workflow (content + skeleton deploy).

> **⚠️ ONE RULE: Module is NOT done until audit PASSES.**
>
> This command includes an audit+fix loop. Keep fixing until all gates pass.
> Do NOT report "DEPLOYED" until audit shows 100% pass. No exceptions.

> **Vocabulary enrichment runs separately** after the entire track/course is content-complete.

> **🤝 COLLABORATION RULE: Write yourself, ask for help when stuck.**
>
> - **YOU must write the content** - never delegate writing to the other agent
> - **When stuck or uncertain** - ask the other agent for help (research, facts, validation, suggestions)
> - **Never guess or hallucinate** - if you don't know, ask instead of making up content
> - **Two agents = faster solutions** - use collaboration for research, fact-checking, Ukrainian validation
>
> **How to ask for help:**
> ```bash
> # Quick way (sends + invokes):
> .venv/bin/python scripts/ai_agent_bridge.py ask-gemini "Your question here" --task-id module-help
>
> # Check for response:
> mcp__message-broker__receive_messages(for_llm="claude", task_id="module-help")
> ```
>
> Example: "Gemini, can you verify when Заньковецька received her title?" NOT "Gemini, write the biography section."

## Usage

```
/module {level} {num}               # Build single module (phases 1-7)
/module {level} {start}-{end}       # Batch build
/module {level} {num} --from=PHASE  # Resume from specific phase
/module {level} {num} --refresh     # Refresh meta+activities (preserves .md content)
/module {level} {num} --check       # Check status only
```

## Examples

```bash
/module b2-hist 5               # Build module 5 (content + skeleton deploy)
/module b2-hist 1-5             # Build modules 1-5
/module b2-hist 5 --from=lesson # Resume from phase 3 (lesson)
/module c1-bio 12 --check       # Show which phases are complete
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────┐
│ CONTENT BUILD (Phases 1-6) - Can run in parallel        │
├─────────────────────────────────────────────────────────┤
│ Phase 1: /module-meta        → meta/{slug}.yaml         │
│ Phase 2: /module-meta-qa     → Validate meta            │
│          ↓ LOCKED                                       │
│ Phase 3: /module-lesson      → {slug}.md                │
│ Phase 4: /module-lesson-qa   → Validate content         │
│          ↓ LOCKED                                       │
│ Phase 5: /module-act         → activities/{slug}.yaml   │
│ Phase 6: /module-act-qa      → Validate activities      │
│          ↓ LOCKED                                       │
├─────────────────────────────────────────────────────────┤
│ SKELETON DEPLOY (Phase 7)                               │
├─────────────────────────────────────────────────────────┤
│ Phase 7: /module-integrate   → Create skeleton vocab    │
│                              → Generate MDX             │
│                              → Deploy module            │
└─────────────────────────────────────────────────────────┘

              Later, when track is complete:

┌─────────────────────────────────────────────────────────┐
│ VOCAB ENRICHMENT (Separate command)                     │
├─────────────────────────────────────────────────────────┤
│ /module-vocab-enrich {level}  → Extract vocab M1→MN     │
│                               → Update MDX with vocab   │
│                               → Update vocabulary.db    │
└─────────────────────────────────────────────────────────┘
```

---

## Instructions

Parse arguments: $ARGUMENTS

> **📄 Seminar Tracks (b2-hist, c1-bio, c1-hist, lit, oes, ruth):**
>
> Before generating content, read `docs/RESEARCH-FIRST-WORKFLOW.md`
>
> These tracks require **Phase 0: Deep Research** before writing:
> 1. **Run /research {topic}** → Uses Ukrainian sources only
> 2. Create outline from research notes
> 3. Write with notes → 4. Activities (4-9 only!)
>
> **⛔ RESEARCH GATE ENFORCED**: Module generation will check for research file.
> If `audit/{slug}-research.md` does not exist, you MUST run `/research` first.
> To skip (NOT recommended): `/module {level} {num} --no-research`
>
> Research notes saved to `audit/{slug}-research.md` for reference.

> **📋 Plan vs Template Conflicts:**
>
> When plan `content_outline` differs from template required sections:
> - **Plan sections take precedence** - use plan section names exactly
> - Template is guidance, not strict requirements
> - Ensure content COVERS template topics (under plan section names)
> - See `claude_extensions/skills/module-restructure-guide.md` for details
> - **DO NOT ask which approach to use** - plan always wins when it has content_outline

**Quick Reference - File Naming:**

| Level Type | Example | File Path |
|------------|---------|-----------|
| Core (a1, a2, b1, b2, c1, c2) | `/module a1 5` | `curriculum/l2-uk-en/a1/05-daily-routine.md` |
| Track (b2-hist, c1-bio, etc.) | `/module b2-hist 41` | `curriculum/l2-uk-en/b2-hist/kozatstvo-vytoky.md` |

**Tracks use slug-only filenames (no number prefix). Always resolve via curriculum.yaml.**

**Extra Resources:** `docs/l2-uk-en/resources/external_resources.yaml` contains podcasts, videos, and external links that can be referenced in modules.

---

### Step 1: Parse Input

Extract:

- `level`: a1, a2, b1, b2, c1, c2, b2-hist, c1-bio, c1-hist, lit
- `num`: Module number or range (e.g., `5` or `1-5`)
- `flags`: --from=PHASE, --check, --refresh (optional)

**If range detected:** Jump to Batch Mode.

### Step 1.5: Pre-flight Check (NEW)

**Before any building, run pre-flight validation:**

```bash
.venv/bin/python scripts/preflight_check.py curriculum/l2-uk-en/${level}/${slug}.md
```

**What it catches early:**
- ❌ Missing plan file
- ❌ Missing meta file
- ❌ Module number mismatch between plan and meta
- ⚠️ Missing word target
- ⚠️ Low vocabulary hints count

**If pre-flight FAILS with blockers (❌):** Stop and fix before proceeding.

### Step 1.6: Research Gate (Seminar Tracks Only)

**For seminar tracks ONLY (b2-hist, c1-bio, c1-hist, lit, oes, ruth):**

**SMART ENFORCEMENT**: Research is required only for:
1. **New modules** - No .md file exists yet
2. **Explicit rewrite** - Using `--from=lesson` flag
3. **Word count failures** - Module under target needs expansion

**NOT required for**: Existing modules that pass audit (content already written).

```bash
# Define seminar tracks
SEMINAR_TRACKS="b2-hist c1-bio c1-hist lit oes ruth"

# Check if current level is a seminar track
if echo "$SEMINAR_TRACKS" | grep -qw "$level"; then
  content_file="curriculum/l2-uk-en/${level}/${slug}.md"
  research_file="curriculum/l2-uk-en/${level}/audit/${slug}-research.md"

  # Determine if this is NEW content or existing content
  if [[ -f "$content_file" ]]; then
    # Content exists - check if it passes word count
    word_count=$(wc -w < "$content_file" | tr -d ' ')
    # Get word target from meta (default 3500 for seminar)
    word_target=$(yq '.word_target // 3500' "curriculum/l2-uk-en/${level}/meta/${slug}.yaml" 2>/dev/null || echo "3500")
    threshold=$((word_target * 95 / 100))

    if [[ "$word_count" -ge "$threshold" ]]; then
      # Content exists AND meets word target - SKIP research gate
      echo "✅ Existing content passes word count ($word_count >= $threshold)"
      echo "   Research gate: SKIPPED (module already has content)"

      # Still show research file status if it exists
      if [[ -f "$research_file" ]]; then
        echo "   Research notes: Available at $research_file"
      else
        echo "   Research notes: Not found (optional for existing content)"
      fi
    else
      # Content exists but UNDER word target - needs expansion with research
      echo "⚠️ Content under target: $word_count / $word_target words"

      if [[ ! -f "$research_file" ]]; then
        if [[ "$flags" != *"--no-research"* ]]; then
          echo "⛔ RESEARCH REQUIRED FOR EXPANSION"
          echo ""
          echo "Module content is under word target and needs expansion."
          echo "Research is required before expanding content."
          echo ""
          echo "Run: /research '{topic}'"
          echo "Then: /expand curriculum/l2-uk-en/${level}/${slug}.md"
          echo ""
          echo "To skip (NOT recommended): /module ${level} ${num} --no-research"
          exit 1
        fi
      fi
    fi
  else
    # NEW module - no content exists yet
    echo "📝 New module detected (no existing content)"

    if [[ ! -f "$research_file" ]]; then
      # Research file missing for NEW module - BLOCK
      if [[ "$flags" != *"--no-research"* ]]; then
        echo "⛔ RESEARCH REQUIRED"
        echo ""
        echo "This is a NEW seminar track module. Research must be completed first."
        echo ""
        echo "Run: /research '{topic}'"
        echo ""
        echo "Expected file: $research_file"
        echo ""
        echo "To skip (NOT recommended): /module ${level} ${num} --no-research"
        exit 1
      else
        echo "⚠️ WARNING: Skipping research gate (--no-research flag)"
        echo "Content quality may suffer without research notes."
      fi
    else
      # Research exists for new module - validate quality
      echo "✅ Research file found: $research_file"

      # Quick quality check
      sources_count=$(grep -c "^\d\+\. \[" "$research_file" 2>/dev/null || echo "0")
      has_quotes=$(grep -q "^>" "$research_file" && echo "yes" || echo "no")
      has_decolonization=$(grep -q "## Деколонізаційні" "$research_file" && echo "yes" || echo "no")

      echo "   Sources: ${sources_count}"
      echo "   Primary quotes: ${has_quotes}"
      echo "   Decolonization notes: ${has_decolonization}"

      if [[ "$sources_count" -lt 3 ]]; then
        echo "⚠️ WARNING: Research has fewer than 3 sources. Consider expanding."
      fi
    fi
  fi
fi
```

**Research Gate Decision Table:**

| Scenario | Content Exists | Word Count | Research | Action |
|----------|---------------|------------|----------|--------|
| New module | No | - | Missing | ⛔ BLOCK |
| New module | No | - | Exists | ✅ PASS |
| Existing, passing | Yes | ≥95% target | - | ✅ SKIP gate |
| Existing, under target | Yes | <95% target | Missing | ⛔ BLOCK (needs expansion) |
| Existing, under target | Yes | <95% target | Exists | ✅ PASS |
| --no-research flag | - | - | - | ⚠️ WARN, proceed |
| Core levels | - | - | - | ✅ SKIP (not seminar) |

**Why smart enforcement:**
- Don't block work on modules that already have good content
- DO require research for new content (prevents thin writing)
- DO require research before expansion (ensures quality additions)
- Research-first workflow where it matters most

### Step 2: Resolve Module Slug

> **⚠️ CRITICAL: Track files have NO numbered prefix!**
> - Core levels: `01-slug.md`, `02-slug.md` (numbered)
> - Tracks (b2-hist, c1-bio, etc.): `slug.md` (NO number prefix)
>
> **NEVER construct paths manually. ALWAYS use curriculum.yaml lookup.**

**For tracks (b2-hist, c1-bio, c1-hist, lit):**

```bash
# Get slug from curriculum.yaml (module numbers are 1-indexed, array is 0-indexed)
slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
# Example: module 41 → slug="kozatstvo-vytoky"
# File path: curriculum/l2-uk-en/b2-hist/kozatstvo-vytoky.md (NO "41-" prefix!)
```

**For core levels (a1, a2, b1, b2, c1, c2):**

```bash
slug=$(ls curriculum/l2-uk-en/${level}/${num:02d}-*.md | head -1 | xargs basename | sed 's/.md$//')
# Example: module 5 → slug="05-daily-routine"
# File path: curriculum/l2-uk-en/a1/05-daily-routine.md (HAS number prefix)
```

### Step 3: Detect Current State

Check which files exist:

```bash
has_meta=$(test -f curriculum/l2-uk-en/${level}/meta/${slug}.yaml && echo 1 || echo 0)
has_lesson=$(test -f curriculum/l2-uk-en/${level}/${slug}.md && echo 1 || echo 0)
has_activities=$(test -f curriculum/l2-uk-en/${level}/activities/${slug}.yaml && echo 1 || echo 0)
# Check for either module-N.mdx (core) or slug.mdx (tracks)
if [[ -f docusaurus/docs/${level}/module-${num}.mdx ]]; then
  has_mdx=1
elif [[ -f docusaurus/docs/${level}/${slug}.mdx ]]; then
  has_mdx=1
else
  has_mdx=0
fi
```

**State detection:**

| has_meta | has_lesson | has_activities | has_mdx | State         |
| -------- | ---------- | -------------- | ------- | ------------- |
| 0        | 0          | 0              | 0       | `NEW`         |
| 1        | 0          | 0              | 0       | `META_DONE`   |
| 1        | 1          | 0              | 0       | `LESSON_DONE` |
| 1        | 1          | 1              | 0       | `ACT_DONE`    |
| 1        | 1          | 1              | 1       | `FILES_EXIST` |

**CRITICAL: Files exist ≠ DEPLOYED. Must run audit to verify:**

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md
```

| Files | Audit | True State |
|-------|-------|------------|
| FILES_EXIST | ❌ FAIL | `NEEDS_FIX` → Run /module-fix |
| FILES_EXIST | ✅ PASS | `DEPLOYED` |

### Step 4: Determine Start Phase

**If `--refresh` provided:**

> **⚠️ WARNING: `--refresh` keeps existing .md content!**
> Only use when .md already meets word count targets.
> For incomplete content, use `--from=lesson` to regenerate.

Special flow (preserves `.md`, rebuilds everything else):
1. Phase 2 (Meta QA)
2. Phase 4 (Lesson QA) - *Skips Phase 3 generation*
3. Phase 5 (Activities Gen) - *Regenerates activities*
4. Phase 6 (Activities QA)
5. Phase 7 (Integrate)

**If `--from=PHASE` provided:**

| --from value | Start at Phase |
| ------------ | -------------- |
| meta         | 1              |
| lesson       | 3              |
| act          | 5              |
| integrate    | 7              |

**If `--check` provided:** Report state and exit.

**Otherwise auto-detect:**

| State         | Start Phase   |
| ------------- | ------------- |
| `NEW`         | 1 (meta)      |
| `META_DONE`   | 3 (lesson)    |
| `LESSON_DONE` | 5 (act)       |
| `ACT_DONE`    | 7 (integrate) |
| `DEPLOYED`    | Done          |

### Step 5: Execute Phases

**If `--refresh` mode:**
Execute specific sequence: 2 → 4 → 5 → 6 → 7.

**Otherwise (standard mode):**
Run phases sequentially from start phase:

**For each phase:**

1. Read phase instructions from `claude_extensions/phases/module-{phase}.md`

**⚠️ CRITICAL FOR PHASE 3 (Lesson) - Seminar Tracks:**

Before generating content, LOAD the research notes:

```bash
# For seminar tracks, read research notes into context
if [[ -f "curriculum/l2-uk-en/${level}/audit/${slug}-research.md" ]]; then
  echo "📚 Loading research notes..."
  # Read the research file - use this as source material
  cat "curriculum/l2-uk-en/${level}/audit/${slug}-research.md"
fi
```

**Use research notes for:**
- Specific dates, names, locations (don't guess!)
- Primary source quotes (include at least 1)
- Decolonization talking points
- Cross-references to other modules
- Chronological structure
2. Execute phase
3. If QA phase FAILS → stop and report
4. If QA phase PASSES → continue to next phase

**Phase 7 (integrate) creates skeleton vocab automatically.**

### Step 6: Audit + Fix Loop (MANDATORY - BATCH FIX PATTERN)

**Keep fixing until audit passes. No exceptions.**

**CRITICAL:** Use **batch-fix-within-module** pattern (see NON-NEGOTIABLE-RULES.md #8).

> **📋 QUICK REFERENCES (read BEFORE writing):**
> - Activity schemas: `claude_extensions/quick-ref/ACTIVITY-SCHEMAS.md`
> - Activity YAML reference: `docs/ACTIVITY-YAML-REFERENCE.md`
>
> These prevent schema iteration loops by providing exact field requirements per activity type.

**NEVER use iterative fix-audit cycles. Instead:**

```
WHILE true:

  # ========================================
  # 6.0 FAST SCHEMA CHECK (Before Full Audit)
  # ========================================

  Run schema validation first (faster feedback):

  .venv/bin/python scripts/validate_activities_schema.py curriculum/l2-uk-en/${level}/activities/${slug}.yaml

  IF schema errors → fix YAML structure before full audit
  (Common issues: wrong field names, missing required fields)

  # ========================================
  # 6.1 DIAGNOSE (Comprehensive Read)
  # ========================================

  1. Run audit:
     .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/${level}/${slug}.md

  2. IF audit PASSES → break loop, go to Step 7

  3. IF audit FAILS:

     Read ALL 4 component files:
     - curriculum/l2-uk-en/${level}/meta/${slug}.yaml
     - curriculum/l2-uk-en/${level}/${slug}.md
     - curriculum/l2-uk-en/${level}/activities/${slug}.yaml
     - curriculum/l2-uk-en/${level}/vocabulary/${slug}.yaml

     Read audit review:
     - curriculum/l2-uk-en/${level}/audit/${slug}-review.md

     Identify ALL violations across ALL components:

     Meta violations:
       - INVALID_ACTIVITY_TYPE → which types?
       - Word target mismatch → actual vs target?
       - Activity_hints gaps → missing types?

     Lesson violations:
       - Word count shortfall → which sections under?
       - Missing sections → which ones from content_outline?
       - **Outline compliance errors** → See `claude_extensions/skills/module-restructure-guide.md`
         (Restructure content to match plan sections, don't ask which approach to use)
       - Missing callouts → how many needed?
       - Low immersion → where is English?

     Activity violations:
       - YAML schema errors → which items?
       - Item count below minimum → how many needed?
       - Mirroring → which activities copy lesson?

     Vocab violations:
       - Missing IPA → how many items?
       - Wrong POS → which entries?
       - Count below target → how many needed?

     Naturalness violations:
       - Score < 7 → which sections?
       - Red flags → template repetition? robotic text?

  # ========================================
  # 6.2 EXECUTE (Fix ALL Issues Atomically)
  # ========================================

  Apply ALL fixes in ONE response:

  Order: meta → vocab → activities → markdown
  (Dependencies flow downstream)

  Meta fixes:
    - Replace invalid activity types
    - Fix activity_hints coverage

  Vocab fixes:
    - Add missing vocabulary items
    - Fix POS tags
    - Run enrichment if needed:
      .venv/bin/python scripts/vocab_enrich_nlp.py ${vocab_file}

  Activity fixes:
    - Fix YAML schema errors
    - Add items to meet minimums
    - Rephrase mirroring activities
    - Ensure activity_hints coverage

  Lesson fixes:
    - Expand sections to meet word targets
      **If significant word shortfall (>500 words): Use /expand skill**
      (OR redistribute from over-target sections - see SUBSECTION-FLEXIBILITY-GUIDE.md)
    - **NEVER change word_target in meta to match short content**
    - Add missing sections from content_outline
    - Add missing callouts/engagement boxes
    - Increase immersion (reduce English)
    - Fix naturalness (vary structures, discourse markers)

  # ========================================
  # 6.3 VERIFY (Loop to Re-Audit)
  # ========================================

  Continue loop → Re-audit with all fixes applied

END WHILE

# ========================================
# 6.4 GENERATE MDX (MANDATORY - After Audit Passes)
# ========================================

⚠️ MANDATORY: Generate MDX immediately after audit passes:

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en ${level} ${num}
# Example: .venv/bin/python scripts/generate_mdx.py l2-uk-en a2 23
```

This ensures the MDX is always up-to-date with the fixed content.
Module is NOT complete until MDX is generated.
```

**Why This Works:**

1. **Efficiency:** One comprehensive read + one atomic fix + one audit = O(3) instead of O(3N)
2. **Coherence:** Fixes reference each other (new vocab drives section expansion)
3. **Consistency:** No intermediate states where components are misaligned
4. **Speed:** Fewer API calls, less token usage

**CRITICAL: Do NOT exit this step until audit shows ALL GATES PASS.**

### Step 7: Report Success

**Only reached after audit passes:**

```
MODULE DEPLOYED: {level}/{slug} ✅

Audit: PASS
  - Words: {actual}/{target} ✅
  - Activities: {count} ✅
  - Naturalness: {score}/10 ✅

Files generated:
  - meta/{slug}.yaml
  - {slug}.md
  - activities/{slug}.yaml
  - vocabulary/{slug}.yaml (skeleton)
  - docusaurus/docs/{level}/{mdx_filename}

Preview: http://localhost:3000/docs/{level}/{slug_or_module_num}

Note: Vocabulary table is empty. Run /module-vocab-enrich {level}
      after all modules are content-complete.
```

---

## Batch Mode

When input is a range (e.g., `/module b2-hist 1-5`):

### Step 0: Pre-Batch Checks

```bash
# Check for Gemini messages first
/check-gemini

# Run batch audit to categorize modules
/batch-fix {level} {range} --dry-run
```

This categorizes modules into:
- **PASSED**: Skip (already done)
- **FIXABLE**: Auto-fix schema/format issues
- **NEEDS EXPANSION**: Require individual /research + /expand (word count issues)
- **NEEDS RESEARCH**: (Seminar tracks) Missing research file

### Step 0.5: Research Gate (Seminar Tracks - Smart Enforcement)

**For seminar tracks (b2-hist, c1-bio, c1-hist, lit, oes, ruth):**

Before building, categorize modules by research need:

```bash
SEMINAR_TRACKS="b2-hist c1-bio c1-hist lit oes ruth"

if echo "$SEMINAR_TRACKS" | grep -qw "$level"; then
  echo "📚 Analyzing research needs for batch..."

  needs_research=()      # New modules without research
  needs_expansion=()     # Existing but under word target, no research
  ready_to_build=()      # Has research OR existing passing content

  for num in {start..end}; do
    slug=$(yq ".levels.\"${level}\".modules[$((num-1))]" curriculum/l2-uk-en/curriculum.yaml)
    content_file="curriculum/l2-uk-en/${level}/${slug}.md"
    research_file="curriculum/l2-uk-en/${level}/audit/${slug}-research.md"

    if [[ -f "$content_file" ]]; then
      # Content exists - check word count
      word_count=$(wc -w < "$content_file" | tr -d ' ')
      word_target=$(yq '.word_target // 3500' "curriculum/l2-uk-en/${level}/meta/${slug}.yaml" 2>/dev/null || echo "3500")
      threshold=$((word_target * 95 / 100))

      if [[ "$word_count" -ge "$threshold" ]]; then
        # Passing content - ready (research optional)
        ready_to_build+=("$num: $slug ✅ (${word_count}w)")
      else
        # Under target - needs expansion
        if [[ -f "$research_file" ]]; then
          ready_to_build+=("$num: $slug ⚠️ (needs expansion, has research)")
        else
          needs_expansion+=("$num: $slug (${word_count}/${word_target}w)")
        fi
      fi
    else
      # New module - check for research
      if [[ -f "$research_file" ]]; then
        ready_to_build+=("$num: $slug 📚 (new, has research)")
      else
        needs_research+=("$num: $slug")
      fi
    fi
  done

  # Report status
  echo ""
  echo "Ready to build: ${#ready_to_build[@]} modules"
  for item in "${ready_to_build[@]}"; do
    echo "   ✅ $item"
  done

  if [[ ${#needs_research[@]} -gt 0 ]]; then
    echo ""
    echo "⛔ NEED RESEARCH (new modules): ${#needs_research[@]}"
    for item in "${needs_research[@]}"; do
      echo "   - $item"
    done
  fi

  if [[ ${#needs_expansion[@]} -gt 0 ]]; then
    echo ""
    echo "⛔ NEED RESEARCH (under word target): ${#needs_expansion[@]}"
    for item in "${needs_expansion[@]}"; do
      echo "   - $item"
    done
  fi

  # Block if any need research (unless --no-research)
  total_blocked=$((${#needs_research[@]} + ${#needs_expansion[@]}))
  if [[ $total_blocked -gt 0 ]] && [[ "$flags" != *"--no-research"* ]]; then
    echo ""
    echo "Options:"
    echo "1. Run /research for each topic first"
    echo "2. Use --no-research flag (NOT recommended)"
    echo "3. Ask Gemini to research in parallel (see below)"
    exit 1
  fi
fi
```

**Parallel research pattern (for blocked modules):**
```bash
# Send batch research requests to Gemini
for slug in needs_research; do
  .venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
    "Research {topic} for ${level} module. Save to audit/${slug}-research.md" \
    --task-id batch-research
done

# Continue with ready_to_build modules while Gemini researches
```

### Step 1: Auto-Fix Fixable Issues

Use `/batch-fix` for non-content issues:
```bash
/batch-fix {level} {range}
```

This fixes: YAML schema, activity types, lint issues, callouts.
**Does NOT fix word count** - those need proper expansion.

### Step 2: Expand Under-Target Modules

For each module flagged as NEEDS EXPANSION:
```bash
/research {topic}        # Gather Ukrainian sources
/expand {module_path}    # Expand content using research
```

**NEVER change word_target to match short content.**

### Step 3: Full Build for Remaining

```
For each module_num in range:
  1. Run /module {level} {module_num}
     - This includes the audit+fix loop (Step 6)
     - Module is NOT done until audit passes
  2. Generate MDX after audit passes:
     .venv/bin/python scripts/generate_mdx.py l2-uk-en ${level} ${module_num}
  3. Only move to next module after current one DEPLOYED + MDX generated
```

**Each module must pass audit AND have MDX generated before proceeding to the next.**

**Batch summary (all should be DEPLOYED with MDX):**

```
Batch: b2-hist 1-5
Results:
  - 1: ✅ DEPLOYED + MDX (4235/4000 words, audit PASS)
  - 2: ✅ DEPLOYED + MDX (4102/4000 words, audit PASS)
  - 3: ✅ DEPLOYED + MDX (4050/4000 words, audit PASS)
  - 4: ✅ DEPLOYED + MDX (4310/4000 words, audit PASS)
  - 5: ✅ DEPLOYED + MDX (4200/4000 words, audit PASS)

Summary: 5/5 deployed with MDX

Next: Run /module-vocab-enrich b2-hist
```

---

## Phase Reference

| Phase | Command           | Creates                                 | Validates            |
| ----- | ----------------- | --------------------------------------- | -------------------- |
| 1     | /module-meta      | meta/{slug}.yaml                        | -                    |
| 2     | /module-meta-qa   | -                                       | Meta validity        |
| 3     | /module-lesson    | {slug}.md                               | -                    |
| 4     | /module-lesson-qa | -                                       | Content quality      |
| 5     | /module-act       | activities/{slug}.yaml                  | -                    |
| 6     | /module-act-qa    | -                                       | Activity schema      |
| 7     | /module-integrate | vocabulary/{slug}.yaml (skeleton) + MDX | Cross-file alignment |

**Later:**

| Command                      | What it does                             |
| ---------------------------- | ---------------------------------------- |
| /module-vocab-enrich {level} | Extract vocab M1→MN in order, update MDX |

---

## Quick Examples

```bash
# Fresh build
/module b2-hist 5

# Regenerate lesson content (for incomplete modules)
/module b2-hist 5 --from=lesson

# Rebuild artifacts ONLY (when lesson already complete)
# WARNING: This keeps existing .md - don't use for incomplete content!
/module b2-hist 5 --refresh

# Check what's done
/module b2-hist 5 --check

# Build batch
/module c1-bio 1-10

# After track complete: enrich vocabulary
/module-vocab-enrich b2-hist
```
