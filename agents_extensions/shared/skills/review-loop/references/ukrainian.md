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
- A reply too long for one answer is split into chunks of at most 250 answer rows, never splitting an activity. The seat's verdict is the union of its chunks. Further chunks of a head that was already dispatched open no new budget round.
- When the brief declares an item denominator, build each chunk with `split_item_chunks` and `build_item_packet` (`scripts.review.review_contract`) and put `render_item_packet` in the brief. That packet is the per-item literal table, character offsets, pointers, state counts and coverage set. The reviewer returns only a `ukrainian-item-judgments` block: for each tool-issued id, a verdict, a finding and Sources evidence. The recorder stores that coverage and the denominator on the verdict. A span presented as a quote of the frozen item, including a quoted span in the finding, the Sources evidence or the reply, must be a literal substring of that item, or an approval of the chunk is void (`quote-mismatch`) and its coverage does not count. Only a Ukrainian-profile chunk adds coverage toward a seat. Offsets, counts, pointers, tables or a coverage set in the reply void the chunk (`reviewer-bookkeeping`) and do not count. The gate approves the head only when every required seat's recorded APPROVE coverage equals the denominator and no non-void rejection is recorded at that head. A review with no item denominator is unchanged.
- Grok is not a language seat. Native Grok dispatch is retired. Cursor `grok-4.7-high`
  stays off language seats (`model-assignment.md`, Grok language routing;
  `scripts/config/model_catalog.yaml` review profiles). Admitting Grok via Cursor for Ukrainian needs a
  separate catalog change backed by the measurement below (Grok 25/27, Sources tools
  reachable).
  Muse is advisory only, never a seat, until it can call the Sources tools.
- `closeout_cli resolve-reviewer` refuses content profiles, so this table is the seat source.
  Dispatch each seat with `--review-profile ukrainian` and record each verdict.

## Findings

- Every Ukrainian error in added or edited text blocks, with a Sources/VESUM citation. Existing §8 coverage, facet-specific verification and escalation remain unchanged. Unverified alleged blockers remain INCONCLUSIVE/BLOCKED pending verification; pedagogy findings cite their governing contract rather than requiring dictionary evidence.
- A breach of an applicable binding pedagogy contract blocks. Contracts include approved learning goals and CEFR scope; authoritative language-role and immersion rules, including A1 English scaffolding and applicable bilingual instructions; adopted ULP presentation requirements within their stated scope and adaptations; and the applicable level/track activity allowlist and placement rules. Advisory percentages and attributed observations alone are not blocking thresholds. CEFR judgments preserve expressly permitted incidental constructs. Each blocker identifies the applicable clause, affected learner-facing evidence and demonstrated contradiction; material contract ambiguity escalates.
- Wording or style choices among correct, contract-compliant alternatives stay non-blocking notes. A "nit" that is a learner-visible error is an error and blocks.
- A language-error finding changes content only after a Sources MCP / VESUM check confirms it, chosen by facet (§4) and cited in the ledger. No content changes before that check. Only an unverified non-blocking note is advisory.
- Measured on 27 tool-verified planted errors plus 2 clean passages (CTO grading 2026-10-27):
  Gemini 27/27 (1 disputed), Sol 25, Grok 25 (Sources tools reachable), Opus 25 (8
  unverified), Muse 26 (all 29 of its findings unverified). One small set, to be replicated before the pairs change.
