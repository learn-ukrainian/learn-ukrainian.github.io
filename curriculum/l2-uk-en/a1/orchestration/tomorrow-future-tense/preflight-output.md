  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=36871 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: PASS
  issues:
    - type: CONTRADICTION
      location: "Section 5: Rule 4 vs. Language Quality Rules (Typography)"
      problem: "Rule 4 explicitly instructs: «Write Ukrainian without stress marks — the pipeline adds them after.» However, the Language Quality Rules section contradicts this by stating: «ALWAYS use lowercase letters with a combining acute accent (´) on the stressed vowel» and marking «ма́ма» as the only correct example. This may confuse the agent regarding whether to include or omit stress marks."
      suggested_fix: "Clarify if the agent should follow Rule 4 (omit stress marks) or the Typography rule (include them). For A1 modules, stress marks are typically expected for quality gates."
      severity: MEDIUM
    - type: PLAN_CONTRADICTION
      location: "Required Vocabulary (збиратися)"
      problem: "The entry for 'збиратися' is rendered as a Python dictionary object: «- {'збиратися (to be going to) ...' : '...'}» rather than a plain string. While understandable, it's a formatting error in the prompt template."
      suggested_fix: "Fix the template rendering to ensure all vocabulary hints are plain text strings."
      severity: LOW
    - type: MISSING_INSTRUCTION
      location: "Section 6: Hard Constraints (Euphony)"
      problem: "The prompt says «follow rules in the shared content rules section below», but the specific section detailing euphony (у/в, і/й alternation) is missing from the prompt text."
      suggested_fix: "Provide the specific euphony rules or remove the broken cross-reference."
      severity: LOW
```
