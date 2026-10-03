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
        print(f"[audit_dependencies] Error: {req_file} not found; missing required inputs fail closed.", file=sys.stderr)
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
            if "id" in item:
                ignore_ids.append(str(item["id"]).strip().upper())
            if "cve" in item:
                ignore_ids.append(str(item["cve"]).strip().upper())
            if "package" in item and not item.get("id"):
                ignore_ids.append(str(item["package"]).strip().lower())
        elif isinstance(item, str):
            ignore_ids.append(item.strip().upper())
    return [i for i in ignore_ids if i]


def filter_npm_audit_vulnerabilities(
    vulns: dict, ignored_list: list[str]
) -> tuple[set[str], dict]:
    """Filter npm audit v2 vulnerabilities against audited suppression IDs.

    Returns (suppressed_packages, unsuppressed_vulnerabilities).
    """
    ignored_set = {i.upper() for i in ignored_list}
    ignored_pkgs = {i.lower() for i in ignored_list}

    suppressed_pkgs: set[str] = set()
    changed = True
    while changed:
        changed = False
        for pkg_name, details in vulns.items():
            if pkg_name in suppressed_pkgs:
                continue
            via_items = details.get("via", [])
            all_via_suppressed = True
            for item in via_items:
                if isinstance(item, dict):
                    url = str(item.get("url", ""))
                    ghsa = re.search(r"GHSA-[a-z0-9-]+", url, re.IGNORECASE)
                    cve = re.search(r"CVE-\d{4}-\d+", url, re.IGNORECASE)
                    dep = str(item.get("dependency", item.get("name", ""))).lower()

                    matched = (
                        bool(ghsa and ghsa.group(0).upper() in ignored_set)
                        or bool(cve and cve.group(0).upper() in ignored_set)
                        or bool(dep and (dep in ignored_pkgs or dep.upper() in ignored_set))
                    )

                    if not matched:
                        all_via_suppressed = False
                        break
                elif isinstance(item, str):
                    if item not in suppressed_pkgs:
                        all_via_suppressed = False
                        break
                else:
                    all_via_suppressed = False
                    break
            if all_via_suppressed and via_items:
                suppressed_pkgs.add(pkg_name)
                changed = True

    unsuppressed = {k: v for k, v in vulns.items() if k not in suppressed_pkgs}
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
            print(f"[audit_dependencies] ERROR: Unexpected npm audit report format (expected JSON object) in {label}.", file=sys.stderr)
            return 1

        if "error" in audit_data:
            err = audit_data["error"]
            err_msg = err.get("summary") or err.get("detail") or err.get("code") or str(err)
            print(f"[audit_dependencies] ERROR: npm audit reported an error in {label}: {err_msg}", file=sys.stderr)
            return 1

        if "vulnerabilities" not in audit_data:
            print(f"[audit_dependencies] ERROR: Invalid npm audit report (missing 'vulnerabilities') in {label}.", file=sys.stderr)
            return 1

        vulns = audit_data["vulnerabilities"]
        if not isinstance(vulns, dict):
            print(f"[audit_dependencies] ERROR: Invalid npm audit report ('vulnerabilities' is not an object) in {label}.", file=sys.stderr)
            return 1

        if not vulns and res.returncode != 0:
            print(
                f"[audit_dependencies] ERROR: npm audit exited with code {res.returncode} but reported no vulnerabilities in {label}.",
                file=sys.stderr,
            )
            return 1

        suppressed, unsuppressed = filter_npm_audit_vulnerabilities(vulns, ignored_ids)
        high_critical_unsuppressed = {
            pkg: info
            for pkg, info in unsuppressed.items()
            if info.get("severity") in {"high", "critical"}
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
