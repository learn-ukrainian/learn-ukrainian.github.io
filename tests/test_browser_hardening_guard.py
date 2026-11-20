"""Every browser launch stays hardened (#12689, AC-05).

Operator decision 2026-11-03: Playwright runs only against our own trusted
content, through one shared Node launcher. It starts the
system's installed Google Chrome with its sandbox on and blocks every origin
except the loopback host and learn-ukrainian.github.io. This guard fails when a
file launches Playwright any other way, disables a browser sandbox, downloads
Playwright's bundled browsers, or configures a Playwright MCP server.

This static guard is a good-faith tripwire, not the control of record. It reads
every tracked text file except prose formats (.md, .txt, .html, .csv, .rst),
data files under curriculum/ and registry/ (a package.json is never data).
Lockfiles have a separate inventory of reviewed browser dependencies. The
source scan cannot see a program or package name constructed at runtime.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import tomllib
from functools import cache
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.repo_wide

ROOT = Path(__file__).resolve().parents[1]
NODE_LAUNCHER = "site/e2e/support/hardened-browser.mjs"
SELF = "tests/test_browser_hardening_guard.py"

JS_SUFFIXES = (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts")
CODE_SUFFIXES = (*JS_SUFFIXES, ".py", ".sh", ".bash", ".yml", ".yaml", ".json", ".toml")
# Cheap pre-filter; every rule below only looks at files matching it.
CANDIDATE = (
    r"playwright|[Pp]uppeteer|chromium|webkit|firefox|sandbox|connectOverCDP|connect_over_cdp|connectOptions"
    r"|PW_TEST_CONNECT|_electron|_android|browser_?[tT]ype|chromeLauncher|google-chrome|chrome/chrome"
)

PLAYWRIGHT_PACKAGE = r"(?:@playwright/test|playwright(?:-core)?)(?:/[^'\"]*)?"
# Outside the launcher, these are the only runtime values a file may import from a Playwright
# package; type-only imports are always fine. Everything else, including `default`, could
# reach a browser type.
JS_IMPORTABLE = {"@playwright/test": {"expect", "devices", "defineConfig"}}
LAUNCH_CALL = re.compile(
    r"\b(?:chromium|firefox|webkit|_electron|_android|browser_?[tT]ype|[Pp]uppeteer|chromeLauncher)\s*\.\s*"
    r"(?:launch\w*|connect\w*)\s*\(|\bconnect(?:OverCDP|_over_cdp)\s*\("
    # A launched browser hands back its browser type: browser.browserType() / browser.browser_type.
    r"|\.\s*browserType\s*\(|\.\s*browser_type\b"
)
CHROME_COMMAND = re.compile(
    r"(?m)(?:^|[;&|])[ \t]*(?:exec[ \t]+)?[\"']?(?:[\w./-]*/)?"
    r"(?:google-chrome(?:-stable)?|chromium(?:-browser)?|chrome/chrome)[\"']?"
    r"(?=[ \t;|&]|$)(?![ \t]+--version(?:[ \t]|$))"
    r"|\b(?:spawn|execFile|Popen)(?:Sync)?\s*\(\s*\[?\s*[\"'](?:[\w./-]*/)?"
    r"(?:google-chrome(?:-stable)?|chromium(?:-browser)?|chrome/chrome)[\"']"
)
PUPPETEER_IMPORT = re.compile(
    r"(?:\b(?:from|import)\s+|\b(?:require|import)\s*\(\s*)[\"']"
    r"(?:puppeteer(?:-core)?|@puppeteer/browsers)(?=[\"'/])"
)
JS_NAMED_IMPORT = re.compile(rf"import\s*\{{([^}}]*)\}}\s*from\s*['\"]({PLAYWRIGHT_PACKAGE})['\"]")
# Outside the launcher, a Playwright package may be named only in these places. The guard
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
# Chrome accepts a switch with one or two leading dashes.
SANDBOX_FLAG = re.compile(
    r"(?<![\w-])--?(?:no-sandbox|disable-(?:setuid|namespace|seccomp-filter|gpu)-sandbox|no-zygote-sandbox)\b"
)
# Only the launcher sets the Chromium sandbox option, so its name appears nowhere else,
# whatever the value or spelling.
SANDBOX_OPTION = re.compile(r"chromium_?[sS]andbox")
BROWSER_DOWNLOAD = re.compile(r"\bplaywright(?:-core)?\s+install\b")
# A browser Playwright Test connects to was started elsewhere, unhardened.
REMOTE_BROWSER = re.compile(r"\bconnectOptions\b|\bPW_TEST_CONNECT_WS_ENDPOINT\b")
PLAYWRIGHT_MCP = re.compile(r"@playwright/mcp|\bplaywright-mcp\b|mcp-server-playwright|mcp__playwright")

# Files that name a Playwright package for a reason other than loading it, with the exact
# number of mentions; one more fails, one fewer asks to update the count.
PLAYWRIGHT_TOKEN_EXEMPT = {
    "tests/agent_runtime/test_npm_shim.py": (3, "argv cases for that npx allowlist"),
    "tests/fixtures/ci_timings/sample_ci_runs.json": (13, "recorded CI job names"),
    "docs/l2-uk-en/v4-seminar-section-templates.yaml": (1, "the English word playwright in seminar prose"),
    "site/.gitignore": (1, "the ignore pattern for Playwright's cache directory"),
}
# The token rule reads every tracked text file, whatever its type: code also lives in .jsx,
# .astro frontmatter, .mdx, .vue, extensionless scripts and more. Only prose formats, which
# nothing executes, are left out.
PROSE_SUFFIXES = (".md", ".txt", ".html", ".csv", ".rst")
# npm and uv write lockfiles and never run anything from them; they only record dependencies.
LOCKFILE_NAMES = ("package-lock.json", "uv.lock")
# Learner content and lexicon data files: nothing executes them, and their prose uses the
# English word playwright. A runnable file under these trees still gets the token rule, and
# every other rule still reads them all. A package.json is never data, wherever it sits:
# npm runs its scripts.
DATA_TREES = ("curriculum/", "registry/")
DATA_SUFFIXES = (".json", ".yaml", ".yml", ".toml")
NPM_MANIFEST_NAME = "package.json"

# npm aliases retain the real package name in the installed entry. Check both
# names, at every nesting level, and packages declaring browser dependencies.
BROWSER_PACKAGE = re.compile(
    r"(?:^|[@/_.-])(?:playwright|puppeteer|chromium|chrome|chromedriver|selenium|webdriver(?:io)?"
    r"|geckodriver|firefox|webkit|cypress|pyppeteer|splinter|nodriver|browser-use|mermaid-isomorphic"
    r"|rehype-mermaid)(?=$|[@/_.-])",
    re.IGNORECASE,
)
DEPENDENCY_KEYS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies")
REVIEWED_BROWSER_DEPENDENCIES = {
    "package-lock.json": {
        "direct: puppeteer",
        "node_modules/@puppeteer/browsers",
        "node_modules/chromium-bidi",
        "node_modules/puppeteer",
        "node_modules/puppeteer-core",
        "node_modules/webdriver-bidi-protocol",
    },
    "site/package-lock.json": {
        "direct: @axe-core/playwright",
        "direct: @playwright/test",
        "direct: playwright",
        "node_modules/@axe-core/playwright",
        "node_modules/@playwright/test",
        "node_modules/playwright",
        "node_modules/playwright-core",
        "node_modules/vitest",
    },
    "uv.lock": set(),
}


@cache
def _browser_files() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "grep", "-lIz", "-E", CANDIDATE, "--", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode in (0, 1), result.stderr
    return tuple(sorted(p for p in result.stdout.split("\0") if p and p != SELF))


@cache
def _token_files() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "grep", "-lIz", "-e", "playwright", "--", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode in (0, 1), result.stderr
    return tuple(sorted(p for p in result.stdout.split("\0") if p and not p.endswith(PROSE_SUFFIXES) and p != SELF))


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
    return [p for p in _browser_files() if p.endswith(suffixes)]


def _is_dependency_data(path: str) -> bool:
    return path.endswith(LOCKFILE_NAMES) or (
        path.startswith(DATA_TREES) and path.endswith(DATA_SUFFIXES) and Path(path).name != NPM_MANIFEST_NAME
    )


def _json_strings(node: object) -> list[str]:
    if isinstance(node, dict):
        return [s for value in node.values() for s in _json_strings(value)]
    if isinstance(node, list):
        return [s for value in node for s in _json_strings(value)]
    return [node] if isinstance(node, str) else []


def _code_strings(path: str) -> list[str]:
    """The parts of a file that can hold runnable code.

    JS: the text without comments. Python: every string constant (code itself is checked by
    its imports). JSON, YAML and TOML: every string value, such as package.json scripts or a
    CI `run:` step; keys such as dependency names are not code. Shell: the whole text, since
    a `#` inside a heredoc can be code. A data file that does not parse is read whole.
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
    return [text]


