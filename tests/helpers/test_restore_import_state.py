"""The import-state helper puts back a parent attribute left on a fresh module."""

from __future__ import annotations

import sys
import types

from tests.helpers.restore_import_state import restore_import_state


def test_restore_import_state_repairs_stale_parent_binding() -> None:
    parent_name = "lu_restore_import_state_pkg"
    child_name = f"{parent_name}.child"
    parent = types.ModuleType(parent_name)
    child = types.ModuleType(child_name)
    parent.child = child
    sys.modules[parent_name] = parent
    sys.modules[child_name] = child
    fresh = types.ModuleType(child_name)
    try:
        with restore_import_state(child_name):
            sys.modules[child_name] = fresh
            parent.child = fresh
            assert sys.modules[child_name] is fresh
            assert parent.child is fresh
        assert sys.modules[child_name] is child
        assert parent.child is child
    finally:
        sys.modules.pop(child_name, None)
        sys.modules.pop(parent_name, None)


def test_restore_import_state_removes_bindings_absent_at_start() -> None:
    parent_name = "lu_restore_import_state_absent"
    child_name = f"{parent_name}.child"
    parent = types.ModuleType(parent_name)
    sys.modules[parent_name] = parent
    sys.modules.pop(child_name, None)
    parent.__dict__.pop("child", None)
    try:
        with restore_import_state(child_name):
            fresh = types.ModuleType(child_name)
            sys.modules[child_name] = fresh
            parent.child = fresh
        assert child_name not in sys.modules
        assert "child" not in parent.__dict__
    finally:
        sys.modules.pop(child_name, None)
        sys.modules.pop(parent_name, None)


def test_restore_import_state_clears_attribute_on_parent_imported_inside_block() -> None:
    parent_name = "lu_restore_import_state_new_parent"
    child_name = f"{parent_name}.child"
    sys.modules.pop(parent_name, None)
    sys.modules.pop(child_name, None)
    try:
        with restore_import_state(child_name):
            parent = types.ModuleType(parent_name)
            fresh = types.ModuleType(child_name)
            parent.child = fresh
            sys.modules[parent_name] = parent
            sys.modules[child_name] = fresh
        assert child_name not in sys.modules
        assert parent_name in sys.modules
        assert "child" not in sys.modules[parent_name].__dict__
    finally:
        sys.modules.pop(child_name, None)
        sys.modules.pop(parent_name, None)


def test_restore_import_state_distinguishes_absent_from_none() -> None:
    name = "lu_restore_import_state_none_sentinel"
    sys.modules.pop(name, None)
    try:
        with restore_import_state(name):
            sys.modules[name] = None
        assert name not in sys.modules

        sys.modules[name] = None
        replacement = types.ModuleType(name)
        with restore_import_state(name):
            sys.modules[name] = replacement
        assert sys.modules[name] is None
    finally:
        sys.modules.pop(name, None)
