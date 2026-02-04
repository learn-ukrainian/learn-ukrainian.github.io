# Handoff: Bug Investigation Template

Use this template for deep-dive root cause analysis of script failures or unexpected behavior
that requires structured investigation (not simple fixes).

## Usage

```bash
gh issue create \
  --title "bug: Brief description of the problem" \
  --body-file /tmp/issue-body.md \
  --label "bug" \
  --label "infrastructure" \
  --label "agent:claude"
```

---

## Template

```markdown
## Problem Statement

**What happened**: [Observable behavior]
**What was expected**: [Desired behavior]
**When it started**: [First observed / after what change]
**Frequency**: [Always / Sometimes / Once]

## Reproduction Steps

1. [Step 1]
2. [Step 2]
3. [Step 3]

**Minimal reproduction**:
```bash
# Command that triggers the issue
.venv/bin/python scripts/example.py --flag
```

## Error Output

```
[Paste full error message / stack trace]
```

## Environment

| Factor | Value |
|--------|-------|
| Python version | 3.12.8 |
| OS | macOS / Linux |
| Branch | main / feature-X |
| Last working commit | abc123 |

## Investigation Tasks

- [ ] Reproduce the issue locally
- [ ] Identify the failing component
- [ ] Trace execution path to failure point
- [ ] Identify root cause (not just symptom)
- [ ] Determine scope of impact
- [ ] Propose fix approach

## Investigation Log

### Attempt 1: [Hypothesis]
**Theory**: [What you think might be wrong]
**Test**: [How you tested it]
**Result**: [What you found]
**Conclusion**: [Confirmed / Ruled out]

### Attempt 2: [Hypothesis]
...

## Root Cause Analysis

### What Broke
[Specific component/function/line]

### Why It Broke
[The actual cause - not just "it threw an error"]

### Contributing Factors
- [Factor 1: e.g., missing validation]
- [Factor 2: e.g., assumption about input format]

### Timeline
- [Date]: [Change that introduced the bug]
- [Date]: [When bug first manifested]
- [Date]: [When bug was discovered]

## Impact Assessment

| Area | Impact |
|------|--------|
| Data integrity | [None / Partial / Severe] |
| User experience | [None / Degraded / Blocked] |
| Other scripts | [None / Some affected / Many affected] |
| Workaround exists | [Yes / No] |

## Proposed Fix

### Approach
[How to fix the root cause]

### Files to Modify
| File | Change |
|------|--------|
| `scripts/example.py` | Add input validation |
| `tests/test_example.py` | Add regression test |

### Risk Assessment
- [Risk 1: Could break X]
- [Mitigation: Test Y before deploying]

## Definition of Done

- [ ] Root cause identified and documented
- [ ] Fix implemented
- [ ] Regression test added
- [ ] No new issues introduced
- [ ] Fix verified in same environment as bug

## Related

- Related issue: #XXX
- Similar past bug: #YYY
- Affected code: `scripts/path/to/file.py`
```

---

## Investigation Best Practices

1. **Reproduce first** - Don't guess, confirm the issue exists
2. **Isolate variables** - Change one thing at a time
3. **Check recent changes** - `git log --oneline -20`
4. **Add logging** - Temporary debug output helps trace flow
5. **Document dead ends** - Failed hypotheses are still valuable
6. **Fix root cause** - Not just the symptom
