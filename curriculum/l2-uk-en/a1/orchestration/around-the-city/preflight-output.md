  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=1452 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: MISSING_INSTRUCTION
      location: "Section 4 (Targets) and Section 5 (Activity Rules)"
      problem: "The audit gates require a minimum of 4 unique activity types ('Min activity types: 4'), but the prompt only explicitly requires 2 unique types (match-up, fill-in) and does not instruct the builder to ensure at least 4 distinct types are used overall. This will likely lead to a Unique_types gate failure."
      suggested_fix: "Update the targets or activity rules to explicitly state: 'You MUST use at least 4 DIFFERENT activity types across your activities to pass the Unique_types audit gate.'"
      severity: HIGH
```
