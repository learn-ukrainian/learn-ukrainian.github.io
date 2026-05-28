# Cursor consultation — V7.1 vs V8 wiki-driven writer + scaling to B1+/seminars/activities

## Context (read before answering)

Codex + Gemini already converged on V8 (new renderer phase) via 2 rounds on this channel — full transcript at `audit/2026-05-27-wiki-driven-pivot-discussion/transcript.md`. User has now pushed back: **V7.1 (adjust the existing `linear-write.md` + add wiki-vocab-bound gate) likely makes more sense** because the V7 prompt already says "wiki is LESSON SOURCE" (`linear-write.md:158,184`) — the failure isn't absence of that idea, it's that the 17 `#R-` rules crowd it out. V7.1 = ~1-2 days of prompt trimming + new gate. V8 = ~2 weeks of new pipeline plumbing. Material end-state is similar (LLM reads a prompt that says "render the wiki, don't invent").

You (cursor) were integrated as a writer option 2026-05-24 (cursor-tools). The previous discussion didn't include you. We want your take before locking the direction.

## Three constraints the previous discussion didn't surface

The user just named these explicitly. The V7.1 (or V8) approach MUST scale to:

1. **B1+ content** — body text is 100% Ukrainian (no English explanations). So "voice rewrite" no longer translates language; it's methodological-UK → teacher-UK register shift only. Does this change the wiki-vocab-bound gate? Cumulative learner state at B2 is ~3000 lemmas; A1 is ~200. The allowlist gets less restrictive but the wiki still bounds new vocab introduction.

2. **Seminar tracks in full Ukrainian** (HIST, BIO, ISTORIO, LIT, OES, RUTH) — content is denser, more contested (historical facts, biographies, dates, sources). Wiki references textbook RAG chunks AND external articles. The verification surface is bigger (`verify_quote`, `verify_source_attribution`, `search_literary`). Does wiki-renderer architecture hold up when the wiki ITSELF is a research output from RAG + external + Wikipedia (not a hand-curated SLOB)?

3. **Activities** (activities.yaml emission, not just module.md) — fill-in, MCQ, error-correction, contrast-pair items. Wiki names exercise formats (Вправа 1, 2, ...) but not concrete items. The LLM still composes activity items. Vocab allowlist applies. Does the renderer framing work for activity generation, or does activity emission need its own constraint set?

## Questions for cursor

1. **V7.1 vs V8**: which would YOU choose, given the difference is mostly prompt-file structure not pipeline plumbing? Defend your pick.

2. **The "crowded failure surface" claim**: Codex argued V7.1 inherits V7's overload of 17 #R- rules competing for attention. Is that an architecture problem (need new prompt file) or a writing problem (need to delete redundant rules)? If the latter, V7.1 with aggressive prompt trimming = same outcome as V8.

3. **B1+ scaling**: does the wiki-vocab-bound gate work when cumulative learner state is 3000+ lemmas? Or does the gate become a no-op at higher levels and shift back to ad-hoc invention?

4. **Seminar scaling**: at HIST/BIO/LIT/etc., the wiki is itself an LLM-generated research artifact citing textbook RAG + external articles + Wikipedia. Treating wiki as "source of truth" risks laundering hallucination upstream. What additional verification does seminar content need that the A1 case didn't?

5. **Activities**: the wiki-renderer framing was discussed mostly for module.md prose. activities.yaml emission isn't pure rendering — the LLM composes concrete fill-in/MCQ items. Does the architecture need a different rule cluster for activities, or does the same vocab-allowlist gate cover it?

6. **Cursor-specific perspective**: your CLI behavior under tool-call-heavy prompts, your MCP integration story, your token budget. Anything we'd be wrong about if we assume cursor behaves like codex-tools or gemini-tools?

7. **Blind spots**: what do you see that codex + gemini missed in their round-1/2 discussion? Especially anything about the B1+/seminars/activities cases that didn't come up.

This is round 1. Don't propose code. Position only, with concrete defenses. Max 1 round.
