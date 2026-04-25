# Audit & Verification Standards

> **Scope:** What PASS/FAIL means, gate hierarchy, and how to interpret audit results.
> Authoritative thresholds: `scripts/audit/config.py`

---

## Gate Hierarchy

Modules pass through gates in order. All must pass for a module to be "fully complete."

```
Content Gates (automated)
├── 1. Word count gate        — prose meets target
├── 2. Outline compliance     — all plan sections present as H2s
├── 3. Activities gate        — correct types, counts, valid YAML
├── 4. Vocabulary gate        — correct count, valid YAML
└── 5. Naturalness gate       — no AI slop patterns detected

Review Gate (LLM — informational only)
└── 6. Adversarial review     — qualitative assessment (does NOT block pass)

MDX Gate (deterministic)
└── 7. MDX generation         — always last, always succeeds if content passes
```

**Shippable = all content gates PASS + review ≥ 8/10.** The review gate is enforced by the module dashboard (`scripts/module_dashboard.py`), not by the automated audit.

---

## Review Lifecycle (#970)

### Artifacts
- **Review findings** → `orchestration/{slug}/review-*.md` (raw outputs, prompts, results)
- **Friction log** → `orchestration/{slug}/friction.yaml` (curated learnings that survive rebuilds)
- **Global friction** → `docs/rules/global-friction.yaml` (project-wide linguistic constraints)
- **Dashboard** → `scripts/module_dashboard.py` (aggregated view of all modules)

### Friction logs
Friction files use YAML with `id`, `status` (active/resolved), `type`, `description`.
Active frictions are injected into content and review prompts automatically.
When a friction is fixed (in code or templates), set `status: resolved` — it stays in the log for history but stops being injected into prompts.

Global frictions apply to ALL modules (e.g., "сес-тра is valid per Правопис §49").
Module frictions are specific to one module (e.g., "M02: сір is not a word").

### No more GH review tickets
The pipeline no longer auto-creates GH issues for review passes. Review artifacts live in orchestration folders. GH issues are for work items only.

### Dashboard
```bash
.venv/bin/python scripts/module_dashboard.py a1           # all A1 modules
.venv/bin/python scripts/module_dashboard.py a1 --first 6  # first 6 only
.venv/bin/python scripts/module_dashboard.py a1 --failing-only
```

---

## Word Count Gate

### Thresholds by level

| Level | Min words (audit passes) |
|-------|--------------------------|
| A1 M01-05 | 300w |
| A1 M06-10 | 500w |
| A1 M11+ | 750w |
| A2 | 1000w |
| B1 | 1500w |
| B2 | 1750w |
| C1 | 3000w |
| C2 | 3000w |
| HIST | 5000w |
| BIO | 5000w |
| ISTORIO | 5000w |
| LIT | 2500w |

**Word target in meta file overrides the above.** If meta sets `word_target: 4000`, that's the gate.

### Word count failures
If the content phase produces <80% of target: automatic retry (up to 3 attempts).
If still failing after retries: the review phase (review+fix) should add content.

---

## Outline Compliance Gate

Every section name in the plan's `content_outline` must appear as an H2 (`##`) heading in the content file. Names must match exactly (or very closely).

**Most common audit failure.** Root cause: the research phase generates meta sections that don't match plan section names, then the content phase writes wrong H2 headings.

Fix: research phase template explicitly says "section names must match plan exactly."

---

## Activities Gate

| Metric | Seminar (hist, bio, etc.) | Core (a1-c2) |
|--------|----------------------------------|--------------|
| Min activities | 3 | 8 (A1), 10 (A2+) |
| Max activities | 9 (soft cap) | varies (soft cap) |
| Required types | reading, essay-response, critical-analysis | varies by level |
| Forbidden types | match-up, fill-in, cloze, mark-the-words | — |
| Min items per activity | 1 | varies |

YAML must validate against `schemas/activities-{level}.schema.json`.

### MIN/MAX philosophy (#1550 unit 4)

Activity counts and word counts are **MINIMUMS, never maximums**. The audit
follows this rule:

| Direction | Behaviour | Example |
|-----------|-----------|---------|
| Below MIN floor | Hard `FAIL` | A1 module with 3 activities (floor 4) |
| At or above MIN | `PASS` | A1 module with 4-15 activities |
| Above soft MAX cap | `WARN` only | A1 module with 17 activities |

