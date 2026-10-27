# `ukrainian` review profile

For every change to learner-facing Ukrainian (lessons, modules, plans, practice decks, word
cards, dataset rows). What blocks, reporting by class and evidence stay in
`agents_extensions/shared/rules/ukrainian-linguistics.md` §8; budget and ledger stay in
[policy](policy.md). Operator-approved plan, 2026-10-27 (tracker C-2811).

## Seats

- **Two independent reviewers from two different families, neither in the author's family.**
  Each reviews the same exact head from the same frozen brief without the other's findings.
- Author Anthropic or any other family: Gemini (AGY) + Sol. Author OpenAI: Gemini (AGY) +
  Grok 4.7 (Cursor). Author Google: Sol + Grok 4.7 (Cursor).
- Opus 5.5 substitutes for one seat when the author is not Anthropic; note the substitution.
  Muse is advisory only, never a seat, until it can call the Sources tools.
- `closeout_cli resolve-reviewer` refuses content profiles, so these pairs are the seat source.
  Dispatch each seat with `--review-profile ukrainian`. The recorder admits only Claude, GPT
  and Gemini seats for this profile, so record those verdicts; a Grok verdict goes in the ledger.

## Findings

- A finding changes content only after a Sources MCP / VESUM check confirms it, chosen by
  facet (§4) and cited in the ledger. A finding without a tool check is advisory only: the
  driver runs the check first; a blocker no tool can settle keeps the review INCONCLUSIVE (§8).
- Measured on 27 tool-verified planted errors plus 2 clean passages (CTO grading 2026-10-27):
  Gemini 27/27 (1 disputed), Sol 25, Grok 25, Opus 25 (8 unverified), Muse 26 (all 29 of its
  findings unverified). One small set, to be replicated before the pairs change.
