"""Automated evaluation harness for Ukrainian Linguistic Decolonization & Reasoning (#7926).

Benchmarks candidate model outputs against the held-out evaluation firewall partition
(`decolonization_trajectories_held_out_part001.jsonl`), measuring:
1. Calque elimination rate (rejection of Soviet calques and Russianisms)
2. Authentic Ukrainian suggestion rate (presence of verified living standard / classical terms)
3. Morphemic and historical grounding score (presence of structural linguistic reasoning)
4. Overall State Standard 2024 compliance index
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HELD_OUT_FILE = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "generated"
    / "decolonization_trajectories_held_out_part001.jsonl"
)

REASONING_MARKERS = [
    re.compile(r"кальк", re.IGNORECASE),
    re.compile(r"росіян", re.IGNORECASE),
    re.compile(r"радянськ", re.IGNORECASE),
    re.compile(r"префікс", re.IGNORECASE),
    re.compile(r"дієприкметник", re.IGNORECASE),
    re.compile(r"суфікс", re.IGNORECASE),
    re.compile(r"питом", re.IGNORECASE),
    re.compile(r"етимолог", re.IGNORECASE),
    re.compile(r"словник", re.IGNORECASE),
    re.compile(r"весум", re.IGNORECASE),
    re.compile(r"підручник", re.IGNORECASE),
    re.compile(r"норм", re.IGNORECASE),
]

AFFIRMATION_PATTERNS = [
    r"правильно\s+(?:вживати|казати|говорити)\s+[«\"]?{term}[»\"]?",
    r"слово\s+[«\"]?{term}[»\"]?\s+є\s+(?:цілком\s+)?нормативним",
    r"вживайте\s+[«\"]?{term}[»\"]?",
]


def normalize_token(s: str) -> str:
    """Strip accents and non-alphanumeric punctuation."""
    s = re.sub(r"[\u0300\u0301]", "", s)
    return s.strip().strip("«»\"'.,;:!?()[]{}").lower()


def evaluate_single_response(
    target_term: str,
    valid_alternatives: list[str],
    response_text: str,
) -> dict[str, Any]:
    """Evaluate one model output against gold decolonization targets."""
    resp_norm = response_text.lower()
    term_norm = normalize_token(target_term)

    # 1. Calque elimination check:
    # If the model explicitly affirms or recommends the calque, it fails elimination.
    calque_affirmed = False
    for pat in AFFIRMATION_PATTERNS:
        regex = re.compile(pat.format(term=re.escape(term_norm)), re.IGNORECASE)
        if regex.search(resp_norm):
            calque_affirmed = True
            break

    # If the calque is mentioned, check if it is explicitly framed as an error / calque / incorrect
    calque_present = term_norm in resp_norm
    if calque_present and not calque_affirmed:
        # Check for critique context
        critique_markers = ("кальк", "помилк", "росіян", "не рекоменд", "не варто", "штучн", "замін", "замість")
        has_critique = any(m in resp_norm for m in critique_markers)
        calque_eliminated = has_critique
    else:
        calque_eliminated = not calque_affirmed

    # 2. Authentic suggestion check:
    # Does the response recommend at least one verified Ukrainian equivalent?
    matched_alts = []
    for alt in valid_alternatives:
        alt_norm = normalize_token(alt)
        if alt_norm and alt_norm in resp_norm:
            matched_alts.append(alt)

    authentic_suggested = len(matched_alts) > 0

    # 3. Morphemic and historical reasoning grounding check:
    reasoning_hit_count = sum(1 for p in REASONING_MARKERS if p.search(resp_norm))
    reasoning_grounded = reasoning_hit_count >= 2

    # 4. Composite score:
    # 0.40 calque_eliminated + 0.40 authentic_suggested + 0.20 reasoning_grounded
    composite_score = 0.0
    if calque_eliminated:
        composite_score += 0.40
    if authentic_suggested:
        composite_score += 0.40
    if reasoning_grounded:
        composite_score += 0.20

    is_pass = composite_score >= 0.80

    return {
        "target_term": target_term,
        "calque_eliminated": calque_eliminated,
        "authentic_suggested": authentic_suggested,
        "matched_alternatives": matched_alts,
        "reasoning_grounded": reasoning_grounded,
        "reasoning_hits": reasoning_hit_count,
        "composite_score": round(composite_score, 2),
        "is_pass": is_pass,
    }


def evaluate_predictions(
    held_out_path: Path,
    predictions_path: Path,
    out_report_path: Path | None = None,
) -> dict[str, Any]:
    """Evaluate a batch of predictions against the held-out evaluation partition."""
    if not held_out_path.is_file():
        raise FileNotFoundError(f"Missing held-out benchmark file at {held_out_path}")
    if not predictions_path.is_file():
        raise FileNotFoundError(f"Missing predictions file at {predictions_path}")

    # Load gold items
    gold_items: dict[str, dict[str, Any]] = {}
    with held_out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            target = item.get("target_term") or normalize_token(item.get("query", ""))
            alts = [a["lemma"] for a in item.get("register_spectrum", {}).get("alternatives", [])]
            gold_items[normalize_token(target)] = {
                "trajectory_id": item.get("trajectory_id"),
                "target_term": target,
                "alternatives": alts,
                "gold_response": item.get("final_response") or item.get("response"),
            }

    # Load predictions
    results: list[dict[str, Any]] = []
    with predictions_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            pred = json.loads(line)
            target = pred.get("target_term", "")
            norm_target = normalize_token(target)
            if norm_target not in gold_items:
                # Try finding by trajectory_id or query
                for k, v in gold_items.items():
                    if v["trajectory_id"] == pred.get("id") or k in pred.get("prompt", "").lower():
                        norm_target = k
                        break

            if norm_target in gold_items:
                gold = gold_items[norm_target]
                resp_text = (
                    pred.get("final_response")
                    or pred.get("response")
                    or pred.get("generated_text")
                    or pred.get("text", "")
                )
                eval_res = evaluate_single_response(gold["target_term"], gold["alternatives"], resp_text)
                eval_res["id"] = pred.get("id", gold["trajectory_id"])
                results.append(eval_res)

    total = len(results)
    if total == 0:
        summary = {
            "total_evaluated": 0,
            "calque_elimination_rate": 0.0,
            "authentic_suggestion_rate": 0.0,
            "reasoning_grounding_rate": 0.0,
            "mean_composite_score": 0.0,
            "pass_rate": 0.0,
            "evaluations": [],
        }
    else:
        elim_count = sum(1 for r in results if r["calque_eliminated"])
        auth_count = sum(1 for r in results if r["authentic_suggested"])
        reas_count = sum(1 for r in results if r["reasoning_grounded"])
        pass_count = sum(1 for r in results if r["is_pass"])
        mean_score = sum(r["composite_score"] for r in results) / total

        summary = {
            "total_evaluated": total,
            "calque_elimination_rate": round(elim_count / total, 4),
            "authentic_suggestion_rate": round(auth_count / total, 4),
            "reasoning_grounding_rate": round(reas_count / total, 4),
            "mean_composite_score": round(mean_score, 4),
            "pass_rate": round(pass_count / total, 4),
            "evaluations": results,
        }

    if out_report_path:
        out_report_path.parent.mkdir(parents=True, exist_ok=True)
        with out_report_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            f.write("\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate model outputs against ULDR held-out benchmark")
    parser.add_argument("--held-out", type=Path, default=DEFAULT_HELD_OUT_FILE)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--out-report", type=Path, default=None)

    args = parser.parse_args()
    summary = evaluate_predictions(args.held_out, args.predictions, args.out_report)
    print("=== ULDR Evaluation Benchmark Results ===")
    print(f"Total Evaluated:             {summary['total_evaluated']}")
    print(f"Calque Elimination Rate:     {summary['calque_elimination_rate']:.2%}")
    print(f"Authentic Suggestion Rate:   {summary['authentic_suggestion_rate']:.2%}")
    print(f"Reasoning Grounding Rate:    {summary['reasoning_grounding_rate']:.2%}")
    print(f"Mean Composite Score:        {summary['mean_composite_score']:.4f}")
    print(f"Pass Rate (Score >= 0.80):   {summary['pass_rate']:.2%}")
    if args.out_report:
        print(f"Full report saved to {args.out_report}")


if __name__ == "__main__":
    main()
