  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=33712 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Rule 1 (Grammar Allowlist) vs Section 6 (Hard Constraints)"
      problem: "Rule 1 explicitly states 'Any other structure (including conjugated verbs) is FORBIDDEN,' while Section 6 explicitly lists 'Simple present tense (я читаю, я бачу)' as ALLOWED. This will confuse the generator regarding the use of verbs."
      suggested_fix: "Clarify whether simple present tense verbs are allowed. If allowed, ensure common verbs like 'читати' or 'бачити' are added to the Vocabulary Bank or Cumulative list, as they are currently missing from both."
      severity: HIGH
    - type: PEDAGOGY
      location: "Outline section '## Чергування (Alternation)'"
      problem: "The point 'к → ц, г → з, х → с before the ending -і — рука → руці, нога → нозі' describes locative/dative singular forms, not plurals (plural of рука is руки, with no consonant alternation). In a module titled 'Plurals and Alternation,' presenting singular case changes as examples of alternation is pedagogically confusing and contradicts the Section 6 constraint 'Do not explicitly teach cases.'"
      suggested_fix: "Remove the preview of consonant alternation (к/г/х → ц/з/с) from this module, as it does not occur in plural formation for these nouns and introduces case grammar prematurely."
      severity: MEDIUM
