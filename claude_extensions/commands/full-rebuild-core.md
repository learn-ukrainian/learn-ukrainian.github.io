# Core Track Full-Rebuild Workflow

> **Scope:** Standard for rebuilding or creating modules in core tracks: `a1`, `a2`, `b1`, `b2`, `c1`, `c2`, `b2-pro`, `c1-pro`. Chains research, build, review, and verification into a single resumable command.

## Usage

```
/full-rebuild-core {level} {num}
/full-rebuild-core {level} {num} --from=PHASE   # Resume from specific phase
```

**Examples:**

```
/full-rebuild-core a1 5               # Rebuild A1 module 5 (Core A workflow)
/full-rebuild-core b2 10              # Rebuild B2 module 10 (Core B workflow)
/full-rebuild-core b1 3               # Core A (M01-05 range)
/full-rebuild-core b1 15              # Core B (M06+ range)
/full-rebuild-core b1 15 --from=review  # Jump to review phase only
```

**Arguments:**

- `{level}` — Core level (a1, a2, b1, b2, c1, c2, b2-pro, c1-pro)
- `{num}` — Module number (1-indexed)
- `--from=PHASE` — Optional: force start from specific phase (research, build, review, verify)

**Validation:** If level is a seminar track (b2-hist, c1-bio, c1-hist, lit, oes, ruth), print error and redirect:

```
❌ "{level}" is a seminar track. Use /full-rebuild instead:

   /full-rebuild {level} {num}

Seminar tracks use the 6-phase research-first workflow with deep source requirements.
```

---

## Auto-Detection: Core A vs Core B

```
CORE_A: a1, a2, b1 where num <= 5
CORE_B: b1 where num >= 6, b2, c1, c2, b2-pro, c1-pro

if level in (a1, a2):
    workflow = "core-a"
elif level == "b1" and num <= 5:
    workflow = "core-a"
else:
    workflow = "core-b"
```

Detection determines:

| | Core A | Core B |
|---|--------|--------|
| Research depth | Lightweight (15-20 min) | Moderate (20-30 min) |
| Workflow doc | `docs/CORE-A-WORKFLOW.md` | `docs/CORE-B-WORKFLOW.md` |
| Review prompt | `/review-content-core-a` (12 dimensions) | `/review-content-v4` (14 dimensions) |
| Tier file | `tier-1-beginner.md` | `tier-2-core.md` or `tier-4-advanced.md` |

---

## RESUMABLE: Run same command across sessions

**This command is idempotent.** Run it in multiple sessions — it detects completed phases and picks up where it left off.

```
Session 1: /full-rebuild-core b1 15  → research + build (context fills up)
Session 2: /full-rebuild-core b1 15  → skips done phases, does align + review
Session 3: /full-rebuild-core b1 15  → review ALWAYS re-runs, then verify
```

> **Note:** Phase 2 (Review) always re-runs even if a previous review exists.
> Review prompts evolve — we always want the latest version evaluating the content.

---

## Step 0: Resolve Module

```bash
# Core levels use numbered prefixes — find the matching file
slug=$(ls curriculum/l2-uk-en/${level}/${num_padded}-*.md 2>/dev/null | head -1 | xargs basename | sed 's/^[0-9]*-//' | sed 's/.md$//')
```

Where `num_padded` is the zero-padded module number (e.g., `05` for num=5).

File paths:

```
plan:       curriculum/l2-uk-en/plans/{level}/{slug}.yaml
research:   curriculum/l2-uk-en/{level}/audit/{slug}-research.md
meta:       curriculum/l2-uk-en/{level}/meta/{slug}.yaml  (may use numbered prefix)
content:    curriculum/l2-uk-en/{level}/{num_padded}-{slug}.md
activities: curriculum/l2-uk-en/{level}/activities/{slug}.yaml
review:     curriculum/l2-uk-en/{level}/review/{slug}-review.md
status:     curriculum/l2-uk-en/{level}/status/{slug}.json
```

---

## Step 1: Detect State (skip completed phases)

Check which phases are already complete. **Unless `--from` is specified, auto-detect:**

| Check | Condition | Phase to skip |
|-------|-----------|---------------|
| Research file exists? | `audit/{slug}-research.md` exists with State Standard §ref | Skip Phase 0 |
| Module audit passes? | Run `scripts/audit_module.sh`, exit code 0 | Skip Phase 1 |
| Content aligned with research? | All research hooks/facts present in `.md` | Skip Phase 1.5 |

> **IMPORTANT: Phase 2 (Review) NEVER skips.**
> Always run the latest review prompt regardless of whether a previous review exists.
> Review prompts evolve — we always want the current version to evaluate the content.
> A prior review PASS does NOT exempt a module from re-review.

**Print state report before starting:**

```
📋 /full-rebuild-core {level} {num} — State Detection ({workflow_name})

  Phase 0 (Research):   ✅ DONE — audit/{slug}-research.md (§2.1.3)
  Phase 1 (Build):      ⏳ PENDING — audit fails (word count)
  Phase 1.5 (Align):    ⏳ PENDING — depends on research + build
  Phase 2 (Review):     🔄 ALWAYS — runs latest review prompt
  Phase 3 (Verify):     ⏳ PENDING — depends on review

▶️ Starting from Phase 1 (Build)
  Workflow: {workflow_name} ({workflow_doc})
  Review prompt: {review_command}
```

**If `--from=PHASE` is specified, force start from that phase regardless of state.**

---

## Phase 0: Research

> **CRITICAL: Research is a BLOCKING dependency for core rebuilds.**
> Phase 0 MUST complete before Phase 1. No writing from memory.

