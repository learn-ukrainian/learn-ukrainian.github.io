# Plan Review: aspect-future

**Track:** B1 | **Sequence:** 11 | **Version:** 2.0
**Verdict:** NEEDS FIXES

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 4000, Config: 4000 |
| section_budgets | PASS | Sum = 4000 vs target 4000 (0%) |
| required_fields | FAIL | Missing: register |
| version_string | PASS | Version is string: '2.0' |

## Issues Found

### HIGH (should fix before build)
1. Missing required `register` field
2. Self-referencing connects_to: b1-11 (Aspect in imperatives)

### MEDIUM (fix if possible)
1. Vague objective: "Learner understands when to use compound vs synthetic imperfective fut..."
