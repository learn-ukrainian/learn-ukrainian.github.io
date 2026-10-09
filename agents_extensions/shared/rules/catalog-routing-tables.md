# Catalog routing tables

Generated from `scripts/config/model_catalog.yaml`; do not edit the tables.
Regenerate with the task-prescribed interpreter:

```bash
.venv/bin/python -m agents_extensions.shared.skills.drive-epic.scripts.render_catalog_tables --write
```

These are candidate identities and order, not permission or health evidence.
The reviewer resolver still applies author-family, subject-seat, risk, runtime
attestation, capability, data-egress and live-health gates before selection.
Excluded candidates can appear in a ladder; membership never grants admission.

## Driver seats

| seat | model_id | effort | escalate_model_id | escalate_effort |
| --- | --- | --- | --- | --- |
| agy | gemini-3.8-flash-high | high | gemini-3.8-flash-high | high |
| claude | claude-opus-5-5 | high | gpt-6.1-sol | high |
| codex | gpt-6.1-sol | high | gpt-6.1-sol | high |
| cursor | grok-4.7 | high | gpt-6.1-sol | high |
| grok | grok-4.7 | high | grok-4.7 | high |

## Review ladders

Rank follows the catalog; entries at the same rank are peers.

| risk | rank | candidate | model_id |
| --- | --- | --- | --- |
| critical | 1 | openai_frontier | gpt-6.1-sol |
| critical | 2 | claude-opus-5-5 | claude-opus-5-5 |
| critical | 3 | grok-4.7 | grok-4.7 |
| critical | 4 | grok-4.7-cursor-fallback | grok-4.7 |
| critical | 5 | claude-opus-5-5-cursor-fallback | claude-opus-5-5 |
| critical | 6 | composer-2.5 | composer-2.5 |
| critical | 7 | pool | poolside/laguna-s-2.1 |
| critical | 8 | pool-xs | poolside/laguna-xs-2.1 |
| high | 1 | openai_frontier | gpt-6.1-sol |
| high | 2 | claude-opus-5-5 | claude-opus-5-5 |
| high | 3 | grok-4.7 | grok-4.7 |
| high | 4 | grok-4.7-cursor-fallback | grok-4.7 |
| high | 5 | claude-opus-5-5-cursor-fallback | claude-opus-5-5 |
| medium | 1 | openai_frontier | gpt-6.1-sol |
| medium | 2 | claude-opus-5-5 | claude-opus-5-5 |
| medium | 3 | grok-4.7 | grok-4.7 |
| medium | 4 | grok-4.7-cursor-fallback | grok-4.7 |
| medium | 5 | claude-opus-5-5-cursor-fallback | claude-opus-5-5 |
| medium | 6 | claude-sonnet-5-5 | claude-sonnet-5-5 |
| medium | 7 | composer-2.5 | composer-2.5 |
| medium | 8 | gemini-3.8-flash-high | gemini-3.8-flash-high |
| medium | 9 | pool | poolside/laguna-s-2.1 |
| medium | 10 | pool-xs | poolside/laguna-xs-2.1 |
| low | 1 | openai_frontier | gpt-6.1-sol |
| low | 2 | claude-opus-5-5 | claude-opus-5-5 |
| low | 3 | grok-4.7 | grok-4.7 |
| low | 4 | grok-4.7-cursor-fallback | grok-4.7 |
| low | 5 | claude-opus-5-5-cursor-fallback | claude-opus-5-5 |
| low | 6 | claude-sonnet-5-5 | claude-sonnet-5-5 |
| low | 7 | composer-2.5 | composer-2.5 |
| low | 8 | gemini-3.8-flash-high | gemini-3.8-flash-high |
| low | 9 | pool | poolside/laguna-s-2.1 |
| low | 10 | pool-xs | poolside/laguna-xs-2.1 |
