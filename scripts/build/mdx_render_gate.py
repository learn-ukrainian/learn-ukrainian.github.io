"""MDX render gate — the gate that was deferred and never ran (#3137).

``python_qg`` validates the *authoring artifacts* but is blind to whether the
*assembled MDX* actually renders. The classic failure is a ``JSON.parse(`…`)``
island prop whose embedded JSON is mis-escaped for the surrounding JS template
literal (see ``scripts/generate_mdx/utils.dump_json_for_jsx`` / #3137): the page
builds-syntax-OK but the prop expression throws when evaluated, so the module
ships and does not render. Only CI's full astro build caught it.

This gate compiles the complete page with the site's configured Astro MDX
processor, then extracts every ``JSON.parse(`…`)`` template literal and evaluates it with
**Node** — the real JS engine — so template-literal + JSON.parse semantics are
exact (no re-implementation of JS string escaping, which is the very thing that
broke). A full Astro build remains the catch-all for import resolution and
render-time failures (``verify_shippable.py --astro-build``).

Degrades gracefully: if Node is unavailable the gate reports ``passed=None``
(skipped) rather than failing, mirroring the DB-gated checks elsewhere.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

_MARKER = "JSON.parse(`"


def iter_template_literals(mdx_text: str) -> list[str]:
    """Yield the raw inner text of every ``JSON.parse(`…`)`` in ``mdx_text``.

    The closing backtick is the first ``\\``-unescaped backtick after the marker,
    so escaped backticks (``\\```) inside a correctly-escaped payload do not end
    the literal early. The inner text is returned *verbatim* (exactly as it
    appears in the MDX) so Node re-evaluation reproduces render semantics.
    """
    inners: list[str] = []
    i = 0
    n = len(mdx_text)
    while True:
        idx = mdx_text.find(_MARKER, i)
        if idx == -1:
            break
        start = idx + len(_MARKER)
        j = start
        terminated = False
        while j < n:
            c = mdx_text[j]
            if c == "\\":
                j += 2  # skip the escaped char (covers \` , \\ , \$ …)
                continue
            if c == "`":
                terminated = True
                break
            j += 1
        if not terminated:
            # Unterminated JSON.parse(` … = truncated/malformed MDX. Do NOT emit a
            # phantom rest-of-file island (it could falsely pass if that suffix is
            # valid JSON, or mis-point the error). A working assembler never emits
            # this; astro build catches genuinely truncated MDX. Stop scanning.
            break
        inners.append(mdx_text[start:j])
        i = j + 1
    return inners


def _node_eval_one(inner: str, *, timeout: int = 30) -> str | None:
    """Return ``None`` if ``JSON.parse(`inner`)`` evaluates, else an error line.

    ``inner`` is written verbatim between backticks into a throwaway ``.mjs``
    file, exactly reproducing the MDX source expression, then run under Node.
    """
    with tempfile.NamedTemporaryFile(
        "w", suffix=".mjs", delete=False, encoding="utf-8"
    ) as fh:
        # Reproduce the MDX expression byte-for-byte: backtick + inner + backtick.
        # The sentinel prints only AFTER JSON.parse returns: an unescaped ``${…}``
        # in the inner would interpolate (run code / process.exit) and short-circuit
        # before JSON.parse, so requiring the sentinel stops that from passing silently.
        fh.write(
            "const c = `" + inner + "`;\nJSON.parse(c);\nprocess.stdout.write('__RENDER_OK__');\n"
        )
        path = fh.name
    try:
        proc = subprocess.run(
            ["node", path], capture_output=True, text=True, timeout=timeout
        )
        if proc.returncode == 0 and "__RENDER_OK__" in proc.stdout:
            return None
        if proc.returncode == 0:
            return "island did not reach JSON.parse (template-literal interpolation / early exit?)"
        stderr_lines = [ln for ln in proc.stderr.strip().splitlines() if ln.strip()]
        # Prefer the most specific error line (SyntaxError / JSON.parse message).
        for ln in stderr_lines:
            if "Error" in ln or "JSON" in ln:
                return ln.strip()[:300]
        return (stderr_lines[-1].strip()[:300] if stderr_lines else "node error")
    except subprocess.TimeoutExpired:
        return "node eval timed out"
    finally:
        Path(path).unlink(missing_ok=True)


def check_mdx_render(mdx_text: str, *, timeout: int = 30) -> dict:
    """Compile the whole page and evaluate its JSON islands with Node.

    Returns a ``python_qg``-style gate report::

        {"passed": True|False|None, "message": str,
         "islands_checked": int, "failures": [{"snippet": str, "error": str}]}

    ``passed=None`` means *skipped* (Node unavailable) — never a hard fail on a
    missing toolchain.
    """
    if shutil.which("node") is None:
        return {
            "passed": None,
            "skipped": True,
            "message": "node unavailable — mdx_render gate skipped",
            "islands_checked": 0,
            "compiled": None,
            "failures": [],
        }

    compilation = _compile_page(mdx_text, timeout=timeout)
    inners = iter_template_literals(mdx_text)
    failures: list[dict] = []
    for inner in inners:
        err = _node_eval_one(inner, timeout=timeout)
        if err is not None:
            snippet = inner[:80].replace("\n", "\\n")
            failures.append({"snippet": snippet, "error": err})

    if compilation["passed"] is not True:
        failures.insert(0, {"snippet": "whole MDX page", "error": compilation["message"]})
    passed = not failures
    if passed:
        msg = f"page compiled with Astro MDX; all {len(inners)} JSON.parse(`…`) island prop(s) evaluate"
    elif compilation["passed"] is not True:
        msg = "whole-page MDX compilation failed — module would not render"
    else:
        msg = (
            f"{len(failures)}/{len(inners)} JSON.parse(`…`) island prop(s) fail to "
            f"evaluate — module would not render"
        )
    return {
        "passed": passed,
        "compiled": compilation["passed"],
        "layer": compilation.get("layer") if not passed else None,
        "message": msg,
        "islands_checked": len(inners),
        "failures": failures,
    }


def _compile_page(mdx_text: str, *, timeout: int = 30) -> dict:
    """Use the same configured renderer and options as @astrojs/mdx.

    Import/setup failures are harness failures, while compiler rejections are
    page failures. No substitute compiler can certify a missing site toolchain.
    """
    site = Path(__file__).resolve().parents[2] / "site"
    script = r"""
import { pathToFileURL } from 'node:url';
let renderer, parseFrontmatter;
try {
  const { default: config } = await import(pathToFileURL(process.cwd() + '/astro.config.mjs'));
  const { markdownConfigDefaults } = await import('@astrojs/internal-helpers/markdown');
  ({ parseFrontmatter } = await import('@astrojs/internal-helpers/frontmatter'));
  renderer = await config.markdown.processor.createMdxRenderer(
    { ...markdownConfigDefaults, ...config.markdown },
    { optimize: false, srcDir: pathToFileURL(process.cwd() + '/src/'), sourcemap: false }
  );
} catch (error) {
  process.stdout.write(JSON.stringify({passed: false, layer: 'harness', message: 'MDX toolchain setup failed: ' + error.message}));
  process.exit(0);
}
let source = '';
for await (const chunk of process.stdin) source += chunk;
try {
  const { frontmatter, content } = parseFrontmatter(source, { frontmatter: 'empty-with-spaces' });
  await renderer.process(content, process.cwd() + '/src/content/docs/__render_gate__.mdx', frontmatter);
  process.stdout.write(JSON.stringify({passed: true, message: 'Astro MDX compiled'}));
} catch (error) {
  process.stdout.write(JSON.stringify({passed: false, layer: 'engine', message: error.message}));
}
"""
    try:
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=site,
            input=mdx_text,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        return {"passed": False, "layer": "harness", "message": "MDX compiler process failed"}
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {"passed": False, "layer": "harness", "message": f"MDX compiler unavailable: {type(exc).__name__}"}


def check_mdx_render_path(mdx_path: str | Path, *, timeout: int = 30) -> dict:
    """``check_mdx_render`` for a file path; fails closed if the file is missing."""
    p = Path(mdx_path)
    if not p.exists():
        return {
            "passed": False,
            "message": f"assembled MDX not found: {p}",
            "islands_checked": 0,
            "failures": [],
        }
    return check_mdx_render(p.read_text(encoding="utf-8"), timeout=timeout)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="MDX render gate (#3137)")
    ap.add_argument("mdx_path", help="path to an assembled .mdx file")
    ap.add_argument("--json", action="store_true", help="emit the raw gate report as JSON")
    args = ap.parse_args(argv)

    report = check_mdx_render_path(args.mdx_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = {True: "✅ PASS", False: "❌ FAIL", None: "⚠️  SKIP"}[report["passed"]]
        print(f"{status}  mdx_render  {report['message']}")
        for f in report["failures"]:
            print(f"   • {f['snippet']}  →  {f['error']}")
    return 0 if report["passed"] in (True, None) else 1


if __name__ == "__main__":
    raise SystemExit(main())
