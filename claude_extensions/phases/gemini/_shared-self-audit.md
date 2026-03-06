## Self-Audit (Run BEFORE Final Output)

After writing all content, you MUST run the audit and fix any issues — all within this session.

### Step 1: Write Content to Disk

Write your complete content to `{CONTENT_PATH}` using write_file or bash:

```bash
cat > {CONTENT_PATH} << 'CONTENT_EOF'
... your content here ...
CONTENT_EOF
```

### Step 2: Run Audit

```bash
bash scripts/audit_module.sh {CONTENT_PATH} --skip-activities --no-rag-verify
```

This checks: word count, Russianisms, engagement callouts, euphony, structure, immersion %.

### Step 3: Parse Results

- If you see `AUDIT PASSED` — proceed to output.
- If you see `AUDIT FAILED` — read the violations, fix content in-place, and re-run the audit.

### Step 4: Fix Loop (max 2 iterations)

If the audit fails:
1. Read the specific gate failures and violation details from the audit output
2. Edit `{CONTENT_PATH}` to fix each issue (add words if under target, remove Russianisms, add callout boxes, etc.)
3. Re-run: `bash scripts/audit_module.sh {CONTENT_PATH} --skip-activities --no-rag-verify`
4. If still failing after 2 fix attempts, proceed to output anyway — the validate phase will handle remaining issues.

### Step 5: Report Self-Audit Result

After audit (pass or fail), include this block in your output:

```
===SELF_AUDIT_START===
status: PASS | FAIL
iterations: {number of audit runs}
final_word_count: {word count from last audit}
gates_passed: {list of passed gates}
gates_failed: {list of failed gates, or "none"}
fixes_applied: {brief description of what you fixed, or "none"}
===SELF_AUDIT_END===
```

**IMPORTANT**: Do NOT skip the audit. Do NOT fabricate audit results. Run the actual command and report real output.
