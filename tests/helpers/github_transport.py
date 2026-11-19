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

    github_client = importlib.import_module("lu_machinery.common.github_client")

    def install(handler):
        calls = []
        install.clients = []

        def transport(method, endpoint, headers, body, timeout):
            calls.append((method, endpoint, headers, body, timeout))
            return handler(method, endpoint, headers, body, timeout)

        def client(_constructor=github_client.GitHubClient, **kwargs):
            store = _constructor(**{**kwargs, "transport": transport})
            install.clients.append(store)
            return store

        monkeypatch.setattr(github_client, "GitHubClient", client)
        return calls

    return install
