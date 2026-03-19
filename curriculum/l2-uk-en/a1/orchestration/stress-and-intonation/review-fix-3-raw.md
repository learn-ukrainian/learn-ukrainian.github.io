All 4 inline fixes from Phase D.1 have already been applied to the files:

1. ✅ **відпо́відь → ві́дповідь** — already fixed (line 75)
2. ✅ **[!did-you-know] box** — already added (line 13, castle cultural hook)
3. ✅ **[!tip] box** — already added (line 86, yes/no question intonation)
4. ✅ **"You can now..." celebration** — already present (line 133)

**Regarding the remaining audit failure `❌ шко`**: This is a **tool bug, not a content bug**. The VESUM word verification script is splitting `шко́ла` at the combining acute accent (U+0301) and extracting `шко` as a standalone token. There is no standalone `шко` anywhere in the file — every occurrence is part of `шко́ла` with a stress mark. The fix belongs in the audit script's tokenizer, not in the content.

No content edits are needed — all issues from the fix plan have already been resolved by the inline fixes.

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: Full Phase D.2
**Friction Type**: NONE
**Raw Error**: None — all 4 inline fixes from D.1 were already applied. The remaining audit failure (❌ `шко`) is a false positive from the VESUM word verification script splitting stress-marked `шко́ла` at the combining acute accent (U+0301) into `шко` + `ла`.
**Self-Correction**: N/A — no edits needed
**Proposed Tooling Fix**: The VESUM prose word extractor should strip combining diacritical marks (U+0300–U+036F) BEFORE tokenizing words, not after. This would prevent `шко́ла` from being split into `шко` and `ла`. The fix likely belongs in the regex or tokenizer in `scripts/audit/` that extracts Ukrainian words from prose for VESUM verification.
===FRICTION_END===
```