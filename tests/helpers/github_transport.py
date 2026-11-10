"""Opt-in HTTP transport seam for tests that exercise GitHubClient (#8506)."""

from __future__ import annotations

import pytest


@pytest.fixture
def github_transport(monkeypatch):
    """Install one HTTP transport seam while retaining the real client and readers.

    The handler receives method, endpoint, headers, body and timeout. Responses
    exercise status, headers, caching and REST reshaping exactly as production.
    """
    import importlib

    # Product tests run the installed release; machinery-classified tests the in-tree copy.  # TRANSITIONAL-PKG3-B2
    modules = [
        importlib.import_module(name) for name in ("scripts.common.github_client", "lu_machinery.common.github_client")
    ]  # TRANSITIONAL-PKG3-B2

    def install(handler):
        calls = []
        install.clients = []

        def transport(method, endpoint, headers, body, timeout):
            calls.append((method, endpoint, headers, body, timeout))
            return handler(method, endpoint, headers, body, timeout)

        for github_client in modules:  # TRANSITIONAL-PKG3-B2

            def client(_constructor=github_client.GitHubClient, **kwargs):
                store = _constructor(**{**kwargs, "transport": transport})
                install.clients.append(store)
                return store

            monkeypatch.setattr(github_client, "GitHubClient", client)
        return calls

    return install