def _playwright_mentions(path: str) -> list[str]:
    """Each place `path` names a Playwright package outside the allowed places."""
    if path == NODE_LAUNCHER or _is_dependency_data(path):
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


def test_the_launcher_pins_installed_chrome_sandbox_and_allowlist() -> None:
    node = _read(NODE_LAUNCHER)
    for needle in ("channel: 'chrome'", "chromiumSandbox: true", "serviceWorkers: 'block'", "'MAP * ~NOTFOUND'"):
        assert needle in node, f"{NODE_LAUNCHER} lost {needle!r}"
    node_hosts = re.search(r"ALLOWED_HOSTS = Object\.freeze\(\[([^\]]*)\]\)", node)
    assert node_hosts, f"{NODE_LAUNCHER} must define ALLOWED_HOSTS"
    assert tuple(re.findall(r"'([^']+)'", node_hosts.group(1))) == (
        "localhost",
        "127.0.0.1",
        "::1",
        "learn-ukrainian.github.io",
    )
    assert "'args'" not in node.split("const CALLER_OPTIONS = new Set(")[1].split(")")[0]


@pytest.mark.site_toolchain
@pytest.mark.parametrize(
    ("argument", "diagnostic"),
    [
        pytest.param("--disable-seccomp-filter-sandbox", "Seccomp-BPF sandbox", id="seccomp-disabled"),
        pytest.param("-disable-gpu-sandbox=1", "forbidden switch --disable-gpu-sandbox", id="forbidden-switch"),
    ],
)
def test_launcher_rejects_and_closes_chrome_when_sandbox_proof_fails(
    argument: str, diagnostic: str, tmp_path: Path
) -> None:
    """Inject a switch only at the Playwright launch seam and exercise real Chrome."""
    result = subprocess.run(
        ["node", "--input-type=module", "-", argument, diagnostic],
        input="""
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { launchHardenedChromium } from './e2e/support/hardened-browser.mjs';

const [argument, diagnostic] = process.argv.slice(2);
const launch = chromium.launch.bind(chromium);
let launched;
chromium.launch = async (options) => {
  launched = await launch({ ...options, args: [...options.args, argument] });
  return launched;
};
try {
  await assert.rejects(launchHardenedChromium(), (error) => error.message.includes(diagnostic));
  assert.ok(launched, 'Chrome must start before the proof can refuse it');
  assert.equal(launched.isConnected(), false, 'The refused browser must be closed');
} finally {
  await launched?.close();
}
""",
        cwd=ROOT / "site",
        # Chrome generates unique directories and puts a Unix socket inside one of them.
        env={"PATH": os.environ["PATH"], "HOME": str(tmp_path), "TMPDIR": str(tmp_path.parent)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_only_the_shared_launcher_launches_a_playwright_browser() -> None:
    offenders = []
    for path in _browser_files():
        if path == NODE_LAUNCHER or path.endswith(PROSE_SUFFIXES) or _is_dependency_data(path):
            continue
        text = _read_code(path)
        code_parts = _code_strings(path) if path.endswith((".json", ".toml", ".yaml", ".yml")) else [text]
        for code in code_parts:
            offenders += [f"{path}: {m.group(0)}" for m in LAUNCH_CALL.finditer(code)]
            offenders += [f"{path}: {m.group(0)}" for m in CHROME_COMMAND.finditer(code)]
            offenders += [f"{path}: {m.group(0)}" for m in PUPPETEER_IMPORT.finditer(code)]
        offenders += [f"{path}: {m.group(0)}" for m in REMOTE_BROWSER.finditer(text)]
        if path.endswith(JS_SUFFIXES):
            for match in JS_NAMED_IMPORT.finditer(text):
                allowed = JS_IMPORTABLE.get(match.group(2), set()) | {"test"}  # `test` has its own rule
                if bad := _imported_names(match.group(1)) - allowed:
                    offenders.append(f"{path}: imports {sorted(bad)} from {match.group(2)}")
            offenders += [f"{path}: {m.group(0)}" for m in JS_BROWSER_FIXTURE.finditer(text)]
            offenders += [f"{path}: {m.group(0)}" for m in JS_PLAYWRIGHT_BROWSER_TYPE.finditer(text)]
    for path in _token_files():
        mentions = _playwright_mentions(path)
        expected = PLAYWRIGHT_TOKEN_EXEMPT.get(path, (0, ""))[0]
        if len(mentions) != expected:
            offenders += [f"{path}: names a Playwright package outside an allowed import: {m}" for m in mentions]
            offenders += [f"{path}: expected {expected} exempt mentions, found {len(mentions)}"] if expected else []
    assert not offenders, "launch browsers through the shared hardened launcher:\n" + "\n".join(offenders)


def _browser_dependencies(path: str, text: str) -> set[str]:
    if path.endswith("uv.lock"):
        return {
            package["name"] for package in tomllib.loads(text)["package"] if BROWSER_PACKAGE.search(package["name"])
        }

    packages = json.loads(text)["packages"]
    browser_locations = set()
    for location, package in packages.items():
        declarations = _npm_browser_declarations(package)
        installed_name = location.rsplit("node_modules/", 1)[-1]
        actual_name = package.get("name", installed_name)
        if not location:
            browser_locations.update(declarations)
        elif declarations or BROWSER_PACKAGE.search(installed_name) or BROWSER_PACKAGE.search(actual_name):
            browser_locations.add(location if actual_name == installed_name else f"{location} ({actual_name})")
    return browser_locations


def _npm_browser_declarations(package: dict) -> set[str]:
    declarations = set()
    for key in DEPENDENCY_KEYS:
        for name, spec in package.get(key, {}).items():
            if spec.startswith("npm:"):
                target = spec.removeprefix("npm:")
                if "@" in target[1:]:
                    target = target.rsplit("@", 1)[0]
                if BROWSER_PACKAGE.search(name) or BROWSER_PACKAGE.search(target):
                    declarations.add(f"direct: {name} ({target})")
            elif BROWSER_PACKAGE.search(name):
                declarations.add(f"direct: {name}")
    return declarations


def test_lockfiles_require_review_of_browser_dependencies() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ":(glob)**/package-lock.json", ":(glob)**/uv.lock"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    paths = set(filter(None, result.stdout.split("\0")))
    missing = REVIEWED_BROWSER_DEPENDENCIES.keys() - paths
    assert not missing, f"missing tracked lockfiles: {sorted(missing)}"
    offenders = []
    for path in sorted(paths):
        unreviewed = _browser_dependencies(path, _read(path)) - REVIEWED_BROWSER_DEPENDENCIES.get(path, set())
        offenders.extend(f"{path}: {entry}" for entry in sorted(unreviewed))
    assert not offenders, "review these browser dependencies before adding them:\n" + "\n".join(offenders)


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


def test_manifests_require_review_of_browser_dependencies() -> None:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", ":(glob)**/package.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    offenders = []
    for path in sorted(filter(None, result.stdout.split("\0"))):
        approved = REVIEWED_BROWSER_DEPENDENCIES.get(path.removesuffix(".json") + "-lock.json", set())
        unreviewed = _npm_browser_declarations(json.loads(_read(path))) - approved
        offenders.extend(f"{path}: {entry}" for entry in sorted(unreviewed))
    assert not offenders, "review these browser dependencies before adding them:\n" + "\n".join(offenders)


def test_no_file_disables_a_browser_sandbox() -> None:
    offenders = []
    for path in _files(CODE_SUFFIXES):
        if path == NODE_LAUNCHER:
            continue
        text = _read(path)
        hits = [m.group(0) for pattern in (SANDBOX_FLAG, SANDBOX_OPTION) for m in pattern.finditer(text)]
        if hits:
            offenders.append(f"{path}: {sorted(set(hits))}")
    assert not offenders, "the browser sandbox stays on everywhere:\n" + "\n".join(offenders)


def test_nothing_downloads_playwright_browsers_or_configures_playwright_mcp() -> None:
    offenders = []
    for path in _files(CODE_SUFFIXES):
        text = _read(path)
        offenders += [f"{path}: {m.group(0)}" for m in BROWSER_DOWNLOAD.finditer(text)]
        offenders += [f"{path}: {m.group(0)}" for m in PLAYWRIGHT_MCP.finditer(text)]
    assert not offenders, "use installed Google Chrome; no bundled browsers, no Playwright MCP:\n" + "\n".join(
        offenders
    )


def _is_playwright(module: str) -> bool:
    return module == "playwright" or module.startswith("playwright.")


def test_python_modules_do_not_import_playwright() -> None:
    offenders = []
    for path in _files((".py",)):
        for node in ast.walk(ast.parse(_read(path), filename=path)):
            if isinstance(node, ast.Import):
                offenders += [f"{path}:{node.lineno}: import {a.name}" for a in node.names if _is_playwright(a.name)]
            elif isinstance(node, ast.ImportFrom) and node.module and _is_playwright(node.module):
                offenders.append(f"{path}:{node.lineno}: imports from {node.module}")
            elif isinstance(node, ast.Call):
                strings = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                offenders += [f"{path}:{node.lineno}: dynamic import of {v}" for v in strings if _is_playwright(v)]
    assert not offenders, "Python modules must not import Playwright:\n" + "\n".join(offenders)
