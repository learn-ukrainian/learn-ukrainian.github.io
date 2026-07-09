"""Tests for shared wiki write-domain resolution."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT))

from wiki.compile import _get_domain
from wiki.domains import resolve_write_domain


def test_resolve_write_domain_preserves_core_domains() -> None:
    assert resolve_write_domain("a1", "greeting") == "pedagogy/a1"
    assert resolve_write_domain("b1", "aspect") == "grammar/b1"


def test_resolve_write_domain_uses_seminar_track_domains() -> None:
    assert resolve_write_domain("BIO", "oleksandr-bilash") == "figures"
    assert resolve_write_domain("hist", "kyivan-rus") == "periods"
    assert resolve_write_domain("istorio", "debate") == "historiography"
    assert resolve_write_domain("lit-war", "poetry") == "literature/works"


def test_resolve_write_domain_uses_folk_slug_subdomains() -> None:
    assert resolve_write_domain("folk", "koliadky-shchedrivky") == "folk/ritual"
    assert resolve_write_domain("folk", "prykazky-ta-pryslivia") == "folk/short-forms"
    assert resolve_write_domain("folk", "unmapped-folk-topic") == "folk"


def test_get_domain_is_compatibility_wrapper() -> None:
    assert _get_domain("bio", "oleksandr-bilash") == resolve_write_domain("bio", "oleksandr-bilash")
    assert _get_domain("folk", "koliadky-shchedrivky") == resolve_write_domain("folk", "koliadky-shchedrivky")
