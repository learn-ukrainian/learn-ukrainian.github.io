# Proposal Review: Content-First Decoupled Pipeline

You are being asked for a BRUTALLY HONEST, creative, thinking-outside-the-box review of a workflow proposal. No diplomatic hedging. Say what you really think.

## Current Pipeline (per module, sequential)
Phase 0 (Research) → Phase 1 (Meta) → Phase 2 (Content) → Phase 3 (Activities+Vocab) → Phase 4 (Audit) → Phase 5 (MDX) → Phase 6 (Review) → Phase 6b (Fixes)

Each module goes through ALL phases before the next module starts.

## Proposed Change
Decouple content creation from activity generation. Work in waves:

**Wave 1:** Content-only for A1, A2, B1 (Phases 0→1→2, content audit only)
**Wave 2:** Activities for A1, A2, B1 (Phase 3, full audit with activities)
**Wave 3:** Content-only for B2, C1, C2
**Wave 4:** Activities for B2, C1, C2

The site would show content-only modules during the gap (theoretical content, no exercises).

## Arguments FOR:
- Activities depend on content but never feed back (one-way dependency)
- Phase 3 schema failures currently block modules with perfect content
- Batching similar work reduces context switching
- Activity generation in a separate session reads the ACTUAL content file, not what Gemini intended to write (reduces self-contamination)

## Arguments AGAINST (identified so far):
- Audit pipeline assumes both content + activities exist
- Vocabulary might belong with content, not activities

## Your Task
1. Is this a good idea? Be brutally honest.
2. What risks/problems are we NOT seeing?
3. Would YOU (as Gemini, the builder) produce better or worse output in this model?
4. Any creative counter-proposals? Think outside the box.

Post your response as a comment on GitHub issue #574.
