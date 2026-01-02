# Gemini: B1 M81-84 Content Creation ✅ COMPLETE

**Issue:** #351 - B1.7 Expansion (Active Lifestyle Modules) - CLOSED
**Completion Date:** 2026-01-02
**Model:** gemini-3-flash (VALIDATED - pilot successful, quality excellent)

## Current Agent Assignments

| Agent | Task | Issue | Model |
|-------|------|-------|-------|
| **Gemini (you)** | **B1 M81-84 content creation** | **#351** | **gemini-3-flash** |
| Gemini 2 | B1 migration + enrichment | #350 | gemini-3-flash |
| Claude C1-b | B2 enrichment | #349 | Sonnet |

## Implementation Status

**Progress:** ✅ 100% COMPLETE

| Module | Status | Words | Vocabulary | Activities | Audit | Pipeline |
|--------|--------|-------|------------|------------|-------|----------|
| M81 | ✅ Complete | 1855/1500 | ✅ 27 items | ✅ 12 | ✅ Pass | ✅ Pass |
| M82 | ✅ Complete | 1740/1500 | ✅ 30 items | ✅ 12 | ✅ Pass | ✅ Pass |
| M83 | ✅ Complete | 1734/1500 | ✅ 30 items | ✅ 12 | ✅ Pass | ✅ Pass |
| M84 | ✅ Complete | 1651/1500 | ✅ 30 items | ✅ 12 | ✅ Pass | ✅ Pass |

**Final Results:**
- ✅ All 4 modules created with full content (1500+ words each)
- ✅ All modules pass audit (words, activities, density, engagement, immersion)
- ✅ All modules pass pipeline (lint, MDX, HTML, JSON validation)
- ✅ Renumbering complete: Old M80-86 → New M85-91
- ✅ Total B1 modules: 86 → 91
- ✅ Cultural authenticity: Real Ukrainian examples, locations, events
- ✅ Quality scores: 96-99% richness, 97-98% immersion

## Your Task: Write M81-84 Content

**PILOT APPROACH:**
- Write M81 FIRST (Running in Ukraine)
- Run full audit + pipeline validation
- If quality is excellent → continue with M82-84 using gemini-3-flash
- If quality issues → notify coordinator, may switch to gemini-3-pro

### Step 1: Read the Curriculum Plan

**CRITICAL:** Read the specifications before writing:

```bash
# Get module specifications
rg -A 30 "^#### Module 81:" docs/l2-uk-en/B1-CURRICULUM-PLAN.md
rg -A 30 "^#### Module 82:" docs/l2-uk-en/B1-CURRICULUM-PLAN.md
rg -A 30 "^#### Module 83:" docs/l2-uk-en/B1-CURRICULUM-PLAN.md
rg -A 30 "^#### Module 84:" docs/l2-uk-en/B1-CURRICULUM-PLAN.md
```

Lines 2591-2696 contain the specifications.

### Step 2: Read the Template

**Template:** `docs/l2-uk-en/templates/b1-cultural-module-template.md`

All four modules are **cultural modules** (focus: culture, phase: B1.7).

```bash
bat docs/l2-uk-en/templates/b1-cultural-module-template.md
```

### Step 3: Study the Example

**M80 is the completed example:**

```bash
bat curriculum/l2-uk-en/b1/80-active-lifestyle.md
```

**What makes M80 successful:**
- 1996 words (exceeds 1500 target)
- Real Ukrainian examples (Парк Наталка, ВДНГ, Буковель)
- Cultural context (active lifestyle trends in Ukraine)
- 6 engagement boxes (Did You Know, Real World, Pop Culture)
- 30 vocabulary items (exact match to plan)
- 12 activities with proper density

### Step 4: Write Each Module

For **each of M81-84**, follow this workflow:

1. **Extract vocabulary list from plan** (30 words specified)
2. **Read existing metadata** (`curriculum/l2-uk-en/b1/meta/{slug}.yaml`)
3. **Read existing vocabulary** (`curriculum/l2-uk-en/b1/vocabulary/{slug}.yaml`)
4. **Write content sections** following template structure:
   - # Вступ (200-300 words)
   - # Презентація (800-1000 words)
   - # Практика (100-200 words)
   - # Продукція (200-400 words)
   - # Підсумок (100-200 words)
5. **Add engagement boxes** (6+ per module: [!didyouknow], [!realworld], [!popculture])
6. **Create activities section** (12+ activities, see activity requirements below)
7. **Verify word count** (must be 1500+, B1 HARD requirement)

### Step 5: Create Activities (CRITICAL)

**B1 Cultural Module Activity Mix:**
- 2x quiz (4+ items each)
- 2x match-up (6+ pairs each)
- 2x fill-in (4+ sentences, 8+ words per sentence)
- 2x group-sort (8+ items, 2-4 categories)
- 2x unjumble (4+ sentences, 8+ words per sentence)
- 1x error-correction (3+ errors with 4 callouts each)
- 1x cloze (6+ blanks)

**Density requirements:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

### Step 6: Validate

