# Level Review Workflow

> **Purpose:** Standard process for AI-assisted quality review of completed curriculum levels.

---

## Pre-Review Checklist

Before starting review, ensure:
- [ ] All modules in level pass automated audit
- [ ] Any auto-fix scripts have been run (fix_anagrams.py, fix_unjumble.py)
- [ ] Human native speaker review completed (if available)

---

## Review Prompt Template

Copy and paste this to the reviewing AI agent:

```
Read these docs first:
- `claude_extensions/skills/module-architect/SKILL.md`
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md`

Review ALL modules in curriculum/l2-uk-en/{level}/ (module-01.md through module-XX.md).

For each module:
1. Run: `python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/module-{XX}.md`
2. Verify Ukrainian grammar (no Surzhyk - check LINGUISTIC-PURITY-GUIDE.md)
3. Verify vocabulary matches {LEVEL}-CURRICULUM-PLAN.md
4. Verify "Soul" standard (specific Ukrainian settings, emotional stakes)
5. Verify decolonization (Myth Buster / History Bite boxes)
6. Verify activity progression (recognition → production)

Output a summary table:
| Module | Audit | Grammar | Vocab | Soul | Decol | Issues |
|--------|-------|---------|-------|------|-------|--------|

At the end, list any modules needing fixes with specific corrections.
```

---

## A1 Specific Prompt

```
Read these docs first:
- `claude_extensions/skills/module-architect/SKILL.md`
- `docs/l2-uk-en/A1-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md`

Review ALL 34 A1 modules (curriculum/l2-uk-en/a1/module-01.md through module-34.md).

For each module:
1. Run: `python3 scripts/audit_module.py curriculum/l2-uk-en/a1/module-{XX}.md`
2. Verify Ukrainian grammar (no Surzhyk)
3. Verify vocabulary matches A1-CURRICULUM-PLAN.md
4. Verify "Soul" standard (specific Ukrainian settings, emotional stakes)
5. Verify decolonization (Myth Buster / History Bite boxes)
6. Verify activity progression (recognition → production)

Output a summary table:
| Module | Audit | Grammar | Vocab | Soul | Decol | Issues |
|--------|-------|---------|-------|------|-------|--------|

At the end, list any modules needing fixes with specific corrections.
```

---

## Post-Review Actions

1. Fix any issues identified in the review
2. Re-run audit on fixed modules
3. Update level status in project documentation
4. Regenerate MDX output: `npm run generate l2-uk-en {level}`
