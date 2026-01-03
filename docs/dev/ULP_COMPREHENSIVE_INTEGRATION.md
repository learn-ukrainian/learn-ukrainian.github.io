# Ukrainian Lessons Podcast - Comprehensive Integration Plan

**Issue Context:** Issue #354 completed (YAML-first resources). Now prioritizing Ukrainian Lessons Podcast (ULP) as the primary external resource.

**User Requirements:**
1. Crawl Ukrainian Lessons blog for additional content (beyond podcast episodes)
2. Establish resource priority order: ULP episodes → ULP blog → other sources
3. Remap all 240 ULP podcast episodes to correct curriculum modules
4. Map ULP blog entries to curriculum modules

---

## Phase 1: Crawl Ukrainian Lessons Blog

### 1.1 Identify Blog Content

**Ukrainian Lessons website structure:**
- Main site: `https://www.ukrainianlessons.com/`
- Podcast episodes: `https://www.ukrainianlessons.com/lesson/{N}/` (ULP)
- 5 Minute Ukrainian: `https://www.ukrainianlessons.com/fmu{N}/`
- Blog articles: Need to discover structure

**Discovery tasks:**
```bash
# Find blog index or sitemap
WebFetch https://www.ukrainianlessons.com/sitemap.xml
WebFetch https://www.ukrainianlessons.com/blog/
WebFetch https://www.ukrainianlessons.com/articles/

# Check existing links in external_resources.yaml for patterns
rg "ukrainianlessons.com" docs/resources/external_resources.yaml | rg -v "lesson/|fmu" | sort -u
```

**Expected blog content types:**
- Grammar guides (e.g., "Noun Genders in Ukrainian")
- Vocabulary lists (e.g., "40+ Ukrainian Dishes")
- Culture articles
- Learning tips

### 1.2 Crawl Blog Articles

**Approach:**
1. Get sitemap or blog index
2. Extract article URLs
3. For each article:
   - Title
   - URL
   - Topic/category
   - Level (if indicated)
   - Summary/description

**Output:** JSON file with blog article database
```json
{
  "articles": [
    {
      "id": "ulp-blog-001",
      "title": "Noun Genders in Ukrainian",
      "url": "https://www.ukrainianlessons.com/noun-genders-in-ukrainian/",
      "topics": ["grammar", "nouns", "gender"],
      "suggested_level": "A1",
      "content_type": "guide",
      "summary": "Infographic with rules and exceptions"
    }
  ]
}
```

**Save to:** `docs/resources/ukrainianlessons/blog_db.json`

---

## Phase 2: Update Resource Priority System

### 2.1 Add Priority Field to YAML Schema

**Current sorting:** Relevance (high/medium/low) → Alphabetical

**New sorting:** Priority → Relevance → Alphabetical

**Priority levels:**
- `1` - Ukrainian Lessons Podcast episodes (ULP)
- `2` - Ukrainian Lessons blog articles
- `3` - Other high-quality sources (Ukrainian with Olena, Real Ukrainian, etc.)
- `4` - General resources

**Example YAML structure:**
```yaml
a1-01-the-cyrillic-code-i:
  podcasts:
    - episode_id: ULP-001
      title: ULP 1-01 Informal Greetings in Ukrainian
      url: https://www.ukrainianlessons.com/lesson/1/
      relevance: high
      priority: 1  # NEW FIELD
      match_reason: 'Beginner listening practice'
  articles:
    - id: ulp-blog-alphabet
      title: Ukrainian Alphabet - Complete Guide
      url: https://www.ukrainianlessons.com/alphabet/
      relevance: high
      priority: 2  # NEW FIELD
      source: Interactive alphabet with audio
  websites:
    - title: Talk Ukrainian - Alphabet
      url: https://talkukrainian.com/ukrainian-alphabet/
      relevance: high
      priority: 3  # NEW FIELD
```

### 2.2 Update Generation Scripts

