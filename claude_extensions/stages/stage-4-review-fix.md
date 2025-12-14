# Stage 4: Review & Fix Loop

Review the module, fix violations, repeat until PASS.

## Input

- **Module file**: Complete module from Stages 1-3
- **Level**: Determines constraints and expectations

## Process

```
┌─────────────────────────────────────────────────┐
│                 REVIEW MODULE                   │
│         Run audit, check all constraints        │
└─────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    VIOLATIONS?        │
            └───────────────────────┘
                   │         │
                   │ NO      │ YES
                   ▼         ▼
        ┌─────────────┐   ┌─────────────────────────┐
        │   PASS!     │   │  COUNT VIOLATIONS       │
        │ Output JSON │   │  ≤3 = FIX               │
        │ & MDX       │   │  >3 = REBUILD SECTION   │
        └─────────────┘   └─────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────────┐
                          │   APPLY FIX or      │
                          │   REBUILD SECTION   │
                          └─────────────────────┘
                                    │
                                    ▼
                              (loop back to REVIEW)
```

## Review Checklist

### 1. Structural Audit
- [ ] Frontmatter complete (module, title, pedagogy, objectives)
- [ ] All required sections present
- [ ] Vocabulary table at end

### 2. Grammar Constraints
- [ ] Only uses grammar allowed at this level
- [ ] See `{LEVEL}-CURRICULUM-PLAN.md` Каталог В

### 3. Vocabulary Constraints
- [ ] Vocabulary table present with required columns
- [ ] IPA present for all vocabulary (A1-B1)
- [ ] Uses vocabulary from curriculum plan
- **Note:** Cross-module vocab validation deferred to `npm run vocab:rebuild`

### 4. Activity Constraints
- [ ] Count meets minimum (8-16+ by level)
- [ ] Items per activity meets minimum (12-18+ by level)
- [ ] Type variety (4-5+ types)
- [ ] Correct syntax (fill-in `___`, unjumble ` / `, etc.)
- [ ] All answers correct

### 5. Richness Constraints
- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum
- [ ] Mini-dialogues present

### 6. Linguistic Purity
- [ ] No Surzhyk (see LINGUISTIC-PURITY-GUIDE.md)
- [ ] No AI contamination ("wait", "actually", "let me")
- [ ] Correct Ukrainian spelling and grammar

## Fix Strategy

### Minor Violations (≤3 issues)
Apply targeted fixes:
- Missing vocabulary → Add to table
- Wrong syntax → Correct the specific line
- Missing engagement box → Add one
- Spelling error → Fix it

### Major Violations (>3 issues in same section)
Rebuild the section:
- Content section failing → Rewrite entire section
- Multiple activity failures → Delete all activities, recreate
- Grammar violations throughout → Rewrite affected paragraphs

### Catastrophic (>10 violations OR structural issues)
Rebuild from Stage 1:
- Frontmatter wrong → Start over
- Wrong pedagogy structure → Start over
- Vocabulary fundamentally wrong → Start over

## Running the Audit

```bash
python3 scripts/audit_module.py {file_path}
```

Audit output categories:
- **FAIL**: Must fix (grammar, vocabulary, syntax)
- **WARN**: Should fix (richness, variety)
- **INFO**: Optional improvement

## Iteration Limit

Maximum 3 fix iterations per stage. If still failing after 3:
1. Report the persistent issues
2. Ask user for guidance
3. Consider rebuilding from earlier stage

## Output on PASS

When all checks pass:

```bash
# Generate final output
npm run generate l2-uk-en {level} {module_num}
npm run generate:json l2-uk-en {level} {module_num}

# Run final audit
python3 scripts/audit_module.py {file_path}
```

Report:
- Final audit score
- MDX file location
- JSON file location
- "MODULE APPROVED"
