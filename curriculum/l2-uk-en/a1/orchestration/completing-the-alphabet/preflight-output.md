  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=39268 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section '## Диграфи ДЖ, ДЗ — Digraphs' outline vs 'Hard Constraints'"
      problem: "The outline point requiring the mention that ДЗ is 'absent from Russian' directly contradicts the Hard Constraint 'No colonial framing: never define Ukrainian by comparing it to Russian. Don't say... \"not found in Russian.\"' and the Friction Constraint '[GLOBAL] NEVER frame Ukrainian as \"lacking\" or \"missing\" letters that Russian has'."
      suggested_fix: "Remove the phrase 'absent from Russian' from the outline point. Focus instead on its unique sound or presence in native Ukrainian words like 'дзвін'."
      severity: MEDIUM
    - type: PLAN_CONTRADICTION
      location: "Pronunciation Videos list vs Outline and Prerequisites"
      problem: "The prompt mandates embedding a video for 'Літера Ґ', but the 'Grammar already taught' section states that the 'Г vs Ґ distinction' was completed in a previous module. 'Ґ' is not in the current outline or objectives, meaning there is no H3 section to host the required video. Conversely, no videos are provided for the digraphs ДЖ and ДЗ, which are primary objectives for this module."
      suggested_fix: "Remove 'Літера Ґ' from the mandatory video list for M4 and, if possible, provide video links for the ДЖ and ДЗ digraphs."
      severity: LOW
```
