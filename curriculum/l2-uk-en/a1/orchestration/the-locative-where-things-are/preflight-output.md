  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=1466 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml

  [watchdog] Output resumed after 143s stall
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: MISSING_INSTRUCTION
      location: "Section 5: Guidelines -> Activity Rules"
      problem: "The prompt specifies 'Required types: fill-in, fill-in, fill-in, match-up', which only covers 2 unique types. The audit gates explicitly require 'Min activity types: 4'. A literal LLM might only generate fill-in and match-up activities to reach the 8 total minimum, which would cause the Unique_types audit gate to fail."
      suggested_fix: "Explicitly add a rule stating 'You MUST use at least 4 UNIQUE activity types' and perhaps require 4 distinct types in the 'Required types' list."
      severity: HIGH
```
