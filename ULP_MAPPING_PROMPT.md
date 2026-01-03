# Task: Map Ukrainian Lessons Podcast Episodes to Curriculum Modules

**Context:** User wants Ukrainian Lessons Podcast (ULP) as the primary external resource for A1-C2 modules. You'll map 240 podcast episodes to relevant curriculum modules based on topic and grammar alignment.

**Your task:** Create podcast → module mappings and prepare for external resources integration.

---

## Step 1: Understand Current State

### Read These Files First

```bash
# Podcast data (JSON format - will convert to YAML)
cat docs/resources/podcasts/podcast_db.json | jq '.' | head -50

# Mapping plan
cat docs/resources/podcasts/CURRICULUM_MAPPING.md

# Media assignment files (per-level resource planning)
cat docs/l2-uk-en/A1-MEDIA-ASSIGNMENT.md | head -100
cat docs/l2-uk-en/A2-MEDIA-ASSIGNMENT.md | head -100
cat docs/l2-uk-en/B1-MEDIA-ASSIGNMENT.md | head -100
cat docs/l2-uk-en/B2-MEDIA-ASSIGNMENT.md | head -100

# Media sources master list
cat docs/l2-uk-en/MEDIA-SOURCES.md | grep -A 10 "Ukrainian Lessons Podcast"
```

### Key Information
- **ULP (Ukrainian Lessons Podcast):** 240 episodes, grammar-focused, beginner to advanced
- **FMU (5 Minute Ukrainian):** Quick dialogues, A1-A2 aligned
- **Current state:** Only 1/34 A1 modules have `[!resources]` sections
- **Goal:** Map all 240 episodes to 623 modules (A1-C2), prepare YAML-based resource structure
- **Progressive reuse:** Episodes can map to multiple levels (e.g., beginner episodes for listening practice at higher levels)

---

## Step 2: Review Module Topics (Per Level)

### A1 Modules (34 total)
```bash
# Get A1 module titles and topics
for i in {1..34}; do
  f="curriculum/l2-uk-en/a1/"*"$i-"*.md
  if [ -f $f ]; then
    echo "M$i: $(grep '^title:' $f | head -1)"
  fi
done
```

**Focus areas:** Cyrillic, greetings, cases, basic verbs, food, shopping, time, modals

### A2 Modules (57 total)
```bash
# Get A2 module titles
for i in {1..57}; do
  f="curriculum/l2-uk-en/a2/"*"$i-"*.md
  if [ -f $f ]; then
    echo "M$i: $(grep '^title:' $f | head -1)"
  fi
done
```

**Focus areas:** Dative, instrumental, prepositions, aspect, comparisons, numerals, complex sentences

### B1 Modules (91 total)
```bash
# Get B1 module titles
for i in {1..91}; do
  f="curriculum/l2-uk-en/b1/"*"$i-"*.md
  if [ -f $f ]; then
    echo "M$i: $(grep '^title:' $f | head -1)"
  fi
done
```

**Focus areas:** Aspect mastery, motion verbs, complex sentences, participles, cultural topics

### B2 Modules (145 target, 131 exist)
```bash
# Get B2 module titles
for i in {1..145}; do
  f="curriculum/l2-uk-en/b2/"*"$i-"*.md
  if [ -f $f ]; then
    echo "M$i: $(grep '^title:' $f | head -1)"
  fi
done
```

**Focus areas:** Passive voice, registers, Ukrainian history, idioms, advanced syntax

### C1 Modules (196 planned)
```bash
# Get C1 module titles (if they exist)
ls curriculum/l2-uk-en/c1/*.md 2>/dev/null | wc -l
```

**Focus areas:** Biographies, stylistics, folk culture, literature (planned)

### C2 Modules (100 planned)
```bash
# Get C2 module titles (if they exist)
ls curriculum/l2-uk-en/c2/*.md 2>/dev/null | wc -l
```

**Focus areas:** Stylistic perfection, professional specialization (planned)

---

## Step 3: Create Mapping Strategy

### Mapping Criteria

**1. Topic Match**
- Episode title/summary ↔ Module theme
- Example: "Informal Greetings" → A1-M01

**2. Grammar Match**
- Episode grammar tags ↔ Module grammar focus
- Example: "Dative Case" → A2-M01, A2-M02

**3. Level Alignment & Progressive Reuse**
- Episodes can map to MULTIPLE levels (beginner → advanced reinterpretation)
- Example: "Greetings" episode → A1 (basic vocab), A2 (review), B1 (listening practice)
- Don't map advanced grammar to beginner levels (but vocab reuse is OK)
- Higher-level modules can use beginner episodes for listening comprehension

**4. Multiple Mappings OK**
- One episode can map to multiple modules (same or different levels)
- One module can have multiple episodes

### Output Format (YAML - NOT JSON)

**Why YAML:** Consistent with vocabulary/activities architecture, supports comments, lower error rate.

**File location:** `docs/resources/podcasts/ulp_mapping.yaml`

