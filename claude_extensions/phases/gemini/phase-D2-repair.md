# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have Read tool access.** Use it to read file content before writing FIND/REPLACE pairs.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)

{EXTRACTED_FIX_PLAN}

---

## Audit Failures (from automated re-audit)

```
{INJECTED_AUDIT_FAILURES}
```

---

## Files to Read

1. **Content**: `{CONTENT_PATH}`
2. **Activities**: `{ACTIVITIES_PATH}`
3. **Vocabulary**: `{VOCAB_PATH}`

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the Fix Plan OR in the audit failures:
   a. Find the exact text in the file you read
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: {CONTENT_PATH}
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: {ACTIVITIES_PATH}
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — copy from Read tool output exactly
- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- To ADD a new YAML item, FIND the last existing item in the list, REPLACE it with that same item followed by your new item. Preserve exact YAML indentation.
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
