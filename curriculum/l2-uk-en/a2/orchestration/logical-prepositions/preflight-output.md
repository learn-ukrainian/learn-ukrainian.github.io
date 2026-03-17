  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=32148 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section: 3. Context -> Vocabulary from Plan AND Section: 5. Guidelines -> Language Quality Rules"
      problem: "The vocabulary list for 'після' and 'завдяки' includes bracketed IPA guides (e.g., [ˈpʲisʲlʲa]), but the 'Language Quality Rules' explicitly state that IPA is BANNED at all levels and 'never include bracketed pronunciation guides like [ˈmɑmɑ]'."
      suggested_fix: "Remove the IPA strings from the vocabulary hints for 'після' and 'завдяки' to prevent the model from accidentally including them in the content or YAML."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section: 3. Context -> Immersion Target AND Section: 4. Outline"
      problem: "The Immersion Target guidelines state 'No abstract nouns', but the Module Goal is to teach 'abstract logical prepositions' and the Practice section specifically requires a 'Case selection drill' for 'abstract contexts'."
      suggested_fix: "Clarify the 'No abstract nouns' rule to allow high-frequency abstract nouns necessary for logical prepositions (e.g., health, help, result, effort) while still avoiding advanced philosophical or academic abstractions."
      severity: MEDIUM
```
