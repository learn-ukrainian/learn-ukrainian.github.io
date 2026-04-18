#!/usr/bin/env python3
"""Seeded-defect authoring tool for the dimensional review benchmark.

Per `docs/design/dimensional-review.md` §7b, threshold calibration and
agent-assignment freezing require a corpus of articles WITH KNOWN
DEFECTS. Reviewer recall/precision can't be measured on real content
because missed errors are invisible there.

Approach: handcraft defects. The benchmark corpus is bounded (5 articles
× 3 versions per §7b budget), so hand-authoring ~150 defects is cheaper
and more realistic than a general-purpose language-aware injector. This
tool is a thin find/replace applier that turns a clean article + a YAML
defect spec into (defective_article, ground_truth.yaml).

### Defect spec format (`defects.yaml`)

```yaml
# Comments are ignored. Each entry describes one planted defect.
- id: d1                          # short stable id
  dim: factual_accuracy            # one of the four dims
  issue_type: FACTUAL_ERROR        # matches reviewer prompt taxonomy
  severity: critical               # critical | major | minor
  find: "Переяславська рада 1654 року"
  replace: "Переяславська рада 1653 року"
  note: "Off-by-one year"          # human-readable description

- id: d2
  dim: register
  issue_type: RUSSIANISM
  severity: major
  find: "брати участь"
  replace: "приймати участь"
  note: "Calque; brati uchast' is idiomatic UK"
```

### Output (`ground_truth.yaml`)

Identical shape as the defect spec, plus resolved byte offsets computed
from the clean article. The benchmark driver uses these offsets to
score reviewer-location reports fuzzily.

### Usage

    # Generate defective article + ground truth from clean + spec
    .venv/bin/python scripts/wiki/benchmark_seed.py \\
        --clean benchmarks/wiki/aspect/clean.md \\
        --defects benchmarks/wiki/aspect/defects.yaml \\
        --out-article benchmarks/wiki/aspect/defective.md \\
        --out-truth benchmarks/wiki/aspect/ground_truth.yaml

    # Verify a defect spec against a clean article (finds unmatched `find:` patterns)
    .venv/bin/python scripts/wiki/benchmark_seed.py \\
        --clean benchmarks/wiki/aspect/clean.md \\
        --defects benchmarks/wiki/aspect/defects.yaml \\
        --verify
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_DIMS = {
    "source_grounding",
    "factual_accuracy",
    "ukrainian_perspective",
    "register",
}
VALID_SEVERITIES = {"critical", "major", "minor"}


@dataclass(frozen=True)
class Defect:
    id: str
    dim: str
    issue_type: str
    severity: str
    find: str
    replace: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dim": self.dim,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "find": self.find,
            "replace": self.replace,
            "note": self.note,
        }


def load_defects(spec_path: Path) -> list[Defect]:
    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise ValueError(f"{spec_path}: expected YAML list, got {type(raw).__name__}")

    defects: list[Defect] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{spec_path}: entry {i} not a mapping")
        for required in ("id", "dim", "issue_type", "severity", "find", "replace"):
            if required not in item:
                raise ValueError(f"{spec_path}: entry {i} missing {required!r}")

        defect = Defect(
            id=str(item["id"]),
            dim=str(item["dim"]),
            issue_type=str(item["issue_type"]),
            severity=str(item["severity"]),
            find=str(item["find"]),
            replace=str(item["replace"]),
            note=str(item.get("note", "")),
        )
        if defect.dim not in VALID_DIMS:
            raise ValueError(
                f"{spec_path}: entry {i} invalid dim {defect.dim!r}; "
                f"valid: {sorted(VALID_DIMS)}"
            )
        if defect.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"{spec_path}: entry {i} invalid severity {defect.severity!r}; "
                f"valid: {sorted(VALID_SEVERITIES)}"
            )
        if defect.id in seen_ids:
            raise ValueError(f"{spec_path}: duplicate id {defect.id!r}")
        seen_ids.add(defect.id)
        defects.append(defect)
    return defects


def verify_defects(clean_text: str, defects: list[Defect]) -> list[str]:
    """Return list of issues (empty = spec is applicable)."""
    issues: list[str] = []
    for d in defects:
        if d.find not in clean_text:
            issues.append(f"{d.id}: find-string not present: {d.find!r}")
        elif clean_text.count(d.find) > 1:
            # Still usable (we apply on first occurrence) but flag for
            # the spec author — they may want more context.
            issues.append(
                f"{d.id}: find-string appears {clean_text.count(d.find)}× "
                "(will apply to first occurrence; add more context to spec)"
            )
    return issues


def inject_defects(clean_text: str, defects: list[Defect]) -> tuple[str, list[dict]]:
    """Apply defects to clean_text. Returns (defective_text, ground_truth).

    Defects are applied in YAML order, first-occurrence each (via
    `str.replace(find, replace, 1)`). Ground truth captures the BYTE
    OFFSET of each defect in the DEFECTIVE article (not the clean one),
    because reviewer location reports reference the defective text they
    were given.
    """
    out = clean_text
    truth: list[dict] = []
    for d in defects:
        if d.find not in out:
            # Could happen if a prior defect's replace consumed part of
            # this one's find. Record as ground truth anyway — the
            # reviewer will never find it, so this is an important
            # signal that the defect spec has ordering issues.
            truth.append({
                **d.to_dict(),
                "offset": -1,
                "applied": False,
                "skip_reason": "find-string consumed by prior defect",
            })
            continue
        offset_before = out.index(d.find)
        out = out.replace(d.find, d.replace, 1)
        truth.append({
            **d.to_dict(),
            "offset": offset_before,
            "length_in_defective": len(d.replace),
            "applied": True,
        })
    return out, truth


def write_ground_truth(path: Path, clean_path: Path, defective_path: Path, truth: list[dict]) -> None:
    header = (
        f"# Ground truth for {defective_path.name}\n"
        f"# Clean source: {clean_path.name}\n"
        "# Each entry: one planted defect. Benchmark driver scores reviewer\n"
        "# findings against (dim, issue_type, offset ± tolerance).\n"
    )
    body = yaml.safe_dump(
        {"defects": truth},
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    path.write_text(header + body, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--clean", required=True, help="Clean article .md path")
    parser.add_argument("--defects", required=True, help="Defect spec YAML path")
    parser.add_argument("--out-article", help="Path to write defective article")
    parser.add_argument("--out-truth", help="Path to write ground truth YAML")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify the spec applies to the clean article; do not write outputs",
    )
    args = parser.parse_args(argv)

    clean_path = Path(args.clean).resolve()
    defects_path = Path(args.defects).resolve()
    if not clean_path.exists():
        print(f"error: clean article not found: {clean_path}", file=sys.stderr)
        return 2
    if not defects_path.exists():
        print(f"error: defects spec not found: {defects_path}", file=sys.stderr)
        return 2

    clean_text = clean_path.read_text(encoding="utf-8")
    defects = load_defects(defects_path)

    verify_issues = verify_defects(clean_text, defects)
    if verify_issues:
        print("Verification issues:", file=sys.stderr)
        for issue in verify_issues:
            print(f"  - {issue}", file=sys.stderr)
        if args.verify:
            return 1 if any("not present" in i for i in verify_issues) else 0

    if args.verify:
        print(f"OK: {len(defects)} defects all applicable to {clean_path.name}")
        return 0

    if not args.out_article or not args.out_truth:
        print(
            "error: --out-article and --out-truth required when not in --verify mode",
            file=sys.stderr,
        )
        return 2

    defective_text, truth = inject_defects(clean_text, defects)
    out_article = Path(args.out_article).resolve()
    out_truth = Path(args.out_truth).resolve()
    out_article.parent.mkdir(parents=True, exist_ok=True)
    out_article.write_text(defective_text, encoding="utf-8")
    write_ground_truth(out_truth, clean_path, out_article, truth)

    applied_count = sum(1 for t in truth if t.get("applied"))
    print(f"Injected {applied_count}/{len(defects)} defects")
    print(f"Wrote: {out_article}")
    print(f"Wrote: {out_truth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
