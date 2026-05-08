#!/usr/bin/env python3
"""Scan decision files and git history for lineage backlinks."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DECISIONS_DIR = Path("docs/decisions")
DECISIONS_YAML = DECISIONS_DIR / "decisions.yaml"
COMMIT_SEP = "\x1e"
FIELD_SEP = "\x1f"
PAYLOAD_SEP = "\x1d"
GIT_FORMAT = "%x1e%H%x1f%cI%x1f%s%x1f%B%x1d"
PATCH_SCAN_COMMIT_LIMIT = 200
NON_DECISION_FILENAMES = {"INDEX.md", "README.md"}
MATCH_KIND_PRIORITY = {"path": 0, "patch": 1, "message": 2}


@dataclass
class DecisionRecord:
    """Parsed decision file plus lineage backlinks."""

    decision_id: str
    file_path: str
    aliases: list[str]
    commits: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_commit(
        self,
        sha: str,
        date: str,
        subject: str,
        matched_aliases: set[str],
        match_kind: str,
    ) -> None:
        """Attach one matching commit, merging duplicate path/alias hits."""
        commit = self.commits.setdefault(
            sha,
            {
                "sha": sha,
                "date": date,
                "subject": subject,
                "match_kind": match_kind,
                "matched_aliases": [],
                "prs": [],
            },
        )
        if MATCH_KIND_PRIORITY[match_kind] > MATCH_KIND_PRIORITY[commit["match_kind"]]:
            commit["match_kind"] = match_kind
        commit["matched_aliases"] = sorted(set(commit["matched_aliases"]) | matched_aliases)
        if _matching_aliases(self, subject):
            commit["prs"] = sorted(set(commit["prs"]) | set(_extract_pr_refs(subject)), key=_pr_sort_key)

    def as_dict(self) -> dict[str, Any]:
        commits = sorted(self.commits.values(), key=lambda item: (item["date"], item["sha"]))
        prs = sorted({pr for commit in commits for pr in commit["prs"]}, key=_pr_sort_key)
        dates = [commit["date"] for commit in commits if commit.get("date")]
        return {
            "decision_id": self.decision_id,
            "file_path": self.file_path,
            "aliases": self.aliases,
            "commits": commits,
            "prs": prs,
            "first_cited_at": dates[0] if dates else None,
            "last_cited_at": dates[-1] if dates else None,
        }


def _extract_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}
    try:
        data = yaml.safe_load(parts[0].removeprefix("---\n"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _normalize_adr(value: str) -> str:
    match = re.search(r"^ADR[-\s#]*(\d{1,3})\b", value, re.IGNORECASE)
    return f"ADR-{int(match.group(1)):03d}" if match else ""


def _normal_title(value: str) -> str:
    value = re.sub(r"^ADR[-\s#]*\d{1,3}\s*[:—–.-]\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^(ACCEPTED|RESOLVED|DECISION REQUIRED|Decision Brief)\s*[—–-]\s*", "", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def _load_decision_yaml_ids(project_root: Path) -> dict[str, list[str]]:
    path = project_root / DECISIONS_YAML
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text("utf-8")) or {}
    by_title: dict[str, list[str]] = {}
    for item in data.get("decisions", []):
        dec_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        if dec_id and title:
            by_title.setdefault(_normal_title(title), []).append(dec_id)
    return by_title


def _declared_ids(frontmatter: dict[str, Any], text: str) -> list[str]:
    ids: list[str] = []
    for key in ("decision_id", "decision_ids", "id", "ids", "aliases", "adr", "adr_id"):
        ids.extend(_as_list(frontmatter.get(key)))

    header_text = "\n".join(text.splitlines()[:30])
    for match in re.finditer(r"^\s*(?:>\s*)?\*\*(?:Decision IDs?|ID)\*\*:\s*(.+)$", header_text, re.MULTILINE):
        ids.extend(part.strip(" `") for part in re.split(r"[,;]", match.group(1)) if part.strip())
    return ids


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value = re.sub(r"\s+", " ", value).strip()
        if not value:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def load_decision_records(project_root: Path = PROJECT_ROOT) -> list[DecisionRecord]:
    """Walk docs/decisions/**/*.md and parse decision IDs and aliases."""
    yaml_ids_by_title = _load_decision_yaml_ids(project_root)
    records: list[DecisionRecord] = []

    for path in sorted((project_root / DECISIONS_DIR).glob("**/*.md")):
        if path.name in NON_DECISION_FILENAMES:
            continue
        rel_path = path.relative_to(project_root).as_posix()
        text = path.read_text("utf-8")
        frontmatter = _extract_frontmatter(text)
        heading = _first_heading(text)
        slug = path.stem
        aliases = [slug, rel_path]
        if heading:
            aliases.append(heading)
            stripped_title = re.sub(r"^ADR[-\s#]*\d{1,3}\s*[:—–.-]\s*", "", heading, flags=re.IGNORECASE)
            aliases.append(stripped_title)

        ids = _declared_ids(frontmatter, text)
        adr = _normalize_adr(heading or slug)
        if adr:
            ids.append(adr)
            ids.append(f"dec-{int(adr.removeprefix('ADR-')):03d}")
        if heading:
            ids.extend(yaml_ids_by_title.get(_normal_title(heading), []))
        aliases.extend(ids)

        decision_id = _unique(ids)[0] if _unique(ids) else slug
        records.append(DecisionRecord(decision_id=decision_id, file_path=rel_path, aliases=_unique(aliases)))

    return records


def _run_git(project_root: Path, args: list[str]) -> str:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    result = subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        env=env,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def _commit_count(project_root: Path) -> int:
    output = _run_git(project_root, ["rev-list", "--all", "--count"]).strip()
    return int(output or "0")


def _parse_git_records(output: str) -> list[tuple[str, str, str, str, str]]:
    records = []
    for chunk in output.split(COMMIT_SEP):
        if not chunk.strip():
            continue
        parts = chunk.split(FIELD_SEP, 3)
        if len(parts) != 4:
            continue
        sha, date, subject, rest = parts
        body, _, payload = rest.partition(PAYLOAD_SEP)
        records.append((sha.strip(), date.strip(), subject.strip(), body, payload))
    return records


def _changed_patch_text(payload: str) -> str:
    lines = []
    for line in payload.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            lines.append(line[1:])
    return "\n".join(lines)


def _alias_git_pattern(records: list[DecisionRecord]) -> str:
    aliases = sorted(
        {alias for record in records for alias in record.aliases if len(alias) >= 3},
        key=len,
        reverse=True,
    )
    patterns = []
    for alias in aliases:
        escaped = re.escape(alias)
        escaped = re.sub(r"\\\s+", r"[[:space:]]+", escaped)
        patterns.append(r"(^|[^[:alnum:]_.-])" + escaped + r"([^[:alnum:]_.-]|$)")
    return "|".join(patterns)


def _alias_python_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias)
    escaped = re.sub(r"\\\s+", r"\\s+", escaped)
    return re.compile(rf"(?<![A-Za-z0-9_.-]){escaped}(?![A-Za-z0-9_.-])", re.IGNORECASE)


def _matching_aliases(record: DecisionRecord, text: str) -> set[str]:
    return {alias for alias in record.aliases if _alias_python_pattern(alias).search(text)}


def _extract_pr_refs(text: str) -> list[str]:
    refs = {f"#{match.group(1)}" for match in re.finditer(r"(?<![\w/#])#(\d{2,6})\b", text)}
    refs.update(f"#{match.group(1)}" for match in re.finditer(r"\bPR\s*#?(\d{2,6})\b", text, re.IGNORECASE))
    return sorted(refs, key=_pr_sort_key)


def _pr_sort_key(value: str) -> tuple[int, str]:
    number = re.search(r"\d+", value)
    return (int(number.group(0)) if number else 0, value)


def _scan_path_touches(project_root: Path, by_path: dict[str, DecisionRecord]) -> None:
    output = _run_git(
        project_root,
        ["log", "--all", "--name-only", "--date=iso-strict", f"--format={GIT_FORMAT}", "--", str(DECISIONS_DIR)],
    )
    for sha, date, subject, _body, payload in _parse_git_records(output):
        for line in payload.splitlines():
            record = by_path.get(line.strip())
            if record:
                record.add_commit(sha, date, subject, set(), "path")


def _scan_alias_hits(project_root: Path, records: list[DecisionRecord], *, with_patch_scan: bool = False) -> None:
    pattern = _alias_git_pattern(records)
    if not pattern:
        return
    command = [
        "log",
        "--all",
        "--date=iso-strict",
        "--regexp-ignore-case",
        "--extended-regexp",
        "--grep",
        pattern,
        f"--format={GIT_FORMAT}",
    ]
    output = _run_git(project_root, command)
    for sha, date, subject, body, _payload in _parse_git_records(output):
        text = f"{subject}\n{body}"
        for record in records:
            matched = _matching_aliases(record, text)
            if matched:
                record.add_commit(sha, date, subject, matched, "message")

    commit_count = _commit_count(project_root)
    if commit_count > PATCH_SCAN_COMMIT_LIMIT and not with_patch_scan:
        print(
            "decision_lineage: patch-text scan skipped "
            f"(repo has {commit_count} commits > {PATCH_SCAN_COMMIT_LIMIT} limit); "
            "add --with-patch-scan to force.",
            file=sys.stderr,
        )
        return
    command = ["log", "--all", "-p", "--date=iso-strict", "-G", pattern, f"--format={GIT_FORMAT}", "--", "."]
    output = _run_git(project_root, command)
    for sha, date, subject, body, payload in _parse_git_records(output):
        message_text = f"{subject}\n{body}"
        patch_text = _changed_patch_text(payload)
        for record in records:
            message_matched = _matching_aliases(record, message_text)
            patch_matched = _matching_aliases(record, patch_text)
            matched = message_matched | patch_matched
            if matched:
                match_kind = "message" if message_matched else "patch"
                record.add_commit(sha, date, subject, matched, match_kind)


def _filter_records(records: list[DecisionRecord], decision_id: str | None) -> list[DecisionRecord]:
    if not decision_id:
        return records
    needle = decision_id.casefold()
    return [
        record for record in records
        if record.decision_id.casefold() == needle or any(alias.casefold() == needle for alias in record.aliases)
    ]


def scan_decision_lineage(
    project_root: Path = PROJECT_ROOT,
    decision_id: str | None = None,
    *,
    with_patch_scan: bool = False,
) -> list[dict[str, Any]]:
    """Return lineage records for every markdown file under docs/decisions."""
    records = _filter_records(load_decision_records(project_root), decision_id)
    if not records:
        return []
    by_path = {record.file_path: record for record in records}
    _scan_path_touches(project_root, by_path)
    _scan_alias_hits(project_root, records, with_patch_scan=with_patch_scan)
    return [record.as_dict() for record in records]


def build_lineage_response(
    project_root: Path = PROJECT_ROOT,
    decision_id: str | None = None,
    *,
    with_patch_scan: bool = False,
) -> dict[str, Any]:
    """Build the JSON response shared by the CLI and Monitor API."""
    decisions = scan_decision_lineage(project_root, decision_id=decision_id, with_patch_scan=with_patch_scan)
    return {"count": len(decisions), "decisions": decisions}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan docs/decisions markdown files and git history for decision-lineage backlinks.\n"
            "Use this when you need read-only JSON showing which commits and PR refs cite or touch a decision."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/audit/decision_lineage.py
  .venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008
  .venv/bin/python scripts/audit/decision_lineage.py --decision-id 2026-05-06-broker-stays-on-sqlite

Outputs:
  JSON to stdout only. Does not write files, update DBs, or mutate git state.

Exit codes:
  0 = scan completed
  1 = git scan or argument failure

Related:
  docs/decisions/INDEX.md
  scripts/audit/check_decisions.py
  Monitor API: GET /api/decisions/lineage
  Issue: #1785
""",
    )
    parser.add_argument(
        "--decision-id",
        help="Filter to one decision ID or alias, e.g. ADR-008, dec-007, or a filename slug. Default: all decisions.",
    )
    parser.add_argument(
        "--with-patch-scan",
        action="store_true",
        help=f"Force git patch-text scan even when repo history exceeds {PATCH_SCAN_COMMIT_LIMIT} commits.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        print(
            json.dumps(
                build_lineage_response(decision_id=args.decision_id, with_patch_scan=args.with_patch_scan),
                ensure_ascii=False,
                indent=2,
            )
        )
    except RuntimeError as exc:
        print(f"decision_lineage: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
