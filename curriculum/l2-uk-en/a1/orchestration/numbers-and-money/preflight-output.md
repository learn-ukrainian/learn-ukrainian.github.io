  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=36874 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "## 4. Outline > Презентація (Presentation) AND Language Quality Rules > Stress Mark Typography"
      problem: "The outline explicitly requests capitalized vowels for stress (одинАдцять, дванАдцять), which directly contradicts the 'Stress Mark Typography' rule that strictly bans capitalizing the stressed vowel (e.g., 'Wrong: мА́ма') and requires the combining acute accent (´)."
      suggested_fix: "Update the outline to use the combining acute accent instead of capital letters: 'одина́дцять, двана́дцять'."
      severity: HIGH
    - type: CONTRADICTION
      location: "## 4. Outline > Презентація (Presentation) AND Language Quality Rules > IPA and Latin Transliteration"
      problem: "The outline requests a bracketed Latin pronunciation guide for the word five: «п'ять» [pjat']. This directly contradicts the 'IPA and Latin Transliteration' rule, which strictly bans bracketed pronunciation guides and Latin transliterations."
      suggested_fix: "Remove the bracketed Latin guide '[pjat']' from the outline and instruct the writer to explain the apostrophe's pronunciation effect using English descriptions rather than transliteration."
      severity: HIGH
```
