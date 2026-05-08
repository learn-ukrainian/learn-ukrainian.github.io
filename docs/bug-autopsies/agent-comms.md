# Agent Communication Bugs

## #1808 — `ab discuss` peer-reply dropout (2026-05-08)

### Symptom

Multi-round `ab discuss` agents reported "I see only the root question and my own round-1 reply — no peer replies attached." Convergence checks falsely failed because no agent could read what the others had said. Hit consistently across rounds 2 and 3 of any discussion in a noisy channel (`pipeline`, `architecture`, `reviews`).

### Root cause

In `scripts/ai_agent_bridge/_channels.py`, `build_agent_prompt` fetched history via `read(channel, tail=20)` — pulling the 20 most recent messages of the entire channel rather than the discussion's specific thread. On any channel with non-trivial existing traffic, those 20 messages were unrelated old posts. They consumed the `max_history_chars` budget (6000 chars by default), so `truncate_history_by_budget` evicted them. When the assembled prompt still exceeded `max_prompt_chars` (24000 chars) due to pinned channel context (which can be large), the wholesale "drop_history" fallback at lines 517-533 stripped ALL history including the discussion's own root + peer replies.

The CLI even printed `dropped 20` every round — but that was treated as a benign histogram counter, not a flag for "your discussion is silently broken."

### Why it slipped

1. `ab discuss` shipped in 2026-04-12 (#1190) when channels were empty. Worked fine at first.
2. As channels accumulated weeks of traffic, the tail truncation began silently shadowing peer replies.
3. The directive in `_handle_discuss` told agents *"Read the prior-round replies in the history above"* — but the prompt didn't actually include them. Agents that hallucinated convergence were treated as evidence the protocol worked.
4. Only Claude headless flagged the discrepancy honestly ("context still missing"). Codex and Gemini fabricated round-2 responses that referenced peer replies they never actually saw.

### Fix (commit 83d08a9604)

1. **`build_agent_prompt(thread_id: str | None = None)`** — new optional parameter. When set, calls `read(channel, thread_id=thread_id)` for the full thread (no tail bound) and skips the budget truncator on those messages.
2. **Budget-overflow precedence inverted in thread mode** — drop monitor first, then pinned context, only the thread itself as last resort. Legacy non-thread callers keep the original drop-history-first behavior.
3. **`_handle_discuss` passes `thread_id=correlation_id`** — every round fetches the in-thread history including all prior round replies.

### Verification

Regression test in `tests/test_bridge_channels.py::test_build_agent_prompt_thread_id_preserves_thread_replies_under_noisy_channel` — seeds 30 noisy non-thread messages + a 4-message thread, asserts all 3 peer replies survive in the prompt.

End-to-end: fresh 2-round discussion (thread `6fe2270d70fb`) where each agent posted a unique secret token in round 1 and listed peer tokens in round 2. All three agents read each other's tokens verbatim and converged with `[AGREE]`.

### Lesson

**The directive in the prompt is not the contract — what the agent ACTUALLY sees in its prompt is the contract.** A round directive that says "read the prior replies" while the prompt assembly silently drops them is worse than no directive at all, because the agents will hallucinate having read them.

For multi-round agent coordination: NEVER rely on a generic channel-tail read for thread history. Always thread-scope and treat in-thread messages as load-bearing — the entire reason the agent is being prompted.

### Prevention

- New regression test locks down thread-mode behavior under channel noise.
- This file documents the failure mode for future grep — when an agent reports "context missing" in a multi-round protocol, check whether history is thread-scoped before assuming the agent is misbehaving.
