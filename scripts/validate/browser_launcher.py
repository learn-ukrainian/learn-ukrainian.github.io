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
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, Request, Route, WebSocketRoute

LOGGER = logging.getLogger(__name__)

ALLOWED_HOSTS: tuple[str, ...] = ("localhost", "127.0.0.1", "::1", "learn-ukrainian.github.io")
_NETWORK_SCHEMES = frozenset({"http", "https", "ws", "wss"})
# Local schemes never reach the network.
_LOCAL_SCHEMES = frozenset({"data", "blob", "about", "file"})

# Chrome's resolver maps every host to "not found" except the allowlist; this also
# covers IP literals, so http://1.1.1.1/ fails as well as example.com.
HOST_RESOLVER_RULES = ", ".join(["MAP * ~NOTFOUND", *(f"EXCLUDE {host}" for host in ALLOWED_HOSTS)])

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
) -> dict[str, Any]:
    """Launch options for installed Chrome with the sandbox on.

    Callers pass no Chrome flags at all: Chrome accepts several spellings of each
    switch, so a denylist of weakening flags cannot hold.
    """
    options: dict[str, Any] = {
        "channel": "chrome",
        "chromium_sandbox": True,
        "args": [f"--host-resolver-rules={HOST_RESOLVER_RULES}"],
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


@asynccontextmanager
async def hardened_browser(**overrides: Any) -> AsyncIterator[Browser]:
    """Installed Chrome with the sandbox on.

    Every context and page the yielded browser opens blocks service workers and
    enforces the origin allowlist. The launcher owns the Playwright driver, so no
    other module needs ``async_playwright``.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**hardened_launch_options(**overrides))
        raw_new_context = browser.new_context

        async def new_context(**options: Any) -> BrowserContext:
            # A context proxy on the loopback host could carry requests the resolver would refuse.
            if options.get("proxy"):
                raise ValueError("hardened launcher: a context proxy is not allowed")
            context = await raw_new_context(**{**options, **HARDENED_CONTEXT_OPTIONS})
            return await enforce_origin_allowlist(context)

        async def new_page(**options: Any) -> Page:
            # Unlike Browser.new_page, the context stays open until the browser closes.
            return await (await new_context(**options)).new_page()

        setattr(browser, "new_context", new_context)  # noqa: B010 - replaces the instance method
        setattr(browser, "new_page", new_page)  # noqa: B010 - replaces the instance method
        try:
            yield browser
        finally:
            await browser.close()
