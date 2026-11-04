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
import json
import re
import subprocess
import tomllib
from functools import cache
from pathlib import Path

import pytest
import yaml

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
CANDIDATE = (
    r"playwright|puppeteer|chromium|webkit|firefox|sandbox|connectOverCDP|connect_over_cdp|connectOptions"
    r"|PW_TEST_CONNECT|mermaid"
)

PLAYWRIGHT_PACKAGE = r"(?:@playwright/test|playwright(?:-core)?)(?:/[^'\"]*)?"
# Outside the launcher, these are the only runtime values a file may import from a Playwright
# package; type-only imports are always fine. Everything else, including `default`, could
# reach a browser type.
JS_IMPORTABLE = {"@playwright/test": {"expect", "devices", "defineConfig"}}
LAUNCH_CALL = re.compile(
    r"\b(?:chromium|firefox|webkit|_electron|_android|browser_?[tT]ype)\s*\.\s*"
    r"(?:launch\w*|connect\w*)\s*\(|\bconnect(?:OverCDP|_over_cdp)\s*\("
    # A launched browser hands back its browser type: browser.browserType() / browser.browser_type.
    r"|\.\s*browserType\s*\(|\.\s*browser_type\b"
)
JS_NAMED_IMPORT = re.compile(rf"import\s*\{{([^}}]*)\}}\s*from\s*['\"]({PLAYWRIGHT_PACKAGE})['\"]")
# Outside the launchers, a Playwright package may be named only in these places. The guard
# keys on the package name itself, wherever it appears in code: in an import, a require(),
# a string, an embedded command or another language's snippet, in any quoting. A new call
# shape or quoting cannot get past it; only a package name built at runtime could.
PLAYWRIGHT_TOKEN = re.compile(
    r"(?<![\w-])(?:@playwright/test|playwright(?:-core)?)(?![\w-])"
    # Config file names such as playwright.config.ts are not the package.
    r"(?!\.(?:[\w-]+\.)*config\b)"
)
# Another package with playwright in its name, such as @axe-core/playwright.
OTHER_SCOPED_PACKAGE = re.compile(r"@(?!playwright/)[\w.-]+/[\w.-]+")
# `playwright test` runs the specs through the Playwright configs, which the guard pins.
PLAYWRIGHT_TEST_CLI = re.compile(r"\bplaywright\s+test\b")
# In JS, the allowed places are these.
JS_ALLOWED_PACKAGE_USE = re.compile(
    # A named import; its names are checked against JS_IMPORTABLE separately.
    rf"import\s*\{{[^}}]*\}}\s*from\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]"
    rf"|(?:import|export)\s+type\b[^;'\"`]*?from\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]"
    # A type position such as import('@playwright/test').Page.
    rf"|\bimport\s*\(\s*['\"]{PLAYWRIGHT_PACKAGE}['\"]\s*\)\s*\.\s*[A-Z]\w*"
)
# Test fixtures that hand a spec a browser type it could launch itself.
JS_BROWSER_FIXTURE = re.compile(r"async\s*\(\s*\{[^}]*\b(?:browserType|playwright)\b[^}]*\}")
JS_PLAYWRIGHT_BROWSER_TYPE = re.compile(r"\bplaywright\s*\.\s*(?:chromium|firefox|webkit|_electron|_android)\b")
PY_USES_PLAYWRIGHT = re.compile(
    r"^\s*(?:from|import)\s+playwright\b|(?:import_module|__import__)\(\s*['\"]playwright", re.M
)
# In a Python file that uses Playwright: any browser-type reference (attribute, getattr or
# subscript string) and any launch or connect call belong in the launcher.
PY_BROWSER_ACCESS = re.compile(
    r"\.\s*(?:chromium|firefox|webkit)\b|['\"][^'\"\n]*\b(?:chromium|firefox|webkit)\b"
    r"|\.\s*(?:launch|launch_persistent_context|launch_server|connect|connect_over_cdp)\s*\("
)
# Chrome accepts a switch with one or two leading dashes.
SANDBOX_FLAG = re.compile(
    r"(?<![\w-])--?(?:no-sandbox|disable-(?:setuid|namespace|seccomp-filter|gpu)-sandbox|no-zygote-sandbox)\b"
)
# Only the launchers set the Chromium sandbox option, so its name appears nowhere else,
# whatever the value or spelling.
SANDBOX_OPTION = re.compile(r"chromium_?[sS]andbox")
# Runtime Playwright entry points a Python module could launch a browser from.
PY_RUNTIME_ENTRY = {"async_playwright", "sync_playwright", "async_api", "sync_api", "_impl", "*"}
BROWSER_DOWNLOAD = re.compile(r"\bplaywright(?:-core)?\s+install\b")
# A browser Playwright Test connects to was started elsewhere, unhardened.
REMOTE_BROWSER = re.compile(r"\bconnectOptions\b|\bPW_TEST_CONNECT_WS_ENDPOINT\b")
PLAYWRIGHT_MCP = re.compile(r"@playwright/mcp|\bplaywright-mcp\b|mcp-server-playwright|mcp__playwright")

