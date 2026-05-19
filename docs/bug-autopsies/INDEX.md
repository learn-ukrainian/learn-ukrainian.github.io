# Bug Autopsy Index

One-liner per bug. Grep for symptoms or categories to find relevant detail files.

<!-- INDEX-START -->
| Date | Issue | Category | Summary |
|------|-------|----------|---------|
| 2026-04-05 | #1150 | score-parsing | Wiki review loop stuck at 8/10 — regex `(\d+)` can't match decimal scores like `8.8/10` |
| 2026-04-08 | — | mdx-parse | `re.sub` unescapes `\n` in JSX replacement strings → acorn parse failure on 39 A2 MDX files |
| 2026-04-08 | — | mdx-parse | Missing blank lines before HTML blocks → MDX parses `<div>` as inline, breaks `<TabItem>` nesting |
| 2026-04-08 | — | mdx-parse | LLM writer artifacts (stray ` ``` `, `<!-- -->`, bare `<br>`) break MDX parser |
| 2026-04-23 | #1431 | prompt-sync | Writer vs reviewer calibration drift on immersion/engagement/dialogue/plan — fixed via shared contract `scripts/build/contracts/module-contract.md` referenced by both sides |
| 2026-04-23 | EPIC | alignment-contracts | Sidecar cache reuse without hash check (`v6_build.py:3207`) — stale contract.yaml/wiki-excerpts.yaml silently consumed after plan/template/tokenizer change |
| 2026-04-23 | EPIC | alignment-contracts | `module_memory` sources_hash updated silently — corpus/rule changes land but old learned constraints persist (`module_memory.py:293-316`) |
| 2026-04-23 | EPIC | alignment-contracts | Rule-after-incident governance pattern — rules added post-incident are advisory, not CI-enforced; live contradiction between "no-rewrite" decision and `convergence_loop.py` rewrite strategies |
| 2026-05-05 | #1683 | agent-hallucination | Gemini fabricates verbatim Антоненко-Давидович quote flagging feminine «собака» as Russianism — reproducible across two threads same day, false per VESUM + АД corpus check + СУМ-11 «ч. і рідше ж.» + Мирний 1949 attestation |
| 2026-05-08 | #1808 | agent-comms | `ab discuss` rounds 2+ silently dropped peer round-1 replies — `build_agent_prompt` pulled channel-wide tail instead of thread-scoped, budget truncator evicted in-thread messages on noisy channels. Fix: `thread_id` parameter + drop monitor/context first when in thread mode (commit 83d08a9604). Detail in `agent-comms.md`. |
| 2026-05-10 | — | secret-leakage | Claude grepped `~/.bash_secrets` for `GEMINI_API_KEY` and printed the matched line in cleartext — value `AIza...` leaked to transcript. User had to rotate. Root: `grep` output included the full line including the value; the same command had `sed 's/=.*/=<REDACTED>/'` applied to `env` output but not file-grep output (inconsistent sanitization). Detail in `secret-leakage.md`. |
| 2026-05-12 | — | secret-leakage | Claude probed `DAGGER_CLOUD_TOKEN` via `env \| grep -i DAGGER \| grep -v -i secret` — substring-name filter is theater because real credential variables don't contain "secret" in their name. Token value `dag_graphtrek_...` leaked. Same conceptual failure as 2026-05-10 (file-only sanitization rule didn't extend to live env). Detail in `secret-leakage.md`. |
| 2026-05-19 | — | secret-leakage | Claude inspected `~/.codex/auth.json` (JSON) using `head -5 \| sed 's/=.*/=<REDACTED>/'` — the shell `KEY=VALUE` redactor is a no-op on JSON `"key": "value"` content. JWT `id_token` leaked to transcript. Third recurrence of the same conceptual failure (sanitizer for one format silently degrades on another). User must rotate Codex auth. Detail in `secret-leakage.md`. |
<!-- INDEX-END -->
