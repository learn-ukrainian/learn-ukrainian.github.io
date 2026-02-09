"""
Audit module initialization.

Provides lazy loading for the main audit_module function to improve
startup performance for batch operations.
"""

def audit_module(file_path: str) -> bool:
    """Lazy import and call audit_module."""
    from .core import audit_module as _audit_module
    return _audit_module(file_path)
