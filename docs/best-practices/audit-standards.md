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

**The review gate does not determine pass/fail.** Only content gates 1-5 do. This removes the incentive for LLMs to inflate review scores.

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
| Max activities | 9 | varies |
| Required types | reading, essay-response, critical-analysis | varies by level |
| Forbidden types | match-up, fill-in, cloze, mark-the-words | — |
| Min items per activity | 1 | varies |

YAML must validate against `schemas/activities-{level}.schema.json`.

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
