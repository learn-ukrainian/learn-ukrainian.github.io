"""Every browser launch stays hardened (#12689, AC-05).

Operator decision 2026-11-03: Playwright runs only against our own trusted
content, through one shared launcher per language. Each launcher starts the
system's installed Google Chrome with its sandbox on and blocks every origin
except the loopback host and learn-ukrainian.github.io. This guard fails when a
file launches Playwright any other way, disables a browser sandbox, downloads
Playwright's bundled browsers, or configures a Playwright MCP server.
"""

from __future__ import annotations

import ast
import re
import subprocess
from functools import cache
from pathlib import Path

import pytest

from scripts.validate import browser_launcher

pytestmark = pytest.mark.repo_wide

ROOT = Path(__file__).resolve().parents[1]
NODE_LAUNCHER = "site/e2e/support/hardened-browser.mjs"
PY_LAUNCHER = "scripts/validate/browser_launcher.py"
LAUNCHERS = {NODE_LAUNCHER, PY_LAUNCHER}
SELF = "tests/test_browser_hardening_guard.py"

JS_SUFFIXES = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts")
CODE_SUFFIXES = (*JS_SUFFIXES, ".py", ".sh", ".bash", ".yml", ".yaml", ".json", ".toml")
# Cheap pre-filter; every rule below only looks at files matching it.
CANDIDATE = r"playwright|puppeteer|chromium|webkit|firefox|sandbox|connectOverCDP|connect_over_cdp|mermaid"

PLAYWRIGHT_PACKAGE = r"(?:@playwright/test|playwright(?:-core)?)(?:/[^'\"]*)?"
BROWSER_TYPES = {"chromium", "firefox", "webkit", "_electron", "_android"}
LAUNCH_CALL = re.compile(
    r"\b(?:chromium|firefox|webkit|_electron|_android|browser_?[tT]ype)\s*\.\s*"
    r"(?:launch\w*|connect\w*)\s*\(|\bconnect(?:OverCDP|_over_cdp)\s*\("
)
JS_NAMED_IMPORT = re.compile(rf"import\s*\{{([^}}]*)\}}\s*from\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]")
JS_WHOLE_IMPORT = re.compile(
    rf"import\s+(?!type\b)(?:\*\s+as\s+)?\w+\s*(?:,\s*\{{[^}}]*\}})?\s*from\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]"
    # import('...').Page is a type position; a runtime dynamic import is not followed by .Type.
    rf"|import\(\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]\s*\)(?!\s*\.\s*[A-Z])"
    rf"|require\(\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]\s*\)"
)
PY_BROWSER_ATTRIBUTE = re.compile(r"\.\s*(?:chromium|firefox|webkit)\b")
SANDBOX_OFF = re.compile(
    r"--no-sandbox\b|--disable-(?:setuid|namespace|seccomp-filter|gpu)-sandbox\b|--no-zygote-sandbox\b"
    r"|chromiumSandbox\s*:\s*false|chromium_sandbox\s*=\s*False"
)
BROWSER_DOWNLOAD = re.compile(r"\bplaywright(?:-core)?\s+install\b")
PLAYWRIGHT_MCP = re.compile(r"@playwright/mcp|\bplaywright-mcp\b|mcp-server-playwright|mcp__playwright")

# Files that name a sandbox flag for a reason other than a browser launch.
SANDBOX_FLAG_EXEMPT = {
    "tests/test_agent_runtime.py": "AGY's CLI has no --no-sandbox flag; a docstring about that CLI, not a browser",
}


@cache
def _candidates() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "grep", "-lIz", "-E", CANDIDATE, "--", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode in (0, 1), result.stderr
    return tuple(sorted(p for p in result.stdout.split("\0") if p.endswith(CODE_SUFFIXES) and p != SELF))


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def _files(suffixes: tuple[str, ...]) -> list[str]:
    return [p for p in _candidates() if p.endswith(suffixes)]


def _imported_names(clause: str) -> set[str]:
    """Value names bound by an import clause; type-only names are skipped."""
    names = set()
    for raw in clause.split(","):
        part = raw.strip()
        if not part or part.startswith("type "):
            continue
        names.add(part.split(" as ")[0].strip())
    return names


def test_the_launchers_pin_installed_chrome_sandbox_and_allowlist() -> None:
    node = _read(NODE_LAUNCHER)
    for needle in ("channel: 'chrome'", "chromiumSandbox: true", "serviceWorkers: 'block'", "'MAP * ~NOTFOUND'"):
        assert needle in node, f"{NODE_LAUNCHER} lost {needle!r}"
    node_hosts = re.search(r"ALLOWED_HOSTS = Object\.freeze\(\[([^\]]*)\]\)", node)
    assert node_hosts, f"{NODE_LAUNCHER} must define ALLOWED_HOSTS"
    assert tuple(re.findall(r"'([^']+)'", node_hosts.group(1))) == browser_launcher.ALLOWED_HOSTS
    assert browser_launcher.ALLOWED_HOSTS == ("localhost", "127.0.0.1", "::1", "learn-ukrainian.github.io")

    options = browser_launcher.hardened_launch_options()
    assert options["channel"] == "chrome"
    assert options["chromium_sandbox"] is True
    assert options["args"] == [f"--host-resolver-rules={browser_launcher.HOST_RESOLVER_RULES}"]
    for flag in ("--no-sandbox", "--disable-setuid-sandbox", "--proxy-server=http://x", "--host-resolver-rules=x"):
        with pytest.raises(ValueError):
            browser_launcher.hardened_launch_options(args=[flag])


