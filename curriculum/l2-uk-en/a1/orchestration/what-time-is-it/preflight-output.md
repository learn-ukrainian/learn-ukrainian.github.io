  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=1452 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
I will read the contents of the specified task file to understand what text generation is required.
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: IMPOSSIBLE_TARGET
      location: "Section 3 (Vocabulary) and Section 4 (Outline)"
      problem: "The outline mandates '20 vocab items' and Section 3 mentions a '20 vocabulary target'. However, only 15 vocabulary items are provided in total (8 required + 7 recommended). The LLM cannot reach the 20-word target without hallucinating/inventing words, which risks validation failures."
      suggested_fix: "Lower the vocabulary target in the outline to 15, or provide 5 additional recommended words in the prompt's context."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section 5 (Guidelines) - Activity Rules"
      problem: "The 'Audit Gates' specify 'Min activity types: 4', but the prompt's 'Required types' list only contains 3 unique types ('match-up, fill-in, quiz, fill-in'). If the LLM only uses these required types and repeats them to reach the 8-activity minimum, it will fail the 'Unique_types' audit gate."
      suggested_fix: "Add a 4th unique activity type to the 'Required types' list (e.g., add 'true-false' or 'group-sort') to guarantee the LLM generates at least 4 unique types."
      severity: HIGH
```
