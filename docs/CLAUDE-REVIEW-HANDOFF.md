# A1 Curriculum & Codebase Review - Handoff Document for Gemini

**Reviewed By:** Claude  
**Date:** 2025-12-11  
**Purpose:** Comprehensive assessment of A1 curriculum and supporting codebase

---

## 1. A1 Curriculum Assessment

### 1.1 Module Coverage

| Status | Count | Notes |
|--------|-------|-------|
| ✅ Complete | 30 | M01-M30 pass all core metrics |
| ❌ Missing | 4 | M31–M34 (Body/Health, Family, Holidays, Checkpoint) |
| **Total Required** | 34 | Per A1-CURRICULUM-PLAN.md |

### 1.2 Audit Results Summary

**All 30 modules pass core metrics:**

| Metric | Target | Result |
|--------|--------|--------|
| Word Count | 750+ | ✅ 858 avg (range: 750-1205) |
| Activities | 8+ | ✅ 8.2 avg (all pass) |
| Items/Activity | 12+ | ✅ All pass |
| Activity Types | 4+ unique | ✅ 5-6 types |
| Engagement Boxes | 3+ | ✅ All pass |
| Vocabulary | 20+ words | ✅ 20-36 words per module |

### 1.3 Lint Issues

| Modules | Issue | Fix Required |
|---------|-------|--------------|
| M01-M14 | Audio links `[🔊](audio_xxx)` in content body | Remove inline audio links; keep only in vocab table |
| M15-M30 | Clean | None |

**Total lint errors:** 106 (across 14 modules)

### 1.4 Linguistic Purity Check

| Pattern Searched | Occurrences | Status |
|------------------|-------------|--------|
| "Самий" (superlative) | 0 | ✅ Clean |
| "Приймати участь" | 0 | ✅ Clean |
| "Давай" | 1 | ⚠️ In cultural context only |
| "Вибачаюсь" | 0 | ✅ Uses correct "Вибачте" |
| "Слідуючий" | 0 | ✅ Clean |

**Overall:** GOOD - No systematic Russification detected.

### 1.5 State Standard Compliance

| Requirement | Status |
|-------------|--------|
| Phonetics (§4.1) | ✅ M01-M02 cover alphabet |
| Noun Gender (§4.2.1.1) | ✅ M03 teaches gender |
| Cases (Nom/Acc/Loc/Gen) | ✅ M11-M14 |
| Present Tense | ✅ M06 |
| Imperative | ✅ M15 |

---

## 2. Codebase Assessment

### 2.1 Architecture Overview

```
scripts/
├── audit_module.py       # 720 lines - Module richness auditor
├── generate.ts           # 618 lines - HTML/JSON generator
├── generate-exercises.ts # 727 lines - Activity generator
├── scope-validator.ts    # 549 lines - Grammar scope checker
├── validate-html.ts      # 363 lines - HTML output validator
├── enrich-activities.ts  # 720 lines - Activity enrichment
├── vocab-manager.py      # 310 lines - Vocabulary database
└── lib/
    ├── parsers/          # Modular activity parsers
    │   └── activities/   # base.ts, quiz.ts, fill-in.ts, etc.
    ├── renderers/        # HTML/JSON renderers
    ├── types.ts          # Type definitions
    └── utils/            # Helpers (markdown parsing, etc.)
```

### 2.2 Lint Status

```
✖ 235 problems (50 errors, 185 warnings)
```

**Key Issues:**

| File | Error Type | Count |
|------|------------|-------|
| `scope-validator.ts` | Unused variable | 1 |
| `vocab-init.ts` | Unused variables | 2 |
| `validate-html.ts` | Explicit `any` types | 6 |
| Various | Missing JSDoc | 185 |

**Fixable with `--fix`:** 162 issues

### 2.3 Code Quality Notes

**Strengths:**
- Clean modular architecture (parsers, renderers, utils)
- TypeScript with proper type definitions
- Well-documented activity parser base class
- Proper CLI handling with help flags

**Areas for Improvement:**
- Remove unused variables in `scope-validator.ts` and `vocab-init.ts`
- Add JSDoc comments to exported functions
- Replace `any` types with proper interfaces
- Consider extracting hardcoded patterns (translations words) to config

---

## 3. Recommended Actions (Priority Order)

### Priority 1: Critical

1. **Create missing modules M31-M34**
   - M31: Body & Health (State Standard §3.10)
   - M32: Family Extended (§3.1)
   - M33: Holidays & Traditions (§3.12)
   - M34: Final Checkpoint

### Priority 2: High

2. **Fix audio lint errors in M01-M14**
   - Remove inline `[🔊](audio_xxx)` links from content body
   - Keep audio links only in vocabulary table

3. **Fix TypeScript lint errors**
   ```bash
   npm run lint -- --fix
   ```

### Priority 3: Medium

4. **Standardize M28 vocabulary table**
   - Current: `Ukrainian | Pronunciation | English | Audio`
   - Expected: `Word | IPA | English | POS | Gender | Note | Audio`

5. **Clean up unused variables**
   - `scope-validator.ts:46` - `TRANSLITERATION_PATTERN`
   - `vocab-init.ts:112` - `LEVEL_RANGES`
   - `vocab-init.ts:167` - `insertLevel`

---

## 4. Files Reference

### Curriculum Files
- `curriculum/l2-uk-en/a1/module-01.md` through `module-30.md`
- Missing: `module-31.md` through `module-34.md`

### Key Documentation
- `docs/l2-uk-en/A1-CURRICULUM-PLAN.md` - 34-module plan
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
- `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md` - Anti-Surzhyk rules

### Key Scripts
- `scripts/audit_module.py` - Run module audits
- `scripts/generate-mdx.ts` - Generate MDX for Docusaurus
- `scripts/generate_json.py` - Generate JSON for Vibe app
- `scripts/scope-validator.ts` - Check grammar scope

---

## 5. Quick Commands

```bash
# Audit a single module
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/module-01.md

# Generate HTML for a module
npm run generate l2-uk-en a1 1

# Run linter with auto-fix
npm run lint -- --fix

# Validate scope
npx ts-node scripts/scope-validator.ts 1
```

---

**End of Handoff Document**