# Files that name a Playwright package for a reason other than loading it, with the exact
# number of mentions; one more fails, one fewer asks to update the count.
PLAYWRIGHT_TOKEN_EXEMPT = {
    "scripts/agent_runtime/npm_guard.py": (1, "the npx program allowlist names the playwright program"),
    "tests/agent_runtime/test_npm_shim.py": (3, "argv cases for that npx allowlist"),
    "tests/fixtures/ci_timings/sample_ci_runs.json": (13, "recorded CI job names"),
    "docs/l2-uk-en/v4-seminar-section-templates.yaml": (1, "the English word playwright in seminar prose"),
}
# npm writes lockfiles and never runs anything from them; they only record dependencies.
LOCKFILE_NAMES = ("package-lock.json",)
# Learner content and lexicon data: nothing executes them, and their prose uses the English
# word playwright. Every other rule still reads them.
DATA_TREES = ("curriculum/", "registry/")

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


def _strip_js_comments(text: str) -> str:
    """Drop JS comments (a comment can sit inside an import); strings and templates stay intact."""
    out, i, quote = [], 0, ""
    while i < len(text):
        char = text[i]
        if quote:
            out.append(char)
            if char == "\\":
                out.append(text[i + 1 : i + 2])
                i += 1
            elif char == quote:
                quote = ""
        elif char in "'\"`":
            quote = char
            out.append(char)
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end < 0 else end + 1
            out.append(" ")
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = (len(text) if end < 0 else end) - 1
        else:
            out.append(char)
        i += 1
    return "".join(out)


def _read_code(path: str) -> str:
    text = _read(path)
    return _strip_js_comments(text) if path.endswith(JS_SUFFIXES) else text


def _files(suffixes: tuple[str, ...]) -> list[str]:
    return [p for p in _candidates() if p.endswith(suffixes)]


def _json_strings(node: object) -> list[str]:
    if isinstance(node, dict):
        return [s for value in node.values() for s in _json_strings(value)]
    if isinstance(node, list):
        return [s for value in node for s in _json_strings(value)]
    return [node] if isinstance(node, str) else []


def _strip_shell_comments(text: str) -> str:
    """Drop shell comments: a `#` that starts a word outside quotes, to the end of the line."""
    out, i, quote = [], 0, ""
    while i < len(text):
        char = text[i]
        if quote:
            if char == "\\" and quote == '"':
                out.append(text[i : i + 2])
                i += 2
                continue
            if char == quote:
                quote = ""
        elif char == "\\":
            out.append(text[i : i + 2])
            i += 2
            continue
        elif char in "'\"":
            quote = char
        elif char == "#" and (i == 0 or text[i - 1] in " \t\n;&|()"):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        out.append(char)
        i += 1
    return "".join(out)


def _code_strings(path: str) -> list[str]:
    """The parts of a file that can hold runnable code, comments left out.

    JS: the text. Python: every string constant (code itself is checked by its imports).
    JSON, YAML and TOML: every string value, such as package.json scripts or a CI `run:`
    step; keys such as dependency names are not code. Shell: the text. A data file that
    does not parse is read whole.
    """
    text = _read_code(path)
    if path.endswith(JS_SUFFIXES):
        return [text]
    if path.endswith(".py"):
        tree = ast.parse(text, filename=path)
        return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    try:
        if path.endswith(".json"):
            return _json_strings(json.loads(text))
        if path.endswith((".yml", ".yaml")):
            return [s for doc in yaml.safe_load_all(text) for s in _json_strings(doc)]
        if path.endswith(".toml"):
            return _json_strings(tomllib.loads(text))
    except (ValueError, yaml.YAMLError):
        return [text]
    return [_strip_shell_comments(text)]


def _playwright_mentions(path: str) -> list[str]:
    """Each place `path` names a Playwright package outside the allowed places."""
    if path in LAUNCHERS or path.endswith(LOCKFILE_NAMES) or path.startswith(DATA_TREES):
        return []
    mentions = []
    for code in _code_strings(path):
        code = OTHER_SCOPED_PACKAGE.sub(lambda m: " " * len(m.group(0)), code)
        allowed = [m.span() for m in PLAYWRIGHT_TEST_CLI.finditer(code)]
        if path.endswith(JS_SUFFIXES):
            allowed += [m.span() for m in JS_ALLOWED_PACKAGE_USE.finditer(code)]
        mentions += [
            " ".join(code[max(0, m.start() - 40) : m.end() + 20].split())
            for m in PLAYWRIGHT_TOKEN.finditer(code)
            if not any(start <= m.start() and m.end() <= end for start, end in allowed)
        ]
    return mentions


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
    # Callers cannot pass Chrome flags at all.
    with pytest.raises(TypeError):
        browser_launcher.hardened_launch_options(args=["-no-sandbox"])  # type: ignore[call-arg]
    assert "'args'" not in node.split("const CALLER_OPTIONS = new Set(")[1].split(")")[0]


