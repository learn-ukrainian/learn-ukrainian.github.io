#!/usr/bin/env bash
# hramatka SOAK v3 — strictly SEQUENTIAL, single teacher/session reused for all 18 bakes.
# Reuses canary HTTP/DB mechanics. Anchors: /root/soak-anchors.json (as-is).
set -euo pipefail

ORIGIN="https://hramatka.46-225-212-209.sslip.io"
DB="/var/lib/hramatka/hramatka.sqlite3"
APP="/opt/hramatka/current"
PY="/opt/hramatka/venv/bin/python"
ANCHORS_FILE="/root/soak-anchors.json"
RESULTS="/root/soak-results.jsonl"
SUMMARY="/root/soak-summary.md"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)-$$"
BACKUP="/var/lib/hramatka/backup-soak-${STAMP}.sqlite3"
WORKDIR="/tmp/hramatka-soak-${STAMP}"
JAR="${WORKDIR}/session.jar"
TEACHER_ID=""
CLEANED=0
POLL_MAX=120          # 120 * 10s = 20 min
POLL_SLEEP=10
BUSY_TIMEOUT_MS=8000

mkdir -p "$WORKDIR"
: > "$RESULTS"   # TRUNCATE stale v1/v2 rows

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

sql() {
  # .timeout is silent (unlike PRAGMA busy_timeout which echoes the value)
  sqlite3 -cmd ".timeout ${BUSY_TIMEOUT_MS}" "$DB" "$@"
}

counts() {
  local j t
  j=$(sql "SELECT status||'|'||COUNT(*) FROM lesson_jobs WHERE status IN ('failed','ready') GROUP BY status ORDER BY status;")
  t=$(sql "SELECT COUNT(*) FROM pilot_teachers;")
  j=$(printf '%s\n' "$j" | tr '\n' ' ' | sed 's/[[:space:]]*$//')
  printf 'lesson_jobs=%s; pilot_teachers=%s' "$j" "$t"
}

cleanup() {
  [ "$CLEANED" = 1 ] && return
  CLEANED=1
  log "CLEANUP start teacher_id=${TEACHER_ID:-none}"
  if [ -n "${TEACHER_ID:-}" ]; then
    (
      cd "$APP"
      set -a; . /etc/hramatka/api.env; set +a
      sudo -u hramatka -E "$PY" -m hramatka.api.teachers deactivate --teacher-id "$TEACHER_ID" >/dev/null 2>&1 || true
    )
    # Remove soak-owned rows so pilot baseline returns to failed|2 ready|14, teachers 5
    sql "DELETE FROM lesson_jobs WHERE teacher_id='${TEACHER_ID}';
         DELETE FROM pilot_sessions WHERE teacher_id='${TEACHER_ID}';
         DELETE FROM pilot_invites WHERE teacher_id='${TEACHER_ID}';
         DELETE FROM pilot_teachers WHERE id='${TEACHER_ID}';" || true
  fi
  rm -rf "$WORKDIR"
  log "CLEANUP done"
}
trap cleanup EXIT INT TERM HUP

# ---------- backup + baseline ----------
BEFORE=$(counts)
log "BEFORE $BEFORE"
sql ".backup ${BACKUP}"
log "BACKUP $BACKUP"

# ---------- load anchors as-is ----------
N=$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$ANCHORS_FILE")
if [ "$N" -ne 18 ]; then
  log "FATAL: expected 18 anchors in $ANCHORS_FILE, got $N"
  exit 1
fi
log "ANCHORS n=$N from $ANCHORS_FILE (as-is)"

# ---------- mint ONE teacher + ONE invite + ONE session ----------
cd "$APP"
set -a; . /etc/hramatka/api.env; set +a

TEACHER_JSON=$(sudo -u hramatka -E "$PY" -m hramatka.api.teachers create --display-name "driver-soak-${STAMP}" 2>/dev/null | head -n1)
TEACHER_ID=$(printf '%s' "$TEACHER_JSON" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['id'])")
log "TEACHER $TEACHER_ID"

INVITE_URL=$(sudo -u hramatka -E "$PY" -m hramatka.api.invites create --teacher-id "$TEACHER_ID" --expires-in-hours 6 2>/dev/null | sed -n '2p')
TOKEN=${INVITE_URL##*invite=}
if [ -z "$TOKEN" ]; then
  log "FATAL: empty invite token"
  exit 1
fi
log "INVITE token_len=${#TOKEN}"

SESSION=$(curl -sf -c "$JAR" -H "Origin: $ORIGIN" -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\"}" "$ORIGIN/api/session/redeem") || {
  log "FATAL: session redeem failed (self-test gate — stopping)"
  exit 1
}
CSRF=$(printf '%s' "$SESSION" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['csrf_token'])") || {
  log "FATAL: session parse failed (self-test gate — stopping)"
  exit 1
}
if [ -z "$CSRF" ]; then
  log "FATAL: empty CSRF"
  exit 1
