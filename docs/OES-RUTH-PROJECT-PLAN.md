# OES & RUTH Track Project Plan

**Created:** 2026-02-03
**Status:** In Progress
**Owner:** Claude + Gemini collaboration

## Overview

Two new historical language tracks for advanced learners:

| Track | Period | Focus | Modules |
|-------|--------|-------|---------|
| **OES** | X-XIII century | Old East Slavic (Давньоруська мова) | 100 |
| **RUTH** | XIV-XVIII century | Ruthenian (Руська мова / Prosta Mova) | 100 |

## Key Decisions

1. **100 modules per track** (not 30 as originally archived)
2. **Prose + vocabulary only** for initial test modules (no activities yet)
3. **Historical document literacy first**, deep linguistics later
4. **Seminar-style pedagogy** (like LIT track) - reading-analysis pairs
5. **Triple-column vocabulary**: OES/RUTH → Modern Ukrainian → English
6. **100% Ukrainian immersion** for explanations
7. **Primary source**: litopys.org.ua (excellent Ukrainian translations)

## Linguistic Model: Diglossia

Based on Shevelov, Nimchuk, Moisiyenko - we use the **Two-Register Model**:

| Register | Name | Description |
|----------|------|-------------|
| **High/Literary** | Книжна мова | Church Slavonic + East Slavic hybrid (chronicles) |
| **Vernacular** | Давньоукраїнська народно-розмовна мова | Actual spoken language (graffiti, birch bark) |

**Key insight:** Regional dialects were ALREADY distinct in 6th-9th centuries - NOT a later "split."

### Terminology
- **Use:** Давньоруська мова, Давньоукраїнська народно-розмовна мова, Книжна мова
- **Avoid:** "Old Russian" (imperialist), "Common East Slavic" (implies uniformity)

## Phase Structure

### OES Phases (Register-Based)
| Phase | Modules | Name | Register | Focus |
|-------|---------|------|----------|-------|
| OES.1 | 001-025 | **«Голос народу»** | Vernacular | Graffiti, Birch bark, Yers |
| OES.2 | 026-050 | **«Книжне слово»** | Literary | Повість врем'яних літ, Aorist |
| OES.3 | 051-075 | **«Право землі»** | Legal | Руська Правда, Dual Number |
| OES.4 | 076-100 | **«Висока поезія»** | Literary Art | Слово о полку, Phonology |

### RUTH Phases
| Phase | Modules | Focus |
|-------|---------|-------|
| RUTH.1 | 001-025 | Chancery: Lithuanian Statutes, Administrative |
| RUTH.2 | 026-050 | Sacred Word: Peresopnytsia Gospel, Vernacular |
| RUTH.3 | 051-075 | Baroque Fight: Smotrytsky, Vyshensky, Polemics |
| RUTH.4 | 076-100 | Cossack Word: Chronicles, Skovoroda |

## File Structure

```
curriculum/l2-uk-en/
├── plans/
│   ├── oes.yaml                 # Track curriculum [DONE]
│   ├── oes_mapping.yaml         # All 100 module slugs/titles [DONE]
│   ├── oes/                     # Individual module plans
│   │   ├── intro-to-oes.yaml    # [DONE]
│   │   ├── alphabet-*.yaml      # [DONE]
│   │   ├── graffiti-*.yaml      # [DONE - 3 files]
│   │   └── ... (95 more needed)
│   ├── ruth.yaml                # Track curriculum [DONE]
│   ├── ruth_mapping.yaml        # All 100 module slugs/titles [DONE]
│   └── ruth/                    # Individual module plans (0 done)
├── oes/
│   ├── meta/                    # Module metadata (0 done)
│   ├── status/                  # Audit cache
│   ├── vocabulary/              # Vocabulary files
│   └── audit/                   # Review logs
└── ruth/
    ├── meta/                    # (0 done)
    ├── status/
    ├── vocabulary/
    └── audit/

claude_extensions/skills/
├── oes-module-architect/SKILL.md  # [DONE]
└── ruth-module-architect/SKILL.md # [DONE]
```

## Task Tracking

### Completed Tasks
- [x] #1 Create directory structure
- [x] #2 Create OES module architect template
- [x] #3 Create RUTH module architect template
- [x] #4 Create OES track curriculum (plans/oes.yaml)
- [x] #5 Create RUTH track curriculum (plans/ruth.yaml)
- [x] #6 Define all 100 OES module slugs/titles (oes_mapping.yaml)
- [x] #7 Define all 100 RUTH module slugs/titles (ruth_mapping.yaml)
- [x] #8 Research deep: OES Phase 1 sources (+ 5 module plans created)

