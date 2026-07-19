#!/usr/bin/env python3
"""Grok epic-lane session canary — mint / questions / score / protocol.

Purpose
-------
Auto-compact compresses **working context** (lossy for nuance). Disk logs and
session-stream dual-writes survive; the model brain does not. This CLI freezes
durable anchors at cold-start and scores recall later so we **end the session
on measured rot**, not on compact count or a guessed token budget.

Policy (operational, not production-rollover)
---------------------------------------------
- Mint **10** anchors from stream + handoff dual-write only (no git/PR scrape).
- Score with legacy ``context_canary``: ``--pass-ratio`` default **0.8** (8/10).
- FAIL-HANDOFF (rc 2) ⇒ write STATE AT HANDBACK, close stream lease, ``/quit``.
- First auto-compact is a **re-score trigger**, not an end signal by itself.
- Production identity rollover remains ``context_canary mint --snapshot`` (strict 10/10).

Paths (gitignored local; under ``.claude/<epic>-epic/canary/``)
---------------------------------------------------------------
  probe.json       frozen ground truth (do not show answers to the scorer turn)
  questions.json   id → question only (agent answers from memory)
  answers.json     agent-written answers for score
  log.csv          (context_tokens, score) time series
  last_verdict.json  latest machine verdict

Usage
-----
  .venv/bin/python -m scripts.session_canary.grok_lane mint --epic atlas
  .venv/bin/python -m scripts.session_canary.grok_lane questions
  .venv/bin/python -m scripts.session_canary.grok_lane score \\
      --answers .claude/atlas-epic/canary/answers.json \\
      --context-tokens 250000 --model grok-4.5
  .venv/bin/python -m scripts.session_canary.grok_lane protocol --epic atlas
  .venv/bin/python -m scripts.session_canary.grok_lane status --epic atlas
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Epic slug → default stream id (aligned with start-grok.sh)
EPIC_STREAM_DEFAULTS: dict[str, str] = {
    "atlas": "epic:4387",
    "practice": "epic:4387",
    "practice-hub": "epic:4387",
    "harness": "epic:4707",
    "infra": "epic:4707",
    "hramatka": "epic:4542",
    "folk": "epic:2836",
    "seminars-folk": "epic:2836",
    "bio": "epic:4431",
    "seminars-bio": "epic:4431",
}

DEFAULT_PASS_RATIO = 0.8
DEFAULT_SIM_THRESHOLD = 0.75
N_ANCHORS = 10


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canary_dir(repo: Path, epic: str) -> Path:
    return repo / ".claude" / f"{epic}-epic" / "canary"


def _handoff_candidates(repo: Path, epic: str) -> list[Path]:
    base = repo / ".claude" / f"{epic}-epic"
    return [
        base / "INTERIM-DRIVER-HANDOFF.md",
        base / "CLAUDE-DRIVER-HANDOFF.md",
        base / "CODEX-DRIVER-HANDOFF.md",
    ]


def _read_text(path: Path, limit: int = 120_000) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def _clip(text: str, max_len: int = 220) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _load_stream_entries(stream_id: str, *, limit: int = 40) -> list[dict[str, str]]:
    """Return [{type, body}, ...] from session stream; empty if store unavailable."""
    try:
        from agents_extensions.shared.session_streams.db import SessionStreamDatabase
        from agents_extensions.shared.session_streams.store import SessionStreamStore

        store = SessionStreamStore(SessionStreamDatabase())
        digest = store.load_digest(stream_id, limit=limit)
        out: list[dict[str, str]] = []
        for entry in list(digest.pinned) + list(digest.recent):
            body = (entry.body or "").strip()
            if not body:
                continue
            out.append(
                {
                    "type": getattr(entry.type, "value", str(entry.type)),
                    "body": body,
                }
            )
        return out
    except Exception as exc:
        # Fail-open to handoff-only mint when stream DB is missing/unreadable.
        print(f"warning: session stream unavailable ({type(exc).__name__}: {exc})", file=sys.stderr)
        return []


def _extract_handoff_bullets(md: str, *, heading_substrings: tuple[str, ...], limit: int = 12) -> list[str]:
    """Pull bullet lines under headings whose title contains any substring (case-insensitive)."""
    if not md:
        return []
    lines = md.splitlines()
    bullets: list[str] = []
    active = False
    for line in lines:
        if re.match(r"^#{1,4}\s+", line):
            title = re.sub(r"^#{1,4}\s+", "", line).strip().lower()
            active = any(s in title for s in heading_substrings)
            continue
        if not active:
            continue
        m = re.match(r"^\s*[-*]\s+(.+)$", line) or re.match(r"^\s*\d+\.\s+(.+)$", line)
        if m:
            item = m.group(1).strip()
            # strip markdown bold/links lightly
            item = re.sub(r"\*\*([^*]+)\*\*", r"\1", item)
            item = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", item)
            if item:
                bullets.append(item)
            if len(bullets) >= limit:
                break
    return bullets


def _build_facts(
    *,
    epic: str,
    stream_id: str,
    stream_entries: list[dict[str, str]],
    handoff_text: str,
    handoff_rel: str,
) -> list[dict[str, str]]:
    """Build exactly 10 unique {id,q,a} facts from durable sources only."""
    facts: list[dict[str, str]] = []
    used_answers: set[str] = set()

    def add(fid: str, q: str, a: str) -> None:
        a_norm = _clip(a, 280)
        if not a_norm or a_norm in used_answers:
            return
        if any(f["id"] == fid for f in facts):
            return
        used_answers.add(a_norm)
        facts.append({"id": fid, "q": q, "a": a_norm})

    # 1) Session identity (always)
    add(
        "lane-stream",
        "What session stream id is this Grok lane driving?",
        stream_id,
    )
    add(
        "lane-epic",
        "What epic slug is this Grok lane bound to?",
        epic,
    )

    # 2) Pinned binding orders from stream
    pinned_orders = [e for e in stream_entries if e["type"] == "binding_order"]
    for i, entry in enumerate(pinned_orders[:4], start=1):
        add(
            f"bind-{i}",
            f"What is binding order #{i} for this lane (plain paraphrase of the frozen stream pin)?",
            entry["body"],
        )

    # 3) Negative constraints from stream
    negs = [e for e in stream_entries if e["type"] == "negative_constraint"]
    for i, entry in enumerate(negs[:2], start=1):
        add(
            f"neg-{i}",
            f"What is negative constraint #{i} pinned on this stream?",
            entry["body"],
        )

    # 4) Next actions from stream (prefer typed next_action)
    nexts = [e for e in stream_entries if e["type"] == "next_action"]
    for i, entry in enumerate(nexts[:3], start=1):
        add(
            f"next-stream-{i}",
            f"What next-action entry #{i} was recorded on the stream?",
            entry["body"],
        )

    # 5) Handoff dual-write: next drive / in-flight / hands-off
    next_bullets = _extract_handoff_bullets(
        handoff_text,
        heading_substrings=("next drive", "next after", "next action", "in flight", "live session"),
    )
    for i, bullet in enumerate(next_bullets[:3], start=1):
        add(
            f"next-handoff-{i}",
            f"According to the dual-write handoff ({handoff_rel}), what is next-item #{i}?",
            bullet,
        )

    hands_off = _extract_handoff_bullets(
        handoff_text,
        heading_substrings=("hands-off", "handsoff", "do not", "out of scope"),
    )
    for i, bullet in enumerate(hands_off[:2], start=1):
        add(
            f"handsoff-{i}",
            f"According to the dual-write handoff, what is hands-off rule #{i}?",
            bullet,
        )

    # 6) Recent durable decisions from stream if still short
    decisions = [e for e in stream_entries if e["type"] == "decision"]
    for i, entry in enumerate(decisions[:3], start=1):
        if len(facts) >= N_ANCHORS:
            break
        add(
            f"decision-{i}",
            f"What decision #{i} was recorded on the stream?",
            entry["body"],
        )

    # 7) Recent state if still short (still dual-written stream entries — durable)
    states = [e for e in stream_entries if e["type"] == "state"]
    for i, entry in enumerate(reversed(states[-6:]), start=1):
        if len(facts) >= N_ANCHORS:
            break
        add(
            f"state-{i}",
            f"What recent state note #{i} is on the stream (paraphrase the frozen text)?",
            entry["body"],
        )

    if len(facts) < N_ANCHORS:
        raise SystemExit(
            f"error: could only derive {len(facts)}/{N_ANCHORS} durable anchors; "
            "open a stream session and dual-write handoff next/hands-off sections, then re-mint"
        )

    # Exactly 10 — prefer earliest (highest-trust: identity + pins)
    return facts[:N_ANCHORS]


def cmd_mint(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    epic = args.epic.strip().lower()
    stream_id = (args.stream or EPIC_STREAM_DEFAULTS.get(epic) or "").strip()
    if not stream_id:
        print(
            f"error: no stream for epic {epic!r}; pass --stream epic:N",
            file=sys.stderr,
        )
        return 1

    handoff_path: Path | None = None
    if args.handoff:
        handoff_path = Path(args.handoff)
        if not handoff_path.is_absolute():
            handoff_path = repo / handoff_path
    else:
        for cand in _handoff_candidates(repo, epic):
            if cand.is_file():
                handoff_path = cand
                break

    handoff_text = _read_text(handoff_path) if handoff_path else ""
    handoff_rel = (
        str(handoff_path.relative_to(repo)) if handoff_path and handoff_path.is_relative_to(repo) else str(handoff_path or "")
    )

    stream_entries = _load_stream_entries(stream_id, limit=int(args.stream_limit))
    try:
        facts = _build_facts(
            epic=epic,
            stream_id=stream_id,
            stream_entries=stream_entries,
            handoff_text=handoff_text,
            handoff_rel=handoff_rel or f".claude/{epic}-epic/",
        )
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else _canary_dir(repo, epic)
    out_dir.mkdir(parents=True, exist_ok=True)
    facts_path = out_dir / "facts.json"
    probe_path = out_dir / "probe.json"
    meta_path = out_dir / "mint_meta.json"

    facts_path.write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Delegate freeze to context_canary (legacy path) so scoring stays shared.
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "context_canary.py"),
            "mint",
            "--facts",
            str(facts_path),
            "--out",
            str(probe_path),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout, end="")
        print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode or 1
    print(proc.stdout, end="")

    meta = {
        "minted_at": _utc_now(),
        "epic": epic,
        "stream_id": stream_id,
        "handoff": handoff_rel,
        "n_anchors": len(facts),
        "pass_ratio_default": DEFAULT_PASS_RATIO,
        "policy": "operational-8/10-legacy-facts-from-stream+handoff",
        "probe": str(probe_path.relative_to(repo)) if probe_path.is_relative_to(repo) else str(probe_path),
        "ids": [f["id"] for f in facts],
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Always refresh questions view (no answers)
    q_path = out_dir / "questions.json"
    questions = {f["id"]: f["q"] for f in facts}
    q_path.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"canary dir: {out_dir}")
    print(f"questions:  {q_path}")
    print(f"policy: operational pass-ratio {DEFAULT_PASS_RATIO} (8/10); re-score after compact")
    return 0


def cmd_questions(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    epic = args.epic.strip().lower()
    out_dir = Path(args.out_dir) if args.out_dir else _canary_dir(repo, epic)
    probe_path = out_dir / "probe.json"
    if not probe_path.is_file():
        print(f"error: missing probe {probe_path}; run mint first", file=sys.stderr)
        return 1
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    anchors = probe.get("anchors") or []
    questions = {a["id"]: a["q"] for a in anchors if a.get("id") and a.get("q")}
    out = Path(args.out) if args.out else out_dir / "questions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Also print a human checklist
    for i, (aid, q) in enumerate(questions.items(), start=1):
        print(f"{i:2d}. [{aid}] {q}")
    print(f"wrote {out}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    epic = args.epic.strip().lower()
    out_dir = Path(args.out_dir) if args.out_dir else _canary_dir(repo, epic)
    probe_path = out_dir / "probe.json"
    if not probe_path.is_file():
        print(f"error: missing probe {probe_path}; run mint first", file=sys.stderr)
        return 1

    answers_path = Path(args.answers)
    if not answers_path.is_absolute():
        answers_path = repo / answers_path
    if not answers_path.is_file():
        print(f"error: answers file not found: {answers_path}", file=sys.stderr)
        return 1

    log_path = out_dir / "log.csv"
    verdict_path = out_dir / "last_verdict.json"
    pass_ratio = float(args.pass_ratio)
    threshold = float(args.threshold)

    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "context_canary.py"),
            "score",
            "--probe",
            str(probe_path),
            "--answers",
            str(answers_path),
            "--pass-ratio",
            str(pass_ratio),
            "--threshold",
            str(threshold),
            "--context-tokens",
            str(int(args.context_tokens)),
            "--model",
            args.model,
            "--log",
            str(log_path),
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    # Parse SCORE line for machine verdict file
    score_line = ""
    for line in (proc.stdout or "").splitlines():
        if line.startswith("SCORE "):
            score_line = line
    verdict = "PASS" if proc.returncode == 0 else "FAIL-HANDOFF"
    payload = {
        "scored_at": _utc_now(),
        "epic": epic,
        "verdict": verdict,
        "pass_ratio": pass_ratio,
        "context_tokens": int(args.context_tokens),
        "model": args.model,
        "score_line": score_line,
        "rc": proc.returncode,
        "policy": "operational-end-on-fail-handoff-not-on-compact-count",
        "action_if_fail": [
            "Append STATE AT HANDBACK to dual-write handoff",
            "session_streams close / force-close expired then stop",
            "Do NOT keep driving after FAIL-HANDOFF",
            "/quit and start a new Grok session with --epic",
        ],
    }
    verdict_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"verdict -> {verdict_path}")
    if verdict == "FAIL-HANDOFF":
        print("ACTION: FAIL-HANDOFF — dual-write STATE AT HANDBACK, close stream, end session now.")
    return 0 if proc.returncode == 0 else (2 if proc.returncode == 2 else proc.returncode)


def cmd_status(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    epic = args.epic.strip().lower()
    out_dir = Path(args.out_dir) if args.out_dir else _canary_dir(repo, epic)
    print(f"canary_dir: {out_dir}")
    for name in ("probe.json", "questions.json", "mint_meta.json", "last_verdict.json", "log.csv"):
        p = out_dir / name
        print(f"  {'OK ' if p.is_file() else '—  '} {name}")
    meta = out_dir / "mint_meta.json"
    if meta.is_file():
        print("mint_meta:", meta.read_text(encoding="utf-8").strip())
    verdict = out_dir / "last_verdict.json"
    if verdict.is_file():
        print("last_verdict:", verdict.read_text(encoding="utf-8").strip())
    return 0


def cmd_protocol(args: argparse.Namespace) -> int:
    """Print the agent-facing protocol (paste into cold-start / after compact)."""
    epic = args.epic.strip().lower()
    stream = args.stream or EPIC_STREAM_DEFAULTS.get(epic, "epic:N")
    canary = f".claude/{epic}-epic/canary"
    text = f"""## Grok lane session canary (operational)

