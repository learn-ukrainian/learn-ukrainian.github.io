"""Host regression probe for #9964: ``pytest -p tests.github_client_default_cache``.

The normal autouse cache override masks default-path writes made by the git
shim's push scanner. Exercise that default only in bounded-advisory tests;
their fake GitHub CLI still prevents live network calls.
"""

import pytest


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    with pytest.MonkeyPatch.context() as patch:
        if item.path.name == "test_delegate_bounded_advisory.py":
            patch.delenv("LU_GITHUB_CACHE_DIR", raising=False)
        return (yield)
