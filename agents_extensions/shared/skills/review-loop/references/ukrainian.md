# `ukrainian` review profile

For every change to learner-facing Ukrainian (lessons, modules, plans, practice decks, word
cards, dataset rows). What blocks, reporting by class and evidence stay in
`agents_extensions/shared/rules/ukrainian-linguistics.md` §8; budget and ledger stay in
[policy](policy.md). Operator-approved plan, 2026-10-27 (tracker C-2811).

## Seats

- **Reviewers are independent and outside the author's family.**
  Each named seat reviews the same exact head from the same frozen brief without another seat's findings.

| Author | Seats |
| --- | --- |
| Anthropic, or any author outside OpenAI and Google | Gemini (AGY) + Sol |
| OpenAI | Gemini (AGY) |
| Google | Sol |

- No Claude seat for any author.
- Every seat keeps the Sources tools and the exact-head recording rule.
- A reply too long for one answer is split into chunks of at most 250 answer rows, never splitting an activity. The seat's verdict is the union of the chunks, checked by the unchanged comparator over every row.
- Grok is not a language seat. Native Grok dispatch is retired. Cursor `grok-4.7-high`
  stays off language seats (`model-assignment.md`, Grok language routing;
  `scripts/config/model_catalog.yaml` review profiles). Admitting Grok via Cursor for Ukrainian needs a
  separate catalog change backed by the measurement below (Grok 25/27, Sources tools
  reachable).
  Muse is advisory only, never a seat, until it can call the Sources tools.
- `closeout_cli resolve-reviewer` refuses content profiles, so this table is the seat source.
  Dispatch each seat with `--review-profile ukrainian` and record each verdict.

## Findings

- A finding changes content only after a Sources MCP / VESUM check confirms it, chosen by
  facet (§4) and cited in the ledger. An alleged blocker without a tool check stays blocking:
  the review is INCONCLUSIVE (`BLOCKED`, §8) until a tool check confirms or refutes it, and no
  content changes before that check. Only an unverified non-blocking note is advisory.
- Measured on 27 tool-verified planted errors plus 2 clean passages (CTO grading 2026-10-27):
  Gemini 27/27 (1 disputed), Sol 25, Grok 25 (Sources tools reachable), Opus 25 (8
  unverified), Muse 26 (all 29 of its findings unverified). One small set, to be replicated before the pairs change.