### Pending Tasks (Claude)
- [ ] #16 Generate remaining 95 OES module plan files (blocked by research)
- [ ] #17 Generate 100 RUTH module plan files (blocked by research)
- [ ] #18 Generate 100 OES meta files (blocked by #16)
- [ ] #19 Generate 100 RUTH meta files (blocked by #17)
- [ ] #20 Create OES quick-ref file
- [ ] #21 Create RUTH quick-ref file
- [ ] #22 Update C1-BIO modules with chronicle quotes

### Completed Tasks (Gemini) - GitHub Issues
- [x] #490 Research: OES Phase 2 (Chronicles) - `docs/issues/artifacts/ISSUE-490-research.md`
- [x] #491 Research: OES Phase 3 (Law & Land) - `docs/issues/artifacts/ISSUE-491-research.md`
- [x] #492 Research: OES Phase 4 (High Literature) - `docs/issues/artifacts/ISSUE-492-research.md`
- [x] #493 Research: RUTH Phase 1 (Chancery) - `docs/issues/artifacts/ISSUE-493-research.md`
- [x] #494 Research: RUTH Phase 2 (Sacred Word) - `docs/issues/artifacts/ISSUE-494-research.md`
- [x] #495 Research: RUTH Phase 3 (Baroque Fight) - `docs/issues/artifacts/ISSUE-495-research.md`
- [x] #496 Research: RUTH Phase 4 (Cossack Word) - `docs/issues/artifacts/ISSUE-496-research.md`

## Primary Sources

### OES Sources (litopys.org.ua)
| Source | URL | Use For |
|--------|-----|---------|
| Повість врем'яних літ | http://litopys.org.ua/pvlyar/yar.htm | Chronicles, verb tenses |
| Руська Правда | http://litopys.org.ua/rizne/pravdstat.htm | Legal vocabulary |
| Слово о полку Ігоревім | http://litopys.org.ua/slovo/slovo.htm | Poetry, phonology |
| Софійські графіті | Wikipedia/Izbornyk | Early vernacular |
| Берестяні грамоти | http://litopys.org.ua/oldukr/zven.htm | Colloquial OES |

### RUTH Sources
| Source | URL | Use For |
|--------|-----|---------|
| Lithuanian Statutes | chtyvo.org.ua | Legal/administrative |
| Smotrytsky's Grammar | http://litopys.org.ua/smotr/smotr.htm | Linguistic standardization |
| Ivan Vyshensky | http://litopys.org.ua/vyshen/vysh.htm | Polemical rhetoric |
| Cossack Chronicles | http://litopys.org.ua/ | Historical narrative |
| Skovoroda | http://litopys.org.ua/skovoroda/skov.htm | Philosophy |
| Peresopnytsia Gospel | NBUV Digital | Vernacular Scripture |

## Related Documentation

- Templates: `claude_extensions/skills/oes-module-architect/SKILL.md`
- Templates: `claude_extensions/skills/ruth-module-architect/SKILL.md`
- Archived plans: `docs/l2-uk-en/_archive/OES-CURRICULUM-PLAN.md`
- Archived plans: `docs/l2-uk-en/_archive/RUTH-CURRICULUM-PLAN.md`

## Technical Dependencies

### #498 - Context-Aware Character Validation
Historical quotes use characters that look "Russian" but are legitimate:
- `ъ` (hard sign) - valid in OES (сънъ → сон)
- `ѣ` (yat) - valid in OES (лѣсъ → ліс)
- `ѫ, ѧ` (yus) - valid in OES (nasal vowels)

**Solution needed:** Validator must recognize quote blocks and apply different rules:
- Always flag: `ы`, `э`, `ё` (Russian-only)
- Context-dependent: `ъ`, `ѣ`, etc. (allowed in quotes, flagged in modern text)

See: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/498

## Next Steps

1. **#498** Implement context-aware character validation (blocker)
2. ~~Gemini completes deep research (GH issues #490-496)~~ ✅ DONE (2026-02-03)
3. **IN PROGRESS:** Claude generates remaining module plan files from research
4. Claude generates meta files
5. Create quick-ref files
6. Begin test module content (prose + vocab only)
7. Review and iterate

## Notes

- C1-BIO modules should be updated with chronicle quotes (task #22)
- No activities yet - validate content/pedagogy first
- Use litopys.org.ua Ukrainian translations for primary sources
