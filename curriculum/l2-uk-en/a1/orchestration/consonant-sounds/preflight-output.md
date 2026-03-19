  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=35287 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 5 Rule 4 / Section 6 Hard Constraints vs. Language Quality Rules"
      problem: "There is a direct contradiction regarding stress mark (´) usage. Section 5 Rule 4 and the Section 6 Hard Constraints explicitly state 'Do NOT add stress marks' and 'Write plain Ukrainian', noting that the pipeline adds them later. However, the 'Language Quality Rules' block and the 'Rule 6' summary explicitly require them ('Use lowercase letters with a combining acute accent (´)', 'stress marks (´) only')."
      suggested_fix: "Standardize the instruction. If the pipeline is intended to add stress marks deterministically, remove the 'Language Quality Rules' requirement to manually add them for this module to prevent generator confusion or double-stressing."
      severity: MEDIUM
```
