# Decision Journal

> **Scope:** When and how to record architectural decisions. Prevents re-litigating settled questions and ensures stale decisions don't calcify.
> Source of truth: `docs/decisions/decisions.yaml` | Index: `docs/decisions/INDEX.md`

---

## Why

Two failure modes this system prevents:

1. **Re-litigation** -- the same question comes up every few sessions because nobody remembers the answer. The `alternatives` field captures what was rejected and why, so the discussion doesn't repeat.
2. **Calcification** -- a decision made under old constraints stays in force long after the context changed. The `expires` field forces periodic review.

---

## When to Create a Decision

| Create | Don't Create |
|--------|-------------|
| Architectural choices (schema design, layer boundaries) | Bug fixes |
| Tool selection (which model, which library) | Config changes |
| Pipeline design (phase ordering, retry strategy) | Typo corrections |
| Pedagogy approaches (immersion progression, activity philosophy) | Routine module builds |
| Track architecture (what goes where, prerequisites) | One-off scripts |

**Rule of thumb:** if two reasonable people could disagree on the approach, record the decision.

---

## Decision Fields

```yaml
- id: dec-042
  status: active              # active | superseded | expired | archived
  date: 2026-04-03
  expires: 2026-07-02         # mandatory — default 90 days from date
  scope: pipeline             # pipeline | content | architecture | tooling | pedagogy
  title: "Use Opus for all content writing"
  reasoning: >
    Gemini produces higher word counts but lower naturalness scores.
    Opus consistently scores 9+ on first pass, reducing fix rounds.
  evidence:
    - "#1100 — Opus vs Gemini A/B test"
    - "#1105 — naturalness regression in Gemini batch"
  alternatives:
    - option: "Gemini for content, Claude for review"
      rejected_because: "Fix rounds doubled, net token cost higher"
    - option: "Gemini with tighter prompts"
      rejected_because: "3 prompt iterations showed no improvement on naturalness"
  superseded_by: null         # dec-NNN if superseded
  depends_on: []              # list of dec-NNN this decision builds on
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | `dec-NNN` — sequential, never reused |
| `status` | Yes | Lifecycle state (see below) |
| `date` | Yes | Date the decision was made |
| `expires` | Yes | Mandatory review date. Default: 90 days. No permanent decisions. |
| `scope` | Yes | One of: `pipeline`, `content`, `architecture`, `tooling`, `pedagogy` |
| `title` | Yes | Short description (< 80 chars) |
| `reasoning` | Yes | Why this approach was chosen |
| `evidence` | Yes | GH issue refs, test results, benchmarks |
| `alternatives` | Yes | What was rejected and why. Minimum 1 alternative. |
| `superseded_by` | No | Points to the replacement decision |
| `depends_on` | No | List of decisions this one builds on |

---

## Status Lifecycle

```
active ──┬──> superseded   (replaced by a newer decision)
         ├──> expired      (past expiry, needs review)
         └──> archived     (reviewed and intentionally retired)
```

- **active** -- currently in force. Injected into relevant prompts and workflows.
- **superseded** -- replaced by another decision. `superseded_by` field points to the replacement.
- **expired** -- past its `expires` date without renewal. Flagged by staleness detection.
- **archived** -- intentionally retired after review. The decision is no longer relevant.

---

## Budget

| Limit | Value |
|-------|-------|
| Max active decisions | 50 |
| Max file length | 500 lines |
| Action when full | Archive oldest resolved decisions to `docs/decisions/archive/` |

When the file approaches 500 lines, archive `superseded` and `archived` entries first. If still over budget, archive the oldest `expired` entries.

---

## Staleness Detection

`scripts/check_decisions.py` scans `docs/decisions/decisions.yaml` for expired or near-expiry decisions.

**Integration:** Runs in the `session-setup` hook. Reports expired decisions at session start.

**Auto-issue creation:** When run with `--create-issues`, creates GH issues with the `decision:stale` label for each expired decision. The issue body includes the original reasoning and alternatives so the reviewer has full context.

```bash
# Full report (default)
.venv/bin/python scripts/check_decisions.py

# Quiet mode — exit 1 if any expired, no output otherwise
.venv/bin/python scripts/check_decisions.py --quiet

# Create GH issues for expired decisions
.venv/bin/python scripts/check_decisions.py --create-issues
```

---

## Commit Convention

When implementing a decision, include the decision ID in the commit body:

```
fix(pipeline): use Opus for all content writing

Decision: dec-042

Co-Authored-By: ...
```

This creates a traceable link from code changes back to the reasoning.

---

## Index File

`docs/decisions/INDEX.md` provides a quick-reference table of all decisions:

```markdown
| ID | Status | Scope | Title | Expires |
|----|--------|-------|-------|---------|
| dec-042 | active | pipeline | Use Opus for all content writing | 2026-07-02 |
| dec-041 | superseded | architecture | Bridge module between A2 and B1 | -- |
```

Keep the index sorted by ID descending (newest first). Update the index whenever `decisions.yaml` changes.