The `*_MAX` keys (`max_activities`, `INLINE_MAX`, `WORKBOOK_MAX`) are
guidance for the writer — they are *not* hard ceilings. CLAUDE.md is
explicit: word-count and activity-count targets are MINIMUMS. Going over
emits a soft warning; the audit does **not** fail the module.

The MIN gates (`min_activities`, `min_types_unique`,
`min_items_per_activity`, `min_vocab`, word-count target) remain hard
fails — those are the contracts.

### `letter_module: true` exception class

Plans for alphabet/letter-driven modules (`A1.1` phonetics) may declare
`letter_module: true` at the top level. When set, the audit:

- **Drops** the activity-count soft `WARN` entirely (letter modules
  legitimately need ~33 letter-recognition items spread across 4–6
  activities, so the level cap of 9 doesn't apply).
- **Keeps** the activity-count MIN floor — letter modules still need at
  least the level minimum.
- **Keeps** the word-count target — prose length expectations are
  level-standard.
- **Keeps** the type-diversity MIN — letter modules still need 3–4
  distinct types (image-to-letter, match-up, fill-in, watch-and-repeat).

Wired into `evaluate_content_heavy(..., letter_module=True)` in
`scripts/audit/gates.py`.

### Two-layer config map

There are two parallel config layers with different consumers:

| Layer | File | Consumer | Canonical for |
|-------|------|----------|---------------|
| **Audit** | `scripts/audit/config.py` `LEVEL_CONFIG` | Post-build audit gates | Word target, naturalness min, activity-count MIN, type-diversity MIN, `forbidden_types`, `priority_types`, `required_types`, `allowed_types` |
| **Pipeline** | `scripts/pipeline/config_tables.py` `ACTIVITY_CONFIGS` | Build-time writer prompt placeholders | `INLINE_MIN`/`INLINE_MAX` (dynamic from injection markers), `TOTAL_TARGET`, prompt-template strings, `INLINE_*`/`WORKBOOK_*` allowed-type partitioning |

For shared concepts (forbidden / allowed / priority type lists), the
audit layer is canonical; the pipeline layer should reflect those sets
in its prompt-facing format. Where the two have intentionally drifted
(e.g. seminar tracks where audit forbids inline drill types but
pipeline allows them as inline-only checks), the divergence is captured
in `tests/audit/test_config_invariants.py::_KNOWN_DIVERGENT_LEVELS`.

Cross-layer invariants (enforced by tests):

- Pipeline `ITEMS_MIN` ≥ audit `min_items_per_activity` for the same level.
- Audit `priority_types` ⊆ pipeline `INLINE_ALLOWED ∪ WORKBOOK_ALLOWED ∪
  ALLOWED_ACTIVITY_TYPES` (no dead-weight priorities).
- Pipeline `REQUIRED_TYPES` ⊆ audit `priority_types ∪ required_types`
  (no force-feeding what audit doesn't even prefer).
- Within audit: `forbidden_types ∩ (priority_types ∪ required_types ∪
  allowed_types) == ∅`.
- Every level has `min_activities > 0` and `min_types_unique >= 2`.

---

## Naturalness Gate

Detects AI slop patterns that make content feel machine-generated.

### Detected patterns (any of these → FAIL)
- Generic opening: "In this module we will..."
- Textbook passive: "It should be noted that..."
- Orphan facts: "Interestingly, they also..."
- Wall of facts without interpretation (>3 facts in sequence)
- Formulaic transitions: "Furthermore,", "Moreover,", "In conclusion,"
- Missing narrative arc (just facts, no story)

### Naturalness score threshold
- Seminar tracks: ≥9.0
- Core tracks: ≥7.5

---

## Anti-Gaming Detection

Two check suites detect LLM content-generation and review-gaming patterns. All checks are deterministic (no LLM calls). Source: `scripts/audit/checks/`.

### Content Gaming (`content_gaming.py` + `content_purity.py`)

| Check | Type | Severity | Trigger |
|-------|------|----------|---------|
| Cross-module plagiarism | `CROSS_MODULE_PLAGIARISM` | warn >3 / crit >8 | Sentences duplicated across modules in same track |
| Content-vocabulary alignment | `VOCAB_NOT_IN_CONTENT` | warn <70% / crit <50% | Vocab YAML words missing from prose+activities |
| Example diversity | `TEMPLATE_EXAMPLE_RUN` | warn ≥3 / crit ≥5 | Consecutive examples with >70% word overlap (B1+) |
| Filler phrase density | `FILLER_PHRASE_OVERUSE` | warn >5 / crit >10 | LLM hedging phrases (level-aware: higher for C1/C2) |
| Section depth (min words) | `SECTION_HEADER_PADDING` | warn any / crit ≥3 | H2 sections below 50w (A1-A2) or 100w (B1+) |
| Section balance (max %) | `SECTION_BALANCE_BLOATED` | warn >40% / crit >60% | Any H2 section exceeding 40% of total word count |
| IPA density cap | `IPA_DENSITY_EXCESSIVE` | warn >5% / crit >10% | Inline IPA tokens as fraction of total words |
| Duplicate sentences | `DUPLICATE_SENTENCES` | warn >3 / crit >6 | Sentences with ≥70% fuzzy overlap within module |
| Robotic sentence starters | `ROBOTIC_SENTENCE_STARTERS` | warn >30% / crit >50% | Same first word starting too many sentences |

### Review Gaming (`review_gaming.py`)

| Check | Type | Severity | Trigger |
|-------|------|----------|---------|
| Score uniformity | `SCORE_UNIFORMITY` | warn <0.5 SD / crit all 10 | Dimension scores too similar (rubber-stamp) |
| Citation density | `LOW_CITATION_DENSITY` | warn <1/300w / crit <1/500w | Review doesn't cite enough specific content |
| Section coverage | `LOW_SECTION_COVERAGE` | warn <60% / crit <40% | Review skips too many H2 sections |
| Score drift | `REVIEW_SCORE_DRIFT` | warn avg>8.5 / crit avg>9.0 | Track-wide inflation across multiple modules |
| Review boilerplate | `REVIEW_BOILERPLATE` | warn >50% / crit >70% | Recycled critique language across reviews |
| Phantom section refs | `PHANTOM_SECTION_REFERENCE` | warn any | Review references non-existent section headers |
| Cross-agent enforcement | `SELF_REVIEW_DETECTED` | critical | Same agent wrote content and review |

### Legacy patterns (still active in review gate)

These patterns trigger **GAMING_LANGUAGE_DETECTED** (critical):

- `"ensuring a high score"`
- `"reflecting the fixes made"`
- `"designed to pass"`
- `"as I improved"`

A flagged review is **invalid**. Request a new review via cross-agent review (Claude reviews Gemini's content, not Gemini reviewing its own).

---

## Running Audits

```bash
# Full audit (saves log automatically)
scripts/audit_module.sh curriculum/l2-uk-en/{track}/{file}.md

# Content-only audit (skip activities/vocab gates)
scripts/audit_module.sh --skip-activities curriculum/l2-uk-en/{track}/{file}.md

# Verify module without rebuilding
.venv/bin/python scripts/build_module_v5.py {track} {num} --verify

# Batch verification
.venv/bin/python scripts/verify_track.py {track}
.venv/bin/python scripts/verify_track.py {track} --quick   # use cached status
.venv/bin/python scripts/verify_track.py {track} --full    # require full pass
```

---

## Status JSON Structure

Each module has `curriculum/l2-uk-en/{track}/status/{slug}.json`:

```json
{
  "slug": "slavic-tribes",
  "track": "hist",
  "timestamp": "2026-02-19T10:00:00Z",
  "overall": "PASS",
  "gates": {
    "word_count": {"status": "PASS", "value": 5123, "threshold": 5000},
    "outline_compliance": {"status": "PASS"},
    "activities": {"status": "PASS", "count": 6},
    "vocabulary": {"status": "PASS", "count": 32},
    "naturalness": {"status": "PASS", "score": 9.2}
  }
}
```

Check status without re-auditing:
```bash
curl -s http://localhost:8765/api/blue/live-status   # all tracks
curl -s http://localhost:8765/api/gold/inspect/{track}/{slug}  # specific module
```

---

## Interpreting PASS vs Content-Complete

| Status | Meaning |
|--------|---------|
| `PASS` | All 5 content gates pass |
| `content-complete` | Prose passes but activities/vocab missing |
| `FAIL` | One or more gates fail |
| `in-progress` | Build currently running |

A module is only "done" when status is `PASS`.
