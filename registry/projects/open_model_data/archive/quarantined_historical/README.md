# Quarantined Historical Datasets Archive

This directory stores historical dataset generations that have been quarantined per operator decision (Issue #8343, Parent Epic #6321):

- `uldr_v04a_kyivan_rus/`: Old East Slavic epigraphic graffiti and chronicle trajectories (#8103). Quarantined due to dating contradictions (15th–20th c. Latin graffiti mislabelled 11th–13th c.) and template monotony.
- `uldr_v04b_middle_ukrainian/`: Middle Ukrainian chancery and Cossack Baroque literature trajectories (#8105). Quarantined due to template monotony (20 reasoning patterns cover 99% of lines) and unvetted linguistic admixtures (Church Slavonic, Polish, Latin).

## Policy
- **DO NOT USE FOR MODEL TRAINING.**
- These datasets must not be included in unified ULDR packaging or training runs.
- Raw historical texts in `data/sources.db` remain untouched.
- Protective historical test cases remain active in the dialect/historical protection suite.
- Re-opening requires domain-expert historical linguist specification and validation.
