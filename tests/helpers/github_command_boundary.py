"""Opt-in subprocess seam for tests that replace whole GitHub commands (#8506)."""

from __future__ import annotations

import subprocess

import pytest


def install_github_command_boundary(monkeypatch):
    """Point ``github_client.run`` at ``subprocess.run`` without a collection import."""
    import importlib

    def run(args, **kwargs):
        kwargs.pop("fresh", None)
        return subprocess.run(args, timeout=kwargs.pop("timeout", 30), **kwargs)

    for name in ("scripts.common.github_client", "lu_machinery.common.github_client"):  # TRANSITIONAL-PKG3-B2
        monkeypatch.setattr(importlib.import_module(name), "run", run)


@pytest.fixture
def github_command_boundary(monkeypatch):
    """Caller tests replace whole GitHub commands; HTTP tests inject transport."""
    install_github_command_boundary(monkeypatch)
