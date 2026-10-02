"""Part 6 of the development-lookup sweep of #9412 (tests/helpers/docs_find_lookups.py says why it is split)."""
import pytest

from tests.helpers.docs_find_lookups import assert_answered_in_one_query, part

# Searches the whole tracked tree, so the module is registered in
# tests/test_repo_wide_marker_invariant.py.
pytestmark = pytest.mark.repo_wide


@pytest.mark.parametrize(('name', 'field', 'lookup'), part(6))
def test_lookup_is_answered_in_one_query(name, field, lookup):
    assert_answered_in_one_query(name, field, lookup)
