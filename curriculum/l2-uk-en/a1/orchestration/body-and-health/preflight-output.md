  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=41199 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Activity Rules (Section 5) vs. Plan activity_hints"
      problem: "The plan specifies a 'fill-in' activity for the 'Pharmacy scenario' with only 5 items. However, the 'Item Minimums' table in Section 5 of the prompt explicitly states that 'fill-in' activities must have a minimum of 6 items and labels anything under this as a 'HARD FAIL'."
      suggested_fix: "Increase the item count for the 'Pharmacy scenario' fill-in activity to at least 6 to ensure it passes the audit gate."
      severity: MEDIUM
```
