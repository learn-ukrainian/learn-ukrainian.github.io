I've carefully compared the current file contents against every issue in the fix plan. Let me verify each one:

**All 8 inline fixes have already been applied.** Here's the verification:

1. **Activity 2 broken items** — ✅ Already fixed. The broken items ("Він сміє___", "Ти сміє___", "Вона вмиває___") are gone. Replacements ("Ти одягаєш___", "Ми сміємо___", "Вони займають___") are at lines 154, 162, 166 in the YAML.

2. **Colonial framing** — ✅ Already fixed. Line 85 reads: "This long, soft sound is a hallmark of authentic Ukrainian speech — it's one of the beautiful sounds that defines the melody of the language." No Russian comparison.

3. **Past tense forms** — ✅ Already added at lines 70-77 with сміявся, сміялася, сміялося, сміялися.

4. **Incomplete transitive sentences** — ✅ Line 156: "**Я мию тарілку.**", Line 162: "**Мама одягає дитину.**"

5. **Yoga persona** — ✅ Lines 180-194 have the yoga dialogue with займатися йогою, розминатися, розслаблятися.

6. **Engagement elements** — ✅ [!did-you-know] box at lines 176-178, YouTube embed at line 193.

7. **VOCAB_NOT_IN_CONTENT 'займатися'** — ✅ Present at line 182: "The verb **займатися**"

8. **ACTIVITY_UNDERCOUNT** — ✅ Activity 1: 25 items, Activity 2: 25 items, Activity 3: 15 items. All meet minimums.

9. **"Вона вчиться грати"** — ✅ Line 203: "**Вона вчиться грати на гітарі.**"

**VESUM failures** — These are all false positives (linguistic fragments being taught as suffixes/letters, plus the proper noun Хрещатик): `сь`, `ться`, `ш`, `ю`, `Хрещатик`. Not fixable content issues.

**No remaining fixes needed.** All documented issues have been resolved by the prior inline fixes.

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: Full Phase D.2
**Friction Type**: NONE
**Raw Error**: None — all 8 inline fixes from D.1 review were already applied correctly
**Self-Correction**: N/A
**Proposed Tooling Fix**: The VESUM audit flags linguistic fragments discussed in prose (сь, ться, ш, ю) as failures. These are false positives — the audit should either exclude content inside bold markers discussing suffixes/letters, or the pipeline should have a whitelist for commonly-discussed morphological fragments in grammar modules.
===FRICTION_END===
```