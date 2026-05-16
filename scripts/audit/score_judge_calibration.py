#!/usr/bin/env python3
"""Score Russianism judges against the calibration gold set.

For each judge's ``judgments-{tag}.jsonl`` file alongside the gold
``eval/russianism/calibration-cases.jsonl``, compute:

  * case-level confusion matrix (TP / TN / FP / FN) — judged as clean vs
    dirty at the cell level.
  * phrase-level confusion — per-flag matching between gold flags and
    judge issues using normalized phrase equality + token-set overlap.
  * sev1-tolerant phrase F1 — debatable gold flags (sev=1) do not count
    as FN if the judge misses them. Reported alongside strict-F1.
  * per-judge precision, recall, F1, case-level accuracy.

Companion to :mod:`scripts.audit.russianism_judge`. Used to pick the
production review judge for the curriculum Russianism review position.

Usage:
    .venv/bin/python scripts/audit/score_judge_calibration.py \\
        --gold eval/russianism/calibration-cases.jsonl \\
        --judgments-dir path/to/judgments/ \\
        [--judges judgments-claudeopus47.jsonl judgments-gpt55.jsonl ...]

If ``--judges`` is omitted, all ``judgments-*.jsonl`` files in
``--judgments-dir`` are scored.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def norm(s: str) -> str:
    """Loose phrase identity for overlap matching."""
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s.strip(".,;:!?\"'()[]«»“”")


def overlap_match(judge_phrase: str, gold_phrase: str) -> bool:
    """A judge phrase matches a gold phrase if they share a multi-word
    substring OR one is contained in the other after normalization.

    Falls back to token-set overlap (>=2 shared tokens of len >=3) to
    catch cases where judge spans a slightly different boundary than gold.
    """
    j = norm(judge_phrase)
    g = norm(gold_phrase)
    if not j or not g:
        return False
    if j == g or j in g or g in j:
        return True
    jt = {t for t in j.split() if len(t) >= 3}
    gt = {t for t in g.split() if len(t) >= 3}
    return len(jt & gt) >= 2


def load_gold(path: Path) -> dict[str, dict]:
    """``prompt_id`` → {clean: bool, flags: list, rationale: str, text: str}"""
    out: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        out[d["prompt_id"]] = {
            "clean": d["gold"]["expected_clean"],
            "flags": d["gold"]["expected_flags"],
            "rationale": d["gold"].get("rationale", ""),
            "text": d.get("output_text", ""),
        }
    return out


def load_judgments(path: Path) -> dict[str, dict]:
    """``prompt_id`` → {flagged: bool, issues: list, model: str}"""
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        v = d.get("verdict", {})
        issues = v.get("issues", []) if v.get("verdict") == "issues_found" else []
        out[d["prompt_id"]] = {
            "flagged": bool(issues),
            "issues": issues,
            "judge_model": d.get("judge_model", "unknown"),
        }
    return out


def score_judge(gold: dict, judgments: dict, strict_sev1: bool = False) -> dict:
    """Compute case-level and phrase-level confusion-matrix counts.

    ``strict_sev1=False``: gold sev=1 flags that judge missed do NOT count
    as FN (treated as debatable). This is the recommended metric for
    judge ranking — sev=1 calls are inherently contested.
    """
    tp_case = tn_case = fp_case = fn_case = 0
    tp_phrase = fp_phrase = fn_phrase = 0
    case_breakdown: list[tuple[str, str]] = []
    n_cases = 0

    for pid, g in gold.items():
        j = judgments.get(pid)
        if j is None:
            continue
        n_cases += 1
        if g["clean"] and not j["flagged"]:
            tn_case += 1
            case_breakdown.append((pid, "TN_case"))
        elif g["clean"] and j["flagged"]:
            fp_case += 1
            case_breakdown.append((pid, "FP_case"))
        elif (not g["clean"]) and j["flagged"]:
            tp_case += 1
            case_breakdown.append((pid, "TP_case"))
        else:
            fn_case += 1
            case_breakdown.append((pid, "FN_case"))

        gold_flags = list(g["flags"])
        judge_issues = list(j["issues"])
        matched_gold: set[int] = set()
        matched_judge: set[int] = set()
        for ji_idx, ji in enumerate(judge_issues):
            for gi_idx, gi in enumerate(gold_flags):
                if gi_idx in matched_gold:
                    continue
                if overlap_match(ji.get("phrase", ""), gi.get("phrase", "")):
                    matched_gold.add(gi_idx)
                    matched_judge.add(ji_idx)
                    tp_phrase += 1
                    break
        # Unmatched judge issues = phrase FPs
        for ji_idx in range(len(judge_issues)):
            if ji_idx not in matched_judge:
                fp_phrase += 1
        # Unmatched gold flags = phrase FNs (sev1-tolerant by default)
        for gi_idx, gi in enumerate(gold_flags):
            if gi_idx in matched_gold:
                continue
            sev = int(gi.get("severity", 2) or 2)
            if not strict_sev1 and sev == 1:
                continue
            fn_phrase += 1

    def safe_div(a: int | float, b: int | float) -> float:
        return a / b if b else 0.0

    prec = safe_div(tp_phrase, tp_phrase + fp_phrase)
    rec = safe_div(tp_phrase, tp_phrase + fn_phrase)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0

    return {
        "n_cases": n_cases,
        "case_tp": tp_case,
        "case_tn": tn_case,
        "case_fp": fp_case,
        "case_fn": fn_case,
        "case_accuracy": safe_div(tp_case + tn_case, n_cases),
        "phrase_tp": tp_phrase,
        "phrase_fp": fp_phrase,
        "phrase_fn": fn_phrase,
        "phrase_precision": prec,
        "phrase_recall": rec,
        "phrase_f1": f1,
        "strict_sev1": strict_sev1,
        "case_breakdown": case_breakdown,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gold", default=str(PROJECT_ROOT / "eval/russianism/calibration-cases.jsonl"),
                    help="Path to calibration gold JSONL.")
    ap.add_argument("--judgments-dir", required=True,
                    help="Directory containing judgments-*.jsonl files.")
    ap.add_argument("--judges", nargs="*", default=None,
                    help="Specific judgment files (relative to --judgments-dir). "
                         "Default: all judgments-*.jsonl in dir.")
    ap.add_argument("--strict-sev1", action="store_true",
                    help="Count gold sev=1 misses as FN (strict scoring). "
                         "Default: sev1-tolerant.")
    ap.add_argument("--out", help="Optional path to write summary JSON.")
    args = ap.parse_args()

    gold_path = Path(args.gold)
    if not gold_path.exists():
        sys.exit(f"Gold file not found: {gold_path}")
    gold = load_gold(gold_path)
    print(f"Loaded {len(gold)} gold cases from {gold_path}\n")

    judgments_dir = Path(args.judgments_dir)
    if args.judges:
        candidates = [judgments_dir / f for f in args.judges]
    else:
        candidates = sorted(judgments_dir.glob("judgments-*.jsonl"))

    summaries: dict[str, dict] = {}
    rows: list[tuple[str, dict]] = []
    for cand in candidates:
        if not cand.exists():
            print(f"  SKIP {cand.name}: not found")
            continue
        judgments = load_judgments(cand)
        if not judgments:
            print(f"  SKIP {cand.name}: empty")
            continue
        # Identify judge model from the first row
        first_judge_model = next(iter(judgments.values())).get("judge_model", cand.stem)
        s = score_judge(gold, judgments, strict_sev1=args.strict_sev1)
        rows.append((first_judge_model, s))
        summaries[first_judge_model] = {k: v for k, v in s.items() if k != "case_breakdown"}
        print(f"{first_judge_model}  ({cand.name})")
        print(f"  cases n={s['n_cases']}  TP={s['case_tp']} TN={s['case_tn']} FP={s['case_fp']} FN={s['case_fn']}")
        print(f"  case accuracy: {s['case_accuracy']:.2%}")
        tag = "strict" if args.strict_sev1 else "sev1-tolerant"
        print(f"  phrase TP={s['phrase_tp']} FP={s['phrase_fp']} FN={s['phrase_fn']}  ({tag})")
        print(f"  phrase precision: {s['phrase_precision']:.2%}")
        print(f"  phrase recall:    {s['phrase_recall']:.2%}")
        print(f"  phrase F1:        {s['phrase_f1']:.2%}")
        print()

    print("=" * 70)
    print(f"RANKING — {'strict' if args.strict_sev1 else 'sev1-tolerant'} phrase F1")
    print("=" * 70)
    print(f"  {'judge':<28} {'F1':>6} {'P':>6} {'R':>6} {'CaseAcc':>8}")
    rows.sort(key=lambda r: -r[1]["phrase_f1"])
    for label, s in rows:
        print(f"  {label:<28} {s['phrase_f1']:>5.0%} {s['phrase_precision']:>5.0%} "
              f"{s['phrase_recall']:>5.0%} {s['case_accuracy']:>7.0%}")

    if args.out:
        Path(args.out).write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
