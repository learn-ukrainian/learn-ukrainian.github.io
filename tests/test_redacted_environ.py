"""Environment objects must not publish values when formatted."""

from __future__ import annotations

import os

from scripts.lib.redacted_environ import RedactedEnvDict, install_redacted_environ_repr

_CANARY = "LU_REPR_CANARY"
_SECRET = "canary-secret-value-9f3a"


def test_plain_mapping_repr_contains_the_value(monkeypatch) -> None:
    """The leak this type closes: a normal mapping formats its values."""
    monkeypatch.setenv(_CANARY, _SECRET)
    leaked = repr({_CANARY: os.environ[_CANARY]})
    assert _SECRET in leaked


def test_environ_formatting_omits_values_and_lookups_keep_them(monkeypatch) -> None:
    monkeypatch.setenv(_CANARY, _SECRET)
    install_redacted_environ_repr()
    shown = " ".join(
        (
            repr(os.environ),
            str(os.environ),
            format(os.environ),
            f"{os.environ}",
        )
    )
    assert _SECRET not in shown
    assert os.environ[_CANARY] == _SECRET


def test_environ_copy_formats_without_values_and_still_copies(monkeypatch) -> None:
    monkeypatch.setenv(_CANARY, _SECRET)
    install_redacted_environ_repr()
    copied = os.environ.copy()
    assert isinstance(copied, RedactedEnvDict)
    assert copied[_CANARY] == _SECRET
    assert _SECRET not in repr(copied)
    assert _SECRET not in repr(copied.copy())


def test_install_is_idempotent() -> None:
    install_redacted_environ_repr()
    install_redacted_environ_repr()
    assert repr(os.environ).startswith("<redacted environ n=")
