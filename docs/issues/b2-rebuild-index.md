# B2 Rebuild - Navigation Index

**Status:** 🚨 In Progress - 1.4% pass rate (2/145 modules)
**Last Updated:** 2026-01-10
**Estimated Completion:** 2-3 working days

---

## Quick Links

### Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| **[Quick Summary](./b2-audit-quick-summary.md)** | 1-page overview, top errors | ✅ Complete |
| **[Detailed Analysis](./b2-rebuild-audit-summary.md)** | Full error breakdown, comparisons | ✅ Complete |
| **[Fix Scripts](./b2-fix-scripts-needed.md)** | Implementation guide, code | ✅ Complete |
| **[Full Audit Report](./b2-rebuild-audit-report.md)** | Raw audit logs (643KB) | ✅ Complete |
| **This Index** | Navigation & progress tracker | ✅ Complete |

### Templates & References

| Resource | Purpose |
|----------|---------|
| [B2 Module Template](../../l2-uk-en/templates/b2-module-template.md) | Standard module structure |
| [B2 History Template](../../l2-uk-en/templates/history-module-template.md) | History module requirements |
| [Module Richness Guidelines](../../l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md) | Quality standards |
| [M102 (Passing)](../../../curriculum/l2-uk-en/b2/102-franko-lesia-hrinchenko.md) | Reference example |
| [M105 (Passing)](../../../curriculum/l2-uk-en/b2/105-unr-zunr.md) | Reference example |

---

## Audit Results Summary

### Overall Statistics

| Metric | Value | Details |
|--------|-------|---------|
| **Total Modules** | 145 | M01-M145 |
| **Passed** | 2 (1.4%) | M102, M105 |
| **Failed** | 143 (98.6%) | See breakdown below |
| **Total Violations** | 4,603 | Across all categories |

### Error Breakdown

| Error Category | Count | % of Total | Severity | Phase |
|----------------|-------|------------|----------|-------|
| `COMPLEXITY_WORD_COUNT` | 3,030 | 65.8% | ⚠️ Moderate | Phase 3 |
| `YAML_SCHEMA_VIOLATION` | 734 | 15.9% | 🔴 Critical | Phase 1 |
| `MISSING_REQUIRED_SECTION` | 663 | 14.4% | 🔴 Critical | Phase 1-2 |
| `DUPLICATE_SYNONYMOUS_HEADERS` | 88 | 1.9% | 🔴 Critical | Phase 1 |
| `MISSING_REQUIRED_CALLOUT` | 47 | 1.0% | ⚠️ Moderate | Phase 2 |
| `TOO_MANY_MORPHEMES` | 39 | 0.8% | ⚠️ Moderate | Phase 4 |
| `EMPTY_REQUIRED_SECTION` | 2 | 0.04% | 🔴 Critical | Phase 1 |

---

## Fix Progress Tracker

### Phase 1: Automated Structural Fixes (2-3 hours)

**Target:** Fix 752 violations (16.3%)

| Task | Script | Impact | Status | Notes |
|------|--------|--------|--------|-------|
| Add "Need More Practice?" | `fix_b2_missing_need_more.py` | 277 modules | ⏳ Pending | All modules M01-M145 |
| Normalize duplicate headers | `fix_b2_duplicate_headers.py` | 88 modules | ⏳ Pending | History + Grammar modules |
| Fix YAML schema | `fix_b2_yaml_schema.py` | 734 violations | ⏳ Pending | All activity YAML files |
| Add grammar sections | `fix_b2_missing_grammar_sections.py` | 190 modules | ⏳ Pending | Grammar modules M01-M51 |

**Completion:** 0/4 tasks ⬜⬜⬜⬜

---

### Phase 2: History Section Completion (4-6 hours)

**Target:** Fix 207 violations + improve 61 modules

| Task | Script | Impact | Status | Notes |
|------|--------|--------|--------|-------|
| Add Читання sections | `fix_history_reading.py` | 80 modules | ⏳ Pending | M71-M131 history modules |
| Add Первинні джерела | `fix_history_callouts.py` | 32 modules | ⏳ Pending | History modules |
| Add Деколонізаційний погляд | `fix_history_callouts.py` | 8 modules | ⏳ Pending | History modules |
| Add [!myth-buster] callouts | `fix_history_callouts.py` | 47 modules | ⏳ Pending | History modules |
| Populate TODO markers | Manual + LLM | 120 sections | ⏳ Pending | Content creation |

**Completion:** 0/5 tasks ⬜⬜⬜⬜⬜

---

### Phase 3: Complexity Enrichment (8-12 hours)

