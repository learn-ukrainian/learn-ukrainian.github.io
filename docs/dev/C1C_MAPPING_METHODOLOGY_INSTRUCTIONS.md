# C1-c Context: Ukrainian Lessons Mapping Methodology

**Agent:** C1-c (Claude Sonnet, User's Claude Max)
**Date:** 2026-01-02
**Task:** Create mapping methodology + batch execute Ukrainian Lessons resource mappings
**Status:** Phase 1b - Create methodology document, then batch execute Phases 2-6
**Approval:** User selected Option B - Create methodology before batch execution

## Background

**Phase 1 Complete:**
- ✅ Discovered 402+ blog articles on Ukrainian Lessons
- ✅ Cataloged 28 high-value articles in `docs/resources/ukrainianlessons/blog_db.json`
- ✅ Categorized by level: A1 (14), A2 (6), B1 (7), B2 (1)

**Remaining Work:**
- 240 ULP podcast episodes need mapping to 328 curriculum modules
- 28 blog articles need mapping to curriculum modules
- Estimated: 4-6 hours systematic work

## Your Task: Create Mapping Methodology Document

**File to create:** `docs/resources/ukrainianlessons/MAPPING_METHODOLOGY.md`

### Required Contents

#### 1. Priority Level Definitions

Define the priority scale and criteria for each level.

**Questions to answer:**
- What scale? (1-5 numeric? critical/high/medium/low/supplementary?)
- What makes a resource "priority 1" vs "priority 5"?
- How does priority affect display order in `[!resources]` sections?

**Example structure:**
```markdown
## Priority Levels

### Priority 1: Critical/Essential
- **Criteria:**
  - Directly teaches the module's primary grammar/vocabulary topic
  - CEFR level exactly matches module level
  - Content type matches module focus (e.g., grammar article for grammar module)
- **Examples:**
  - Dative case article → A2 Dative case module
  - ULP episode "Family vocabulary" → A1 Family module

### Priority 2: High Relevance
- **Criteria:**
  - Strongly related to module topic but not exact match
  - CEFR level ±1 from module level
  - Provides important supplementary context
- **Examples:** ...

### Priority 3-5: Medium to Low Relevance
...
```

#### 2. Relevance Scoring Criteria

Define how to determine if a resource is relevant to a module.

**Matching dimensions:**
1. **Grammar topic matching**
   - Exact match (article about genitive → genitive module)
   - Partial match (article about all cases → specific case module)
   - No match
2. **CEFR level matching**
   - Same level (A1 article → A1 module)
   - Adjacent level (A1 article → A2 module)
   - Distant level (A1 article → B2 module)
3. **Content type alignment**
   - Grammar guides → grammar modules
   - Vocabulary lists → vocabulary modules
   - Phrasebooks → beginner conversation modules
   - Cultural guides → cultural modules
4. **Vocabulary overlap**
   - Check if article vocabulary appears in module vocabulary section
   - Calculate overlap percentage?

**Decision tree:**
```
IF grammar_topic_exact_match AND level_match:
  → Priority 1 (Critical)
ELSE IF grammar_topic_partial_match AND level_adjacent:
  → Priority 2 (High)
...
```

#### 3. Sample Mappings (5-10 Examples)

Provide concrete examples showing your reasoning.

**Format for each example:**
```markdown
### Example 1: ULP Episode → Module Mapping

**Resource:** ULP Episode #42 "Ukrainian Family Vocabulary"
- **Type:** Podcast
- **Level:** A1
- **Topics:** family, relationships, kinship terms

**Target Module:** A1 M32 "My Family"
- **Module level:** A1
- **Module topics:** family members, possessive pronouns, describing relationships

**Mapping Decision:**
- **Priority:** 1 (Critical)
- **Reasoning:**
  - Exact topic match (family vocabulary)
  - Exact level match (A1)
  - Content type alignment (vocabulary podcast → vocabulary module)
  - High vocabulary overlap (estimated 80%+ of episode terms in module)

**Alternative matches (lower priority):**
- A1 M14 "Mine and Yours" - Priority 3 (possessive context, but not primary topic)
```

**Include examples for:**
- ✅ Perfect match (Priority 1)
- ✅ Strong match (Priority 2)
- ✅ Moderate match (Priority 3)
- ✅ Weak match (Priority 4-5)
- ✅ No match (don't map)
- ✅ ULP episode example
- ✅ Blog article example
- ✅ Edge case (resource matches multiple modules - how to handle?)

#### 4. Automation Strategy

Describe how you'll execute the mapping efficiently.

**Questions to address:**
- Manual mapping vs automated keyword matching?
- How to handle 240 episodes × 328 modules = 78,720 potential combinations?
- Quality control checkpoints (e.g., review every 50 mappings?)
- Batch processing strategy (by level? by resource type?)

**Suggested approach:**
```markdown
## Automation Strategy

### Phase 1: Automated First Pass
- Parse blog_db.json (28 articles)
- Parse podcast_db.json (240 ULP episodes)
- Parse curriculum module metadata (titles, topics, levels)
- Keyword matching algorithm:
  - Extract topic keywords from resource titles/descriptions
  - Match against module titles/topics
  - Calculate relevance score (0-100%)
  - Auto-assign priority based on score thresholds

### Phase 2: Manual Review
- Review all Priority 1 assignments (critical resources)
- Spot-check Priority 2-3 (10% sample)
- Validate edge cases

### Phase 3: Batch Update YAML
- Update `docs/resources/external_resources.yaml` with all mappings
- Sort by priority within each module
- Validate YAML structure

### Quality Control
- Checkpoint every 50 resources mapped
- Track unmapped resources (relevance score too low)
- Flag ambiguous mappings for manual review
```

## Deliverable

**File:** `docs/resources/ukrainianlessons/MAPPING_METHODOLOGY.md`

**Structure:**
```markdown
# Ukrainian Lessons Resources: Mapping Methodology

## 1. Priority Level Definitions
(Define scale, criteria, examples)

## 2. Relevance Scoring Criteria
(Matching dimensions, decision tree)

## 3. Sample Mappings
(5-10 concrete examples with reasoning)

## 4. Automation Strategy
(Execution plan, quality control)

## 5. Next Steps
(Ready for user approval, then batch execution)
```

## User Approval Required

After creating the methodology document:
1. User reviews and approves approach
2. User may request revisions to criteria/priorities
3. Once approved → proceed with batch execution (Phases 2-6)

## Success Criteria

**Methodology document must:**
- ✅ Define clear, actionable priority levels (not subjective)
- ✅ Provide specific matching criteria (not vague)
- ✅ Include diverse sample mappings (show reasoning)
- ✅ Describe efficient automation strategy (not manual one-by-one)
- ✅ Enable batch execution after approval (no ambiguity)

## Context Files

**Reference these for context:**
- `docs/resources/ukrainianlessons/blog_db.json` - 28 blog articles you cataloged
- `docs/resources/podcast_db.json` - 240 ULP episodes + ~100 FMU episodes
- `docs/resources/external_resources.yaml` - Current resource database (297KB)
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` - Module topics and scope
- `curriculum/l2-uk-en/{level}/*.md` - Actual module content

## Timeline

**Estimated effort:** 1-2 hours to create methodology document
**User review:** ~30 minutes
**Batch execution (Phases 2-6):** 3-4 hours after approval

---

**Ready to proceed?** Create `docs/resources/ukrainianlessons/MAPPING_METHODOLOGY.md` with the structure above.
