  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=38906 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section Outline (Presentation: Wishes) vs. Language Quality Rules"
      problem: "The mandatory outline point for the Wishes section includes IPA symbols (/ˈʃtʃɑstʲɐ/, /zdɔˈrɔu̯jɐ/), but the 'Language Quality Rules' and 'Hard Constraints' strictly ban IPA and Latin transliteration at all levels. Following the outline verbatim would trigger a 'Linguistic Accuracy' or 'Hard Rule' failure."
      suggested_fix: "Remove the IPA symbols from the phonetic exercise; instead, describe the sounds (Щ, Я, Ь, апостроф) using English phonetic approximations or descriptions of the mechanics of the sounds."
      severity: LOW
```
