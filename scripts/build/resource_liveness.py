"""resource_liveness — best-effort URL liveness / existence checker (#3079).

A single, injectable resource-liveness checker shared by every static
re-verification path that lacks build-time writer search telemetry:

* ``scripts.build.verify_shippable`` — the Definition-of-Done predicate (#3138).
* ``scripts.build.v7_build --enhance`` — review + craft loop on curated content
  (no writer phase, so no resource-search telemetry on disk).

``linear_pipeline.run_python_qg`` accepts this as the injected
``resource_liveness_fn``: when build-time writer telemetry is absent, the
``resources_search_attempted`` gate substitutes PROOF the resources are real
(every url-bearing resource confirmed live) for the missing search telemetry. A
fabricated or dead resource fails liveness, so a fabricated-resource module can
never reach the skip. Build-time runs leave this ``None`` and never touch the
network.

This lives in its own module (not inside ``verify_shippable`` or
``linear_pipeline``) so the pipeline can depend on it without back-depending on
the ``verify_shippable`` CLI, and so the network-touching code stays out of
``linear_pipeline`` (which must never perform liveness checks at build time).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.parse

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


def url_is_live(url: str) -> bool:
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
