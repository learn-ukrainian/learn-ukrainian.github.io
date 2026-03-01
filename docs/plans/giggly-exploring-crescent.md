# Plan: Tabbed Module Layout (Lesson | Vocabulary | Activities | Resources)

## Context

Module pages currently render everything in a single long scroll: prose → activities → vocabulary → resources. Students must scroll back and forth between lesson content and vocabulary reference, breaking reading flow. The user wants a tabbed layout separating concerns into 4 tabs.

**Decision log:**
- 4 tabs (not 3): Vocabulary deserves its own quick-reference tab
- Grammar tables stay in Lesson tab for now — grammar reference tab is a future iteration
- Use Starlight's built-in `<Tabs>` / `<TabItem>` components (no custom wrapper needed)

## Tab Structure

| Tab | Label | Icon | Content |
|-----|-------|------|---------|
| 1 | Lesson | 📖 | Prose body (H2 sections, callouts, inline YouTubeVideo embeds) |
| 2 | Vocabulary | 📝 | Vocabulary table |
| 3 | Activities | 🎯 | All interactive activity components |
| 4 | Resources | 🔗 | External resources callout + YouTube video embeds from research |

**UX details:**
- `syncKey="module-tab"` — remembers last-selected tab across modules (localStorage)
- Default tab: Lesson (first tab)
- Scroll position preserved per tab when switching

## Implementation

### Step 1: Modify `generate_mdx.py` — restructure output assembly

**File:** `scripts/generate_mdx.py`
**Function:** `generate_mdx()` (line ~1316)

Currently the function assembles: `body + resources + vocabulary + activities` linearly.

Change to wrap in Starlight Tabs:

```python
# Add Tabs import to the imports block
imports += "\nimport { Tabs, TabItem } from '@astrojs/starlight/components';"

# Instead of appending activities/vocab/resources to body,
# build 4 separate content blocks:
lesson_content = processed_body   # prose only (no activities/vocab/resources)
vocab_content = vocab_md           # vocabulary table
activities_content = activities_jsx # activity components
resources_content = resources_md + youtube_embeds  # callout + videos

# Wrap in tabs
tabbed = f"""
<Tabs syncKey="module-tab">
<TabItem label="📖 Lesson">

{lesson_content}

</TabItem>
<TabItem label="📝 Vocabulary">

{vocab_content}

</TabItem>
<TabItem label="🎯 Activities">

{activities_content}

</TabItem>
<TabItem label="🔗 Resources">

{resources_content}

</TabItem>
</Tabs>
"""
```

**Key changes to the assembly logic:**

1. **Stop appending** resources/vocab/activities to `body` (remove steps 2-4 in current flow)
2. **Build each content block separately** — each block is a string of MDX/markdown
3. **Wrap in `<Tabs>` / `<TabItem>`** structure
4. **Empty tab handling**: If vocab/activities/resources are empty, still show the tab but with a placeholder message (e.g., "No vocabulary for this module" in italic)

**Import changes:**
- Add `import { Tabs, TabItem } from '@astrojs/starlight/components';` to the imports string
- Keep all existing activity component imports (they're needed in Activities tab)
- Keep `YouTubeVideo` import (used in both Lesson and Resources tabs)

### Step 2: Handle the Lesson tab content

The lesson tab gets the prose body ONLY:
- All H2/H3 sections with teaching content
- Inline callouts (:::note, :::tip, etc.)
- Inline `<YouTubeVideo>` embeds (pronunciation videos from plans — these are part of the lesson)
- NO vocabulary table
- NO activities
- NO external resources section

The current cleanup logic (lines 1410-1416) already removes Activities/Vocabulary/Resources from body. This stays the same — we just don't append them back.

### Step 3: Handle the Vocabulary tab content

Build the vocabulary table as a standalone block:
- Reuse existing `_vocab_items_to_markdown()` / `_b1_vocab_items_to_markdown()`
- Remove the H2 header ("## Vocabulary" / "## Словник") — the tab label serves as the header
- If no vocab items: show `*No vocabulary for this module.*`

### Step 4: Handle the Activities tab content

Build the activities JSX as a standalone block:
- Reuse existing `yaml_activities_to_jsx()`
- Remove the H2 header ("## 🎯 Activities" / "## 🎯 Вправи") — the tab label serves as the header
- If no activities: show `*No activities for this module.*`

### Step 5: Handle the Resources tab content

Build the resources content as a standalone block:
- External resources callout (podcasts, articles, books, websites) — from `format_resources_for_mdx()`
- YouTube video embeds — from `format_resources_for_mdx()` (already renders `<YouTubeVideo>` components)
- If no resources: show `*No external resources for this module.*`

**Important:** The `_embed_youtube_video_links()` function currently runs on the entire body. After the refactor, it should ONLY run on the lesson content (Tab 1), since resource YouTube videos are already rendered as `<YouTubeVideo>` by `format_resources_for_mdx()`.

### Step 6: Handle edge case — modules with no activities/vocab

Some modules (especially early A1, checkpoints, exams) may lack activities or vocabulary. Each tab should gracefully handle empty content with an italic placeholder rather than an empty tab.

## Files to Modify

1. **`scripts/generate_mdx.py`** — restructure `generate_mdx()` output assembly
   - Add Tabs/TabItem import
   - Build 4 separate content blocks instead of linear append
   - Wrap in `<Tabs>` / `<TabItem>` structure
   - Adjust `_embed_youtube_video_links()` scope to lesson content only

No new components needed — Starlight's built-in Tabs/TabItem handle everything.

## Verification

1. **Regenerate a1-01 MDX:** `.venv/bin/python scripts/generate_mdx.py l2-uk-en a1 1`
2. **Check MDX structure:** Verify `<Tabs>` wraps 4 `<TabItem>` blocks
3. **Visual check:** Run `npm run dev:starlight` and navigate to a1/the-cyrillic-code-i — verify:
   - 4 tabs visible
   - Lesson tab has prose + inline pronunciation videos
   - Vocabulary tab has the word table
   - Activities tab has interactive components
   - Resources tab has external links + YouTube embeds
4. **Tab sync:** Click Activities tab, navigate to another module, verify Activities tab is still selected
5. **Empty handling:** Check a module with no activities/vocab — verify placeholder text appears

## Future Iteration (Not This PR)

- **Grammar Reference tab**: Add grammar paradigm tables extracted from lesson content
- **Rename "Vocabulary" → "Reference"** and include both vocab + grammar
- **Sticky tab bar**: Keep tabs visible when scrolling within a tab (CSS position: sticky)
