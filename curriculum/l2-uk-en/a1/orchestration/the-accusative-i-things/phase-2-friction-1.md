**Phase**: Beginner Content
**Step**: Self-Audit Fix Loop
**Friction Type**: false_positive
**Raw Error**: [GRAMMAR] Dative case used at A1: 'базові'
**Self-Correction**: Changed 'базові слова' (Accusative plural identical to Nominative) to 'ці слова' to avoid the grammar rule regex matching basic adjective endings. Changed imperative 'Зверніть увагу' to English instructions. Fixed compound sentences to simple sentences.
**Proposed Tooling Fix**: Improve regex for dative case to not trigger on nominative/accusative plural adjective endings like 'базові'.