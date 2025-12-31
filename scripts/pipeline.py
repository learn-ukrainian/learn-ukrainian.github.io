#!/usr/bin/env python3
"""
Learn Ukrainian Pipeline

Unified command for the full module processing workflow:
1. Lint MD (audit for format issues)
2. Generate MDX (convert to Docusaurus format)
3. Validate MDX (ensure no content loss)
4. Grammar Queue (generate validation queues for error-correction activities)
5. Validate HTML (headless browser check - requires dev server)
6. Sync Landing (update website landing pages with stats) - opt-in

Usage:
    python scripts/pipeline.py [lang_pair] [level] [module_num] [--steps STEPS]

Examples:
    python scripts/pipeline.py                      # All modules, all steps
    python scripts/pipeline.py l2-uk-en a1          # All A1 modules
    python scripts/pipeline.py l2-uk-en a1 5        # Single module
    python scripts/pipeline.py l2-uk-en a1 --steps lint,generate  # Specific steps
    python scripts/pipeline.py l2-uk-en b2 --steps lint,generate,validate_mdx,sync_landing  # With sync
"""

import argparse
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

@dataclass
class StepResult:
    step: str
    success: bool
    message: str
    details: Optional[str] = None

def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            cwd=PROJECT_ROOT
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def step_lint(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Run MD audit/lint."""
    print("\n" + "="*60)
    print("📝 Step 1: Lint Markdown")
    print("="*60)

    cmd = [str(VENV_PYTHON), "scripts/audit_module.py"]

    # Build path based on arguments
    if level and module_num:
        # Find the specific module file
        level_path = CURRICULUM_DIR / lang_pair / level
        module_files = list(level_path.glob(f"{module_num:02d}-*.md")) + list(level_path.glob(f"{module_num}-*.md"))
        # Support module-LEVEL-NUM format (e.g. module-LIT-005.md)
        if level:
            module_files += list(level_path.glob(f"module-{level.upper()}-{module_num:03d}*.md"))
        if module_files:
            cmd.append(str(module_files[0]))
        else:
            return StepResult("lint", False, f"Module {module_num} not found in {level}")
    elif level:
        # All modules in a level
        level_path = CURRICULUM_DIR / lang_pair / level
        if not level_path.exists():
            return StepResult("lint", False, f"Level {level} not found")
        module_files = sorted(level_path.glob("*.md"))
        if not module_files:
            return StepResult("lint", False, f"No modules in {level}")
        # Run audit on each module
        all_passed = True
        failed_modules = []
        for md_file in module_files:
            code, stdout, stderr = run_command([str(VENV_PYTHON), "scripts/audit_module.py", str(md_file)])
            if code != 0 or "FAIL" in stdout:
                all_passed = False
                failed_modules.append(md_file.stem)
            # Print condensed output
            if "PASS" in stdout:
                print(f"  ✅ {md_file.stem}")
            else:
                print(f"  ❌ {md_file.stem}")
                # Show first error
                for line in stdout.split('\n'):
                    if ('❌' in line or 'ERROR' in line.upper()) and not line.strip().startswith('>'):
                        print(f"     {line.strip()}")
                        break

        if all_passed:
            return StepResult("lint", True, f"All {len(module_files)} modules passed lint")
        else:
            return StepResult("lint", False, f"{len(failed_modules)}/{len(module_files)} modules failed",
                            details=", ".join(failed_modules[:5]))
    else:
        return StepResult("lint", False, "Level required for lint step")

    code, stdout, stderr = run_command(cmd)

    if code == 0 and "FAIL" not in stdout:
        return StepResult("lint", True, "Lint passed")
    else:
        return StepResult("lint", False, "Lint failed", details=stdout[:500])

def step_generate(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Generate MDX from MD."""
    print("\n" + "="*60)
    print("🔄 Step 2: Generate MDX")
    print("="*60)

    cmd = [str(VENV_PYTHON), "scripts/generate_mdx.py", lang_pair]
    if level:
        cmd.append(level)
    if module_num:
        cmd.append(str(module_num))

    code, stdout, stderr = run_command(cmd, capture=False)

    if code == 0:
        return StepResult("generate", True, "MDX generation complete")
    else:
        return StepResult("generate", False, "MDX generation failed", details=(stderr or "")[:500])

def step_validate_mdx(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Validate MDX against source MD."""
    print("\n" + "="*60)
    print("✅ Step 3: Validate MDX")
    print("="*60)

    cmd = [str(VENV_PYTHON), "scripts/validate_mdx.py", lang_pair]
    if level:
        cmd.append(level)
    if module_num:
        cmd.append(str(module_num))

    code, stdout, stderr = run_command(cmd, capture=False)

    if code == 0:
        return StepResult("validate_mdx", True, "MDX validation passed")
    else:
        return StepResult("validate_mdx", False, "MDX validation failed", details=(stderr or "")[:500])

def step_grammar_queue(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Generate grammar validation queue from error-correction activities."""
    print("\n" + "="*60)
    print("📋 Step: Generate Grammar Queue")
    print("="*60)

    if not level:
        return StepResult("grammar_queue", False, "Level required for grammar queue")

    level_path = CURRICULUM_DIR / lang_pair / level
    generated = 0
    skipped = 0

    if module_num:
        # Single module
        module_files = list(level_path.glob(f"{module_num:02d}-*.md")) + list(level_path.glob(f"{module_num}-*.md"))
        if not module_files:
            return StepResult("grammar_queue", False, f"Module {module_num} not found")
    else:
        # All modules in level
        module_files = sorted(level_path.glob("*.md"))

    for md_file in module_files:
        cmd = [str(VENV_PYTHON), "scripts/generate_grammar_queue.py", str(md_file)]
        code, stdout, stderr = run_command(cmd)

        if "Generated queue" in stdout:
            generated += 1
            print(f"  ✅ {md_file.stem}")
        else:
            skipped += 1

    if generated > 0:
        return StepResult("grammar_queue", True, f"Generated {generated} queue files ({skipped} skipped)")
    else:
        return StepResult("grammar_queue", True, f"No validatable activities found ({skipped} modules checked)")

def step_validate_html(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Validate HTML rendering with headless browser."""
    print("\n" + "="*60)
    print("🌐 Step 4: Validate HTML")
    print("="*60)

    # Check if dev server is running
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:3000/", timeout=5)
    except:
        print("  ⚠️ Docusaurus dev server not running")
        print("  Start with: cd docusaurus && npm start")
        return StepResult("validate_html", False, "Dev server not running")

    cmd = [str(VENV_PYTHON), "scripts/validate_html.py", lang_pair]
    if level:
        cmd.append(level)
    if module_num:
        cmd.append(str(module_num))

    code, stdout, stderr = run_command(cmd, capture=False)

    if code == 0:
        return StepResult("validate_html", True, "HTML validation passed")
    else:
        return StepResult("validate_html", False, "HTML validation failed", details=(stderr or "")[:500])

def step_sync_landing(lang_pair: str, level: Optional[str], module_num: Optional[int]) -> StepResult:
    """Step 6: Sync landing pages with current stats."""
    print("\n📊 Step 6: Sync Landing Pages")
    print("-" * 40)

    cmd = [str(VENV_PYTHON), "scripts/sync_landing_pages.py"]
    code, stdout, stderr = run_command(cmd, capture=False)

    if code == 0:
        return StepResult("sync_landing", True, "Landing pages synced")
    else:
        return StepResult("sync_landing", False, "Sync failed", details=(stderr or "")[:500])


def run_pipeline(
    lang_pair: str,
    level: Optional[str],
    module_num: Optional[int],
    steps: list[str]
) -> bool:
    """Run the full pipeline."""

    print("\n" + "="*60)
    print("🚀 Learn Ukrainian Pipeline")
    print("="*60)
    print(f"  Language pair: {lang_pair}")
    print(f"  Level: {level or 'all'}")
    print(f"  Module: {module_num or 'all'}")
    print(f"  Steps: {', '.join(steps)}")

    results: list[StepResult] = []

    step_functions = {
        "lint": step_lint,
        "generate": step_generate,
        "validate_mdx": step_validate_mdx,
        "grammar_queue": step_grammar_queue,
        "validate_html": step_validate_html,
        "sync_landing": step_sync_landing,
    }

    for step_name in steps:
        if step_name not in step_functions:
            print(f"\n❌ Unknown step: {step_name}")
            continue

        result = step_functions[step_name](lang_pair, level, module_num)
        results.append(result)

        if not result.success and step_name != "validate_html":
            print(f"\n⛔ Pipeline stopped at {step_name}: {result.message}")
            if result.details:
                print(f"   Details: {result.details}")
            break

    # Summary
    print("\n" + "="*60)
    print("📊 Pipeline Summary")
    print("="*60)

    all_passed = True
    for r in results:
        status = "✅" if r.success else "❌"
        print(f"  {status} {r.step}: {r.message}")
        if not r.success:
            all_passed = False

    if all_passed:
        print("\n✅ PIPELINE PASSED")
    else:
        print("\n❌ PIPELINE FAILED")

    return all_passed

def main():
    print("🚀 Learn Ukrainian Pipeline")
    parser = argparse.ArgumentParser(
        description="Learn Ukrainian unified processing pipeline",
    )
    parser.add_argument("lang_pair", nargs="?", default="l2-uk-en",
                       help="Language pair (default: l2-uk-en)")
    parser.add_argument("level", nargs="?", default=None,
                       help="CEFR level (a1, a2, b1, b2, c1, c2)")
    parser.add_argument("module_num", nargs="?", type=int, default=None,
                       help="Module number")
    parser.add_argument("--steps", default="lint,generate,validate_mdx,grammar_queue,validate_html",
                       help="Comma-separated steps to run (default: all)")

    args = parser.parse_args()

    steps = [s.strip() for s in args.steps.split(",")]

    success = run_pipeline(
        lang_pair=args.lang_pair,
        level=args.level,
        module_num=args.module_num,
        steps=steps
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
