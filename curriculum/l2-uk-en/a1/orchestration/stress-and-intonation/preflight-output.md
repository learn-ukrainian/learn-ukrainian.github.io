  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=33532 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: PLAN_CONTRADICTION
      location: "vocabulary_hints in Plan/Prompt vs FRICTION CONSTRAINTS"
      problem: "The plan and prompt vocabulary section specify last-syllable stress for the word 'далеко' (далеко́), but the Friction Constraints section (listing past errors to avoid) explicitly states that 'далеко́ should be дале́ко' (penultimate stress). Following the plan will likely result in a Language Accuracy audit failure."
      suggested_fix: "Use 'дале́ко' as the primary stress form throughout the module content and vocabulary YAML to align with the corrective feedback in the Friction Constraints."
      severity: HIGH
```