**Target:** Fix 3,030 violations (65.8%)

| Task | Script | Impact | Status | Notes |
|------|--------|--------|--------|-------|
| Identify short quiz prompts | `fix_b2_quiz_complexity.py` | ~1,500 items | ⏳ Pending | Analysis script |
| Enrich quiz prompts | LLM-assisted | ~1,500 items | ⏳ Pending | 10-25 word target |
| Identify short unjumble | `fix_b2_unjumble_complexity.py` | ~800 items | ⏳ Pending | Analysis script |
| Expand unjumble sentences | LLM-assisted | ~800 items | ⏳ Pending | 10-18 word target |
| Identify short fill-in | `fix_b2_fillin_complexity.py` | ~500 items | ⏳ Pending | Analysis script |
| Extend fill-in contexts | LLM-assisted | ~500 items | ⏳ Pending | 12-20 word target |
| Review 30% sample | Manual | ~900 items | ⏳ Pending | Quality check |

**Completion:** 0/7 tasks ⬜⬜⬜⬜⬜⬜⬜

---

### Phase 4: Manual Review & Validation (2-3 hours)

**Target:** Quality assurance

| Task | Scope | Status | Notes |
|------|-------|--------|-------|
| Review TOO_MANY_MORPHEMES | 39 violations | ⏳ Pending | Accept/reject each |
| Validate history callouts | 47 modules | ⏳ Pending | Factual accuracy |
| Re-run comprehensive audit | All 145 modules | ⏳ Pending | Target 95%+ pass rate |
| Fix remaining edge cases | <10 modules | ⏳ Pending | Manual fixes |
| Update documentation | 5 docs | ⏳ Pending | This index + summaries |

**Completion:** 0/5 tasks ⬜⬜⬜⬜⬜

---

## Module Health by Range

| Range | Modules | Pass Rate | Primary Issues | Priority |
|-------|---------|-----------|----------------|----------|
| M01-M10 | 10 | 0% | Missing grammar sections, short sentences | High |
| M11-M20 | 10 | 0% | Missing sections, YAML schema | High |
| M21-M30 | 10 | 0% | Missing sections, short sentences | High |
| M31-M40 | 10 | 0% | Missing sections, YAML schema | High |
| M41-M50 | 10 | 0% | Missing sections, short sentences | High |
| M51-M70 | 20 | 0% | Missing sections, YAML, complexity | High |
| M71-M90 | 20 | 0% | Missing history sections, duplicate headers | Critical |
| M91-M110 | 20 | 10% | Missing history sections (M102, M105 pass) | Medium |
| M111-M131 | 21 | 0% | Missing history sections, duplicate headers | Critical |
| M132-M145 | 14 | 0% | Incomplete scaffolding | High |

**Focus areas:**
- **M71-M131 (History):** Most complex fixes - missing Читання, Первинні джерела, callouts
- **M01-M70 (Grammar/Vocab):** Mostly automated fixes + complexity enrichment
- **M132-M145 (Skills):** Incomplete - may need module creation

---

## Passing Modules (Reference Examples)

### ✅ M102: Franko, Lesia Ukrainka, Hrinchenko

**Why it passes:**
- All required sections present (Вступ, Читання, Словник, Граматика, Первинні джерела, Деколонізаційний погляд, Need More Practice)
- YAML activities validate against current schema
- Sentence complexity meets B2 targets (10-25 words)
- No duplicate headers
- Required callouts present (`[!myth-buster]`, `[!history-bite]`)

**File:** `curriculum/l2-uk-en/b2/102-franko-lesia-hrinchenko.md`

**Use for:**
- Biography module structure reference
- History callout examples
- B2 complexity benchmarks

---

### ✅ M105: UNR and ZUNR

**Why it passes:**
- Full compliance with `history-module-template.md`
- All history-specific sections complete
- Clean YAML schema
- Enriched activities (no complexity violations)
- Proper header naming (no duplicates)

**File:** `curriculum/l2-uk-en/b2/105-unr-zunr.md`

**Use for:**
- History module template adherence
- Primary source integration examples
- Decolonization perspective modeling

---

## Timeline & Milestones

### Week 1 (Estimated 14-21 hours)

| Day | Phases | Hours | Milestones |
|-----|--------|-------|------------|
| Monday | Phase 1 | 2-3 | All automated structural fixes complete |
| Tuesday | Phase 2 (start) | 2-3 | History sections scaffolded |
| Wednesday | Phase 2 (cont) | 2-3 | Читання sections populated |
| Thursday | Phase 3 (start) | 4-6 | Quiz prompts enriched |
| Friday | Phase 3 (cont) | 4-6 | Unjumble & fill-in enriched |

