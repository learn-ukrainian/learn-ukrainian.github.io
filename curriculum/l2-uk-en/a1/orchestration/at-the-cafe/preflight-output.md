  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=35400 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 5 Rule 4 vs. Language Quality Rules"
      problem: "Section 5 Rule 4 explicitly instructs the agent to 'Write Ukrainian without stress marks' because the 'pipeline adds them after'. However, the 'Language Quality Rules' and 'Immersion Target' sections state that stress marks are the 'ONLY pronunciation aid' and 'ALWAYS use lowercase letters with a combining acute accent (´)'. Missing stress marks in A1 content typically results in a Pedagogy and Experience Quality gate failure, as learners require them for correct pronunciation."
      suggested_fix: "Remove Section 5 Rule 4 to align with the mandatory quality standards and ensure the agent provides the necessary stress marks for beginner learners."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section 5 Rule 4 (Notation) vs. Language Quality Rules"
      problem: "The exception in Section 5 Rule 4 allows the use of capitalized stress notation (e.g., молокО), which directly contradicts the Language Quality Rules that categorize such capitalization as 'Wrong' (e.g., мА́ма)."
      suggested_fix: "Standardize the prompt to use only the combining acute accent (´) and remove the allowance for capitalized stress."
      severity: LOW
```
