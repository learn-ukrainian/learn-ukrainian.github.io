# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}, {PHASE}).

**Word target: {WORD_TARGET} words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
{PLAN_CONTENT}
</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Skim these for content ideas. Reference specific examples you plan to use.

<knowledge_packet>
{KNOWLEDGE_PACKET}
</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- Exercise: [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
...

## {SUMMARY_HEADING} (~150 words)
- P1 (~150 words): [recap key concepts, encourage practice]

Grand total: ~{WORD_TARGET} words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to {WORD_TARGET}+.** Aim for ~10% overshoot ({WORD_OVERSHOOT} words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Spread exercises evenly.** Place one after each key teaching point, matching the plan's `activity_hints`.
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
