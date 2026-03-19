  [gemini] attempt 1/5, model=gemini-3-flash-preview, prompt=33615 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: PLAN_CONTRADICTION
      location: "Prompt Title/Subtitle vs. Outline Sections"
      problem: "The Title ('Genitive Prepositions') and Subtitle ('біля, без, від, для, до + Родовий') directly contradict the MANDATORY Outline. Sections 1 and 2 focus exclusively on the Locative Case (в/у, на + Місцевий), which are not Genitive prepositions. Furthermore, the prepositions 'без, від, для, до' listed in the title are entirely absent from the outline and required vocabulary."
      suggested_fix: "Update the Title to 'Location Prepositions' and align the subtitle with the actual outline (в/у, на, біля, навпроти). Alternatively, if Genitive prepositions like 'без, від, для, до' are required, add bullet points for them in the Genitive section."
      severity: MEDIUM
    - type: CONTRADICTION
      location: "Activity Rules section"
      problem: "The prompt lists 'cloze' as a 'Forbidden type' in the first list of activity types, but then states 'M11+ | ... cloze (needs 14+ blanks)' is allowed in the following table. For a Module 32, this is ambiguous."
      suggested_fix: "Remove 'cloze' from the forbidden list if it is allowed for M11+ with constraints, or clarify that it remains forbidden for this specific module."
      severity: LOW
```
