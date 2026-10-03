"""Audit Python and Node.js dependencies for security vulnerabilities.

Enforces blocking gates on Critical and High vulnerabilities while allowing
audited suppressions via .pip-audit-ignore.yaml.

Reference issue: learn-ukrainian-infra-private#703
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


def load_pip_audit_ignores(ignore_file: Path) -> list[str]:
    """Load list of suppressed vulnerability IDs from YAML config."""
    if not ignore_file.exists():
        return []
    with open(ignore_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    vulns = data.get("vulnerabilities", [])
    ignore_ids: list[str] = []
    for item in vulns:
        if isinstance(item, dict) and "id" in item:
            ignore_ids.append(str(item["id"]).strip())
        elif isinstance(item, str):
            ignore_ids.append(item.strip())
    return [i for i in ignore_ids if i]


def audit_python(repo_root: Path, ignore_file: Path) -> int:
    """Run pip-audit on requirements-lock.txt with suppressions."""
    req_file = repo_root / "requirements-lock.txt"
    if not req_file.exists():
        print(
            f"[audit_dependencies] Error: {req_file} not found; missing required inputs fail closed.", file=sys.stderr
        )
        return 1

    ignored_ids = load_pip_audit_ignores(ignore_file)
    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(req_file),
        "--desc",
        "--progress-spinner=off",
    ]
    for vuln_id in ignored_ids:
        cmd.extend(["--ignore-vuln", vuln_id])

    print(f"[audit_dependencies] Running pip-audit with {len(ignored_ids)} suppressed vulnerability ID(s)...")
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=300)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)

    return res.returncode


SEVERITY_ORDER: dict[str, int] = {
    "info": 1,
    "low": 2,
    "moderate": 3,
    "medium": 3,
    "high": 4,
    "critical": 5,
}
SEVERITY_BY_RANK: dict[int, str] = {
    1: "info",
    2: "low",
    3: "moderate",
    4: "high",
    5: "critical",
}


def load_npm_audit_ignores(ignore_file: Path | None) -> list[str]:
    """Load list of suppressed vulnerability IDs / package names from YAML config."""
    if not ignore_file or not ignore_file.exists():
        return []
    with open(ignore_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    vulns = data.get("vulnerabilities", [])
    ignore_ids: list[str] = []
    for item in vulns:
        if isinstance(item, dict):
            has_id = bool(item.get("id") and str(item["id"]).strip())
            has_cve = bool(item.get("cve") and str(item["cve"]).strip())
            if has_id:
                ignore_ids.append(str(item["id"]).strip().upper())
            if has_cve:
                ignore_ids.append(str(item["cve"]).strip().upper())
            if not has_id and not has_cve and item.get("package") and str(item["package"]).strip():
                ignore_ids.append(str(item["package"]).strip().lower())
        elif isinstance(item, str):
            val = item.strip()
            if val:
                ignore_ids.append(val)
    return [i for i in ignore_ids if i]


def is_advisory_suppressed(
    item: dict,
    ignored_set: set[str],
    ignored_pkgs: set[str],
) -> bool:
    """Check if an advisory dict is suppressed by ID, CVE, or package fallback."""
    for field in ("url", "title", "id", "name", "source"):
        val = str(item.get(field, ""))
        if not val:
            continue
        ghsa = re.search(r"GHSA-[a-z0-9-]+", val, re.IGNORECASE)
        if ghsa and ghsa.group(0).upper() in ignored_set:
            return True
        cve = re.search(r"CVE-\d{4}-\d+", val, re.IGNORECASE)
        if cve and cve.group(0).upper() in ignored_set:
            return True
        if val.upper() in ignored_set:
            return True

    dep = str(item.get("dependency", item.get("name", ""))).lower()
    return bool(dep and dep in ignored_pkgs)


def filter_npm_audit_vulnerabilities(vulns: dict, ignored_list: list[str]) -> tuple[set[str], dict]:
    """Filter npm audit v2 vulnerabilities against audited suppression IDs.

    Returns (suppressed_packages, unsuppressed_vulnerabilities).
    """
    ignored_set = {i.upper() for i in ignored_list}
    ignored_pkgs = {
        i.lower() for i in ignored_list if not (i.upper().startswith(("GHSA-", "CVE-", "PYSEC-")) or i.isdigit())
    }

    direct_rank: dict[str, int] = {}
    unsuppressed_direct: dict[str, list[dict]] = {}

    for pkg_name, details in vulns.items():
        via_items = details.get("via", [])
        direct_advisories = [v for v in via_items if isinstance(v, dict)]
        transitive_deps = [v for v in via_items if isinstance(v, str)]

        unsuppressed_adv: list[dict] = []
        max_rank = 0

        for adv in direct_advisories:
            if is_advisory_suppressed(adv, ignored_set, ignored_pkgs):
                continue
            unsuppressed_adv.append(adv)
            sev = SEVERITY_ORDER.get(str(adv.get("severity", "")).lower(), 0)
            if sev == 0:
                sev = SEVERITY_ORDER.get(str(details.get("severity", "")).lower(), SEVERITY_ORDER["high"])
            if sev > max_rank:
                max_rank = sev

        if not direct_advisories and not transitive_deps:
            if pkg_name.lower() in ignored_pkgs:
                max_rank = 0
            else:
                max_rank = SEVERITY_ORDER.get(str(details.get("severity", "")).lower(), 0)

        direct_rank[pkg_name] = max_rank
        unsuppressed_direct[pkg_name] = unsuppressed_adv

    effective_rank = dict(direct_rank)
    changed = True
    while changed:
        changed = False
        for pkg_name, details in vulns.items():
            transitive_deps = [v for v in details.get("via", []) if isinstance(v, str)]
            current_rank = effective_rank[pkg_name]
            for dep in transitive_deps:
                dep_rank = effective_rank.get(dep, 0)
                if dep_rank > current_rank:
                    current_rank = dep_rank
            if current_rank > effective_rank[pkg_name]:
                effective_rank[pkg_name] = current_rank
                changed = True

    suppressed_pkgs: set[str] = set()
    unsuppressed: dict[str, dict] = {}

    for pkg_name, details in vulns.items():
        if effective_rank[pkg_name] == 0:
            suppressed_pkgs.add(pkg_name)
        else:
            transitive_deps = [v for v in details.get("via", []) if isinstance(v, str)]
            remaining_via = list(unsuppressed_direct[pkg_name]) + [
                dep for dep in transitive_deps if effective_rank.get(dep, 0) > 0
            ]
            info = dict(details)
            info["severity"] = SEVERITY_BY_RANK.get(effective_rank[pkg_name], details.get("severity", "high"))
            info["via"] = remaining_via
            unsuppressed[pkg_name] = info

    return suppressed_pkgs, unsuppressed


def audit_node(repo_root: Path, ignore_file: Path | None = None) -> int:
    """Run npm audit on production dependencies in repository root and site/."""
    targets = [
        ("root", repo_root),
        ("site", repo_root / "site"),
    ]
    ignored_ids = load_npm_audit_ignores(ignore_file) if ignore_file else []
    print(f"[audit_dependencies] Running npm audit with {len(ignored_ids)} suppressed vulnerability ID(s)...")

    exit_code = 0
    for label, target_dir in targets:
        pkg_file = target_dir / "package.json"
        lock_file = target_dir / "package-lock.json"
        if not pkg_file.exists() or not lock_file.exists():
            print(
                f"[audit_dependencies] Error: {pkg_file} or {lock_file} not found; missing required inputs fail closed.",
                file=sys.stderr,
            )
            return 1

        cmd = ["npm", "audit", "--omit=dev", "--audit-level=high", "--json"]
        print(f"[audit_dependencies] Running npm audit in {label} ({target_dir})...")
        res = subprocess.run(cmd, cwd=target_dir, capture_output=True, text=True, timeout=120)

        if res.returncode == 0:
            print(f"[audit_dependencies] npm audit ({label}): found 0 high/critical vulnerabilities.")
            continue

        try:
            audit_data = json.loads(res.stdout)
        except (ValueError, TypeError):
            print(f"[audit_dependencies] ERROR: Failed to parse npm audit JSON output in {label}:", file=sys.stderr)
            if res.stderr:
                print(res.stderr, file=sys.stderr)
            return 1

        if not isinstance(audit_data, dict):
            print(
                f"[audit_dependencies] ERROR: Unexpected npm audit report format (expected JSON object) in {label}.",
                file=sys.stderr,
            )
            return 1

        if "error" in audit_data:
            err = audit_data["error"]
            err_msg = err.get("summary") or err.get("detail") or err.get("code") or str(err)
            print(f"[audit_dependencies] ERROR: npm audit reported an error in {label}: {err_msg}", file=sys.stderr)
            return 1

        if "vulnerabilities" not in audit_data:
            print(
                f"[audit_dependencies] ERROR: Invalid npm audit report (missing 'vulnerabilities') in {label}.",
                file=sys.stderr,
            )
            return 1

        vulns = audit_data["vulnerabilities"]
        if not isinstance(vulns, dict):
            print(
                f"[audit_dependencies] ERROR: Invalid npm audit report ('vulnerabilities' is not an object) in {label}.",
                file=sys.stderr,
            )
            return 1

        if not vulns and res.returncode != 0:
            print(
                f"[audit_dependencies] ERROR: npm audit exited with code {res.returncode} but reported no vulnerabilities in {label}.",
                file=sys.stderr,
            )
            return 1

        suppressed, unsuppressed = filter_npm_audit_vulnerabilities(vulns, ignored_ids)
        high_critical_unsuppressed = {
            pkg: info for pkg, info in unsuppressed.items() if info.get("severity") in {"high", "critical"}
        }

        if high_critical_unsuppressed:
            print(
                f"[audit_dependencies] ERROR: Found {len(high_critical_unsuppressed)} unsuppressed High/Critical vulnerable package(s) in {label}:",
                file=sys.stderr,
            )
            for pkg, info in high_critical_unsuppressed.items():
                via_desc = []
                for v in info.get("via", []):
                    if isinstance(v, dict):
                        via_desc.append(f"{v.get('title', v.get('name'))} ({v.get('url', '')})")
                    else:
                        via_desc.append(str(v))
                print(
                    f"  - {pkg} ({info.get('severity', 'unknown')} severity): via {', '.join(via_desc)}",
                    file=sys.stderr,
                )
            exit_code = 1
        elif suppressed:
            print(
                f"[audit_dependencies] npm audit ({label}): all High/Critical vulnerable package(s) match audited suppressions."
            )
        else:
            print(f"[audit_dependencies] npm audit ({label}): no unsuppressed High/Critical vulnerabilities.")

    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit production dependencies for vulnerabilities.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root directory",
    )
    parser.add_argument(
        "--ignore-file",
        type=Path,
        default=None,
        help="Path to .pip-audit-ignore.yaml",
    )
    parser.add_argument(
        "--npm-ignore-file",
        type=Path,
        default=None,
        help="Path to npm-audit-ignore.yaml",
    )
    parser.add_argument("--skip-python", action="store_true", help="Skip Python pip-audit")
    parser.add_argument("--skip-node", action="store_true", help="Skip Node.js npm audit")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.ignore_file:
        ignore_file = args.ignore_file.resolve()
    else:
        config_path = repo_root / "scripts" / "config" / "pip-audit-ignore.yaml"
        ignore_file = config_path if config_path.exists() else repo_root / ".pip-audit-ignore.yaml"

    if args.npm_ignore_file:
        npm_ignore_file = args.npm_ignore_file.resolve()
    else:
        npm_config_path = repo_root / "scripts" / "config" / "npm-audit-ignore.yaml"
        npm_ignore_file = npm_config_path if npm_config_path.exists() else repo_root / ".npm-audit-ignore.yaml"

    exit_code = 0

    if not args.skip_python:
        py_code = audit_python(repo_root, ignore_file)
        if py_code != 0:
            print(f"[audit_dependencies] ERROR: pip-audit failed with exit code {py_code}", file=sys.stderr)
            exit_code = py_code

    if not args.skip_node:
        node_code = audit_node(repo_root, npm_ignore_file)
        if node_code != 0:
            print(f"[audit_dependencies] ERROR: npm audit failed with exit code {node_code}", file=sys.stderr)
            if exit_code == 0:
                exit_code = node_code

    if exit_code == 0:
        print("[audit_dependencies] All dependency security audits passed.")
    else:
        print("[audit_dependencies] One or more dependency audits failed. Action required.", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
