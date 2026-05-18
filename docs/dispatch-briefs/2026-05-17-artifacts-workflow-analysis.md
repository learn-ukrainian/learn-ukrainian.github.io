# Dispatch brief — analyze /api/artifacts/ corpus for workflow improvements

**Agent:** Gemini gemini-3.1-pro-preview (free; long-context fit for 1007-artifact synthesis)
**Mode:** workspace-write (READ corpus + write ONE report file; no commits to project code)
**Worktree:** required (per #1952)
**Deliverable:** ONE markdown report at `audit/2026-05-17-artifacts-workflow-analysis/REPORT.md` with concrete, actionable workflow-improvement recommendations grounded in evidence from the artifact corpus.
**No PR.** Report writes to repo via commit on the dispatch branch; orchestrator reviews + decides what gets actioned via follow-up PRs.

---

## Why

User question 2026-05-17 night: "process our http://localhost:8765/artifacts/ this is lots of data and analyse what shoud we improve in our workflows?"

The artifacts endpoint surfaces 1007 documents (handoffs, dispatch briefs, decisions, audit reports, bug autopsies, agent matrices, ADRs, etc.) — the project's full institutional memory. Reading the corpus end-to-end for patterns + frictions + repeat failures should produce a punch list of concrete improvements that the orchestrator can then split into PRs.

Goal is NOT "summarize what's there" — that's a table of contents, low value. Goal IS "find the repeated failure patterns, the work that should have been automated, the orchestration gaps, the brief-template improvements, the missing standards" — with file:line references so each recommendation is auditable.

---

## What you read (smart strategy, NOT brute force)

The corpus is too big to read every body. Use this 3-stage approach:

### Stage 1: Pull the full index (cheap)

```bash
curl -s --max-time 10 'http://localhost:8765/api/artifacts/html?limit=2000' > /tmp/artifacts-index.json
```

This is ~500KB of structured metadata: `path`, `class`, `date`, `title`, `kpi_summary`, `related_issues`, `related_prs`, `agents`, `size_bytes`, `modified_at` per entry. Read it ALL — the metadata is already 80% of the signal.

### Stage 2: Pick representative documents to deep-read

From the index, pick AT LEAST these categories (target ~40-60 documents total):

| Category | Filter | Sample target |
|---|---|---|
| **Session handoffs** | `path LIKE 'docs/session-state/%'` | Latest 15 (chronological — handoffs ARE the project's workflow narrative) |
| **Dispatch briefs** | `path LIKE 'docs/dispatch-briefs/%'` | Latest 10 + 5 OLDEST (so you see template evolution) |
| **Decision cards / ADRs** | `path LIKE 'docs/decisions/%'` OR `path LIKE 'docs/adr/%'` | ALL (they're load-bearing; usually <30) |
| **Bug autopsies** | `path LIKE 'docs/bug-autopsies/%'` | ALL — repeat-failure source material |
| **Audit reports** | `path LIKE 'audit/%REPORT.md'` | Last 10 by date |
| **Agent matrices / capability docs** | `path LIKE 'docs/agents/%'` | ALL |
| **Friction / postmortem files** | `path` matches `(friction|postmortem|retro|lessons)` | ALL |

For each picked document, fetch the body:

```bash
curl -s --max-time 5 "http://localhost:8765/artifacts/${path}" > /tmp/artifact-bodies/${slug}.md
```

If you exceed your context budget, prefer to skim per-file (first 200 lines + last 100 lines) rather than truncate the SET — coverage breadth beats depth on most documents.

### Stage 3: Cross-pattern synthesis

Look for these specific signals (NOT "what is this project doing" — that's already documented):

1. **Repeat failure patterns**: same bug/mistake/misroute mentioned in ≥2 handoffs or autopsies. Each instance gets a file:line citation.
2. **Brief-template improvements**: dispatch briefs that produced bad output, scope creep, anti-fabrication failures, or unclear test plans. What template change would have prevented it?
3. **Orchestration gaps**: handoff items that fell through cycles (mentioned, deferred, mentioned again, deferred again). What process change closes the gap?
4. **Standards drift**: decisions that contradict each other, or decisions that aren't being followed (especially around routing, MEMORY-budget, pre-commit gates, worktree hygiene).
5. **Tool/automation gaps**: work that's mentioned repeatedly as manual that could be scripted (e.g., "I had to grep for X again" appearing in 3+ handoffs).
6. **Missing audit gates**: bugs that escaped because no gate caught them; what would the gate look like?
7. **MEMORY/rule rot**: rules that are no longer being applied (referenced in MEMORY but ignored in practice per the handoff record).
8. **Brief or rule contradictions**: explicit contradictions between two load-bearing documents — file:line on both sides.
9. **Cost/budget signals**: dispatches that wasted budget on routine work that Gemini/DeepSeek should have done per #M0 routing.
10. **Per-agent friction**: places where a specific agent (Codex/Gemini/Claude/Grok/DeepSeek) is being mis-routed against its lane.

---

## Output format — strict

Write `audit/2026-05-17-artifacts-workflow-analysis/REPORT.md` with this structure:

```markdown
# Workflow improvement analysis — artifacts corpus (2026-05-17)

> Source: `/api/artifacts/html` (N=1007 artifacts at audit time).
> Sample: <count> documents deep-read across <count> categories.
> Method: index scan + targeted deep-reads + cross-pattern synthesis.

## TL;DR — top 10 concrete improvements

(One sentence each. Each has a `→` pointer to the recommendation number below.)

1. [Improvement headline] → §1
2. ...
10. ...

## Detailed recommendations

### §1 — [Improvement name]

**Pattern observed**:
- `path/to/handoff.md:line` — quoted evidence
- `path/to/other-handoff.md:line` — quoted evidence
- (≥2 instances required; isolated incidents go to §Notable Singletons, not here)

**Root cause** (your read): one paragraph.

**Concrete fix** (what would prevent the next recurrence):
- (a) [file or rule to change]
- (b) [test, audit gate, or automation to add]
- (c) [brief-template addition]

**Effort estimate**: small / medium / large

**Tracking**: file a new GH issue OR reference existing #NNNN.

(Repeat §N for each recommendation. Aim for 8-15 recommendations total — fewer than 8 means you're under-sampling; more than 15 means you're padding.)

## Notable singletons (1-instance issues worth filing but not patterns)

Bullet list, each with evidence path + 1-sentence framing.

## Out-of-scope observations

Things you noticed that aren't "workflow improvements" but are worth surfacing (code quality, doc rot, dead files, etc.). Bullet list.

## Coverage report

| Category | Total in corpus | Deep-read | Skipped |
|---|---|---|---|
| Session handoffs | N | M | N-M |
| ... | | | |

## Method notes

- What heuristic you used to pick documents
- What you would have read if you had 2x the budget
- Confidence: high / medium / low for each top-10 recommendation
```

The TL;DR is the highest-value section — write it LAST, after the detailed analysis settles. Each TL;DR line must be backed by a §N section.

---

## Verifiable claims this work must produce (per #M-4)

| Claim | Tool + raw output to quote in REPORT.md "Method notes" section |
|---|---|
| Index fetched | `curl ... 'http://localhost:8765/api/artifacts/html?limit=2000' | head -c 200` raw |
| Sample count | `python3 -c "import json; d=json.load(open('/tmp/artifacts-index.json')); print('total:', d['total'], 'sampled:', len(read_paths))"` raw |
| Each recommendation has ≥2 evidence citations | inline in each §N (visible to reviewer) |
| No invented file paths | every `path/to/file.md:line` citation refers to a path returned by `/api/artifacts/html` (cross-check with the index) |
| Report file landed | `git log -1 --oneline` raw + `git diff --stat origin/main` raw |

**No claim allowed without its evidence.** Per #M-4: hallucinated patterns are worse than no patterns — they waste orchestrator time chasing fictional fixes.

---

## Anti-fabrication preamble

If a "pattern" you identify is actually ONE handoff repeating itself across multiple session-state files (because handoffs cite prior handoffs), that's NOT a pattern — that's one observation. Require ≥2 INDEPENDENT instances.

If you can't find ≥8 real recommendations, write fewer. Padding to 10 is forbidden. State the actual count in the TL;DR header.

If a recommendation requires reading documents you didn't sample, name the unsampled documents in the "Method notes" coverage section so the orchestrator knows what to fund a follow-up dispatch on.

If you find a recommendation that contradicts an existing rule or decision, quote both sides and surface the contradiction explicitly — don't silently pick one.

---

## Worktree setup

`delegate.py dispatch --worktree` handles creation. Branch name: `audit/artifacts-workflow-analysis-20260517`.

---

## Verification (before pushing)

```bash
# Confirm the report file is non-trivial
test -s audit/2026-05-17-artifacts-workflow-analysis/REPORT.md
wc -l audit/2026-05-17-artifacts-workflow-analysis/REPORT.md  # expect >150 lines

# Lint markdown (if mdl is available; otherwise skip)
which mdl >/dev/null 2>&1 && mdl audit/2026-05-17-artifacts-workflow-analysis/REPORT.md || true

# Confirm no path citations point at non-existent files
grep -oE '`[a-zA-Z0-9._/-]+\.(md|py|yaml|json|sh)`' audit/2026-05-17-artifacts-workflow-analysis/REPORT.md \
  | tr -d '`' | sort -u | while read p; do test -e "$p" || echo "MISSING: $p"; done
```

If the "MISSING" check finds any paths that don't exist, either fix the citation (it's probably a typo) or remove the recommendation (it was hallucinated).

---

## Commit

```bash
git add audit/2026-05-17-artifacts-workflow-analysis/REPORT.md
git commit -m "$(cat <<'EOF'
audit(workflow): analyze /api/artifacts/ corpus for workflow improvements

Per user request 2026-05-17 night — analyze the 1007-artifact corpus
served by /api/artifacts/html for repeat patterns, brief-template
improvements, orchestration gaps, standards drift, and per-agent
mis-routing. Output is a concrete punch list the orchestrator can
split into PRs.

Method: full index scan (curl /api/artifacts/html?limit=2000) +
targeted deep-reads on ~40-60 representative docs from session-state,
dispatch-briefs, decisions, bug-autopsies, audit reports, and agent
matrices. Cross-pattern synthesis to extract ≥2-instance failure
patterns; isolated incidents go to a "notable singletons" section.

Top 10 recommendations are in the TL;DR; full evidence + root cause +
concrete fix per recommendation in §1-§N. Effort estimates included.

Report only — no PR opened. Orchestrator reviews + splits into PRs.
EOF
)"

git push -u origin audit/artifacts-workflow-analysis-20260517

# NO gh pr create — this is a report, not a code change
# Orchestrator will read the report and split it into actionable issues/PRs
```

---

## Out of scope (do NOT do)

* Write code (any code change is the orchestrator's call after reading the report).
* Edit existing handoffs, decisions, rules, or briefs (read-only on those).
* Open GitHub issues from inside the dispatch (the orchestrator files issues based on the report).
* Recommend changes to project mission, decolonization stance, or pedagogy quality bar (those are user-owned decisions, not workflow).
* Recommend tool changes for the agent runtime (delegate.py, ai_agent_bridge) — those have their own review track; mention if you see friction but don't propose specific edits.
* Generate >15 recommendations. Hard ceiling — past 15 you're padding.
