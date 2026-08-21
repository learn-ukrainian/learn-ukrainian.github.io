# Phase 3 Cycle 007 Ukrainian source-authority review brief v1

Review only the exact bytes of
`batch_state/phase3-cycle007-source-grounded-amendment-v1.md`. Do not inspect
private packets, prompts, labels, provider outputs, account data, or raw logs.

Lead with failure modes. Verify the proposed source hierarchy against the
repository's Ukrainian-linguistics and Sources MCP rules. In particular check:

1. VESUM absence is escalation, never condemnation.
2. Russian-shadow is suspicion only, never an authority.
3. Антоненко-Давидович and heritage sources are used for their proper roles.
   UA-GEC is paired with the partly indexed style guide so modern calques are
   not silently missed.
4. Within this Phase 3 evaluation, the frozen Pravopys 2026 edition remains
   the sole current normative authority. Verify that claim against the public
   text-free receipt
   `data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json`
   and the official-decision-locator requirement in
   `data/projects/open_model_data/contracts/phase3_source_universe_freeze_v1.schema.json`;
   do not reject the task-specific source identity merely because the general
   Sources MCP `query_pravopys` tool currently exposes 2019. Its 2019 output is
   comparison-only for this evaluation, and textbook/corpus occurrence cannot
   masquerade as a current normative rule.
5. Evidence IDs and abstention rules actually prevent source-free positive
   decisions.
6. The risk-triggered full review and 600-row consensus audit are strong enough
   to detect shared Gemini/Grok Russianism or Surzhyk errors.
7. Public canaries test semantic Ukrainian behavior, not tool configuration or
   JSON transport alone.

Return the amendment SHA-256, `APPROVE` or `REQUEST_CHANGES`, numbered findings
with severity, and concrete corrections. This is prompt/contract review, not
the later exact-head implementation or cross-family PR review.
