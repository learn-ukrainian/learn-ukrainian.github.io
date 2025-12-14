#!/usr/bin/env python3
"""
HTML Validator

Validates that generated MDX renders correctly in the browser.
Uses Playwright to check for JavaScript errors, missing components, etc.

Usage:
    python scripts/validate_html.py [lang_pair] [level] [module_num]

Requires Docusaurus dev server running on port 3000.
"""

import asyncio
import re
import sys
import subprocess
import time
import signal
from pathlib import Path
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page, ConsoleMessage

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DOCUSAURUS_DIR = PROJECT_ROOT / "docusaurus"

BASE_URL = "http://localhost:3000/curricula-opus"

# Activity component names to check for
ACTIVITY_COMPONENTS = [
    'quiz', 'match-up', 'fill-in', 'true-false', 'unjumble',
    'group-sort', 'anagram', 'error-correction', 'cloze',
    'select', 'translate', 'dialogue-reorder', 'mark-the-words'
]

@dataclass
class ValidationResult:
    module: str
    level: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    activities_found: int = 0

class DevServer:
    """Manage Docusaurus dev server lifecycle."""

    def __init__(self):
        self.process = None

    def start(self) -> bool:
        """Start dev server if not running."""
        # Check if already running
        if self._is_running():
            print("  Dev server already running on port 3000")
            return True

        print("  Starting Docusaurus dev server...")
        self.process = subprocess.Popen(
            ["npm", "start"],
            cwd=DOCUSAURUS_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )

        # Wait for server to be ready (max 60s)
        for i in range(60):
            if self._is_running():
                print(f"  Dev server ready (took {i+1}s)")
                return True
            time.sleep(1)

        print("  Failed to start dev server")
        return False

    def stop(self):
        """Stop dev server."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("  Dev server stopped")

    def _is_running(self) -> bool:
        """Check if server is responding."""
        import urllib.request
        try:
            urllib.request.urlopen(BASE_URL, timeout=2)
            return True
        except:
            return False

async def validate_module(page: Page, level: str, module_num: int) -> ValidationResult:
    """Validate a single module page."""
    module_str = f"{module_num:02d}"
    url = f"{BASE_URL}/docs/{level}/module-{module_str}"

    result = ValidationResult(
        module=f"module-{module_str}",
        level=level,
        passed=True
    )

    console_messages = []

    def handle_console(msg: ConsoleMessage):
        if msg.type == "error":
            console_messages.append(msg.text)

    page.on("console", handle_console)

    try:
        # Navigate to page
        response = await page.goto(url, wait_until="networkidle", timeout=30000)

        if not response:
            result.passed = False
            result.errors.append("No response from server")
            return result

        if response.status >= 400:
            result.passed = False
            result.errors.append(f"HTTP {response.status}")
            return result

        # Wait for React to hydrate
        await page.wait_for_timeout(1000)

        # Check for error boundary (React crash)
        error_boundary = await page.query_selector('[class*="errorBoundary"], .theme-doc-markdown h1:has-text("Error")')
        if error_boundary:
            result.passed = False
            result.errors.append("React error boundary triggered")

        # Check for 404 content
        not_found = await page.query_selector('h1:has-text("Page Not Found")')
        if not_found:
            result.passed = False
            result.errors.append("Page not found (404)")
            return result

        # Check for activities section
        activities_section = await page.query_selector('h2:has-text("Activities")')
        if not activities_section:
            result.warnings.append("No Activities section found")

        # Check activity containers for proper content rendering
        # Each activity should have more than 1 button (header help button + actual items)
        activity_check = await page.evaluate('''() => {
            const containers = document.querySelectorAll('[class*="activityContainer"]');
            const results = { total: 0, working: 0, broken: [] };

            containers.forEach(container => {
                results.total++;
                const buttons = container.querySelectorAll('button').length;
                const header = container.querySelector('[class*="activityHeader"]');
                const headerText = header?.innerText?.split('\\n')[1]?.trim() || 'Unknown';

                // Activity is working if it has more than 1 button (help button + items)
                if (buttons > 1) {
                    results.working++;
                } else {
                    // Get title from preceding h3
                    let el = container.previousElementSibling;
                    while (el && el.tagName !== 'H3') {
                        el = el.previousElementSibling;
                    }
                    const title = el?.textContent?.trim() || 'Unknown';
                    results.broken.push(`${title} (${headerText})`);
                }
            });

            return results;
        }''')

        result.activities_found = activity_check['working']

        # Fail if any activities are broken (have header but no content)
        if activity_check['broken']:
            result.passed = False
            for broken_activity in activity_check['broken'][:3]:  # Report first 3
                result.errors.append(f"Activity not rendering: {broken_activity}")

        # Check for JavaScript errors in console
        for msg in console_messages:
            # Filter out noise and non-critical warnings
            if any(skip in msg.lower() for skip in [
                'favicon', 'serviceworker', 'hot update', 'websocket',
                'hydration', 'cannot be a descendant'  # React hydration warnings
            ]):
                continue
            result.console_errors.append(msg[:200])

        if result.console_errors:
            # Only fail on serious errors (not warnings)
            serious_errors = [e for e in result.console_errors if 'error' in e.lower() and 'warning' not in e.lower()]
            if serious_errors:
                result.passed = False
                result.errors.append(f"{len(serious_errors)} JS errors")

        # Check page has content
        content = await page.content()
        if len(content) < 1000:
            result.passed = False
            result.errors.append("Page content too short")

        # Check for Ukrainian text (sanity check)
        ukrainian_pattern = r'[\u0400-\u04FF]{3,}'
        if not re.search(ukrainian_pattern, content):
            result.warnings.append("No Ukrainian text found")

    except Exception as e:
        result.passed = False
        result.errors.append(f"Exception: {str(e)[:100]}")

    return result

async def validate_level(level: str, target_module: int | None = None) -> list[ValidationResult]:
    """Validate all modules in a level."""
    results = []

    # Determine module range
    mdx_dir = PROJECT_ROOT / "docusaurus" / "docs" / level
    if not mdx_dir.exists():
        print(f"  Level {level} not found")
        return results

    module_files = sorted(mdx_dir.glob("module-*.mdx"))
    if not module_files:
        print(f"  No modules in {level}")
        return results

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for mdx_file in module_files:
            match = re.search(r'module-(\d+)', mdx_file.name)
            if not match:
                continue

            module_num = int(match.group(1))

            if target_module and module_num != target_module:
                continue

            result = await validate_module(page, level, module_num)
            results.append(result)

            # Print result
            if result.passed:
                status = "✅"
                extra = ""
                if result.warnings:
                    extra = f" - ⚠️ {result.warnings[0]}"
                elif result.activities_found > 0:
                    extra = f" ({result.activities_found} interactive elements)"
            else:
                status = "❌"
                extra = f" - {result.errors[0]}" if result.errors else ""

            print(f"  {status} Module {module_num:02d}{extra}")

        await browser.close()

    return results

async def main_async():
    args = sys.argv[1:]
    lang_pair = args[0] if args else 'l2-uk-en'
    target_level = args[1].lower() if len(args) > 1 else None
    target_module = int(args[2]) if len(args) > 2 else None

    print("\n🌐 HTML Validator\n")

    # Check dev server
    import urllib.request
    try:
        urllib.request.urlopen(BASE_URL, timeout=5)
        print(f"  Server running at {BASE_URL}\n")
    except Exception as e:
        print("❌ Docusaurus dev server not running or not accessible!")
        print("   Start it with: cd docusaurus && npm start")
        print(f"   Error: {e}")
        sys.exit(1)

    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    all_results = []

    for level in levels:
        if target_level and level != target_level:
            continue

        level_dir = PROJECT_ROOT / "docusaurus" / "docs" / level
        if not level_dir.exists() or not list(level_dir.glob("module-*.mdx")):
            continue

        print(f"📁 Level {level.upper()}")

        results = await validate_level(level, target_module)
        all_results.extend(results)

    # Summary
    passed = sum(1 for r in all_results if r.passed)
    failed = len(all_results) - passed

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("\n❌ VALIDATION FAILED")
        print("\nFailed modules:")
        for r in all_results:
            if not r.passed:
                print(f"  - {r.level}/{r.module}: {', '.join(r.errors)}")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED")
        sys.exit(0)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