### Core A — Lightweight Research (15-20 min)

Follow template from `docs/CORE-A-WORKFLOW.md`:

1. **Grammar**: Find §section in State Standard 2024 for the grammar point taught
2. **Vocabulary**: Check frequency on lcorp.ulif.org.ua for key vocabulary items
3. **Cultural hook**: 1-2 verified facts (not from memory) to anchor the lesson

### Core B — Moderate Research (20-30 min)

Follow template from `docs/CORE-B-WORKFLOW.md`:

1. **Grammar**: Find and quote §section from State Standard
2. **Vocabulary**: Frequency verification + collocations from corpus data
3. **Cross-references**: Builds-on / prepares-for chain with adjacent modules
4. **PRO tracks**: Domain-specific vocabulary from professional glossaries
5. **C2**: Stylistic/dialectal features from academic sources

**Save to:** `curriculum/l2-uk-en/{level}/audit/{slug}-research.md`

**Completion gate:** Research file must exist with State Standard §reference before Phase 1.

---

## Phase 1: Build (via /module)

> **Delegates to `/module` for the 7-phase build + audit loop.**

**Before `/module` runs, load research notes into context** so the build uses researched facts:

```bash
cat "curriculum/l2-uk-en/${level}/audit/${slug}-research.md"
```

Then run:

```
/module {level} {num}
```

This runs:
1. Meta generation/validation (Phases 1-2)
2. Lesson generation/validation (Phases 3-4)
3. Activity generation/validation (Phases 5-6)
4. Integration + skeleton deploy (Phase 7)
5. Audit + fix loop (Step 6) — keeps fixing until audit passes
6. MDX generation

**Exit criteria:** Audit passes (all gates green).

---

## Phase 1.5: Content Alignment (Research → Prose)

> **CRITICAL: Every research finding must be reflected in the prose content.**
> This phase ensures the lesson integrates all researched facts, cultural hooks,
> and State Standard references — not just passes audit mechanically.

### Procedure

1. **Load research notes** into context:

```bash
cat "curriculum/l2-uk-en/${level}/audit/${slug}-research.md"
```

2. **Load current lesson content** into context:

```bash
cat "curriculum/l2-uk-en/${level}/${num_padded}-${slug}.md"
```

3. **Compare research against prose.** Check each research finding:

| Research Element | What to Check in Prose |
|-----------------|----------------------|
| State Standard §reference | Cited or reflected in grammar explanation? |
| Cultural hooks / facts | Integrated into lesson sections (not just mentioned)? |
| Verified vocabulary | Used in examples and practice? |
| Corpus collocations | Included in natural example sentences? |
| Cross-references | Builds-on / prepares-for chain mentioned? |
| Etymology notes | Woven into explanations where pedagogically useful? |

4. **If gaps found — expand or rebuild the prose:**

- **Missing cultural hook?** Add it to the relevant section with context
- **State Standard ref not reflected?** Ensure grammar explanation aligns with §section
- **Verified facts absent?** Integrate into lesson narrative naturally
- **Vocabulary from research unused?** Add to examples, dialogues, or practice sections

5. **Re-audit after any changes:**

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{num_padded}-{slug}.md
```

**Exit criteria:** All research findings present in prose content. Audit still passes.

**Skip condition:** If ALL research hooks/facts are already present in the `.md` content, print:

```
✅ Phase 1.5 (Align): All research findings present in prose — no changes needed.
```

---

## Phase 2: Review (ALWAYS RUNS)

> **Phase 2 NEVER skips.** Always run the latest review prompt, even if a previous
> review exists with PASS status. Review prompts evolve and improve over time —
> we always want the current version evaluating the content.

> **Run review at TOP LEVEL, not as a subagent.**
> (Same rule as `/full-rebuild` — subagents lack schema context)

**Auto-select review prompt based on workflow:**

```
if workflow == "core-a":
    /review-content-core-a {LEVEL} {NUM}
    # 12 dimensions: L1/L2 Balance, Beginner Safety, IPA, State Standard
elif workflow == "core-b":
    /review-content-v4 {LEVEL} {NUM}
    # 14 dimensions: Propaganda Filter, Semantic Nuance, State Standard
```

**Review includes:**
- Deep Ukrainian verification (every sentence)
- Activity item-by-item check
- Scoring on all dimensions
- Fix issues as found
- Set naturalness score in meta

**Re-audit after review fixes:**

```bash
scripts/audit_module.sh curriculum/l2-uk-en/{level}/{num_padded}-{slug}.md
```

**Exit criteria:** Review PASS (no dimension below auto-fail threshold).

---

## Phase 3: Verify

Final checks:
1. Re-run audit after review fixes — confirm PASS
2. Confirm `status/{slug}.json` has `overall.status: "pass"`
3. MDX is up-to-date (run pipeline if needed)

```bash
# Verify status
jq '.overall.status' curriculum/l2-uk-en/{level}/status/{slug}.json
# Should output: "pass"
```

---

## Completion Report

```
✅ /full-rebuild-core {level} {num} — COMPLETE ({workflow_name})

  Phase 0 (Research):  ✅ State Standard §{ref}, {hooks} cultural hooks
  Phase 1 (Build):     ✅ {words}/{target} words, {activities} activities, audit PASS
  Phase 1.5 (Align):   ✅ All research findings present in prose
  Phase 2 (Review):    ✅ {score}/10 ({dimensions} dimensions, {review_command})
  Phase 3 (Verify):    ✅ All gates PASS

  Workflow: {workflow_name} ({workflow_doc})
```