### Week 2 (Estimated 2-3 hours)

| Day | Phases | Hours | Milestones |
|-----|--------|-------|------------|
| Monday | Phase 4 | 2-3 | Manual reviews complete, final audit |
| Tuesday | Cleanup | 1-2 | Edge cases fixed, docs updated |

**Total estimated time:** 16-24 hours over 2 weeks

---

## Success Criteria

### Quantitative Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| **Pass rate** | 1.4% (2/145) | 95%+ (138/145) | Audit pass/fail |
| **COMPLEXITY violations** | 3,030 | <100 | Word count audits |
| **YAML violations** | 734 | 0 | Schema validation |
| **Missing sections** | 663 | 0 | Template compliance |
| **Duplicate headers** | 88 | 0 | Header normalization |
| **Missing callouts** | 47 | 0 | History template |

### Qualitative Criteria

- ✅ All history modules (M71-M131) have complete Читання sections
- ✅ All history modules have Ukrainian-perspective primary sources
- ✅ All modules have "Need More Practice?" resource sections
- ✅ All YAML activities render correctly in Docusaurus
- ✅ All B2 sentences meet complexity targets (10-25 words)
- ✅ No remaining template violations

---

## Next Steps

1. **Read documentation:**
   - ✅ Quick Summary (you are here)
   - ⏳ Detailed Analysis
   - ⏳ Fix Scripts Guide

2. **Start Phase 1:**
   - ⏳ Review `fix_b2_missing_need_more.py`
   - ⏳ Run automated fixes
   - ⏳ Verify with re-audit

3. **Track progress:**
   - ⏳ Update this index after each phase
   - ⏳ Document blockers or deviations
   - ⏳ Commit changes incrementally

---

## Known Issues & Blockers

*No blockers identified yet. Update this section as work progresses.*

---

## Questions & Clarifications

*Document any questions or decisions needed during the rebuild process.*

---

## Comparison with B1 Rebuild

| Aspect | B1 | B2 | Notes |
|--------|----|----|-------|
| Total modules | 91 | 145 | B2 is 59% larger |
| Initial pass rate | 8.8% | 1.4% | B2 worse condition |
| Total violations | ~2,800 | 4,603 | +64% more errors |
| Complexity violations | ~1,200 | 3,030 | +153% - biggest issue |
| Estimated fix time | 12-18h | 16-24h | +33% more effort |
| History modules | 0 | 61 | Unique to B2 |

**Key differences:**
- **B2 has dedicated history track** (M71-M131) requiring specialized sections
- **B2 complexity targets higher** (10-25 words vs 8-20 for B1)
- **B2 worse initial condition** (1.4% vs 8.8% pass rate)
- **B2 has more template violations** due to history-specific requirements

---

## Related Projects

- **B1 Rebuild:** `docs/issues/b1-rebuild-index.md` (completed 2026-01-09)
- **A2 Rebuild:** Completed 2025-12
- **A1 Rebuild:** Completed 2025-12

**Lessons learned from B1:**
- Automated fixes save 80% of time
- LLM-assisted enrichment works well with manual review
- Template compliance critical for passing audits
- History content requires manual expertise

---

## Glossary

| Term | Definition |
|------|------------|
| **Читання** | Reading section (history modules) |
| **Первинні джерела** | Primary sources (history modules) |
| **Деколонізаційний погляд** | Decolonization perspective (history modules) |
| **[!myth-buster]** | Callout debunking imperial myths |
| **[!history-bite]** | Callout with historical trivia |
| **COMPLEXITY_WORD_COUNT** | Sentence word count below target |
| **YAML_SCHEMA_VIOLATION** | Invalid YAML activity structure |

---

**Status Legend:**
- ✅ Complete
- ⏳ Pending / In Progress
- ❌ Blocked
- ⚠️ Needs Attention

**Last Updated:** 2026-01-10 by Claude Code

---

## Appendix: Full Module Status

See detailed violation breakdown in **[Module Status Table](./b2-module-status-table.md)**

**Quick stats by severity:**
- **High severity (20+ violations):** 90 modules
- **Medium severity (10-19 violations):** 43 modules  
- **Low severity (<10 violations):** 10 modules
- **Passing (0 violations):** 2 modules (M102, M105)

**Module ranges by health:**
- **Critical (30+ violations):** M30, M40, M132-135, M141-145
- **Needs work (20-29 violations):** Most grammar/register modules (M01-M70)
- **Nearly passing (<10 violations):** M101, M103, M107, M110, M83 (biography/synthesis modules)
