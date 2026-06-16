#!/usr/bin/env python3
"""Run deterministic certification checks for one curriculum module.

This wrapper intentionally does not invoke LLM/QG backends. It fails closed on
leftover QG artifacts unless --clean-qg-artifacts removes known untracked files.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
MDX_ROOT = PROJECT_ROOT / "site" / "src" / "content" / "docs"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

if str(PROJECT_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from manifest_utils import get_module_by_number, get_modules_for_level, parse_numbered_slug

from scripts.audit import check_mdx_source_parity

QG_ARTIFACT_NAMES = frozenset({"llm_qg.json", "python_qg.json"})
QG_ARTIFACT_GLOBS = (
    "llm-qg-*-prompt.md",
    "llm-qg-*-response.raw.md",
)


@dataclass(frozen=True)
class ModuleTarget:
    lang_pair: str
    level: str
    slug: str
    local_num: int

    @property
    def label(self) -> str:
        return f"{self.level}/{self.slug}"

    @property
    def module_dir(self) -> Path:
        return CURRICULUM_ROOT / self.level / self.slug

    @property
    def mdx_path(self) -> Path:
        return MDX_ROOT / self.level / f"{self.slug}.mdx"


@dataclass(frozen=True)
class CommandCheck:
    name: str
    command: tuple[str, ...]
    cwd: Path = PROJECT_ROOT


@dataclass(frozen=True)
class QGInspectionFinding:
    code: str
    path: Path
    message: str


@dataclass(frozen=True)
class QGCleanupResult:
    artifacts: tuple[Path, ...]
    removed: tuple[Path, ...]
    refused_tracked: tuple[Path, ...]
    findings: tuple[QGInspectionFinding, ...]


def _rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _rel_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sanitized_git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}


def parse_target(values: list[str]) -> ModuleTarget:
    """Resolve supported target forms into a manifest-backed module target."""
    if len(values) == 1:
        value = values[0]
        if "/" not in value:
            raise ValueError("single-argument target must be LEVEL/slug")
        lang_pair = "l2-uk-en"
        level, module_ref = value.split("/", 1)
    elif len(values) == 2:
        lang_pair = "l2-uk-en"
        level, module_ref = values
    elif len(values) == 3:
        lang_pair, level, module_ref = values
    else:
        raise ValueError("target must be LEVEL MODULE, LEVEL/slug, or l2-uk-en LEVEL MODULE")

    lang_pair = lang_pair.strip().lower()
    level = level.strip().lower()
    module_ref = module_ref.strip()
    if lang_pair != "l2-uk-en":
        raise ValueError("only l2-uk-en is supported by the current manifest utilities")
    if not level or not module_ref:
        raise ValueError("level and module target are required")

    if module_ref.isdigit():
        module = get_module_by_number(level, int(module_ref))
        if module is None:
            raise ValueError(f"unknown module number: {level} {module_ref}")
        return ModuleTarget(lang_pair=lang_pair, level=level, slug=module.slug, local_num=module.local_num)

    _, bare_slug = parse_numbered_slug(module_ref)
    for module in get_modules_for_level(level):
        if module.slug == bare_slug or module.numbered_slug == module_ref:
            return ModuleTarget(lang_pair=lang_pair, level=level, slug=module.slug, local_num=module.local_num)

    raise ValueError(f"unknown module slug: {level}/{module_ref}")


def module_source_files(target: ModuleTarget) -> list[Path]:
    """Return existing curriculum source files that feed this module's MDX."""
    candidates = [
        CURRICULUM_ROOT / "plans" / target.level / f"{target.slug}.yaml",
        target.module_dir / "module.md",
        target.module_dir / "activities.yaml",
        target.module_dir / "vocabulary.yaml",
        target.module_dir / "resources.yaml",
        CURRICULUM_ROOT / target.level / "meta" / f"{target.slug}.yaml",
        CURRICULUM_ROOT / target.level / f"{target.slug}.md",
        CURRICULUM_ROOT / target.level / "activities" / f"{target.slug}.yaml",
        CURRICULUM_ROOT / target.level / "vocabulary" / f"{target.slug}.yaml",
        CURRICULUM_ROOT / target.level / "resources" / f"{target.slug}.yaml",
    ]
    return [path for path in candidates if path.exists()]


