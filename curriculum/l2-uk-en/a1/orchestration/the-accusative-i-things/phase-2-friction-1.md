**Phase**: Beginner Content
**Step**: Self-Audit Fix Loop
**Friction Type**: Pedagogy Validation Over-sensitivity
**Raw Error**: "Dative case used at A1: 'чолові'"
**Self-Correction**: The audit script tokenized the word "чолові́чий" by splitting on the combining acute accent into non-word boundaries, creating fragments like "чолові" that falsely triggered the Dative Case check. Avoided the word entirely, falling back to English explanations of gender for the Ukrainian blocks.
**Proposed Tooling Fix**: Update the grammar regex for word boundary `\b` checking to account for unicode combining acute accents (`\u0301`) or normalize strings by removing combining accents before matching pedagogical forbidden word lists.