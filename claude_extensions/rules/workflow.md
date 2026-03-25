# How We Work (Mandatory Workflow)

<critical>

Every task follows this workflow. No exceptions for non-trivial changes.

1. **Create GH issue** — describe the problem, draft a plan
2. **Adversarial review of plan** — send to Gemini, incorporate feedback
3. **Finalize ACs** — update issue with concrete acceptance criteria
4. **Implement** — work through ACs one by one
5. **Verify all ACs** — every AC checked and documented on the issue
6. **Adversarial review of implementation** — send code to Gemini, fix findings
7. **Close** — only when all ACs pass and review is clean

**Skip plan review** (step 2) only for trivial changes (< 50 lines, config/typo fixes).

**Adversarial review command** (steps 2 & 6). Always use `--model gemini-3.1-pro-preview`. Document findings on the GH issue.
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN --model gemini-3.1-pro-preview
```

**Why**: GH issues are persistent memory. Without them, context is lost between sessions and work gets repeated or silently broken.

**Issue discipline (coding issues)**:
- **Never leave half-done.** If you open it, finish it. If you can't finish it now, document exactly where you stopped and what remains.
- **Never close unless ALL acceptance criteria are verified.** Partial completion = still open.
- **Aim to fully resolve and close.** Open issues are debt. Minimize them aggressively.
- **The human manages content generation issues.** Claude owns coding/infrastructure issues. But proactively remind when it's time to start building a new track or batch — initiative is welcome.

**Proactive issue hygiene**: At the start of each session, check open coding issues. Prioritize, resolve, close — don't let them go stale.

</critical>
