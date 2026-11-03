"""The one hardened Playwright launcher for Python (#12689).

Operator decision 2026-11-03: Playwright runs only against our own trusted
content. Every browser is the system's auto-updated Google Chrome
(``channel="chrome"``, never Playwright's bundled build), with its sandbox on,
and it can reach only the loopback host and learn-ukrainian.github.io.

Two layers keep a page inside that allowlist:

1. A context route aborts every other request and logs why.
2. Chrome's resolver refuses every other host name or IP address, so requests a
   route never sees (redirect hops, service workers) still cannot leave the host.
   Those refusals are logged too.

Node has the same contract in ``site/e2e/support/hardened-browser.mjs``; the
guard in ``tests/test_browser_hardening_guard.py`` keeps every launch on these two.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Playwright, Request, Route, WebSocketRoute

LOGGER = logging.getLogger(__name__)

ALLOWED_HOSTS: tuple[str, ...] = ("localhost", "127.0.0.1", "::1", "learn-ukrainian.github.io")
_NETWORK_SCHEMES = frozenset({"http", "https", "ws", "wss"})
# Local schemes never reach the network.
_LOCAL_SCHEMES = frozenset({"data", "blob", "about", "file"})

# Chrome's resolver maps every host to "not found" except the allowlist; this also
# covers IP literals, so http://1.1.1.1/ fails as well as example.com.
HOST_RESOLVER_RULES = ", ".join(["MAP * ~NOTFOUND", *(f"EXCLUDE {host}" for host in ALLOWED_HOSTS)])

# Flags that turn a sandbox layer off or move traffic around the resolver rules.
_FORBIDDEN_ARG = re.compile(
    r"^--(no-sandbox|disable-setuid-sandbox|disable-namespace-sandbox|disable-seccomp-filter-sandbox"
    r"|disable-gpu-sandbox|no-zygote-sandbox|no-zygote|single-process|host-resolver-rules|host-rules"
    r"|proxy-server|proxy-pac-url|proxy-bypass-list)(=|$)"
)
HARDENED_CONTEXT_OPTIONS: dict[str, Any] = {"service_workers": "block"}


def is_allowed_url(url: str) -> bool:
    """True when a request to ``url`` may proceed."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return False
    if parts.scheme in _LOCAL_SCHEMES:
        return True
    return parts.scheme in _NETWORK_SCHEMES and host is not None and host.lower() in ALLOWED_HOSTS


def hardened_launch_options(
    *,
    headless: bool | None = None,
    timeout: float | None = None,
    slow_mo: float | None = None,
    args: Iterable[str] = (),
) -> dict[str, Any]:
    """Launch options for installed Chrome with the sandbox on; refuses weakening flags."""
    extra = list(args)
    for arg in extra:
        if _FORBIDDEN_ARG.match(arg):
            raise ValueError(f'hardened launcher: Chrome flag "{arg}" is not allowed')
    options: dict[str, Any] = {
        "channel": "chrome",
        "chromium_sandbox": True,
        "args": [f"--host-resolver-rules={HOST_RESOLVER_RULES}", *extra],
    }
    for key, value in (("headless", headless), ("timeout", timeout), ("slow_mo", slow_mo)):
        if value is not None:
            options[key] = value
    return options


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}" if parts.netloc else f"{parts.scheme}:"


async def enforce_origin_allowlist(
    context: BrowserContext, log: Callable[[str], None] = LOGGER.warning
) -> BrowserContext:
    """Abort and log every request from ``context`` whose origin is outside the allowlist."""

    def reason(url: str) -> str:
        return f"origin {_origin(url)} is not in the allowlist ({', '.join(ALLOWED_HOSTS)})"

    async def block(route: Route) -> None:
        request = route.request
        log(f"[origin-allowlist] blocked {request.resource_type} {request.url}: {reason(request.url)}")
        await route.abort("blockedbyclient")

    async def block_socket(ws: WebSocketRoute) -> None:
        log(f"[origin-allowlist] blocked websocket {ws.url}: {reason(ws.url)}")
        await ws.close(code=1008, reason="origin not in allowlist")

    # Requests the route never sees (redirect hops) die in the resolver; log those too.
    def log_resolver_refusal(request: Request) -> None:
        if not is_allowed_url(request.url) and request.failure == "net::ERR_NAME_NOT_RESOLVED":
            log(
                f"[origin-allowlist] blocked {request.resource_type} {request.url}: "
                f"{reason(request.url)}; refused by the resolver"
            )

    def not_allowed(url: str) -> bool:
        return not is_allowed_url(url)

    await context.route(not_allowed, block)
    await context.route_web_socket(not_allowed, block_socket)
    context.on("requestfailed", log_resolver_refusal)
    return context


async def launch_hardened_chromium(playwright: Playwright, **overrides: Any) -> Browser:
    """Launch installed Chrome with the sandbox on. Open contexts with ``new_hardened_context``."""
    return await playwright.chromium.launch(**hardened_launch_options(**overrides))


async def new_hardened_context(browser: Browser, **options: Any) -> BrowserContext:
    """A context that blocks service workers and enforces the origin allowlist."""
    context = await browser.new_context(**{**options, **HARDENED_CONTEXT_OPTIONS})
    return await enforce_origin_allowlist(context)