```yaml
# Ukrainian Lessons Podcast → Curriculum Mapping
# Generated: 2026-01-02
# Episodes: 240 from ULP + FMU
# Modules: A1 (34), A2 (57), B1 (91), B2 (145), C1 (196), C2 (100) = 623 total

mappings:
  # A1 Modules
  - module_id: a1-01-cyrillic-code-i
    module_title: "The Cyrillic Code I"
    level: A1
    recommended_episodes:
      - episode_id: ULP-001
        title: "Informal Greetings"
        url: "https://ukrainianlessons.com/thepodcast/001"
        match_reason: "Greeting phrases, pronunciation practice"
        relevance: high
      - episode_id: FMU-001
        title: "I don't speak Ukrainian well"
        url: "https://ukrainianlessons.com/fmu/001"
        match_reason: "Beginner conversation starter"
        relevance: medium

  - module_id: a1-04-this-is-i-am
    module_title: "This is / I am"
    level: A1
    recommended_episodes:
      - episode_id: ULP-022
        title: "First Verb Conjugation"
        url: "https://ukrainianlessons.com/thepodcast/022"
        match_reason: "Verb conjugation (бути, це)"
        relevance: high

  # A2 Modules
  - module_id: a2-01-the-dative-i-pronouns
    module_title: "The Dative I: Pronouns"
    level: A2
    recommended_episodes:
      - episode_id: ULP-XXX
        title: "Dative Case Introduction"
        url: "https://ukrainianlessons.com/thepodcast/XXX"
        match_reason: "Dative case grammar"
        relevance: high

  # B1 Modules
  - module_id: b1-16-motion-verbs-full-system
    module_title: "Motion Verbs: Full System"
    level: B1
    recommended_episodes:
      - episode_id: ULP-YYY
        title: "Motion Verbs йти/ходити"
        url: "https://ukrainianlessons.com/thepodcast/YYY"
        match_reason: "Motion verb pairs"
        relevance: high

  # B2 Modules (history, advanced grammar)
  - module_id: b2-75-volodymyr-i-khreshchennia
    module_title: "Volodymyr I and Christianization"
    level: B2
    recommended_episodes:
      - episode_id: ULP-ZZZ
        title: "Interview about Ukrainian history"
        url: "https://ukrainianlessons.com/thepodcast/ZZZ"
        match_reason: "Historical context, immersed Ukrainian"
        relevance: medium

  # C1 Modules (if applicable)
  # C2 Modules (if applicable)

  # ... continue for all relevant modules
```

**Field definitions:**
- `module_id` - Slug from filename (e.g., `01-cyrillic-code-i`)
- `module_title` - Human-readable title
- `level` - A1, A2, B1, B2, C1, or C2
- `episode_id` - ULP-XXX or FMU-XXX
- `match_reason` - Why this episode matches this module
- `relevance` - high/medium/low

---

## Step 4: Analyze Podcast Database

### Extract Episode Metadata
```bash
# View podcast structure
jq '.episodes[] | {id, title, tags}' docs/resources/podcasts/podcast_db.json | head -50

# Count episodes
jq '.episodes | length' docs/resources/podcasts/podcast_db.json

# List unique tags (for grammar matching)
jq '[.episodes[].tags[]?] | unique' docs/resources/podcasts/podcast_db.json
```

### Episode Data Format (Current JSON)
```json
{
  "episodes": [
    {
      "id": "ULP-001",
      "title": "Informal Greetings",
      "url": "https://ukrainianlessons.com/thepodcast/001",
      "summary": "Learn informal greeting phrases",
      "tags": ["greetings", "A1", "pronunciation"],
      "level": "A1"
    }
  ]
}
```

---

## Step 5: Create Mappings (Systematic Approach)

### Process (Level by Level)

**For A1 (Highest Priority):**
1. List all 34 A1 modules with topics
2. Search podcast_db.json for matching episodes:
   - Topic keywords (greeting, food, case, verb, etc.)
   - Grammar tags (nominative, accusative, genitive, etc.)
   - Level tag (A1)
3. Create mappings with match reasons
4. Aim for 1-3 episodes per module (not all modules will have matches)

**For A2:**
1. Focus on grammar-heavy modules (cases, aspect, complex sentences)
2. Search for intermediate-level episodes
3. Map dative, instrumental, aspect episodes