fi
log "SESSION ok csrf_len=${#CSRF}"

# ---------- bake one anchor (sequential) ----------
# Args: idx (0-based). Appends one JSONL line to RESULTS. Prints outcome.
bake_one() {
  local idx="$1"
  local t0 wall s status code msg lesson_json lid body anchor_id chars bucket text_file

  t0=$(date +%s)
  text_file="${WORKDIR}/anchor-${idx}.txt"
  read -r anchor_id chars bucket < <("$PY" - "$ANCHORS_FILE" "$idx" "$text_file" <<'PY'
import json, sys
path, i, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
a = json.load(open(path))[i]
open(out, "w", encoding="utf-8").write(a["text"])
print(a["id"], a["chars"], a["bucket"])
PY
)

  lid=$("$PY" -c 'import uuid; print(uuid.uuid4())')
  body=$("$PY" - "$lid" "$text_file" <<'PY'
import json, sys
lid, path = sys.argv[1], sys.argv[2]
print(json.dumps({
  "id": lid,
  "anchor": {"text": open(path, encoding="utf-8").read(), "source": "teacher-paste"},
  "level": "B1",
  "duration": 45,
}, ensure_ascii=False))
PY
)

  if ! curl -sf -b "$JAR" -H "Origin: $ORIGIN" -H "X-CSRF-Token: $CSRF" \
      -H 'Content-Type: application/json' -d "$body" "$ORIGIN/api/lessons" >/dev/null; then
    wall=$(( $(date +%s) - t0 ))
    "$PY" - "$RESULTS" "$idx" "$anchor_id" "$chars" "$bucket" "error" "lesson_submit_failed" \
      "Lesson submission failed" "$wall" <<'PY'
import json, sys
f, idx, aid, chars, bucket, outcome, code, msg, wall = sys.argv[1:10]
row = {
  "idx": int(idx), "anchor_id": aid, "anchor_chars": int(chars), "bucket": bucket,
  "outcome": outcome, "failure_code": code, "failure_message": msg[:120],
  "wall_clock_s": int(wall), "blocks": 0, "rich_blocks": 0, "block_types": {},
  "marks": {}, "external_options_flags": 0, "rejected": 0, "rejected_top_reasons": {},
}
open(f, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
print(outcome)
PY
    return
  fi

  status=""
  for _ in $(seq 1 "$POLL_MAX"); do
    s=$(sql "SELECT status FROM lesson_jobs WHERE id='${lid}';" || true)
    status="$s"
    if [ "$status" = "ready" ] || [ "$status" = "failed" ]; then
      break
    fi
    sleep "$POLL_SLEEP"
  done

  wall=$(( $(date +%s) - t0 ))

  if [ "$status" != "ready" ] && [ "$status" != "failed" ]; then
    "$PY" - "$RESULTS" "$idx" "$anchor_id" "$chars" "$bucket" "error" "timeout" \
      "Bake did not reach terminal state within 1200 seconds" "$wall" <<'PY'
import json, sys
f, idx, aid, chars, bucket, outcome, code, msg, wall = sys.argv[1:10]
row = {
  "idx": int(idx), "anchor_id": aid, "anchor_chars": int(chars), "bucket": bucket,
  "outcome": outcome, "failure_code": code, "failure_message": msg[:120],
  "wall_clock_s": int(wall), "blocks": 0, "rich_blocks": 0, "block_types": {},
  "marks": {}, "external_options_flags": 0, "rejected": 0, "rejected_top_reasons": {},
}
open(f, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
print(outcome)
PY
    return
  fi

  # Pass lesson_json via temp file to avoid argv size / quoting issues
  local lj_file="${WORKDIR}/lj-${idx}.json"
  sql "SELECT COALESCE(lesson_json,'') FROM lesson_jobs WHERE id='${lid}';" > "$lj_file"
  code=$(sql "SELECT COALESCE(failure_code,'') FROM lesson_jobs WHERE id='${lid}';")
  msg=$(sql "SELECT COALESCE(failure_message,'') FROM lesson_jobs WHERE id='${lid}';")

  "$PY" - "$RESULTS" "$idx" "$anchor_id" "$chars" "$bucket" "$status" "$code" "$msg" "$wall" "$lj_file" <<'PY'
import collections, json, sys

f, idx, aid, chars, bucket, status, code, msg, wall, lj_path = sys.argv[1:11]
code = code or ""
msg = " ".join((msg or "").split())[:120]
outcome = "ready" if status == "ready" else ("floor_unmet" if "floor" in code.lower() else "error")
blocks, rejected = [], []
try:
    raw = open(lj_path, encoding="utf-8").read()
    if raw.strip():
        d = json.loads(raw)
        blocks = d.get("blocks") or []
        rejected = d.get("rejected") or []
except Exception:
    if status == "ready":
        outcome, code, msg = "error", "lesson_json_parse_failed", "Terminal ready row had unreadable lesson_json"
        blocks, rejected = [], []

# rich_blocks: not review_flagged and not mark/disposition in {review, flagged}
def is_flagged(b):
    if bool(b.get("review_flagged")):
        return True
    if b.get("mark") in ("review", "flagged"):
        return True
    if b.get("disposition") in ("review", "flagged"):
        return True
    return False

rich = sum(1 for b in blocks if not is_flagged(b))
row = {
    "idx": int(idx),
    "anchor_id": aid,
    "anchor_chars": int(chars),
    "bucket": bucket,
    "outcome": outcome,
    "failure_code": code,
    "failure_message": msg,
    "wall_clock_s": int(wall),
    "blocks": len(blocks),
    "rich_blocks": rich,
    "block_types": dict(collections.Counter(str(b.get("type") or "unknown") for b in blocks)),
    "marks": dict(collections.Counter(str(b.get("mark") or "none") for b in blocks)),
    "external_options_flags": sum(
        1 for b in blocks if (b.get("provenance") or {}).get("external_options")
    ),
    "rejected": len(rejected),
    "rejected_top_reasons": dict(
        collections.Counter(str(r.get("reason") or "unknown")[:80] for r in rejected).most_common(10)
    ),
}
open(f, "a", encoding="utf-8").write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
print(outcome)
PY
}

# ---------- self-test gate: bake anchor #1 (index 0) ----------
log "SELFTEST start anchor idx=0"
SELF_OUT=$(bake_one 0) || true
LINES=$(wc -l < "$RESULTS" | tr -d ' ')
if [ "$LINES" != "1" ]; then
  log "FATAL self-test: expected exactly 1 JSONL line, got $LINES"
  cat "$RESULTS" || true
  exit 1
fi
"$PY" - "$RESULTS" <<'PY'
import json, sys
row = json.loads(open(sys.argv[1], encoding="utf-8").readline())
assert row["outcome"] in ("ready", "floor_unmet", "error"), row
print("SELFTEST_OK", row["outcome"], "wall", row["wall_clock_s"], "blocks", row["blocks"],
      "code", row.get("failure_code") or "-")
PY
log "SELFTEST ok lines=$LINES out=$SELF_OUT"

# ---------- sequential bakes anchors #2..#18 (idx 1..17) ----------
for i in $(seq 1 17); do
  log "BAKE start idx=$i"
  OUT=$(bake_one "$i") || true
  log "BAKE done idx=$i outcome=$OUT lines=$(wc -l < "$RESULTS" | tr -d ' ')"
done

FINAL_LINES=$(wc -l < "$RESULTS" | tr -d ' ')
log "ALL_BAKES done lines=$FINAL_LINES"

# ---------- summary + cleanup ----------
PRE=$(counts)
log "PRE_CLEANUP $PRE"
cleanup
AFTER=$(counts)
log "AFTER $AFTER"

"$PY" - "$RESULTS" "$SUMMARY" "$BACKUP" "$BEFORE" "$PRE" "$AFTER" <<'PY'
import json, math, statistics, sys

results_path, summary_path, backup, before, pre, after = sys.argv[1:7]
rows = [json.loads(line) for line in open(results_path, encoding="utf-8") if line.strip()]
n = len(rows)
counts = {k: sum(r["outcome"] == k for r in rows) for k in ("ready", "floor_unmet", "error")}

def pct(x):
    return 100.0 * x / n if n else 0.0

walls = sorted(r["wall_clock_s"] for r in rows)
rich = sorted(r["rich_blocks"] for r in rows if r["outcome"] == "ready")

def median(xs):
    return statistics.median(xs) if xs else 0

def p90(xs):
    if not xs:
        return 0
    return xs[max(0, math.ceil(0.9 * len(xs)) - 1)]

def is_honest_floor(r):
    if r["outcome"] != "floor_unmet":
        return False
    msg = (r.get("failure_message") or "").lower()
    blaming_markers = (
        "некоректн", "помилков", "ваш текст поганий", "невалід",
        "invalid text", "malformed",
    )
    if any(m in msg for m in blaming_markers):
        return False
    return True

non_ready = [r for r in rows if r["outcome"] != "ready"]
honest = [r for r in non_ready if is_honest_floor(r)]
silent = [r for r in non_ready if r not in honest]

live_success = counts["ready"]
live_reject = n - live_success
engine_bench_reject = 24.2
live_reject_pct = pct(live_reject)
gap = live_reject_pct - engine_bench_reject

lines = []
lines.append("# Hramatka live soak summary (v3 sequential)")
lines.append("")
lines.append(f"Backup: `{backup}`")
lines.append("")
lines.append(
    f"N bakes: **{n}** (anchors as-is from `/root/soak-anchors.json`: "
    "6 short / 6 medium / 6 long)."
)
lines.append(
    f"Outcomes: ready **{counts['ready']}** ({pct(counts['ready']):.1f}%); "
    f"floor_unmet **{counts['floor_unmet']}** ({pct(counts['floor_unmet']):.1f}%); "
    f"error **{counts['error']}** ({pct(counts['error']):.1f}%)."
)
lines.append(f"**Live success rate:** {live_success}/{n} ({pct(live_success):.1f}%).")
lines.append(
    f"**Live rejection rate:** {live_reject}/{n} ({live_reject_pct:.1f}%). "
    f"Engine benchmark rejection = 24.2%; live gap = {gap:+.1f} pp "
    f"(live expected worse until slot-repair #183 — raw gap, no spin)."
)
lines.append(
    f"Wall-clock seconds: median **{median(walls):.1f}**; p90 **{p90(walls):.1f}**."
)
lines.append("")
lines.append(
    "Rich-block method: `rich_blocks` = blocks where `review_flagged` is not true "
    "AND `mark` ∉ {review, flagged} AND `disposition` ∉ {review, flagged}."
)
if rich:
    lines.append(
        f"Ready-bake rich blocks: min / median / max = "
        f"**{min(rich)}** / **{median(rich)}** / **{max(rich)}**."
    )
else:
    lines.append("Ready-bake rich blocks: min / median / max = n/a / n/a / n/a.")
lines.append("")
lines.append(
    f"**Honesty check:** of {len(non_ready)} non-ready bakes — "
    f"**{len(honest)} honest** (floor_unmet + non-blaming message), "
    f"**{len(silent)} silent/wrong** "
    f"(crash / engine_unavailable / timeout / parse / blaming non-thin)."
)
if not silent:
    lines.append("Silent/wrong failures: none.")
else:
    lines.append("")
    lines.append("Silent/wrong failures:")
    for r in silent:
        lines.append(
            f"- idx={r['idx']} anchor_id={r.get('anchor_id')} chars={r['anchor_chars']} "
            f"bucket={r.get('bucket')} code={r.get('failure_code') or 'none'} "
            f"message={r.get('failure_message') or 'none'}"
        )
lines.append("")
lines.append(f"Before cleanup: `{before}`")
lines.append(f"Immediately before cleanup: `{pre}`")
lines.append(f"After cleanup: `{after}`")
lines.append("")
lines.append(
    "| idx | anchor_id | chars | bucket | outcome | code | wall_s | blocks | rich | rejected |"
)
lines.append("| ---: | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |")
for r in sorted(rows, key=lambda x: x["idx"]):
    lines.append(
        f"| {r['idx']} | {r.get('anchor_id', '')} | {r['anchor_chars']} | "
        f"{r.get('bucket', '')} | {r['outcome']} | {r.get('failure_code') or '-'} | "
        f"{r['wall_clock_s']} | {r['blocks']} | {r['rich_blocks']} | {r['rejected']} |"
    )
lines.append("")
open(summary_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("SUMMARY_WRITTEN", summary_path)
honesty = "clean" if not silent else "leaky"
worst = ""
if silent:
    # name worst: prefer engine_unavailable / timeout / parse
    order = ("engine_unavailable", "timeout", "lesson_json_parse_failed", "lesson_submit_failed")
    ranked = sorted(
        silent,
        key=lambda r: (
            order.index(r.get("failure_code")) if r.get("failure_code") in order else 99,
            -(r.get("anchor_chars") or 0),
        ),
    )
    w = ranked[0]
    worst = f" worst={w.get('failure_code') or 'unknown'}:idx={w['idx']}:chars={w['anchor_chars']}"
print(f"VERDICT live_success={live_success}/{n} honesty={honesty} silent={len(silent)}{worst}")
PY

log "SOAK_COMPLETE backup=$BACKUP results=$RESULTS summary=$SUMMARY"
