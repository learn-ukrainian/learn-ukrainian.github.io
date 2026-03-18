  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=36396 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Rule 1 (Grammar Allowlist) vs Rule 6 (Hard Constraints)"
      problem: "Rule 1 states 'Any other structure (including conjugated verbs) is FORBIDDEN,' while Rule 6 lists 'Simple present tense (я читаю, я бачу)' as ALLOWED. This creates ambiguity regarding the use of verbs in the module."
      suggested_fix: "Clarify whether simple present tense verbs are allowed for A1.1 First Contact. Usually, M1-M14 avoid conjugated verbs except for fixed phrases."
      severity: MEDIUM
    - type: IMPOSSIBLE_TARGET
      location: "Rule 2 (Vocabulary Bank) vs Outline and Vocabulary Hints"
      problem: "Rule 2 explicitly commands: 'Use ONLY these Ukrainian words' and provides a very limited list (e.g., 'добрий', 'до', 'будь', 'дякую'). However, the required vocabulary and mandatory outline points include many nouns and phrases not present in this bank, such as 'ранок', 'день', 'вечір', 'побачення', 'ласка', 'приємно', 'звати', 'мене', 'мамо', 'тату', 'друже', etc. Following Rule 2 strictly makes it impossible to fulfill the content requirements."
      suggested_fix: "Update Rule 2 to include all words listed in the 'Required' and 'Recommended' vocabulary sections, as well as the vocative forms (мамо, тату, etc.) mentioned in the 'Звертання' outline."
      severity: HIGH
    - type: CONTRADICTION
      location: "Rule 2 (Vocabulary Bank) vs Language Quality Rules (Typography)"
      problem: "Rule 2 says 'Use ONLY these Ukrainian words', but the Typography section says 'Base content vocabulary on the plan's vocabulary_hints. Function words... are always allowed.' These instructions are inconsistent."
      suggested_fix: "Consolidate vocabulary restrictions into a single rule that permits plan vocabulary, function words, and words required by the outline."
      severity: LOW
```
