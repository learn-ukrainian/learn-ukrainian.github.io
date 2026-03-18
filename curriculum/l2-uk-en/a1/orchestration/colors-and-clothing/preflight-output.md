  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=33850 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 5. Guidelines -> Activity Rules vs Activity Rules Table"
      problem: "The 'Forbidden types' list explicitly bans 'translate', while the 'Activity Rules' table states 'M11+ | all types including translate' are allowed. Since this is Module 12, the generator may be confused as to whether translation activities are permissible."
      suggested_fix: "Remove 'translate' from the Forbidden types list for modules 11+ or clarify in the prose that it becomes available at this level."
      severity: MEDIUM
```