You are bound to epic **{epic}** / stream **{stream}**.

### SSOT (survives compact)
- Session stream dual-write (typed entries)
- `{canary.replace('canary', 'INTERIM-DRIVER-HANDOFF.md')}` or CLAUDE-DRIVER-HANDOFF.md (read-only if not interim)

### End signal = canary score, NOT compact count
- Auto-compact is lossy for working memory. Disk logs ≠ model brain.
- **First auto-compact ⇒ re-score**, do not auto-quit solely because compact fired.
- **FAIL-HANDOFF (&lt; 8/10 at pass-ratio 0.8) ⇒ end now** regardless of token %.

### Cold-start (after stream open + handoff load)
```bash
.venv/bin/python -m scripts.session_canary.grok_lane mint --epic {epic} --stream {stream}
.venv/bin/python -m scripts.session_canary.grok_lane questions --epic {epic}
```
Do not open `probe.json` when later scoring from memory.

### When to score
1. After **any** auto-compact notification
2. Around **60–70%** context (`/session-info` or `/context`)
3. After a big merge/gate wave if still long-running

### Score procedure (from memory — no re-read of probe answers)
1. `.venv/bin/python -m scripts.session_canary.grok_lane questions --epic {epic}`
2. Write answers **from memory only** to `{canary}/answers.json` as `{{"id": "answer", ...}}`
3. Run:
```bash
.venv/bin/python -m scripts.session_canary.grok_lane score \\
  --epic {epic} \\
  --answers {canary}/answers.json \\
  --context-tokens <N> --model grok-4.5
```
4. rc 0 = PASS (continue). rc 2 = FAIL-HANDOFF → dual-write STATE AT HANDBACK, close stream, `/quit`.

