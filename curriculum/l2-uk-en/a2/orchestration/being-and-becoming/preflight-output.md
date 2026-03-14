```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 5 (Create Activities) vs Audit Gates"
      problem: "The prompt specifies 'Required types: fill-in, fill-in, quiz, match-up, fill-in' which only contains 3 distinct types. The Audit Gate explicitly requires 'Min activity types: 4'."
      suggested_fix: "Update the required types list in Section 5 to include at least 4 unique activity types (e.g., add true-false or group-sort)."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section 4 (Dialogue Quality) vs Section 6 (Content Checks)"
      problem: "Section 4 instructs the model to 'Include 4-6 substantial dialogues per module'. The checklist in Section 6 explicitly contradicts this by requiring 'Max 2-3 dialogues total'."
      suggested_fix: "Align the dialogue counts. Either change Section 4 to request 2-3 dialogues or update the Section 6 checklist to allow 4-6 dialogues."
      severity: HIGH
```
