---
id: R-VOICE-META
description: Adult peer voice; no English meta-narration or teacherly transitions in module.md.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

Adult peer voice only. No English meta-narration or teacherly transitions in `module.md`. The `engagement_floor` gate HARD-fails on phrases that describe the artifact rather than addressing the learner. Forbidden patterns (English): "Welcome to the start of our journey", "In this section we will learn", "in this module", "in this lesson", "this module covers", "this lesson covers", "we will learn", "you will learn" (in the meta sense, not a real plan), "Now that you have seen these verbs", "Let's now look at", "Before we move on", "Note that…", "Notice that…", "Observe that…", "Pay attention to…", "Remember that…", "It is important to…". Forbidden patterns (Ukrainian): "у цьому модулі", "у цьому уроці", "у цьому розділі", "у цій темі", "ми вивчимо", "ми побачимо", "далі ми…". Rule of thumb: speak TO the learner in second person about the LANGUAGE; never narrate ABOUT the module or section. Open every section with a fact, an example, a dialogue line, or a direct second-person instruction — never with a preamble about what the section will do.

B1+ body text outside Tab 2 is Ukrainian only: no rescue notes, mirrored translations, parenthetical English grammar glosses, or English activity instructions. Tab 2 may carry English translations and expression notes.

Activities test Ukrainian, not content recall. Pure language mechanics are fine; trivia such as "У якому році Хмельницький підписав Переяславську угоду?" is not.

**Engagement floor.** Emit at least 1 content-anchored callout (`:::tip`, `:::note`, `:::caution`, `:::warning`, `[!myth-buster]`, `[!history-bite]`). It must contain a mnemonic, myth-bust, cultural note, or common-mistake reminder. Empty filler does not count. Meta-narration hits fail `engagement_floor` immediately.
