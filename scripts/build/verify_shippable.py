"""verify_shippable — one-command Definition-of-Done for a built module (#3138).

A module is *not* shippable just because ``python_qg`` is green. The 2026-06-14
incident: three modules shipped python_qg-green but #01 did not render — the
``mdx_render`` gate is deferred and never ran, so a template-literal escape bug
(#3137) reached ``main`` and only CI's astro build caught it. "Ready" was
*asserted*, not *verified*.

This script makes the Definition-of-Done a single deterministic predicate:

    python_qg green  AND  assembled MDX renders  [AND astro build green]

and prints ONE green/red verdict. Corpus-hammer (#M-11, a human reading of the
content) remains a required ship step and is reported as an explicit TODO — this
tool gates the machine-checkable half so a driver never declares "done" on the
build-time gates alone.

Usage:
    python -m scripts.build.verify_shippable <level> <slug>
    python -m scripts.build.verify_shippable folk narodna-kultura-yak-systema
    python -m scripts.build.verify_shippable folk dumy --module-dir DIR --plan PLAN
    python -m scripts.build.verify_shippable folk kalendarna-obriadovist-zvychai --astro-build

Default render check is the fast, always-on Node island gate
(``scripts.build.mdx_render_gate``) which catches the #3137 class deterministically
without touching ``site/``. ``--astro-build`` additionally runs the full astro
build (what CI does) as the catch-all for non-island render breaks.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM = PROJECT_ROOT / "curriculum" / "l2-uk-en"
SITE_DOCS = PROJECT_ROOT / "site" / "src" / "content" / "docs"

_RESOURCE_LIVENESS_UA = "Mozilla/5.0 (learn-ukrainian resource-liveness verification)"
_RESOURCE_LIVENESS_TIMEOUT = 15
_url_live_cache: dict[str, bool] = {}


def _curl(url: str, *, status_only: bool) -> tuple[int, str]:
    """Fetch ``url`` via curl. Returns (http_status, body).

    curl is used (not urllib) because real-world resource hosts (e.g.
    ukrlib.com.ua) serve incomplete TLS chains that urllib+certifi cannot verify
    but the system store / AIA fetching resolves. curl follows redirects and
    matches browser behaviour. status 0 / empty body on any failure (fail-closed).
    """
    if not shutil.which("curl"):
        return 0, ""
    args = ["curl", "-sS", "-L", "--max-time", str(_RESOURCE_LIVENESS_TIMEOUT),
            "-A", _RESOURCE_LIVENESS_UA]
    if status_only:
        args += ["-o", "/dev/null", "-w", "%{http_code}"]
    args.append(url)
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, timeout=_RESOURCE_LIVENESS_TIMEOUT + 5
        )
    except Exception:
        return 0, ""
    if status_only:
        try:
            return int((proc.stdout or "0").strip() or 0), ""
        except ValueError:
            return 0, ""
    return (200 if proc.returncode == 0 else 0), proc.stdout


def _wikipedia_article_exists(url: str) -> bool | None:
    """True/False if ``url`` is a wikipedia URL (existence via MediaWiki API);
    None ONLY if ``url`` is not a wikipedia host.

    Wikipedia returns HTTP 200 for a *missing* article across all its URL forms
    (``/wiki/<title>`` create-stub, ``/w/index.php?title=<missing>``, etc.), so an
    HTTP-status liveness check cannot detect a fabricated article. Therefore EVERY
    wikipedia-host URL is resolved here (never falls through to a generic curl):
    the article identifier is read from the ``/wiki/`` path or the ``?title=``
    query and confirmed via the MediaWiki API ``missing`` flag. A wikipedia URL
    with no extractable article title fails closed (cannot be confirmed real).
    Hostname is normalized via ``.hostname`` (lowercase, no port/userinfo) so case
    or ``:443`` cannot dodge the check. (Codex re-review holes #2 and #3.)
    """
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if not (host == "wikipedia.org" or host.endswith(".wikipedia.org")):
        return None  # not wikipedia -> caller uses generic curl liveness
    title = ""
    if parts.path.startswith("/wiki/"):
        title = urllib.parse.unquote(parts.path[len("/wiki/"):])
    else:
        title = (urllib.parse.parse_qs(parts.query).get("title") or [""])[0]
    if not title:
        # A wikipedia host URL we cannot resolve to an article title (search,
        # Special:, raw /w/ endpoints, curid/oldid). Cannot confirm a real article
        # and Wikipedia 200s on missing pages -> fail closed (do NOT curl-pass it).
        return False
    api = f"{parts.scheme}://{parts.netloc}/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "titles": title, "redirects": "1", "format": "json"}
    )
    _, body = _curl(api, status_only=False)
    if not body:
        return False
    try:
        pages = json.loads(body).get("query", {}).get("pages", {})
    except json.JSONDecodeError:
        return False
    return bool(pages) and all("missing" not in page for page in pages.values())


def _url_is_live(url: str) -> bool:
    """Best-effort liveness/existence check for a resource URL (fail-closed).

    Wikipedia articles are checked for genuine existence via the MediaWiki API
    (a fabricated title returns ``missing``). All other URLs are checked by a
    redirect-following request accepting 2xx/3xx. Any network/parse error =>
    False. Results are cached per-process so repeated resources are checked once.
    """
    if url in _url_live_cache:
        return _url_live_cache[url]
    ok = False
    try:
        wiki = _wikipedia_article_exists(url)
        if wiki is not None:
            ok = wiki
        elif urllib.parse.urlsplit(url).scheme in ("http", "https"):
            status, _ = _curl(url, status_only=True)
            ok = 200 <= status < 400
    except Exception:
        ok = False
    _url_live_cache[url] = ok
    return ok


def _default_module_dir(level: str, slug: str) -> Path:
    return CURRICULUM / level / slug


def _default_plan_path(level: str, slug: str) -> Path:
    return CURRICULUM / "plans" / level / f"{slug}.yaml"


def _site_mdx_path(level: str, slug: str) -> Path:
    return SITE_DOCS / level / f"{slug}.mdx"


def _astro_build(log_path: Path) -> bool:
    """Run the full astro build (what CI does); write its raw output to ``log_path``.

    The subprocess stdout/stderr is written to a FILE, never returned into the
    printed report: npm/build logs can echo environment values, so keeping raw
    build output out of stdout/JSON is the #M-5-safe path (and removes the
    clear-text-logging taint CodeQL flagged). The caller prints only a fixed
    pointer to the log, not the build output.
    """
    site = PROJECT_ROOT / "site"
    try:
        proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=site,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except FileNotFoundError:
        log_path.write_text("npm not found — cannot run astro build\n", encoding="utf-8")
        return False
    except subprocess.TimeoutExpired:
        log_path.write_text("astro build timed out (>900s)\n", encoding="utf-8")
        return False
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return proc.returncode == 0


def verify(
    level: str,
    slug: str,
    *,
    module_dir: Path | None = None,
    plan_path: Path | None = None,
    astro_build: bool = False,
) -> dict:
    """Run the shippability predicate. Returns a structured report dict."""
    # Import lazily — linear_pipeline pulls in a heavy graph.
    from scripts.build.linear_pipeline import (
        assemble_mdx,
        run_mdx_render_gate,
        run_python_qg,
    )

    module_dir = module_dir or _default_module_dir(level, slug)
    plan_path = plan_path or _default_plan_path(level, slug)

    steps: list[dict] = []

    def add(name: str, passed: bool | None, detail: str) -> None:
        steps.append({"step": name, "passed": passed, "detail": detail})

    # --- preconditions ---
    if not module_dir.exists():
        add("inputs", False, f"module dir not found: {module_dir}")
        return _finalize(level, slug, steps)
    if not plan_path.exists():
        add("inputs", False, f"plan not found: {plan_path}")
        return _finalize(level, slug, steps)

    # --- 1. python_qg (deterministic build gates) ---
    # Static re-verification: pre-built modules have no build-time search
    # telemetry, so supply a real per-resource liveness checker. This lets
    # resources_search_attempted substitute PROOF the resources are real for the
    # absent telemetry (a fabricated/dead resource fails liveness -> gate fails).
    try:
        qg = run_python_qg(module_dir, plan_path, resource_liveness_fn=_url_is_live)
        qg_gates = qg.get("gates", {})
        qg_pass = bool(qg_gates.get("passed"))
        failed = [
            k
            for k, g in qg_gates.items()
            if isinstance(g, dict) and g.get("passed") is False
        ]
        add(
            "python_qg",
            qg_pass,
            "all gates green" if qg_pass else f"failed gates: {', '.join(failed) or 'unknown'}",
        )
    except Exception as exc:
        # Do NOT short-circuit on a python_qg CRASH: a render break must still be
        # surfaced even when python_qg fails (the #3137 design intent). Record the
        # failure and continue to assemble + render.
        add("python_qg", False, f"run_python_qg raised: {type(exc).__name__}: {str(exc)[:200]}")

    # --- 2. assemble MDX (to a temp file; do not touch site/) ---
    with tempfile.TemporaryDirectory() as td:
        tmp_mdx = Path(td) / f"{slug}.mdx"
        try:
            mdx_text = assemble_mdx(module_dir, tmp_mdx, plan_path)
            add("assemble_mdx", True, f"assembled {len(mdx_text)} chars")
        except Exception as exc:
            add("assemble_mdx", False, f"assemble_mdx raised: {type(exc).__name__}: {str(exc)[:200]}")
            return _finalize(level, slug, steps)

        # --- 3. render gate (Node island eval — the #3137 guard) ---
        render = run_mdx_render_gate(mdx_text)
        add("mdx_render", render.get("passed"), render.get("message", ""))
        for f in render.get("failures", []):
            steps.append({"step": "mdx_render.failure", "passed": False, "detail": f"{f['snippet']} → {f['error']}"})

    # --- 4. optional full astro build (catch-all) ---
    if astro_build:
        site_mdx = _site_mdx_path(level, slug)
        prior = site_mdx.read_text(encoding="utf-8") if site_mdx.exists() else None
        log_path = PROJECT_ROOT / "batch_state" / "verify_shippable" / f"{level}-{slug}.astro-build.log"
        try:
            # Write inside the try so the finally always restores, even if the
            # write/mkdir itself raises (never leave site/ corrupted).
            log_path.parent.mkdir(parents=True, exist_ok=True)
            site_mdx.parent.mkdir(parents=True, exist_ok=True)
            site_mdx.write_text(mdx_text, encoding="utf-8")
            ok = _astro_build(log_path)
            add("astro_build", ok, "astro build green" if ok else f"astro build FAILED — full log: {log_path}")
        finally:
            if prior is None:
                site_mdx.unlink(missing_ok=True)
            else:
                site_mdx.write_text(prior, encoding="utf-8")

    return _finalize(level, slug, steps)


def _finalize(level: str, slug: str, steps: list[dict]) -> dict:
    by_step = {s["step"]: s["passed"] for s in steps}
    no_failures = all(s["passed"] in (True, None) for s in steps)
    any_pass = any(s["passed"] is True for s in steps)
    # Render must be POSITIVELY validated, never merely skipped: a None render gate
    # (Node unavailable) does not certify render, so it must not count as shippable.
    island_render_ok = by_step.get("mdx_render") is True
    full_render_ok = by_step.get("astro_build") is True
    shippable = no_failures and any_pass and (island_render_ok or full_render_ok)
    return {
        "level": level,
        "slug": slug,
        "shippable": shippable,
        # The island gate is necessary-not-sufficient: it catches the #3137 class
        # but not non-island JSX/render breaks. Only --astro-build is the full check.
        "render_fully_validated": full_render_ok,
        "steps": steps,
        "corpus_hammer_required": True,
    }


def _print_human(report: dict) -> None:
    icon = {True: "✅", False: "❌", None: "⚠️ "}
    print(f"\n  verify_shippable: {report['level']}/{report['slug']}\n")
    for s in report["steps"]:
        print(f"   {icon[s['passed']]} {s['step']:<22} {s['detail']}")
    print()
    if report["shippable"]:
        print("  ✅ SHIPPABLE (machine checks green)")
        if not report.get("render_fully_validated"):
            print("  ⚠️  island-render only — re-run with --astro-build for full render")
            print("     validation (the island gate does not catch non-island JSX breaks).")
        print("  ⚠️  STILL REQUIRED before ship: corpus-hammer (#M-11) — read the")
        print("     content + independently verify_quote every embedded fragment.")
    else:
        print("  ❌ NOT SHIPPABLE — fix the red step(s) above. Do NOT declare ready.")
    print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Definition-of-Done predicate for a built module (#3138)")
    ap.add_argument("level", help="track/level token, e.g. folk, a1, b1")
    ap.add_argument("slug", help="module slug")
    ap.add_argument("--module-dir", type=Path, default=None)
    ap.add_argument("--plan", type=Path, default=None, dest="plan_path")
    ap.add_argument("--astro-build", action="store_true", help="also run the full astro build (catch-all)")
    ap.add_argument("--json", action="store_true", help="emit the raw report as JSON")
    args = ap.parse_args(argv)

    report = verify(
        args.level,
        args.slug,
        module_dir=args.module_dir,
        plan_path=args.plan_path,
        astro_build=args.astro_build,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report["shippable"] else 1


if __name__ == "__main__":
    sys.exit(main())
