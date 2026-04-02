### 🚀 Update: Checkpoint Realignment & Landing Pages Regenerated

As requested, I thoroughly investigated the B1 curriculum flow after removing the premature foundation checkpoint. 

Removing `checkpoint-b1-foundation` meant that the baseline tenses, aspect, and relationship vocabulary (M01-M03) were left untested. I have officially closed this gap:

1. **Updated `checkpoint-morphophonemics.yaml`:** I expanded the scope of the next checkpoint in the sequence (now M13) to become a comprehensive test of both Phases 1 and 2. 
    *   It now explicitly tests baseline past/present/future tenses.
    *   It tests imperfective/perfective aspect.
    *   It tests the relationship/portrait vocabulary from M03 alongside the morphophonemic topics (M04-M12).
    *   I updated all internal references from the old "M08-M16" numbering to properly point to "M01-M12".

2. **Landing Pages Regenerated:** I ran `build_landing_pages.py` and regenerated all the React `.mdx` components in Starlight to reflect the new sequence and module counts.

3. **Frontend Rebuilt:** I wiped the Vite cache and successfully executed a clean `npm run build`. The frontend is 100% updated, compiling without errors, and the B1 index properly reflects the new progression.

The curriculum is structurally sound and ready for content generation!