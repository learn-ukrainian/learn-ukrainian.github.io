  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=32564 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Rule 1 (Grammar Allowlist) vs. Rule 6 (Hard Constraints)"
      problem: "Rule 1 states that any structure including conjugated verbs is FORBIDDEN, while Rule 6 (Hard Constraints) states that simple present tense (e.g., 'я читаю') and basic imperatives are ALLOWED. This creates significant ambiguity for an A1.1 module."
      suggested_fix: "Clarify if verbs are permitted. Given the plan specifies 'verb-free patterns' for describing outfits, Rule 1 is likely the intended constraint."
      severity: HIGH
    - type: CONTRADICTION
      location: "Rule 2 (Vocabulary Bank) vs. Cumulative Vocabulary and Rule 1"
      problem: "Rule 2 commands 'Use ONLY these Ukrainian words' and lists only 14 terms. However, the 'What the Learner Already Knows' section provides 91 cumulative words, and Rule 1 requires using words like 'Це' and 'кіт' which are not in the Rule 2 list. Following Rule 2 strictly would make it impossible to write any sentences or use prior knowledge."
      suggested_fix: "Change Rule 2 to 'Use these target words in addition to the cumulative vocabulary' and remove the 'ONLY' restriction."
      severity: HIGH
    - type: CONTRADICTION
      location: "Rule 4 (Stress Marks) vs. Language Quality Rules"
      problem: "Rule 4 explicitly forbids adding stress marks ('Do NOT add stress marks'), whereas the 'Language Quality Rules' section under Section 5 mandates their use ('ALWAYS use... combining acute accent (´) on the stressed vowel')."
      suggested_fix: "Clarify if the model should provide stress marks or if they are handled by a post-processing pipeline. Remove the conflicting instruction."
      severity: MEDIUM
```
