# Consultation Workflow — Template Stabilization & Quality Loop

## Overview

The consultation loop is how templates improve. Gemini builds content, Claude reviews it, and when issues are systemic (template-caused, not content-caused), a consultation proposes template fixes. After 2-3 confirmed fixes, the template stabilizes and batch builds can run cleanly.

**Review runs by default.** Every build goes through the full pipeline including review. Use `--skip-review` only for debugging.

---

## The Build → Review → Consult → Fix Loop

```
┌─────────────────────────────────────────────────────┐
│  1. BUILD SAMPLE (1-3 modules)                      │
│     .venv/bin/python scripts/build_module_v5.py     │
│     a1 1                                            │
│                                                     │
│  Pipeline runs automatically:                       │
│  research → discover → content → validate →         │
│  REVIEW → activities → mdx                          │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│  2. CHECK RESULTS                                   │
│     - Audit: .venv/bin/python scripts/audit_module.py│
│     - Review scores: check orchestration/review/    │
│     - Content quality: 12-dimension scoring         │
│       (9-10 = A+ = PASS, <9 = needs work)          │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─────────┴──────────┐
          │ Quality OK?        │
          │ All dims 9-10?     │
          └─────────┬──────────┘
              YES   │   NO
              │     │
              │     ▼
              │   ┌───────────────────────────────────┐
              │   │  3. REQUEST CONSULTATION          │
              │   │     Build with --restart-from     │
              │   │     review, or manually trigger   │
              │   │     consultation phase            │
              │   └───────────────┬───────────────────┘
              │                   │
              │                   ▼
              │   ┌───────────────────────────────────┐
              │   │  4. REVIEW PROPOSALS              │
              │   │                                   │
              │   │  CLI:                             │
              │   │  .venv/bin/python                 │
              │   │    scripts/consultation_cli.py    │
              │   │    list                           │
              │   │                                   │
              │   │  .venv/bin/python                 │
              │   │    scripts/consultation_cli.py    │
              │   │    show FILENAME.yaml             │
              │   │                                   │
              │   │  Web UI:                          │
              │   │  http://localhost:8765/            │
              │   │    consultation.html              │
              │   └───────────────┬───────────────────┘
              │                   │
              │                   ▼
              │   ┌───────────────────────────────────┐
              │   │  5. APPROVE / REJECT              │
              │   │                                   │
              │   │  # Dry-run first                  │
              │   │  .venv/bin/python                 │
              │   │    scripts/consultation_cli.py    │
              │   │    approve FILENAME.yaml          │
              │   │    --dry-run                      │
              │   │                                   │
              │   │  # Then apply                     │
              │   │  .venv/bin/python                 │
              │   │    scripts/consultation_cli.py    │
              │   │    approve FILENAME.yaml          │
              │   │                                   │
              │   │  This patches the GLOBAL template │
              │   │  in claude_extensions/phases/     │
              │   │  gemini/. All future builds use   │
              │   │  the fixed template.              │
              │   └───────────────┬───────────────────┘
              │                   │
              │                   ▼
              │   ┌───────────────────────────────────┐
              │   │  6. REBUILD SAME MODULE           │
              │   │     .venv/bin/python               │
              │   │     scripts/build_module_v5.py    │
              │   │     a1 1 --restart-from content   │
              │   │                                   │
              │   │  Verify the fix works.            │
              │   │  If still failing → back to 3.    │
              │   └───────────────┬───────────────────┘
              │                   │
              │                   ▼
              │   ┌───────────────────────────────────┐
              │   │  7. BUILD 2 MORE SAMPLES          │
              │   │     to confirm template stable    │
              │   │     (different modules, same      │
              │   │     level/template)               │
              │   └───────────────┬───────────────────┘
              │                   │
              ▼                   ▼
┌─────────────────────────────────────────────────────┐
│  8. TEMPLATE STABLE — BATCH BUILD                   │
│     .venv/bin/python scripts/build_module_v5.py     │
│     a1 --all                                        │
│                                                     │
│  Or use batch dispatcher for autonomous scheduling. │
└─────────────────────────────────────────────────────┘
```

---

## Consultation Scopes

| Scope | What happens | Human needed? |
|-------|-------------|---------------|
| `this_module` | Auto-patches module-local content, rebuilds | No |
| `all_modules` | Queues template change for approval | Yes — review + approve |

Most consultations at scale should be `this_module` (automated). Template-level `all_modules` proposals decrease as templates stabilize.

---

## CLI Quick Reference

```bash
# List pending proposals
.venv/bin/python scripts/consultation_cli.py list

# Show detail
.venv/bin/python scripts/consultation_cli.py show FILENAME.yaml

# Approve (dry-run first, then for real)
.venv/bin/python scripts/consultation_cli.py approve FILENAME.yaml --dry-run
.venv/bin/python scripts/consultation_cli.py approve FILENAME.yaml

# Reject
.venv/bin/python scripts/consultation_cli.py reject FILENAME.yaml --reason "Why"

# Batch approve all high-confidence proposals
.venv/bin/python scripts/consultation_cli.py approve-all --confidence high --dry-run
.venv/bin/python scripts/consultation_cli.py approve-all --confidence high
```

---

## Quality Scoring (12 Dimensions)

Each module is scored on 12 dimensions, 0-10 each. **Only 9-10 = A+ = PASS.**

| # | Dimension | Weight | Auto-fail threshold |
|---|-----------|--------|---------------------|
| 1 | Experience Quality | 1.5x | — |
| 2 | Coherence | 1.0x | — |
| 3 | Relevance | 1.0x | — |
| 4 | Educational | 1.2x | — |
| 5 | Language | 1.1x | <7 (Tier 2+) |
| 6 | Pedagogy | 1.2x | — |
| 7 | Immersion | 0.8x | — |
| 8 | Activities | 1.3x | — |
| 9 | Richness | 0.9x | — |
| 10 | Humanity | 0.8x | — |
| 11 | LLM Fingerprint | 1.1x | ≥3 patterns (Tier 2+) |
| 12 | Linguistic Accuracy | 1.5x | ≤5 |

Tier rubrics: `claude_extensions/skills/plan-review/review-tiers/`

---

## Template Conflict Handling

When two consultations target the same template region:
- The first one's FIND/REPLACE applies normally
- The second one's FIND string won't match (text already changed)
- CLI reports "FIND string not found" and skips — safe, no corruption
- **Action**: review the skipped proposal manually, adapt the FIND string if the change is still needed

---

## Files

| Path | Purpose |
|------|---------|
| `claude_extensions/phases/gemini/*.md` | Global templates (patched by approve) |
| `claude_extensions/consultation-queue/` | Pending proposals |
| `claude_extensions/consultation-queue/applied/` | Approved proposals |
| `claude_extensions/consultation-queue/rejected/` | Rejected proposals |
| `scripts/consultation_cli.py` | CLI tool |
| `scripts/api/consultation_router.py` | API endpoints |
| `playgrounds/consultation.html` | Web UI |
| `scripts/pipeline/consultation.py` | Core parser + patcher |
| `claude_extensions/skills/plan-review/review-tiers/` | Tier scoring rubrics |
