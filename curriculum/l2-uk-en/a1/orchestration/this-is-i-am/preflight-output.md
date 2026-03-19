  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=32911 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Activity Rules (Item Minimums) vs activity_hints in Plan"
      problem: "The plan specifies 'items: 4' for the 'Meeting someone new' fill-in activity, but the prompt's hard constraints in the 'Item Minimums' table require a minimum of 6 items for 'fill-in' activities. Following the plan's count will trigger a 'HARD FAIL' during the audit phase."
      suggested_fix: "Increase the item count for the 'Meeting someone new' activity in the plan to 6 or more to satisfy the audit gate requirements."
      severity: HIGH
```
