"""Classify stripped / invalid groundings for bakeoff probe analysis (#4761).

Splits failed groundings into:
- ``paraphrase_of_retrieved`` — near-miss citation of text present in captured tool output
  (Hypothesis B: harness/style artifact)
- ``query_or_tool_metadata_mismatch`` — excerpt present in output but not the queried
  tool call (Hypothesis B: harness pairing/metadata artifact)
- ``excerpt_not_in_tool_output`` — excerpt absent from all captured outputs
  (Hypothesis A: fabrication while holding no supporting evidence)
- ``confirmed_against_evidence`` — model ``CONFIRMED`` a gold-false claim while citing
  retrieved evidence (the sharper Hypothesis-A signal: overconfidence /
  verdict-against-evidence, NOT fabrication). Only assigned when the artifact carries
  gold ``score`` labels; gold-free artifacts never see this bucket.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.audit import llm_reviewer_dispatch

PARAPHRASE_TOKEN_OVERLAP_THRESHOLD = 0.5
PARAPHRASE_MATCHED_EVENT_THRESHOLD = 0.4


@dataclass(frozen=True)
class GroundingClassification:
    source: str
    claim: str
    tool: str
    query: str
    evidence_excerpt: str
    bucket: str
    token_overlap_best: float
    query_matched_event_count: int
    in_any_output: bool

def _content_tokens(text: str) -> list[str]:
    normalized = llm_reviewer_dispatch._normalize_for_match(text)
    return [token for token in normalized.split() if len(token) >= 3]


def _token_overlap_ratio(excerpt: str, output: str) -> float:
    tokens = _content_tokens(excerpt)
    if not tokens:
        return 0.0
    normalized_output = llm_reviewer_dispatch._normalize_for_match(output)
    hits = sum(1 for token in tokens if token in normalized_output)
    return hits / len(tokens)


def _excerpt_in_any_output(excerpt: str, events: Sequence[Mapping[str, Any]]) -> bool:
    for event in events:
        output = llm_reviewer_dispatch._event_output_text(event)
        if output is None:
            continue
        if _token_overlap_ratio(excerpt, output) >= PARAPHRASE_TOKEN_OVERLAP_THRESHOLD:
            return True
    return False


def _query_matched_events(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    query = str(grounding.get("query") or "").strip()
    tool = llm_reviewer_dispatch._canonical_tool_name(grounding.get("tool"))
    if not query:
        return ()
    matches: list[Mapping[str, Any]] = []
    for event in events:
        if tool and llm_reviewer_dispatch._canonical_tool_name(event.get("tool")) != tool:
            continue
        if llm_reviewer_dispatch._event_input_matches_query(event, query):
            matches.append(event)
    return tuple(matches)


def classify_grounding(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    source: str,
    claim: str,
    against_evidence: bool = False,
) -> GroundingClassification | None:
    """Return a classification when grounding fails the verbatim gate; else None.

    ``against_evidence`` is set by the caller when gold labels show the model
    ``CONFIRMED`` a false claim: the excerpt-vs-output overlap buckets then defer to
    the sharper ``confirmed_against_evidence`` signal (as long as some evidence was
    actually retrieved — a pure fabrication with no supporting output stays
    ``excerpt_not_in_tool_output``).
    """
    excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not excerpt:
        return None
    if llm_reviewer_dispatch._grounding_matches_events(grounding, events):
        return None

    query_matches = _query_matched_events(grounding, events)
    best_overlap = 0.0
    for event in events:
        output = llm_reviewer_dispatch._event_output_text(event)
        if output is None:
            continue
        best_overlap = max(best_overlap, _token_overlap_ratio(excerpt, output))

    matched_overlap = 0.0
    for event in query_matches:
        output = llm_reviewer_dispatch._event_output_text(event)
        if output is None:
            continue
        matched_overlap = max(matched_overlap, _token_overlap_ratio(excerpt, output))

    in_any_output = _excerpt_in_any_output(excerpt, events)
    has_supporting_output = in_any_output or best_overlap >= PARAPHRASE_TOKEN_OVERLAP_THRESHOLD
    if against_evidence and has_supporting_output:
        # Model CONFIRMED a gold-false claim while holding retrieved evidence — the
        # verdict contradicts the source it cited. Sharper than paraphrase; this is
        # the real Hypothesis-A failure (overconfidence, not fabrication).
        bucket = "confirmed_against_evidence"
    elif not query_matches and in_any_output and best_overlap >= PARAPHRASE_TOKEN_OVERLAP_THRESHOLD:
        bucket = "query_or_tool_metadata_mismatch"
    elif (
        in_any_output
        or matched_overlap >= PARAPHRASE_MATCHED_EVENT_THRESHOLD
        or best_overlap >= PARAPHRASE_TOKEN_OVERLAP_THRESHOLD
    ):
        bucket = "paraphrase_of_retrieved"
    else:
        bucket = "excerpt_not_in_tool_output"
    return GroundingClassification(
        source=source,
        claim=claim,
        tool=str(grounding.get("tool") or ""),
        query=str(grounding.get("query") or ""),
        evidence_excerpt=excerpt,
        bucket=bucket,
        token_overlap_best=round(best_overlap, 3),
        query_matched_event_count=len(query_matches),
        in_any_output=in_any_output,
    )


def _iter_groundings(
    payload: Mapping[str, Any],
) -> list[tuple[str, str, Mapping[str, Any], str]]:
    rows: list[tuple[str, str, Mapping[str, Any], str]] = []
    for index, finding in enumerate(payload.get("findings") or [], start=1):
        if not isinstance(finding, Mapping):
            continue
        grounding = finding.get("grounding")
        if isinstance(grounding, Mapping):
            claim = str(finding.get("claim") or finding.get("summary") or f"finding-{index}")
            rows.append(("finding", claim, grounding, str(finding.get("verdict") or "")))
    for index, fact_check in enumerate(payload.get("fact_checks") or [], start=1):
        if not isinstance(fact_check, Mapping):
            continue
        grounding = fact_check.get("grounding")
        if isinstance(grounding, Mapping):
            claim = str(fact_check.get("claim") or f"fact_check-{index}")
            rows.append(("fact_check", claim, grounding, str(fact_check.get("verdict") or "")))
    return rows


def _false_confirmed_claims(artifact: Mapping[str, Any]) -> set[str]:
    """Gold-labelled claim texts the model CONFIRMED but which are actually false.

    Reads the bakeoff ``score.claims`` block (present only for gold fixtures). Returns
    the normalized ``model_claim`` / ``claim`` text for every scored claim where the
    model's verdict was ``CONFIRMED`` and the gold label is ``is_true == False``.
    Empty set for gold-free artifacts → ``confirmed_against_evidence`` never fires.
    """
    score = artifact.get("score")
    if not isinstance(score, Mapping):
        return set()
    confirmed_false: set[str] = set()
    for claim in score.get("claims") or []:
        if not isinstance(claim, Mapping):
            continue
        if claim.get("is_true") is not False:
            continue
        verdict = str(claim.get("model_judgment_verdict") or claim.get("verdict") or "")
        if verdict != "CONFIRMED":
            continue
        for key in ("model_claim", "claim"):
            text = str(claim.get(key) or "").strip()
            if text:
                confirmed_false.add(llm_reviewer_dispatch._normalize_for_match(text))
    return confirmed_false


def classify_artifact(artifact: Mapping[str, Any]) -> list[GroundingClassification]:
    dispatch = artifact.get("dispatch")
    if not isinstance(dispatch, Mapping):
        return []
    events = llm_reviewer_dispatch.tool_events_from_dispatch_meta(dispatch)
    if not events:
        return []

    payload = artifact.get("payload")
    if not isinstance(payload, Mapping):
        return []

    confirmed_false = _false_confirmed_claims(artifact)
    classified: list[GroundingClassification] = []
    for source, claim, grounding, verdict in _iter_groundings(payload):
        against_evidence = (
            verdict == "CONFIRMED"
            and llm_reviewer_dispatch._normalize_for_match(claim) in confirmed_false
        )
        row = classify_grounding(
            grounding,
            events,
            source=source,
            claim=claim,
            against_evidence=against_evidence,
        )
        if row is not None:
            classified.append(row)
    return classified


BUCKETS = (
    "paraphrase_of_retrieved",
    "query_or_tool_metadata_mismatch",
    "confirmed_against_evidence",
    "excerpt_not_in_tool_output",
)


def _histogram(rows: Sequence[GroundingClassification]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in BUCKETS}
    for row in rows:
        counts[row.bucket] = counts.get(row.bucket, 0) + 1
    return counts


def _artifact_label(path: Path, artifact: Mapping[str, Any]) -> str:
    model = artifact.get("model")
    pin = model.get("pin") if isinstance(model, Mapping) else None
    fixture = artifact.get("fixture")
    slug = fixture.get("slug") if isinstance(fixture, Mapping) else path.stem
    arm = artifact.get("arm") or "unknown"
    run_index = artifact.get("run_index")
    suffix = f" r{run_index}" if run_index else ""
    return f"{pin or path.stem} / {slug} / {arm}{suffix}"


def analyze_paths(paths: Sequence[Path]) -> dict[str, Any]:
    per_artifact: list[dict[str, Any]] = []
    all_rows: list[GroundingClassification] = []
    for path in paths:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(artifact, Mapping):
            continue
        rows = classify_artifact(artifact)
        if not rows:
            continue
        per_artifact.append(
            {
                "path": str(path),
                "label": _artifact_label(path, artifact),
                "histogram": _histogram(rows),
                "rows": [asdict(row) for row in rows],
            }
        )
        all_rows.extend(rows)
    return {
        "artifact_count": len(per_artifact),
        "failed_grounding_count": len(all_rows),
        "histogram": _histogram(all_rows),
        "artifacts": per_artifact,
    }


def _collect_artifacts(root: Path, *, arm: str | None, fixture: str | None) -> list[Path]:
    paths = sorted(root.glob("*.json"))
    selected: list[Path] = []
    for path in paths:
        if path.name in {"SCORECARD.md"}:
            continue
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(artifact, Mapping):
            continue
        if arm and artifact.get("arm") != arm:
            continue
        fixture_meta = artifact.get("fixture")
        slug = fixture_meta.get("slug") if isinstance(fixture_meta, Mapping) else None
        if fixture and slug != fixture:
            continue
        if artifact.get("arm") != "tooled":
            continue
        selected.append(path)
    return selected


def render_markdown(report: Mapping[str, Any]) -> str:
    hist = report.get("histogram") or {}
    total = int(report.get("failed_grounding_count") or 0)
    lines = [
        "# Grounding failure histogram",
        "",
        f"Artifacts with failed groundings: **{report.get('artifact_count', 0)}**",
        f"Failed grounding rows: **{total}**",
        "",
        "| Bucket | Count | Share |",
        "| --- | ---: | ---: |",
    ]
    for bucket in BUCKETS:
        count = int(hist.get(bucket) or 0)
        share = f"{(100.0 * count / total):.1f}%" if total else "n/a"
        lines.append(f"| {bucket} | {count} | {share} |")
    lines.extend(["", "## Per-artifact", ""])
    for artifact in report.get("artifacts") or []:
        lines.append(f"### {artifact.get('label')}")
        lines.append("")
        mini = artifact.get("histogram") or {}
        for bucket in BUCKETS:
            lines.append(f"- {bucket}: {mini.get(bucket, 0)}")
        lines.append("")
        for row in artifact.get("rows") or []:
            excerpt = str(row.get("evidence_excerpt") or "")
            if len(excerpt) > 120:
                excerpt = excerpt[:117] + "..."
            lines.append(
                f"- **{row.get('bucket')}** ({row.get('source')}) overlap="
                f"{row.get('token_overlap_best')} query_matches="
                f"{row.get('query_matched_event_count')}: {excerpt!r}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory of qg_bakeoff artifact JSON files")
    parser.add_argument("--fixture", default=None, help="Optional fixture slug filter")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    args = parser.parse_args(argv)

    paths = _collect_artifacts(args.root, arm="tooled", fixture=args.fixture)
    report = analyze_paths(paths)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"histogram": report["histogram"], "artifact_count": report["artifact_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
