  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=36776 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Outline (Presentation: Forms and Conjugation) vs. Section 6 (Hard Constraints)"
      problem: "The outline point for the Shibboleth Pronunciation requires the tutor to describe the sound as 'distinct from the hard Russian [ца]'. This directly violates the Hard Constraint in Section 6: 'No colonial framing: never define Ukrainian by comparing it to Russian. Don't say \"unlike Russian...\" or \"not found in Russian.\"'."
      suggested_fix: "Remove the explicit comparison to Russian. Focus on describing the unique soft and long quality of the Ukrainian sound cluster on its own merits."
      severity: HIGH
    - type: CONTRADICTION
      location: "Outline (Presentation: Forms and Conjugation) vs. Section 5 (Guidelines: Language Quality Rules)"
      problem: "The outline requests the inclusion of the phonetic guide '[ц':а]'. However, the Language Quality Rules in Section 5 strictly forbid bracketed pronunciation guides ('Never include... bracketed pronunciation guides like [ma-ma], [a-na-nas], [ˈmɑmɑ]'). Including this would likely trigger a automated gate failure for the 'No IPA/Transliteration' rule."
      suggested_fix: "Instruct the tutor to describe the sound cluster phonetically in prose (e.g., 'a long, soft ts-sound') without using square brackets, or explicitly whitelist Cyrillic-based phonetic notation for this specific shibboleth."
      severity: MEDIUM
```
