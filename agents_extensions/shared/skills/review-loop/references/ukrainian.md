# `ukrainian` review profile

For every change to learner-facing Ukrainian (lessons, modules, plans, practice decks, word
cards, dataset rows). What blocks, reporting by class and evidence stay in
`agents_extensions/shared/rules/ukrainian-linguistics.md` §8; budget and ledger stay in
[policy](policy.md). Operator-approved plan, 2026-10-27 (tracker C-2811).

## Seats

- **Two independent reviewers from two different families, neither in the author's family.**
  Each reviews the same exact head from the same frozen brief without the other's findings.
- Default, and for an Anthropic author: Gemini (AGY) + Sol. Author OpenAI: Gemini (AGY) +
  Opus 5.5. Author Google: Sol + Opus 5.5. Any other author: Gemini (AGY) + Sol.
- Grok is not a seat. Cursor stays off language seats (`model-assignment.md`, native Grok
  language seat), and delegate admission refuses xAI for Ukrainian
  (`UKRAINIAN_MODEL_REFUSED`, `scripts/dispatch.py`; grok-4.7 note in
  `scripts/config/model_catalog.yaml`). Admitting Grok via Cursor for Ukrainian needs a
  separate catalog change backed by the measurement below (Grok 25/27, Sources tools
  reachable).
  Muse is advisory only, never a seat, until it can call the Sources tools.
- `closeout_cli resolve-reviewer` refuses content profiles, so these pairs are the seat source.
  Dispatch each seat with `--review-profile ukrainian` and record each verdict.

## Findings

- A finding changes content only after a Sources MCP / VESUM check confirms it, chosen by
  facet (§4) and cited in the ledger. An alleged blocker without a tool check stays blocking:
  the review is INCONCLUSIVE (`BLOCKED`, §8) until a tool check confirms or refutes it, and no
  content changes before that check. Only an unverified non-blocking note is advisory.
- Measured on 27 tool-verified planted errors plus 2 clean passages (CTO grading 2026-10-27):
  Gemini 27/27 (1 disputed), Sol 25, Grok 25 (Sources tools reachable), Opus 25 (8
  unverified), Muse 26 (all 29 of its findings unverified). One small set, to be replicated before the pairs change.
