  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=35399 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Outline section '## Шість основних голосних — Six Base Vowels' vs 'FRICTION CONSTRAINTS'"
      problem: "The outline explicitly instructs to 'Drill with minimal pairs: сир (cheese) vs сір (grey)'. However, the 'FRICTION CONSTRAINTS' section (Section 7) explicitly labels this a previous failure, stating: 'Hallucinated word \"сір\" claimed as Ukrainian for \"grey\". The correct word is \"сірий\". Replace the сир/сір minimal pair with a verified pair like кит/кіт'."
      suggested_fix: "Update the outline and plan points to use 'кит (whale) vs кіт (cat)' instead of the incorrect 'сир vs сір' minimal pair."
      severity: HIGH
```
