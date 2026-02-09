"""
Audit module for validating curriculum modules.

This package provides tools for auditing Ukrainian language curriculum modules,
checking grammar constraints, activity requirements, and pedagogical standards.
"""

def audit_module(*args, **kwargs):
    """Lazy import of audit_module to avoid heavy dependency chain on simple imports."""
    from .core import audit_module as _audit_module
    return _audit_module(*args, **kwargs)

__all__ = ['audit_module']
