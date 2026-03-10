**Phase**: Full Build (Content + Activities + Vocabulary)
**Step**: Content writing and auditing for Immersion
**Friction Type**: IMMERSION_CALCULATION_MISMATCH
**Raw Error**: Audit returned IMMERSION TOO LOW (14.7%) despite significant Ukrainian text.
**Self-Correction**: Discovered that `clean_for_immersion` function strips markdown tables entirely (ignoring all Cyrillic inside them). Switched from tables to blockquote sequences and list clusters to reach the 30% threshold.
**Proposed Tooling Fix**: The `clean_for_immersion` regex in `scripts/audit/cleaners.py` aggressively removes tables (`^\s*\|.*$`). If tables are intended to contain instructional language or immersion data, this regex should be modified so that the Cyrillic text inside them is counted.