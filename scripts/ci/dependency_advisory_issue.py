"""Scheduled dependency-advisory tracking issue helper (#9871).

Two subcommands support the scheduled ``security-audit.yml`` job:

``collect`` runs pip-audit (requirements-lock.txt) and npm audit (root and
``site/``), keeps only *unsuppressed* findings after the audited ignore files,
and writes them as JSON. Tool failures exit non-zero so a broken audit never
closes the tracking issue.

``plan`` turns a findings file plus the currently open tracking issue number
into an action (``create`` / ``update`` / ``close`` / ``none``) and renders the
issue body. The workflow applies the action with ``gh``.

Reuses the suppression logic from ``scripts/ci/audit_dependencies.py`` so
"unsuppressed" means exactly what the blocking audit enforces: every pip-audit
finding, and High/Critical npm findings.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts.ci.audit_dependencies import (
    filter_npm_audit_vulnerabilities,
    load_npm_audit_ignores,
    load_pip_audit_ignores,
)

ISSUE_LABEL = "dependency-advisory"
ISSUE_TITLE = "Dependency advisories: unsuppressed findings (scheduled audit)"

PIP_AUDIT_TIMEOUT_SECONDS = 300
NPM_AUDIT_TIMEOUT_SECONDS = 120

# npm audit blocks (and therefore reports) at High/Critical; pip-audit has no
# severity gate in audit_dependencies.py, so every unsuppressed finding counts.
NPM_BLOCKING_SEVERITIES = frozenset({"high", "critical"})

_GHSA_RE = re.compile(r"GHSA-[a-z0-9-]+", re.IGNORECASE)
_CVE_RE = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)

Finding = dict[str, str]


def _advisory_id(advisory: dict) -> str:
    """Best stable advisory identifier from an npm audit ``via`` entry."""
    url = str(advisory.get("url", ""))
    match = _GHSA_RE.search(url)
    if match:
        return match.group(0).upper()
    for field in ("url", "title"):
        match = _CVE_RE.search(str(advisory.get(field, "")))
        if match:
            return match.group(0).upper()
    title = str(advisory.get("title", "")).strip()
    if title:
        return title
    source = advisory.get("source")
    return f"npm:{source}" if source else "unknown"


def collect_python_findings(report: dict) -> list[Finding]:
    """Extract unsuppressed findings from ``pip-audit --format json`` output.

    Suppressions are already applied via ``--ignore-vuln`` when pip-audit runs,
    so every vulnerability in the report is unsuppressed. pip-audit's JSON
    carries no severity field; report ``unknown`` rather than inventing one.
    """
    findings: list[Finding] = []
    dependencies = report.get("dependencies", [])
    if not isinstance(dependencies, list):
        return findings
    for dep in dependencies:
        if not isinstance(dep, dict):
            continue
        package = str(dep.get("name", "")).strip()
        for vuln in dep.get("vulns", []) or []:
            if not isinstance(vuln, dict):
                continue
            fix_versions = [str(v) for v in vuln.get("fix_versions", []) or []]
            findings.append(
                {
                    "ecosystem": "python",
                    "package": package,
                    "advisory_id": str(vuln.get("id", "")).strip() or "unknown",
                    "severity": str(vuln.get("severity", "")).strip() or "unknown",
                    "fixed_version": ", ".join(fix_versions) if fix_versions else "none",
                }
            )
    return findings


def collect_npm_findings(vulns: dict, ignored_ids: list[str], *, target: str) -> list[Finding]:
    """Extract unsuppressed High/Critical findings from npm audit v2 JSON."""
    _suppressed, unsuppressed = filter_npm_audit_vulnerabilities(vulns, ignored_ids)
    findings: list[Finding] = []
    for package, info in sorted(unsuppressed.items()):
        severity = str(info.get("severity", "")).lower()
        if severity not in NPM_BLOCKING_SEVERITIES:
            continue
        fix = info.get("fixAvailable")
        fixed_version = str(fix.get("version", "")) if isinstance(fix, dict) else ""
        via = [item for item in info.get("via", []) if isinstance(item, dict)]
        if not via:
            findings.append(
                {
                    "ecosystem": f"npm ({target})",
                    "package": package,
                    "advisory_id": "transitive dependency",
                    "severity": severity,
                    "fixed_version": fixed_version or "see advisory",
                }
            )
            continue
        for advisory in via:
            findings.append(
                {
                    "ecosystem": f"npm ({target})",
                    "package": package,
                    "advisory_id": _advisory_id(advisory),
                    # Report the effective package severity (transitive-max from
                    # filter_npm_audit_vulnerabilities), not the severity of this
                    # one via entry, which can be lower.
                    "severity": severity,
                    "fixed_version": fixed_version or "see advisory",
                }
            )
    return findings


def _run_json_command(cmd: list[str], *, cwd: Path, timeout: int, label: str) -> tuple[dict, int]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    try:
        data = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"{label}: failed to parse JSON output (exit={result.returncode})") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{label}: unexpected report format (expected JSON object)")
    return data, result.returncode


def run_collect(
    repo_root: Path,
    *,
    pip_ignore_file: Path | None = None,
    npm_ignore_file: Path | None = None,
) -> list[Finding]:
    """Run both audits and return unsuppressed findings.

    Exit codes 0 (clean) and 1 (findings) are normal; anything else, a parse
    failure, or an npm audit error payload raises so the job fails instead of
    reporting a false "clean".
    """
    findings: list[Finding] = []

    req_file = repo_root / "requirements-lock.txt"
    if not req_file.exists():
        raise RuntimeError(f"{req_file} not found; missing required inputs fail closed")
    pip_ignore = pip_ignore_file or repo_root / "scripts" / "config" / "pip-audit-ignore.yaml"
    pip_cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(req_file),
        "--format",
        "json",
        "--progress-spinner=off",
    ]
    for vuln_id in load_pip_audit_ignores(pip_ignore):
        pip_cmd.extend(["--ignore-vuln", vuln_id])
    pip_report, pip_code = _run_json_command(
        pip_cmd, cwd=repo_root, timeout=PIP_AUDIT_TIMEOUT_SECONDS, label="pip-audit"
    )
    if pip_code not in (0, 1):
        raise RuntimeError(f"pip-audit failed with exit code {pip_code}")
    findings.extend(collect_python_findings(pip_report))

    npm_ignore = npm_ignore_file or repo_root / "scripts" / "config" / "npm-audit-ignore.yaml"
    ignored_ids = load_npm_audit_ignores(npm_ignore) if npm_ignore.exists() else []
    for label, target_dir in (("root", repo_root), ("site", repo_root / "site")):
        if not (target_dir / "package.json").exists() or not (target_dir / "package-lock.json").exists():
            raise RuntimeError(f"{target_dir}: package.json or package-lock.json missing; fail closed")
        npm_report, npm_code = _run_json_command(
            ["npm", "audit", "--omit=dev", "--json"],
            cwd=target_dir,
            timeout=NPM_AUDIT_TIMEOUT_SECONDS,
            label=f"npm audit ({label})",
        )
        if "error" in npm_report:
            err = npm_report["error"]
            message = err.get("summary") or err.get("detail") or err.get("code") or str(err)
            raise RuntimeError(f"npm audit reported an error in {label}: {message}")
        vulns = npm_report.get("vulnerabilities")
        if not isinstance(vulns, dict):
            raise RuntimeError(f"npm audit ({label}): invalid report (missing 'vulnerabilities' object)")
        if npm_code != 0 and not vulns:
            raise RuntimeError(f"npm audit ({label}) exited {npm_code} but reported no vulnerabilities")
        findings.extend(collect_npm_findings(vulns, ignored_ids, target=label))

    return findings


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip() or "—"


def build_issue_body(findings: list[Finding]) -> str:
    """Render the tracking-issue body for a non-empty findings list."""
    rows = sorted(
        findings,
        key=lambda f: (f["ecosystem"], f["package"], f["advisory_id"]),
    )
    lines = [
        "The scheduled dependency audit on the default branch found **unsuppressed** "
        "dependency advisories. These are the findings the per-PR audit would block on.",
        "",
        "| Ecosystem | Package | Advisory | Severity | Fixed version |",
        "| --- | --- | --- | --- | --- |",
    ]
    for finding in rows:
        lines.append(
            "| {eco} | {pkg} | {adv} | {sev} | {fix} |".format(
                eco=_cell(finding["ecosystem"]),
                pkg=_cell(finding["package"]),
                adv=_cell(finding["advisory_id"]),
                sev=_cell(finding["severity"]),
                fix=_cell(finding["fixed_version"]),
            )
        )
    lines += [
        "",
        "Resolve by upgrading the affected package or adding an audited suppression to "
        "`scripts/config/pip-audit-ignore.yaml` / `scripts/config/npm-audit-ignore.yaml`. "
        "This issue updates on each scheduled run and closes automatically when the audit is clean.",
        "",
        f"_Maintained by the scheduled security audit (#9871). Label: `{ISSUE_LABEL}`._",
    ]
    return "\n".join(lines) + "\n"


def decide_action(findings: list[Finding], issue_number: str) -> str:
    """Map (findings, open tracking issue) to create/update/close/none."""
    if findings:
        return "update" if issue_number else "create"
    return "close" if issue_number else "none"


def write_github_output(values: dict[str, str], path: Path | None = None) -> None:
    output = path
    if output is None:
        raw = os.environ.get("GITHUB_OUTPUT")
        if not raw:
            return
        output = Path(raw)
    with output.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _load_findings(path: Path) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        raise ValueError(f"{path}: expected an object with a 'findings' list")
    return [f for f in data["findings"] if isinstance(f, dict)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Maintain the scheduled dependency-advisory tracking issue from audit findings.\n"
            "Use from the security-audit.yml advisory-issue job; not for the blocking per-PR audit."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ci.dependency_advisory_issue collect --out ci-artifacts/dependency-findings.json\n"
            "  .venv/bin/python -m scripts.ci.dependency_advisory_issue plan --findings ci-artifacts/dependency-findings.json --issue-number 123 --body-out ci-artifacts/advisory-issue-body.md\n"
            "\n"
            "Outputs:\n"
            "  collect: writes a {\"findings\": [...]} JSON file to --out.\n"
            "  plan: writes the rendered issue body to --body-out for create/update and appends\n"
            "  action=<create|update|close|none> and issue_number=<n> to $GITHUB_OUTPUT.\n"
            "\n"
            "Exit codes:\n"
            "  0 on success (a clean audit is success). Non-zero when pip-audit or npm audit\n"
            "  fails, is missing inputs, or returns unparseable output, so a broken audit can\n"
            "  never close the tracking issue.\n"
            "\n"
            "Related:\n"
            "  Suppression logic: scripts/ci/audit_dependencies.py with\n"
            "  scripts/config/pip-audit-ignore.yaml and scripts/config/npm-audit-ignore.yaml.\n"
            "  Workflow: the advisory-issue job in .github/workflows/security-audit.yml (#9871)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    collect_parser = sub.add_parser("collect", help="run audits and write unsuppressed findings JSON")
    collect_parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help=(
            "repository root holding requirements-lock.txt plus root and site/ npm manifests "
            "(default: %(default)s)"
        ),
    )
    collect_parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="findings JSON output path, e.g. ci-artifacts/dependency-findings.json (required)",
    )

    plan_parser = sub.add_parser("plan", help="decide the tracking-issue action and render its body")
    plan_parser.add_argument(
        "--findings",
        type=Path,
        required=True,
        help="findings JSON written by collect (required)",
    )
    plan_parser.add_argument(
        "--issue-number",
        default="",
        help="number of the currently open tracking issue, or empty when none is open (default: '')",
    )
    plan_parser.add_argument(
        "--body-out",
        type=Path,
        required=True,
        help="path to write the rendered issue body for create/update actions (required)",
    )

    args = parser.parse_args(argv)

    if args.command == "collect":
        findings = run_collect(args.repo_root.resolve())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"findings": findings}, indent=2) + "\n", encoding="utf-8")
        print(f"[dependency_advisory_issue] collected {len(findings)} unsuppressed finding(s) -> {args.out}")
        return 0

    findings = _load_findings(args.findings)
    issue_number = str(args.issue_number or "").strip()
    action = decide_action(findings, issue_number)
    if action in {"create", "update"}:
        args.body_out.parent.mkdir(parents=True, exist_ok=True)
        args.body_out.write_text(build_issue_body(findings), encoding="utf-8")
    print(
        f"[dependency_advisory_issue] action={action} findings={len(findings)} "
        f"issue_number={issue_number or 'none'}"
    )
    write_github_output({"action": action, "issue_number": issue_number})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
