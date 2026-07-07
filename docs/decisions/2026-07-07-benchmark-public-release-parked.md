# ACCEPTED — Public benchmark release (epic #4639) PARKED; deploy-first

**Status:** ACCEPTED
**Decided on:** 2026-07-07 (user decision, recorded same day)
**Scope:** The community-release track of the Ukrainian LLM factuality benchmark
(#2156 → epic #4639): freeze → external validation → packaging → upstream outreach.
**Review trigger:** Hramatka ships to its first teacher pilot, OR a community
signal arrives (reply on the lang-uk outreach thread / UNLP interest), OR
2026-10-05 — whichever comes first.

## Decision

The public release of the factuality benchmark is **parked**. The user's call
(2026-07-07): the release has no demonstrated audience yet ("probably no one
will care"), and the driver concurred on the evidence — no external signal,
no reply pressure, and the internal value of the harness does not depend on
publication. Effort moves to **deploy-first**: run the tooled QG gate over our
own built modules (#4764, after the #4761/#4762/#4763 engine measurement) and
build Hramatka v1 as a homework-first teacher tool (#4542).

### Parked with the release (all release-only work)

| Item | What it was | Disposition |
| --- | --- | --- |
| #4638 | lang-uk leaderboard outreach (USER-GATED) | closed: parked |
| #4632 | native-expert validation of v1 trap ground-truth (USER-GATED) | closed: parked |
| #4647 | OpenCode Go as deepseek transport (optional; deepseek-direct #4730 already shipped the flake fix) | closed: parked |
| #4312 | UNLP 2027 documentation/results track | closed: parked |
| #4742 classes A/B/D | REPLACE-list re-authoring (release-only rights hygiene; Class C shipped via #4751, list 63→41) | annotated: parked scope |
| Freeze (spec F3 final matrix + `freeze_benchmark` tag) | release precondition | parked with the epic |
| #4541 packaging children | OSS extraction | parked under epic #4639 |

Epic #4639 stays OPEN as the parking record, annotated with this decision.

### Explicitly NOT parked

- **#4761 / #4762 / #4763** — the tooled-seat measurement (decides which engine
  runs the LU content quality gate). Cursor drives #4761; gpt/claude seats are
  capacity-gated (Jul 12 / Jul 13 resets).
- **#4764** — the production llm_qg sweep over built modules (engine from the
  measurement; canary two-greens + E0 user arming first).
- **Hramatka (#4542)** — homework-first pilot; HF-infra design doc.
- The harness, fixtures, scorer, and gates themselves — they are production
  tooling for our own content regardless of publication.

## Reasoning

Publication was always the secondary payoff; the primary one is a load-bearing
factuality gate over our own curriculum and the teacher service. The
release-only work (external validation, packaging, outreach, rights
re-authoring for redistribution) costs real driver + fleet capacity that the
deploy-first plan needs. Parking is reversible: the freeze spec
(`.agent/tmp/design-4626-freeze-and-split.md` v2, machinery on main), the
rights resolver (#4684/#4739, 0 UNKNOWN), and the multirun scorecard evidence
(#4715/#4726) all survive on main/issues, so un-parking is a resume, not a
rebuild.

## Alternatives considered

- **Release anyway on the current evidence** — rejected: no demonstrated
  audience; capacity is the scarce resource this week (claude 2.5×/codex 2.1×
  over weekly pace), and the deploy-first work is user-priority.
- **Kill the release track outright (close epic #4639 too)** — rejected:
  triggers are plausible (Hramatka shipping is itself the strongest release
  argument); keep the epic as the parking record.

Refs: #4639 #4638 #4632 #4647 #4312 #4742 #4541 #4751 #2156. Journal entry: dec-009.