def qg_artifacts(module_dir: Path) -> tuple[Path, ...]:
    """Return known QG artifact files directly inside a module directory."""
    if not module_dir.exists():
        return ()

    paths: set[Path] = set()
    for filename in QG_ARTIFACT_NAMES:
        path = module_dir / filename
        if path.is_file():
            paths.add(path)
    for pattern in QG_ARTIFACT_GLOBS:
        paths.update(path for path in module_dir.glob(pattern) if path.is_file())
    return tuple(sorted(paths, key=lambda path: path.name))


def inspect_qg_artifacts(paths: tuple[Path, ...]) -> tuple[QGInspectionFinding, ...]:
    findings: list[QGInspectionFinding] = []
    for path in paths:
        if path.name in QG_ARTIFACT_NAMES:
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError as exc:
                findings.append(QGInspectionFinding("qg-read-error", path, str(exc)))
                continue
            if not raw.strip():
                findings.append(QGInspectionFinding("empty-qg-json", path, "QG JSON artifact is empty"))
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                findings.append(QGInspectionFinding("malformed-qg-json", path, f"QG JSON is malformed: {exc}"))
                continue
            if not isinstance(parsed, dict):
                findings.append(QGInspectionFinding("malformed-qg-json", path, "QG JSON must be an object"))
        elif path.name.endswith("-response.raw.md"):
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError as exc:
                findings.append(QGInspectionFinding("qg-read-error", path, str(exc)))
                continue
            if not raw.strip():
                findings.append(QGInspectionFinding("empty-qg-response", path, "QG raw response is empty"))
    return tuple(findings)


def tracked_paths(repo_root: Path, paths: tuple[Path, ...]) -> set[Path]:
    if not paths:
        return set()
    rels = [_rel_to(path, repo_root) for path in paths]
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--", *rels],
        check=False,
        capture_output=True,
        env=_sanitized_git_env(),
        text=True,
    )
    if proc.returncode != 0:
        return set()
    by_rel = {_rel_to(path, repo_root): path for path in paths}
    return {by_rel[line] for line in proc.stdout.splitlines() if line in by_rel}


def clean_qg_artifacts(module_dir: Path, *, repo_root: Path = PROJECT_ROOT, dry_run: bool = False) -> QGCleanupResult:
    artifacts = qg_artifacts(module_dir)
    findings = inspect_qg_artifacts(artifacts)
    tracked = tracked_paths(repo_root, artifacts)
    removed: list[Path] = []
    refused: list[Path] = []

    for path in artifacts:
        if path in tracked:
            refused.append(path)
            continue
        removed.append(path)
        if not dry_run:
            path.unlink()

    return QGCleanupResult(
        artifacts=artifacts,
        removed=tuple(removed),
        refused_tracked=tuple(refused),
        findings=findings,
    )


def run_qg_guard(target: ModuleTarget, *, clean: bool, dry_run: bool) -> int:
    artifacts = qg_artifacts(target.module_dir)
    if not artifacts:
        print("[OK] QG artifact guard: no QG artifacts found")
        return 0

    findings = inspect_qg_artifacts(artifacts)
    print("[FAIL] QG artifact guard found generated QG files:")
    for path in artifacts:
        print(f"  - {_rel(path)}")
    for finding in findings:
        print(f"  - {finding.code}: {_rel(finding.path)}: {finding.message}")

    if not clean:
        print("Re-run with --clean-qg-artifacts to remove known untracked QG leftovers.")
        return 1

    result = clean_qg_artifacts(target.module_dir, dry_run=dry_run)
    if result.removed:
        action = "would remove" if dry_run else "removed"
        for path in result.removed:
            print(f"  {action}: {_rel(path)}")
    if result.refused_tracked:
        print("Tracked QG artifacts were not removed:")
        for path in result.refused_tracked:
            print(f"  - {_rel(path)}")
        return 1
    if dry_run:
        print("[FAIL] QG artifact dry-run completed; remove artifacts before certification.")
        return 1
    print("[OK] QG artifact guard: cleaned untracked QG artifacts")
    return 0


