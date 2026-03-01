# Context Engineering Best Practices

> **Scope:** What information to inject into each Gemini call, and why.
> For how to write the prompt instructions themselves, see `prompt-engineering.md`.

---

## Core Principle

Every Gemini call has a fixed context budget. What you include determines quality more than how you phrase the instructions. Bad context → hallucination, thin content, wrong structure. Good context → Gemini writes as if it researched the topic itself.

---

## The Context Hierarchy

For any module build, context priority (highest → lowest):

1. **Plan file** — SOURCE OF TRUTH. Section names, vocabulary, objectives.
2. **Research file** — Deep factual content. Dates, quotes, sources, engagement hooks.
3. **Meta file** — Structural blueprint. Section allocations, writing points.
4. **Quick-ref** — Level constraints. Immersion %, activity types, vocabulary limits.
5. **Track context** — Cross-module consistency. *(Seminar tracks: omit entirely.)*

---

## Research File

### When to include
Always for seminar tracks (hist, bio, istorio, lit, oes, ruth). Optional for core tracks.

### Quality threshold
A research file under 500 words is not usable — dispatch Phase A in full research mode instead.

### Content requirements
Good research files contain:
- Timeline (5+ dated events)
- Primary source quotes (2+)
- Section-mapped notes (headings match plan sections)
- Engagement hooks mapped to sections (`[!myth-buster]`, `[!history-bite]`, etc.)
- Decolonization framing
- Contested terms table (if applicable)

### Research-exists optimisation
If a substantial research file already exists (≥500 words), skip the research call and dispatch meta-only. This saves one Gemini call per pre-researched module.

```python
# build_module.py
if _research_file_is_usable(ctx):
    template_name = "phase-A-meta-only.md"  # meta only, 1 call saved
else:
    template_name = "phase-A-seminar.md"    # full research + meta
```

---

## Meta File (Content Outline)

### Purpose
The meta's `content_outline` is the section-level blueprint Phase B writes against. Each entry = one H2 section with word allocation and writing points.

### Health check (auto-enforced)
Before treating Phase A as complete, `build_module.py` checks that no section exceeds 25% of `word_target`. If violated, Phase A re-runs automatically:

```python
# Any section consuming >25% of word_target → re-run Phase A
_META_SECTION_MAX_PCT = 0.25
```

### Section splitting rule
Plan sections with 5+ bullet points must become multiple meta sections. Bullets = section topics, not sub-bullets.

**Wrong:** `Читання: 3200w` (one section, 14 bullets)
**Right:** `Читання: I — Розселення: 700w`, `Читання: II — Суспільний устрій: 600w`, etc.

### Section size targets
- Minimum: 200w (merge if smaller)
- No hard maximum — Gemini paces naturally
- For ≥4000w modules: aim for 8-12 sections total

---

## Track Context

### Decision matrix

| Track type | Track context | Rationale |
|-----------|---------------|-----------|
| Seminar (hist, bio, istorio, lit, oes, ruth) | **Empty** | Topics are independent. Plans + research + meta are sufficient. |
| Core (a1, a2, b1, b2, c1, c2, b2-pro, c1-pro) | Last 5 modules | Needed for vocabulary/grammar consistency across sequential modules. |

**Never include full-track context for seminar tracks.** Even 50KB of context costs output budget and adds no consistency value when topics are independent (Bohdan Khmelnytskyi has nothing to do with Lesya Ukrainka).

---

## Placeholder System

Every module build writes a `placeholders.yaml` in the orchestration directory. Phase templates read paths from this file via `{PLACEHOLDER_NAME}` substitution.

### Key paths
```yaml
PLAN_PATH: curriculum/l2-uk-en/plans/{track}/{slug}.yaml
META_PATH: curriculum/l2-uk-en/{track}/meta/{slug}.yaml
RESEARCH_PATH: curriculum/l2-uk-en/{track}/research/{slug}-research.md
CONTENT_PATH: curriculum/l2-uk-en/{track}/{slug}.md
ACTIVITIES_PATH: curriculum/l2-uk-en/{track}/activities/{slug}.yaml
VOCAB_PATH: curriculum/l2-uk-en/{track}/vocabulary/{slug}.yaml
QUICK_REF_PATH: claude_extensions/quick-ref/{LEVEL}.md
WORD_TARGET: 5000
```

### Injection rule
Never hardcode paths in templates. Always use placeholders — they make templates portable across all modules.

---

## Word Target Injection

`WORD_TARGET` is always injected as a placeholder. Templates use it for:
- Section allocation validation (sum ≈ WORD_TARGET)
- Overshoot calculation (Phase B targets 1.5× word_target to account for natural shortfall)
- Activity count guidance

**Never hardcode word targets in templates** — different tracks have different targets (A1: 750w, B2: 1750w, BIO: 5000w).

---

## Context Ordering in Templates

Within a template, always present context in this order:

1. Plan (structure, vocabulary, objectives)
2. Research (facts, quotes, hooks)
3. Meta (current outline to replace/update)
4. Quick-ref (level constraints, last)

**Why:** Gemini weights earlier context more heavily. Plan should be the anchor, not the existing meta (which might be wrong).

---

## What NOT to Include

| What | Why not |
|------|---------|
| Full track context for seminar tracks | Topics independent; wastes budget; adds noise |
| Old meta `content_outline` as authoritative | Anchors Gemini to wrong structure |
| Russian-language sources | Forbidden. Biased framing. |
| Other modules' content | Risks cross-contamination of examples |
| System prompts / persona instructions | Assigned at deployment time, not in content calls |

---

## Context Size Budgeting

For a 1M token context window, typical per-call breakdown:

| Item | Typical size |
|------|-------------|
| Phase template prompt | ~3-5K tokens |
| Plan file | ~2-4K tokens |
| Research file | ~2-5K tokens |
| Meta file | ~1-2K tokens |
| Quick-ref | ~5-10K tokens |
| Track context (core only) | ~15-30K tokens |
| **Total input** | **~30-55K tokens** |
| **Available for output** | **~945-970K tokens** |

For a 5000w module, output is ~7500 tokens. Context cost is not the constraint — output quality is.

---

## Failure Patterns and Fixes

| Failure | Root Cause | Fix |
|---------|-----------|-----|
| Gemini copies old meta | Meta shown before plan | Show plan first; label old meta "for reference only" |
| Thin content despite large research file | Section too big (>25% target) | Health check splits meta before Phase B |
| Hallucinated facts | No research file | Ensure research phase runs before content |
| Wrong section names | Plan not shown | Always include plan as first context item |
| Inconsistent vocabulary across modules | No track context (core) | Inject last 5 modules for core tracks |