**For B1:**
1. Focus on advanced grammar (motion verbs, participles)
2. Cultural modules may not have ULP matches (that's OK)
3. Map available episodes
4. Consider beginner episodes for listening comprehension practice

**For B2:**
1. Focus on interview episodes (Q&A, natural conversation)
2. Advanced grammar episodes
3. History/culture topics
4. Episodes can be used for immersed listening practice

**For C1/C2:**
1. Map if episodes exist with appropriate complexity
2. Use for listening comprehension and cultural context
3. Not all C1/C2 modules will have ULP matches (literature, specialized topics)

---

## Step 6: Validation & Review

### Quality Checks
- [ ] All episode IDs valid (exist in podcast_db.json)
- [ ] All module IDs valid (files exist in curriculum)
- [ ] Match reasons make sense
- [ ] Progressive reuse documented (episodes mapped to multiple levels where appropriate)
- [ ] High relevance > Medium relevance > Low relevance
- [ ] YAML syntax valid (`yq . ulp_mapping.yaml`)

### Coverage Metrics
```bash
# Count mapped modules per level
yq '.mappings | group_by(.level) | map({level: .[0].level, count: length})' ulp_mapping.yaml

# Count episodes used
yq '[.mappings[].recommended_episodes[].episode_id] | unique | length' ulp_mapping.yaml
```

**Expected coverage:**
- A1: 30-34 modules mapped (~90-100%) - Strong grammar and topic alignment
- A2: 45-55 modules mapped (~80-95%) - Grammar episodes + progressive reuse
- B1: 60-85 modules mapped (~65-95%) - Advanced grammar + listening practice
- B2: 80-130 modules mapped (~55-90%) - Interviews, conversations, listening comprehension
- C1: 100-180 modules mapped (~50-90%) - Listening practice, cultural context
- C2: 50-90 modules mapped (~50-90%) - Advanced listening, professional topics
- Total episodes used: 240 episodes (extensive multi-level reuse)

**Goal: Maximum coverage through progressive reuse.** With 240 ULP episodes and 623 modules, episodes should be mapped to ALL appropriate levels - beginner episodes work for listening comprehension at advanced levels, advanced episodes provide challenge for intermediate learners.

---

## Step 7: Document Your Work

### Create Summary Report

**File:** `docs/resources/podcasts/ULP_MAPPING_REPORT.md`

```markdown
# ULP Mapping Report

**Date:** 2026-01-02
**Agent:** [Your name]
**Episodes analyzed:** [count]
**Modules mapped:** [count]

## Coverage Summary

| Level | Modules | Mapped | Coverage |
|-------|---------|--------|----------|
| A1 | 34 | XX | XX% |
| A2 | 57 | XX | XX% |
| B1 | 91 | XX | XX% |
| B2 | 145 | XX | XX% |
| C1 | 196 | XX | XX% |
| C2 | 100 | XX | XX% |
| **Total** | **623** | **XX** | **XX%** |

## Episode Usage

- Total episodes in ULP database: 240
- Episodes used in mappings: XX
- Most mapped episode: [ID] ([title]) - XX modules
- Average episodes per module: XX
- Average modules per episode: XX (progressive reuse)

## High-Confidence Mappings

[List 5-10 examples of excellent matches]

## Low-Confidence Mappings

[List mappings that need review]

## Modules Without Matches

[List modules that have no ULP episodes]

## Recommendations

- Which modules need alternative resources?
- Which episodes are underutilized?
- Any gaps in podcast coverage?
```

---

## Step 8: Prepare for Phase 2 Integration

### Future Work (Not Your Task - Document Only)

After this mapping is complete, Phase 2 will:
1. Extract existing resources from markdown `[!resources]` sections
2. Design YAML schema for external resources
3. Apply ULP mappings automatically
4. Generate updated `[!resources]` sections in modules

**Your output enables Phase 2.**

---

## Expected Deliverables

1. **`docs/resources/podcasts/ulp_mapping.yaml`** - Complete episode → module mappings
2. **`docs/resources/podcasts/ULP_MAPPING_REPORT.md`** - Coverage summary and quality notes
3. **Comment on issue #334** - Report completion with metrics

---

## Tools & Commands

### Helpful Commands
```bash
# Count A1 modules
ls curriculum/l2-uk-en/a1/*.md | wc -l

# Get module metadata
rg "^title:" curriculum/l2-uk-en/a1/01-*.md

# Search podcast by keyword
jq '.episodes[] | select(.title | contains("Dative"))' podcast_db.json

# Validate YAML syntax
yq . docs/resources/podcasts/ulp_mapping.yaml

# Pretty print YAML
yq -P docs/resources/podcasts/ulp_mapping.yaml
```

### Modern CLI Tools Available
- `rg` (ripgrep) - Fast search
- `fd` - Find files
- `jq` - JSON processor
- `yq` - YAML processor
- `bat` - View files with syntax highlighting

---

## Important Rules

1. **Use YAML, not JSON** - Consistent with project architecture
2. **Include match_reason** - Explain why episode matches module
3. **Progressive reuse encouraged** - Episodes can map to multiple levels
4. **Quality > Quantity** - Better to have 50 high-confidence mappings than 100 weak ones
5. **Document gaps** - Note modules that need other resources

---

## Questions?

Reference:
- `docs/resources/podcasts/CURRICULUM_MAPPING.md` - Original plan
- `docs/l2-uk-en/MEDIA-SOURCES.md` - All media sources
- `docs/l2-uk-en/*-MEDIA-ASSIGNMENT.md` - Per-level resource plans

**Ready to begin?** Start with A1 modules and build systematically.