def build_checks(
    target: ModuleTarget,
    *,
    site_build: bool,
    install_site_deps: bool,
) -> list[CommandCheck]:
    source_files = module_source_files(target)
    checks = [
        CommandCheck(
            "generate MDX",
            (
                str(VENV_PYTHON),
                "scripts/generate_mdx.py",
                target.lang_pair,
                target.level,
                str(target.local_num),
                "--validate",
            ),
        ),
        CommandCheck(
            "validate activities",
            (
                str(VENV_PYTHON),
                "scripts/validate_activities.py",
                target.lang_pair,
                target.level,
                str(target.local_num),
            ),
        ),
        CommandCheck(
            "validate plan config",
            (
                str(VENV_PYTHON),
                "scripts/validate_plan_config.py",
                f"{target.level}/{target.slug}",
            ),
        ),
        CommandCheck(
            "check MDX generation drift",
            (
                str(VENV_PYTHON),
                "scripts/audit/check_mdx_generation_drift.py",
                "--files",
                *(_rel(path) for path in source_files),
            ),
        ),
        CommandCheck("git diff whitespace check", ("git", "diff", "--check")),
    ]

    if site_build:
        site_dir = PROJECT_ROOT / "site"
        if install_site_deps:
            checks.append(CommandCheck("install site dependencies", ("npm", "ci"), cwd=site_dir))
        checks.append(CommandCheck("production site build", ("npm", "run", "build"), cwd=site_dir))

    return checks


def run_check(check: CommandCheck) -> int:
    print(f"\n== {check.name} ==")
    print("$ " + shlex.join(check.command))
    proc = subprocess.run(list(check.command), cwd=check.cwd)
    if proc.returncode == 0:
        print(f"[OK] {check.name}")
    else:
        print(f"[FAIL] {check.name} exited {proc.returncode}")
    return proc.returncode


def run_mdx_source_parity(target: ModuleTarget) -> int:
    print("\n== check MDX source parity ==")
    source_files = module_source_files(target)
    if not source_files:
        print(f"[FAIL] no source files found for {target.label}")
        return 1
    if not target.mdx_path.exists():
        print(f"[FAIL] missing generated MDX: {_rel(target.mdx_path)}")
        return 1

    changed_files = set(source_files)
    changed_files.add(target.mdx_path)
    violations = check_mdx_source_parity.check_parity([target.mdx_path], changed_files)
    for path, message in violations:
        print(f"{_rel(path)}: {message}")
    if violations:
        print("[FAIL] check MDX source parity")
        return 1
    print("[OK] check MDX source parity")
    return 0


def certify(args: argparse.Namespace) -> int:
    try:
        target = parse_target(args.target)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not VENV_PYTHON.exists():
        print(f"ERROR: expected venv python at {_rel(VENV_PYTHON)}", file=sys.stderr)
        return 2

    print(f"Certifying {target.label} with deterministic checks only.")
    rc = run_qg_guard(target, clean=args.clean_qg_artifacts, dry_run=args.dry_run_qg_cleanup)
    if rc != 0:
        return rc

    for check in build_checks(
        target,
        site_build=not args.skip_site_build,
        install_site_deps=args.install_site_deps,
    ):
        rc = run_check(check)
        if rc != 0:
            return rc
        if check.name == "check MDX generation drift":
            rc = run_mdx_source_parity(target)
            if rc != 0:
                return rc

    print(f"\n[OK] {target.label} deterministic certification passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="+",
        help="Module target: LEVEL MODULE, LEVEL/slug, or l2-uk-en LEVEL MODULE",
    )
    parser.add_argument(
        "--clean-qg-artifacts",
        action="store_true",
        help="Remove known untracked QG artifacts before running checks.",
    )
    parser.add_argument(
        "--dry-run-qg-cleanup",
        action="store_true",
        help="Show QG artifact cleanup without deleting files; certification still fails.",
    )
    parser.add_argument(
        "--skip-site-build",
        action="store_true",
        help="Skip npm production build in site/.",
    )
    parser.add_argument(
        "--install-site-deps",
        action="store_true",
        help="Run npm ci in site/ before the production build.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    return certify(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
