```yaml
prompt_preflight:
  status: ISSUES_FOUND
  issues:
    - type: CONTRADICTION
      location: "Section 4: 'REQUIRED H2 Sections and Points' vs 'Output Format'"
      problem: "The outline explicitly requires the H2 heading '## Підсумок — Summary' and warns 'missing/renamed sections fail validation'. However, earlier instructions say 'MUST end with a # Summary section' and the Output Format block dictates an H1 '# Summary'. This will cause a missing section validation failure or duplicate summaries."
      suggested_fix: "Consolidate to a single standard. Change the Output Format block to use '## Підсумок — Summary' to match the required H2 outline."
      severity: HIGH
    - type: CONTRADICTION
      location: "Section 5: 'Item Minimums (HARD FAIL if under)' vs 'Activity Schemas'"
      problem: "The Item Minimums table states 'watch-and-repeat' requires '≥1 items' and 'image-to-letter' requires '≥5 items'. But their corresponding YAML schema examples contain the comment 'items:  # minItems: 6', creating a direct conflict that could cause a JSON schema failure."
      suggested_fix: "Update the comments in the YAML schema examples to match the Item Minimums table (e.g., change to '# minItems: 1' and '# minItems: 5')."
      severity: HIGH
    - type: UNCLEAR
      location: "Section 4: Pronunciation Videos"
      problem: "The instructions state 'Each letter below MUST get its video embedded in the corresponding H3 section'. However, the required outline only specifies H2 headings and heavily enforces 'EXACT H2 titles from the outline below'. It is ambiguous whether the text generator is allowed to create its own H3 headings."
      suggested_fix: "Explicitly instruct the generator to create H3 sub-headings for each letter within the '## Перші 10 літер — First 10 Letters' section, or instruct it to embed the videos directly in the H2 text."
      severity: MEDIUM
```