def test_only_the_shared_launchers_launch_a_playwright_browser() -> None:
    offenders = []
    for path in _files((*JS_SUFFIXES, ".py")):
        if path in LAUNCHERS:
            continue
        text = _read(path)
        offenders += [f"{path}: {m.group(0)}" for m in LAUNCH_CALL.finditer(text)]
        if path.endswith(JS_SUFFIXES):
            for match in JS_NAMED_IMPORT.finditer(text):
                if bad := _imported_names(match.group(1)) & BROWSER_TYPES:
                    offenders.append(f"{path}: imports {sorted(bad)} from Playwright")
            offenders += [f"{path}: {m.group(0)}" for m in JS_WHOLE_IMPORT.finditer(text)]
        elif re.search(r"^\s*(?:from|import)\s+playwright\b", text, re.M):
            offenders += [f"{path}: {m.group(0)}" for m in PY_BROWSER_ATTRIBUTE.finditer(text)]
    assert not offenders, "launch browsers through the shared hardened launcher:\n" + "\n".join(offenders)


def test_playwright_test_files_use_the_hardened_fixture() -> None:
    offenders = []
    for path in _files(JS_SUFFIXES):
        if path == NODE_LAUNCHER:
            continue
        for match in JS_NAMED_IMPORT.finditer(_read(path)):
            if "test" in _imported_names(match.group(1)):
                offenders.append(f"{path}: import test from {NODE_LAUNCHER}")
    assert not offenders, "\n".join(offenders)


def test_playwright_configs_use_the_hardened_launch_options() -> None:
    configs = [p for p in _files(JS_SUFFIXES) if re.search(r"(^|/)playwright[\w.-]*\.config\.\w+$", p)]
    assert configs, "expected at least one Playwright config"
    offenders = []
    for path in configs:
        text = _read(path)
        projects = text.count("launchOptions: hardenedLaunchOptions(")
        if projects == 0 or text.count("launchOptions:") != projects:
            offenders.append(f"{path}: every launchOptions must be hardenedLaunchOptions()")
        if text.count("channel: 'chrome'") != projects or "...HARDENED_CONTEXT_OPTIONS" not in text:
            offenders.append(f"{path}: every project needs channel 'chrome' and HARDENED_CONTEXT_OPTIONS")
        if re.search(r"\b(?:browserName|connectOptions)\b", text):
            offenders.append(f"{path}: browserName and connectOptions are not allowed")
    assert not offenders, "\n".join(offenders)


def test_libraries_that_launch_chrome_get_the_hardened_browser_type() -> None:
    offenders = [
        path
        for path in _files(JS_SUFFIXES)
        if re.search(r"from\s*['\"](?:rehype-mermaid|mermaid-isomorphic)['\"]", text := _read(path))
        and "browserType: hardenedChromium" not in text
    ]
    assert not offenders, "pass { browserType: hardenedChromium } to rehype-mermaid: " + ", ".join(offenders)


def test_no_file_disables_a_browser_sandbox() -> None:
    offenders = []
    for path in _candidates():
        hits = [m.group(0) for m in SANDBOX_OFF.finditer(_read(path))]
        if hits and path not in SANDBOX_FLAG_EXEMPT:
            offenders.append(f"{path}: {sorted(set(hits))}")
    assert not offenders, "the browser sandbox stays on everywhere:\n" + "\n".join(offenders)
    stale = [p for p in SANDBOX_FLAG_EXEMPT if not SANDBOX_OFF.search(_read(p))]
    assert not stale, f"drop stale exemptions: {stale}"


def test_nothing_downloads_playwright_browsers_or_configures_playwright_mcp() -> None:
    offenders = []
    for path in _candidates():
        text = _read(path)
        offenders += [f"{path}: {m.group(0)}" for m in BROWSER_DOWNLOAD.finditer(text)]
        offenders += [f"{path}: {m.group(0)}" for m in PLAYWRIGHT_MCP.finditer(text)]
    assert not offenders, "use installed Google Chrome; no bundled browsers, no Playwright MCP:\n" + "\n".join(
        offenders
    )


def test_python_playwright_users_import_the_launcher() -> None:
    offenders = []
    for path in _files((".py",)):
        if path in LAUNCHERS:
            continue
        tree = ast.parse(_read(path), filename=path)
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module} | {
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
        }
        uses_playwright = any(m == "playwright" or m.startswith("playwright.") for m in modules)
        if uses_playwright and not any(m.endswith("browser_launcher") for m in modules):
            offenders.append(path)
    assert not offenders, f"Python files using Playwright must launch through {PY_LAUNCHER}: {offenders}"
