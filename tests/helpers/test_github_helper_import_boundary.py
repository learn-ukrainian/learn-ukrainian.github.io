"""Verify helper imports do not eagerly load scripts.common.github_client at collection time (#8506)."""

from __future__ import annotations

import importlib
import sys

from tests.helpers.restore_import_state import restore_import_state


def test_github_helper_imports_do_not_load_github_client() -> None:
    client = "scripts.common.github_client"
    helpers = (
        "tests.helpers.github_command_boundary",
        "tests.helpers.github_transport",
    )
    with restore_import_state(client, *helpers):
        sys.modules.pop(client, None)
        for name in helpers:
            sys.modules.pop(name, None)
            importlib.import_module(name)
        assert client not in sys.modules, f"Importing helpers eagerly loaded {client}"
