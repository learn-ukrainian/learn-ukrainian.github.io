```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 4 (Dialogue Quality) vs Section 6 (Self-Audit)"
      problem: "Section 4 instructs to 'Include 4-6 substantial dialogues per module', but the Section 6 Self-Audit Checklist states 'Max 2-3 dialogues total'."
      suggested_fix: "Align the required number of dialogues in both sections so they do not contradict each other."
      severity: HIGH
    - type: MISSING_INSTRUCTION
      location: "Writing Style vs Scoring Dimensions (Emotional Safety)"
      problem: "The Audit Gates will score based on 'Emotional Safety — ≥15 direct address, encouragement, quick wins', but the prompt does not explicitly instruct the writer to hit this numeric target of 15+ instances."
      suggested_fix: "Add a clear instruction in the Writing Style or Targets section mandating at least 15 instances of direct address and encouragement."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section 5 (Create Activities) vs Audit Gates"
      problem: "Section 5 specifies 'Required types: fill-in, fill-in, quiz, match-up, fill-in', which only amounts to 3 distinct activity types. The Audit Gates, however, require 'Min activity types: 4'."
      suggested_fix: "Update the required activity types list in Section 5 to include at least 4 distinct types (e.g., adding 'true-false' or 'group-sort')."
      severity: HIGH
```
