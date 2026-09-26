# TypeSafe Jev — fleet best practice

**Audience:** every local agent (Cursor, Claude, Codex/Astra, AGY, Kimi, …)
**Skill:** `agents_extensions/shared/skills/typesafe-ai/SKILL.md`
**Upstream docs:** [llms.txt](https://docs.typesafe.ai/llms.txt) (live SSOT for API/SDK)
**Model:** `jev-latest` (resolved e.g. `jev-1.13.0`)
**Endpoint:** `POST https://api.typesafe.ai/v1/systemone`

Jev is a **System One** decision model: you send `state` + typed questions; you get
Choice / Score / Noul answers with probabilities (and confidence where applicable).
**Code owns the workflow.** Prefer Jev over a full generative LLM whenever the need
is a snap judgment, not long-form writing.

Operator posture (2026-09-17): **experiment freely.** Use Jev wherever a structured
judgment helps — including Cyrillic / Ukrainian **word qualification and labeling**.

---

## 1. Session setup

```bash
export TYPESAFE_API_KEY="$(tr -d '\r\n' < ~/.secrets/typesafe-ai.key)"
```

- Host path is `~/.secrets/typesafe-ai.key`.
- Never commit, paste, or log the key.
- Optional: `pip install typesafe-sdk` and `TypeSafeClient()` (reads the same env).
- Stdlib is enough: `urllib` POST JSON to `/v1/systemone`.

Smoke (expect ~1s):

```bash
curl -sS -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"state":"ping","model":"jev-latest","questions":{"ok":{"type":"noul","instructions":"Is this a connectivity check?"}}}'
```

---

## 2. Mental model (read this once)

| Primitive | Question shape | You get | Use for |
| --- | --- | --- | --- |
| **Choice** | Which of these options? | `choice`, `probabilities`, `confidence` | Routing, buckets, closed labels |
| **Score** | Where on this ordered spectrum? | `score`, `legend`, `probabilities`, `confidence` | Priority, severity, quality bands |
| **Noul** | Is this true? (P(yes)) | `noul` ∈ [0,1] | Gates, flags (no separate confidence) |

Rules of thumb from upstream:

1. **One snap judgment per question** — “OCR-garbage?” not “analyze this word and decide everything.”
2. **Batch** every question that shares the same `state` in **one** request (speculative fan-out). Parallel questions are cheap; one-question-per-call is the anti-pattern.
3. **Compose in code** — weights, thresholds, “if A then ignore B.”
4. **Second request only** when you need the first answer to *fetch* new state or build new options.
5. Prefer **JSON `state`** and backtick paths in instructions (`` `words[0].form` ``).

**Confidence:** Choice/Score `confidence` = how peaked the distribution is (act vs escalate).
Noul near **0.5** means uncertain yes/no — **not** “medium intensity.”

---

## 3. Where this fleet should use Jev

### 3.1 Cyrillic / Ukrainian word qualify & label (high value)

Batch forms with context; label in one call:

- `modern_uk_lemma_candidate` / `proper_name` / `dialect_or_regional`
- `russian_or_surzhyk_suspect` / `ocr_garbage` / `needs_human`
- Plus Noul/Score: eligible?, annotation priority

Then **code** routes: auto-keep, quarantine, human queue.
When you later need **attested** lemma/stress/paradigm as *fact*, call VESUM /
`sources` MCP — Jev labels first; dictionary verifies.

Live shape that worked on this host: five words → five Choices + one batch Noul,
~1400 input / ~450 output tokens, sub-second.

### 3.2 open-model-data (#7423) row / chunk gates

Same pattern at row level: rights-eligible?, OCR-suspect?, historical bucket?,
STEM admit?, priority Score. Never rewrite human Ukrainian — only classify/route.

### 3.3 Pre-dispatch / lane triage

Before expensive `delegate.py` seats: stream/lane Choice, effort Score, “needs CF?”
Noul. High confidence → cheap seat; low confidence → Fable/Astra/human.

### 3.4 PR / CF packet triage

Docs-only?, blocking vs nit?, evidence-missing?, scope-creep? → fewer review loops.

`scripts/delegate.py dispatch --preflight-triage` is the pre-dispatch hook (#8183): it triages the
candidate diff plus a bounded local test log before spawning a seat and exits 3 on a confident
`broken_or_failing` verdict (missing key / API failure skips). It reuses the CI primitives; the
`typesafe_pr_triage` CI job remains the advisory Gate job once a PR exists. Neither is CF or merge authority.

### 3.5 RAG / review / skills

Citation supported?; pick at most one skill from a closed catalog. (Note: earlier experimental passage gate and reranker modules were removed in #8525 due to unsafe failure modes and policy forbidding Jev from evaluating Ukrainian language phenomena.)

Skill suggestion pipeline (#8201, parent #6943):
- CLI: `.venv/bin/python -m scripts.typesafe.skill_suggestion --turn '...'`
- Module: `scripts/typesafe/skill_suggestion.py` (`suggest_skill`, `suggestion_block`)
- Cookbook: https://docs.typesafe.ai/cookbooks/skill_suggestion.md
- Two batched `system_one` calls (rank catalog + Noul `needs_skill`, then verify top-3); 0-or-1 skill name; **advisory only**
- Issue #8201 (parent #6943)
- Tests: `tests/typesafe/test_skill_suggestion.py` (`TYPESAFE_LIVE=1` for live)

Citation and source-grounding verifier (#8192, parent #4913):

- CLI: `.venv/bin/python -m scripts.audit.typesafe_citation_verifier --input cases.jsonl --out receipt.json`
- Module: `scripts/audit/typesafe_citation_verifier.py`. Stage 1 is a deterministic quote match (a miss is `fabricated`, and the model is not called). Stage 2 is one Choice (`supports` / `contradicts` / `says_nothing`) on the source passage versus the claim.
- Routing stays in code: only `supports` at confidence ≥ 0.80 is an accept (`verified`); `contradicts` at any confidence is `contradicted`; `says_nothing` at ≥ 0.80 is `unsupported`; API failure, a malformed answer, or anything less confident is `needs_human_review`.
- Client: `scripts/typesafe/client.py`. Tests: `tests/audit/test_typesafe_citation_verifier.py` (`TYPESAFE_LIVE=1` for the live smoke).

### 3.6 Anywhere you’d prompt-and-parse

If the generative model would return a single enum, score, or yes/no — use Jev.

---

## 4. Confidence-gated routing (pattern)

```text
answer  = what to do
confidence / noul = whether to trust it automatically
```

Example policy (tune on *our* data; cookbook numbers are not gospel):

| Stakes | Rule of thumb |
| --- | --- |
| Low (bucket label, keep/drop junk) | Act if Choice conf ≥ ~0.7 or Noul ≥ 0.8 / ≤ 0.2 |
| Medium (dispatch lane) | Act if conf ≥ ~0.75; else ask a language-lane LLM |
| High (delete source, publish, merge-affecting) | Require very high conf **or** human/CF |

Escalate uncertain Noul (~0.4–0.6) and low-confidence Choices on purpose.

---

## 5. Question design checklist

- [ ] Instructions are a **clear judgment**, complete without relying on the question id
- [ ] Choice criteria cover reality — include `other` / `needs_human` / `reject` when needed
- [ ] Score levels are **concrete situations**, ordered, stand alone
- [ ] Noul defines yes clearly (“Does X hold?”) — not vague “is it good?”
- [ ] State has enough context (form + surrounding sentence / rights claim / PR summary)
- [ ] Independent questions share one request; dependent fetches use a second call
- [ ] Thresholds and weights live in **code**, not in the prompt

Bad: one mega-prompt asking Jev to “handle the dataset.”
Good: eight narrow questions + a 20-line router.

---

## 6. Hard rails (only these)

1. **Never** commit or paste `TYPESAFE_API_KEY`.
2. **Do not** treat Jev as a replacement for VESUM/`sources` when you need attested
   morphology/stress as fact (labeling is fine and encouraged).
3. **Do not** rewrite or impersonate human-authored Ukrainian source text in
   dataset pipelines — label and route.
4. **Do not** replace Fleet Comms, Monitor leases, formal cross-family review, or
   merge gates with a Jev score.

Everything else: explore, measure, keep what works.

---

## 7. Receipts & hygiene

On each call, retain (safe to log):

- `model` id returned
- question ids
- `usage.input_tokens` / `usage.output_tokens`
- answers + confidence/noul

Do **not** log the bearer token or full secret paths in public artifacts.

---

## 8. Anti-patterns

| Anti-pattern | Do instead |
| --- | --- |
| One question per HTTP call | Fan-out many questions per `state` |
| Free-text “JSON please” from a big LLM | Choice/Score/Noul |
| Using Noul 0.5 as “medium quality” | Score with defined levels |
| Asking Jev for full stress paradigms as truth | Label, then VESUM verify |
| Hand-editing `.claude/skills/` TypeSafe copies | Edit `agents_extensions/…`, `npm run agents:deploy` |
| Blocking all use behind a single pilot | Experiment; tighten thresholds with evidence |

---

## 9. Minimal Python sketch

```python
import json, os, urllib.request
from pathlib import Path

def api_key() -> str:
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    path = Path.home() / ".secrets" / "typesafe-ai.key"
    return path.read_text(encoding="utf-8").splitlines()[0].strip()

def system_one(state, questions, model="jev-latest", timeout=60):
    body = json.dumps({"state": state, "model": model, "questions": questions}).encode()
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)
```

Fleet CLIs should call `scripts/typesafe/client.py` (`load_typesafe_api_key`, `system_one`) rather than copying this snippet.

---

## 10. Related

- Skill suggestion: `scripts/typesafe/skill_suggestion.py` (#8201)
- Skill + overlay: `agents_extensions/shared/skills/typesafe-ai/`
- Upstream: [System One](https://docs.typesafe.ai/concepts/system-one.md),
  [primitives](https://docs.typesafe.ai/primitives.md),
  [confidence routing](https://docs.typesafe.ai/patterns/confidence-routing.md),
  [fan-out](https://docs.typesafe.ai/patterns/fan-out.md),
  [cookbooks index](https://docs.typesafe.ai/llms.txt)
- Deterministic-over-hallucination culture:
  [`deterministic-over-hallucination.md`](deterministic-over-hallucination.md)
  (Jev for judgments; attested sources for language facts)
