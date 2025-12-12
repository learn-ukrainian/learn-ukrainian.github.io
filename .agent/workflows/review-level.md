---
description: Review a completed curriculum level using SKILL.md standards
---

# Review Level Workflow

// turbo-all

## Prerequisites

1. Ensure all modules in the level pass automated audit:
   ```bash
   python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/module-*.md 2>&1 | grep -c "PASSED"
   ```

2. Run any auto-fix scripts if needed:
   ```bash
   python3 scripts/fix_anagrams.py curriculum/l2-uk-en/{level}/module-*.md
   python3 scripts/fix_unjumble.py curriculum/l2-uk-en/{level}/module-*.md
   ```

## Review Steps

3. Read the reference documents:
   - `claude_extensions/skills/module-architect/SKILL.md`
   - `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
   - `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
   - `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md`

4. For each module, verify:
   - **Audit:** Run `python3 scripts/audit_module.py {file}` passes
   - **Grammar:** No Surzhyk, correct Ukrainian
   - **Vocabulary:** Matches curriculum plan
   - **Soul:** Specific Ukrainian settings, emotional stakes
   - **Decolonization:** Myth Buster / History Bite boxes present
   - **Activities:** Progression from recognition → production

5. Create summary table:
   ```markdown
   | Module | Audit | Grammar | Vocab | Soul | Decol | Issues |
   |--------|-------|---------|-------|------|-------|--------|
   | M01    | ✅    | ✅      | ✅    | ✅   | ✅    | None   |
   ```

6. Fix any issues found and re-run audit.

7. Regenerate MDX output:
   ```bash
   npm run generate l2-uk-en {level}
   ```

## Output

Save review results to:
```
curriculum/l2-uk-en/{level}/gemini/{LEVEL}-REVIEW-SUMMARY.md
```
