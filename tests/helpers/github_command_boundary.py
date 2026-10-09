"""Opt-in subprocess seam for tests that replace whole GitHub commands (#8506)."""

from __future__ import annotations

import subprocess

import pytest


def install_github_command_boundary(monkeypatch):
    """Point ``github_client.run`` at ``subprocess.run`` without a collection import."""
    from scripts.common import github_client

    def run(args, **kwargs):
        kwargs.pop("fresh", None)
        return subprocess.run(args, timeout=kwargs.pop("timeout", 30), **kwargs)

    monkeypatch.setattr(github_client, "run", run)


@pytest.fixture
def github_command_boundary(monkeypatch):
    """Caller tests replace whole GitHub commands; HTTP tests inject transport."""
    install_github_command_boundary(monkeypatch)
