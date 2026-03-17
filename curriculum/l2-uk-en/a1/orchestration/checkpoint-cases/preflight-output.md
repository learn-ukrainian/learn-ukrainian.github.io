  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=1453 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Boundaries section vs Audit Gates section"
      problem: "The Boundaries section states 'Do NOT generate activities or vocabulary tables (separate phase)', but the Audit Gates require 'Min activities: 8' and 'Min activity types: 4'. Following the boundary rule will cause the Activities gate to fail."
      suggested_fix: "Remove the activities and unique types requirements from the Audit Gates section for the content phase, or update the prompt to include activity generation instructions."
      severity: HIGH
```
