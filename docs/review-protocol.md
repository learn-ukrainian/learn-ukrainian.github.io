# Universal Review Protocol

## Evidence requirement — NON-NEGOTIABLE

Every finding you return MUST include:
1. **Exact `file:line` reference** — quote the literal line number from the file on the branch you reviewed.
2. **Verbatim quote** of the current code/text, copy-pasted exactly as it appears.
3. **The correction** with a one-paragraph justification of why the current code/text is wrong.
4. **Source citation if available**.

Findings without all four elements will be DISCARDED by the verifier.
If you are not certain the text you are quoting is verbatim from the file, DO NOT include it.
Mark each finding `SEVERITY: {blocker | major | minor | nit}`.

## Hallucination Guards

1. **DIFF vs FILE distinction**: lines outside the diff still exist on the branch. A reviewer claiming something is "missing" must prove absence in the FILE, not just in the DIFF.
2. **Mandatory FINDING format**: every finding must use the schema below.
3. **"Missing" claims require proof of absence**: give a verbatim grep miss or quote the relevant file line. "I don't see it in the diff" is not evidence.
4. **No invented line numbers**: every `file:line` reference must resolve to a real line on the branch at review time.
5. **Self-check before submitting**: ask "could the code I think is missing actually exist at a line I haven't read?" If yes, read more before reporting it.

## Mandatory Per-Finding Schema

```text
FINDING:
FILE:LINE: <path>:<n>
CURRENT CODE (verbatim from branch):
```
<copy-paste from file>
```
WHY WRONG:
<one paragraph>
FIX:
<patch or instruction>
SEVERITY: {blocker | major | minor | nit}
SOURCE: <citation or "none">
```

Findings without all fields are DISCARDED by `scripts/verify_review.py`.

## Universal Review Loop

1. Dispatch the reviewer with `--review` so this protocol is prepended before any channel or task-specific context.
2. The reviewer reads the actual files on the branch, not just the diff.
3. The reviewer returns only schema-complete `FINDING:` blocks with verbatim evidence.
4. Run `.venv/bin/python scripts/verify_review.py --from-stdin` on pasted output, or `.venv/bin/python scripts/verify_review.py --issue <N>` to verify the latest issue comment.
5. Read the JSONL outcomes:
   - `verified`: quote exists at the claimed line
   - `line_mismatch`: quote exists, but not at the claimed line
   - `quote_missing`: quoted code/text is not present on the branch
   - `discarded`: malformed finding with missing required fields
6. Decide the next step:
   - If findings are `verified`, address or rebut them normally.
   - If findings are `line_mismatch`, treat them as weak evidence and re-check the file before acting.
   - If findings are `quote_missing` or `discarded`, reject those findings; do not auto-retry in a loop.
