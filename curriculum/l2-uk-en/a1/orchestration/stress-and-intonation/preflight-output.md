  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=31512 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Rules Section 5 -> Rule 4 vs Language Quality Rules -> Stress Mark Typography"
      problem: "Rule 4 states: 'Exception: if the plan uses capitalized stress (молокО, далекО) to indicate stress position, you may use that notation'. However, the Language Quality Rules section explicitly states: 'Wrong: мА́ма... (do NOT capitalize the stressed vowel)' and 'ALWAYS use lowercase letters with a combining acute accent'. Following the Rule 4 exception will trigger a typography failure in the audit gate."
      suggested_fix: "Remove the permission to use capitalized stress notation. Instruct the generator to convert plan examples like 'зАмок' into 'за́мок' using the combining acute accent on a lowercase vowel."
      severity: MEDIUM
    - type: CONTRADICTION
      location: "Rules Section 5 -> Rule 4 vs Language Quality Rules -> Stress Mark Typography"
      problem: "Rule 4 says 'Write Ukrainian without stress marks — the pipeline adds them after', but the Language Quality Rules state 'The ONLY pronunciation aid is the stress mark (´) on the vowel' and provide 'Correct: ма́ма' examples. In a module specifically about Stress and Intonation, omitting stress marks in the prose makes the content pedagogically useless, while including them may conflict with the 'pipeline' instruction."
      suggested_fix: "Clarify that for this specific module (M06), the generator MUST use stress marks (combining acute accent) for all teaching examples and vocabulary items to fulfill the 'Linguistic Accuracy' and 'Pedagogy' gates, even if a pipeline exists for other modules."
      severity: MEDIUM
```