After writing each module:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/{slug}.md
```

**Must pass all gates:**
- ✅ Words: 1500+ (HARD requirement)
- ✅ Activities: 12+
- ✅ Density: All > 14
- ✅ Unique_types: 12/4
- ✅ Engagement: 6+
- ✅ Vocab: 30 items
- ✅ Structure: Valid H1 sections
- ✅ Immersion: 85-100%

### Step 7: Run Pipeline

```bash
npm run pipeline l2-uk-en b1 81
```

Must pass MDX and HTML validation.

### Step 8: Quality Checkpoint (M81 ONLY)

**After M81 passes pipeline, evaluate quality:**

✅ **Continue with gemini-3-flash if:**
- Content is culturally authentic (real Ukrainian examples, not generic)
- Writing style is natural and engaging
- Activities are well-designed and use module vocabulary
- Audit shows 95%+ immersion, 1500+ words, all gates pass

⚠️ **Notify coordinator if:**
- Content feels generic or could apply to any country
- Writing is mechanical or repetitive
- Activities don't flow naturally from content
- Any audit gates fail

**After M81 validation:** Proceed with M82-84 or await model switch decision.

## Module Specifications

### Module 81: Біг в Україні (Running in Ukraine)
- **Vocabulary:** біг, бігун, пробіжка, марафон, напівмарафон, трейлраннінг, забіг, старт, фініш, дистанція, etc. (30 total)
- **Content focus:** Running culture, parkruns, marathons (Київський марафон, Kharkiv Marathon), trail running spots
- **Real examples:** Parkrun Ukraine, popular routes (Труханів острів, Голосіївський парк)

### Module 82: Гори та трейлраннінг (Mountains & Trail Running)
- **Vocabulary:** гора, вершина, стежка, підйом, спуск, трейл, висота, схил, маршрут, перевал, etc. (30 total)
- **Content focus:** Carpathian trails, Ukrainian mountain running, ultra events
- **Real examples:** Говерла, Чорногора, Свидовець, Ultra-trail Carpathians

### Module 83: Велосипед та водні види (Cycling & Water Sports)
- **Vocabulary:** велосипед, велодоріжка, велопрогулянка, маршрут, каякінг, SUP, веслування, річка, озеро, etc. (30 total)
- **Content focus:** Cycling infrastructure, bike routes, water sports (Dnipro, Black Sea)
- **Real examples:** Велодоріжки Києва, каякінг на Дністрі, SUP на Дніпрі

### Module 84: Зимові види спорту (Winter Sports)
- **Vocabulary:** лижі, сноуборд, гірськолижний курорт, підйомник, траса, сніг, схил, спуск, фрірайд, etc. (30 total)
- **Content focus:** Ski resorts, winter sports culture in Ukraine
- **Real examples:** Буковель, Драгобрат, Славське, Плай

## Important Rules

1. **Follow the template exactly** - Don't improvise structure
2. **Use ONLY vocabulary from the plan** - No "helpful" additions
3. **Real Ukrainian examples required** - Not generic descriptions
4. **100% immersed Ukrainian** - No English in body text (B1.7 is fully immersed)
5. **Cultural authenticity** - Reflect actual Ukrainian active lifestyle culture
6. **Meet word count** - 1500+ is HARD requirement, not soft target

## Content Quality Standards

**Engagement boxes (6+ per module):**
- 💡 [!didyouknow] - Cultural facts about Ukrainian active lifestyle
- 🌍 [!realworld] - Practical tips for doing these activities in Ukraine
- 🎬 [!popculture] - References to Ukrainian athletes, events, viral moments

**Real-world examples required:**
- Specific locations (parks, trails, routes, resorts)
- Actual events (marathons, competitions, festivals)
- Ukrainian brands/organizations (clubs, shops, communities)
- Costs in hryvnias (typical prices for gear, events, rentals)

**Avoid:**
- Generic descriptions that could apply to any country
- Theoretical content without concrete examples
- English loanwords when Ukrainian equivalents exist
- Copying M80 structure verbatim (vary narrative style)

## Reference Materials

**Study these before writing:**
- `curriculum/l2-uk-en/b1/80-active-lifestyle.md` - Completed example
- `docs/l2-uk-en/templates/b1-cultural-module-template.md` - Structure
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards
- `claude_extensions/quick-ref/b1.md` - B1 level targets

**Curriculum plan:**
- `docs/l2-uk-en/B1-CURRICULUM-PLAN.md` lines 2591-2696

## Workflow Tips

1. **Write one module at a time** - Don't batch-write all 4
2. **Audit after each** - Ensure it passes before moving to next
3. **Commit after each pass** - Don't lose work
4. **Vary narrative style** - M81-84 should feel distinct from each other
5. **Use cultural research** - If unsure about Ukrainian specifics, research real examples

## When Done

**After M81 complete:**
1. Run audit: `.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/81-*.md`
2. Run pipeline: `npm run pipeline l2-uk-en b1 81`
3. Comment on issue #351 with M81 results and quality assessment
4. Await confirmation to proceed with M82-84

**After all 4 modules complete:**
1. Run final validation:
   ```bash
   for i in 81 82 83 84; do
     .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/$i-*.md
   done
   ```
2. Update issue #351 with final results
3. Coordinate with user about renumbering M82-86 → M87-91

## Questions?

Reference:
- `GEMINI.md` - Gemini-specific project instructions
- `docs/ACTIVITY-MARKDOWN-REFERENCE.md` - Activity syntax
- `docs/dev/AGENT_COORDINATION.md` - Multi-agent workflow