**Files to modify:**
- `scripts/generate_mdx.py` → Update `format_resources_for_mdx()` sorting logic
- `scripts/generate_json.py` → Sort resources by priority before output

**Sorting logic:**
```python
# Current (line ~1660 in generate_mdx.py)
sorted_items = sorted(
    items,
    key=lambda x: (-relevance_priority.get(x.get('relevance', 'low'), 0),
                   x.get('title', '').lower())
)

# NEW sorting
priority_map = {1: 4, 2: 3, 3: 2, 4: 1}  # 1 = highest
relevance_map = {'high': 3, 'medium': 2, 'low': 1}

sorted_items = sorted(
    items,
    key=lambda x: (
        -priority_map.get(x.get('priority', 4), 1),      # Priority first
        -relevance_map.get(x.get('relevance', 'low'), 0), # Then relevance
        x.get('title', '').lower()                        # Then alphabetical
    )
)
```

---

## Phase 3: Remap 240 ULP Episodes to Correct Modules

### 3.1 Current State Analysis

**Podcast database:** `docs/resources/podcasts/podcast_db.json` (602 episodes total)
- ULP (Ukrainian Lessons Podcast): 240 episodes
- FMU (5 Minute Ukrainian): ~100 episodes
- Other podcasts: ~262 episodes

**Current mapping issues:**
- ULP-001 mapped to B2-16 (wrong - should be A1 greeting module)
- Many A1 modules have NO podcasts
- ULP episodes may be scattered incorrectly

### 3.2 Mapping Strategy

**A1 Modules (34 total) - ULP Season 1 (Episodes 1-50)**

**Mapping approach:**
1. Read A1 curriculum plan: `docs/l2-uk-en/A1-CURRICULUM-PLAN.md`
2. Read each A1 module frontmatter for topics
3. Match ULP episode topics to module topics
4. Allow multi-module mapping (episode can appear in multiple modules if relevant)

**Example mappings:**
```yaml
# ULP-001: Informal Greetings
a1-04-this-is-i-am:  # "Привіт! Я Марія."
  podcasts:
    - episode_id: ULP-001
      priority: 1
      relevance: high
      match_reason: 'Level-aligned: greetings and introductions'

# ULP-011: Ordering drinks
a1-09-food-and-drinks:  # Already correct
  podcasts:
    - episode_id: ULP-011
      priority: 1
      ...

# ULP-005: Numbers 1-20
a1-17-numbers-and-money:
  podcasts:
    - episode_id: ULP-005
      priority: 1
      relevance: high
      match_reason: 'Level-aligned: numbers 1-20'
```

**Progressive reuse for higher levels:**
- A1-level ULP episodes can appear in A2/B1 as "review listening practice"
- Relevance decreases at higher levels: `high` (A1) → `medium` (A2) → `low` (B1)

### 3.3 Mapping Execution Plan

**Step-by-step process:**

1. **Extract ULP episodes from podcast_db.json:**
   ```bash
   jq '.[] | select(.id | startswith("ULP-"))' docs/resources/podcasts/podcast_db.json > ulp_episodes.json
   ```

2. **For each level (A1 → A2 → B1 → B2):**
   - List all module titles and topics
   - Match ULP episode topics to modules
   - Create mapping entries

3. **Validation:**
   - Ensure each ULP episode is mapped at least once
   - Check that episode levels match module levels
   - Flag ULP episodes with no clear mapping

4. **Update external_resources.yaml:**
   - Add ULP episodes with `priority: 1`
   - Add `match_reason` explaining alignment

---

## Phase 4: Map ULP Blog Entries to Modules

### 4.1 Blog Content Categorization

**After crawling (Phase 1), categorize blog articles by:**
1. **Grammar guides** → Map to grammar modules
2. **Vocabulary lists** → Map to vocab modules
3. **Cultural articles** → Map to cultural modules
4. **Pronunciation guides** → Map to early A1 modules

### 4.2 Blog Mapping Strategy

**Mapping rules:**
- Blog articles get `priority: 2` (after podcast episodes)
- Can map to multiple modules if content is comprehensive
- Prefer mapping to module that introduces the topic