def test_only_the_shared_launchers_launch_a_playwright_browser() -> None:
    offenders = []
    for path in _files((*JS_SUFFIXES, ".py")):
        if path in LAUNCHERS:
            continue
        text = _read_code(path)
        offenders += [f"{path}: {m.group(0)}" for m in LAUNCH_CALL.finditer(text)]
        if path.endswith(JS_SUFFIXES):
            for match in JS_NAMED_IMPORT.finditer(text):
                allowed = JS_IMPORTABLE.get(match.group(2), set()) | {"test"}  # `test` has its own rule
                if bad := _imported_names(match.group(1)) - allowed:
                    offenders.append(f"{path}: imports {sorted(bad)} from {match.group(2)}")
            offenders += [f"{path}: {m.group(0)}" for m in JS_BROWSER_FIXTURE.finditer(text)]
            offenders += [f"{path}: {m.group(0)}" for m in JS_PLAYWRIGHT_BROWSER_TYPE.finditer(text)]
        elif PY_USES_PLAYWRIGHT.search(text):
            offenders += [f"{path}: {m.group(0)}" for m in PY_BROWSER_ACCESS.finditer(text)]
    for path in _files(CODE_SUFFIXES):
        if path in LAUNCHERS:
            continue
        if not path.endswith((*JS_SUFFIXES, ".py")):
            for code in _code_strings(path):
                offenders += [f"{path}: embedded {m.group(0)}" for m in LAUNCH_CALL.finditer(code)]
        offenders += [f"{path}: {m.group(0)}" for m in REMOTE_BROWSER.finditer(_read_code(path))]
        mentions = _playwright_mentions(path)
        expected = PLAYWRIGHT_TOKEN_EXEMPT.get(path, (0, ""))[0]
        if len(mentions) != expected:
            offenders += [f"{path}: names a Playwright package outside an allowed import: {m}" for m in mentions]
            offenders += [f"{path}: expected {expected} exempt mentions, found {len(mentions)}"] if expected else []
    assert not offenders, "launch browsers through the shared hardened launcher:\n" + "\n".join(offenders)


def test_playwright_test_files_use_the_hardened_fixture() -> None:
    offenders = []
    for path in _files(JS_SUFFIXES):
        if path == NODE_LAUNCHER:
            continue
        for match in JS_NAMED_IMPORT.finditer(_read_code(path)):
            if "test" in _imported_names(match.group(1)):
                offenders.append(f"{path}: import test from {NODE_LAUNCHER}")
    assert not offenders, "\n".join(offenders)


def test_playwright_configs_use_the_hardened_launch_options() -> None:
    configs = [p for p in _files(JS_SUFFIXES) if re.search(r"(^|/)playwright[\w.-]*\.config\.\w+$", p)]
    assert configs, "expected at least one Playwright config"
    offenders = []
    for path in configs:
        text = _read_code(path)
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
        if re.search(r"from\s*['\"](?:rehype-mermaid|mermaid-isomorphic)['\"]", text := _read_code(path))
        and "browserType: hardenedChromium" not in text
    ]
    assert not offenders, "pass { browserType: hardenedChromium } to rehype-mermaid: " + ", ".join(offenders)


def test_no_file_disables_a_browser_sandbox() -> None:
    offenders = []
    for path in _candidates():
        text = _read(path)
        hits = [m.group(0) for m in SANDBOX_FLAG.finditer(text)] if path not in SANDBOX_FLAG_EXEMPT else []
        if path not in LAUNCHERS:
            hits += [m.group(0) for m in SANDBOX_OPTION.finditer(text)]
        if hits:
            offenders.append(f"{path}: {sorted(set(hits))}")
    assert not offenders, "the browser sandbox stays on everywhere:\n" + "\n".join(offenders)
    stale = [p for p in SANDBOX_FLAG_EXEMPT if not SANDBOX_FLAG.search(_read(p))]
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


def _is_playwright(module: str) -> bool:
    return module == "playwright" or module.startswith("playwright.")


def test_python_modules_reach_playwright_only_through_the_launcher() -> None:
    """Outside the launcher, Python imports Playwright types only, never its driver."""
    offenders = []
    for path in _files((".py",)):
        if path in LAUNCHERS:
            continue
        for node in ast.walk(ast.parse(_read(path), filename=path)):
            if isinstance(node, ast.Import):
                offenders += [f"{path}:{node.lineno}: import {a.name}" for a in node.names if _is_playwright(a.name)]
            elif isinstance(node, ast.ImportFrom) and node.module and _is_playwright(node.module):
                entry = {a.name for a in node.names} & PY_RUNTIME_ENTRY
                offenders += [f"{path}:{node.lineno}: from {node.module} import {sorted(entry)}"] if entry else []
            elif isinstance(node, ast.Call):
                strings = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                offenders += [f"{path}:{node.lineno}: dynamic import of {v}" for v in strings if _is_playwright(v)]
    assert not offenders, f"Python reaches Playwright's driver only through {PY_LAUNCHER}:\n" + "\n".join(offenders)