### Operator compact config (optional)
In `~/.grok/config.toml`:
```toml
[session]
auto_compact_threshold_percent = 95
```
Default is 85% (~400k on large Grok windows). Higher leaves runway for a deliberate close.

### Production rollover (different tool)
Strict 10/10 identity rollover still uses:
`scripts/context_canary.py mint --snapshot …` + score — not this operational lane canary.
"""
    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m scripts.session_canary.grok_lane",
        description="Operational Grok epic-lane session canary (8/10 rot gate).",
    )
    p.add_argument("--repo", type=Path, default=ROOT, help="Repository root")
    sub = p.add_subparsers(dest="command", required=True)

    mint = sub.add_parser("mint", help="Freeze 10 durable anchors from stream + handoff")
    mint.add_argument("--epic", required=True, help="Epic slug (atlas, harness, …)")
    mint.add_argument("--stream", default=None, help="Stream id (default from epic map)")
    mint.add_argument("--handoff", default=None, help="Override dual-write handoff path")
    mint.add_argument("--out-dir", default=None, help="Canary directory override")
    mint.add_argument("--stream-limit", type=int, default=40)
    mint.set_defaults(func=cmd_mint)

    questions = sub.add_parser("questions", help="Print/write id→question map (no answers)")
    questions.add_argument("--epic", default="atlas")
    questions.add_argument("--out-dir", default=None)
    questions.add_argument("--out", default=None, help="Questions JSON path")
    questions.set_defaults(func=cmd_questions)

    score = sub.add_parser("score", help="Score answers vs probe (rc 2 = FAIL-HANDOFF)")
    score.add_argument("--epic", default="atlas")
    score.add_argument("--out-dir", default=None)
    score.add_argument("--answers", required=True, help="JSON map id→answer from memory")
    score.add_argument("--context-tokens", type=int, default=0)
    score.add_argument("--model", default="grok-4.5")
    score.add_argument("--pass-ratio", type=float, default=DEFAULT_PASS_RATIO, help="Default 0.8 (8/10)")
    score.add_argument("--threshold", type=float, default=DEFAULT_SIM_THRESHOLD, help="Per-anchor sim threshold")
    score.set_defaults(func=cmd_score)

    status = sub.add_parser("status", help="Show canary artifact presence + last verdict")
    status.add_argument("--epic", default="atlas")
    status.add_argument("--out-dir", default=None)
    status.set_defaults(func=cmd_status)

    protocol = sub.add_parser("protocol", help="Print agent-facing lifecycle protocol")
    protocol.add_argument("--epic", default="atlas")
    protocol.add_argument("--stream", default=None)
    protocol.set_defaults(func=cmd_protocol)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