**Example:**
```yaml
a1-03-the-gender-code:
  podcasts:
    - episode_id: ULP-XXX  # If exists
      priority: 1
      ...
  articles:
    - id: ulp-blog-gender
      title: "Noun Genders in Ukrainian"
      url: https://www.ukrainianlessons.com/noun-genders-in-ukrainian/
      priority: 2  # ULP blog
      relevance: high
      source: "Infographic with rules and exceptions"
    - title: "How to Know Noun Gender"  # Other source
      url: https://example.com
      priority: 3  # Non-ULP
      relevance: medium
```

---

## Phase 5: Validation & Testing

### 5.1 Validation Checks

**After all mappings complete:**

1. **Coverage metrics:**
   ```bash
   # Count modules with ULP podcast episodes
   yq '.resources | to_entries | map(select(.value.podcasts[]?.priority == 1)) | length' external_resources.yaml

   # Count modules with ULP blog articles
   yq '.resources | to_entries | map(select(.value.articles[]?.priority == 2)) | length' external_resources.yaml

   # List ULP episodes NOT mapped to any module
   # (compare podcast_db.json ULP episodes vs. external_resources.yaml)
   ```

2. **Priority sorting test:**
   ```bash
   # Generate MDX for a sample module and verify ULP appears first
   npm run generate l2-uk-en a1 9
   tail -30 docusaurus/docs/a1/module-09.mdx | grep -A 10 "Podcasts:"
   ```

3. **Quality checks:**
   - ULP episodes match module topics (no random assignments)
   - Blog articles are relevant to module content
   - Priority ordering is correct in generated output

### 5.2 Test Modules

**Test full pipeline on these modules:**
- A1-01 (alphabet - should have ULP blog article)
- A1-04 (greetings - should have ULP-001)
- A1-09 (food - already has ULP, verify it's priority 1)
- A1-17 (numbers - should have ULP-005)
- A2-01 (dative - check ULP season 2)
- B1-25 (motion verbs - check ULP season 3)

---

## Phase 6: Documentation Updates

### 6.1 Update Documentation

**Files to update:**
- `docs/ARCHITECTURE.md` - Add priority field explanation
- `docs/resources/external_resources_schema.yaml` - Document priority levels
- `CLAUDE.md` - Note ULP priority in resource guidelines

**New section for ARCHITECTURE.md:**
```markdown
## Resource Priority System

Resources are sorted by priority:
1. **Priority 1:** Ukrainian Lessons Podcast episodes (ULP/FMU)
2. **Priority 2:** Ukrainian Lessons blog articles
3. **Priority 3:** Other high-quality sources
4. **Priority 4:** General resources

Within each priority level, resources sort by relevance (high/medium/low), then alphabetically.
```

---

## Success Metrics

**Upon completion, we should have:**

✅ ULP blog crawled and catalogued (JSON database)
✅ Priority field added to external_resources.yaml
✅ Generation scripts updated to sort by priority
✅ All 240 ULP podcast episodes mapped to correct modules
✅ ULP blog articles mapped to relevant modules
✅ ULP content appears FIRST in all resource lists
✅ A1-01 has Ukrainian Lessons content (blog + listening)
✅ All tests pass (pipeline validation)
✅ Documentation updated

**Coverage targets:**
- **A1:** 30+ modules with ULP content (88%+)
- **A2:** 40+ modules with ULP content (70%+)
- **B1:** 50+ modules with ULP content (55%+)
- **B2:** 30+ modules with ULP content (20%+)

---

## Next Steps

1. **Immediate:** Crawl Ukrainian Lessons blog (Phase 1)
2. **Then:** Add priority field and update scripts (Phase 2)
3. **Then:** Systematic ULP episode mapping (Phase 3)
4. **Then:** Blog article mapping (Phase 4)
5. **Finally:** Validation and testing (Phase 5-6)

**Estimated effort:** 4-6 hours of systematic work across all phases.
