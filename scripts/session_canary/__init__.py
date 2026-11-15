"""Lane session canaries for long interactive sessions (Grok/Codex/Claude).

Operational mid-session rot check reuses ``scripts.context_canary`` legacy
scoring (pass-ratio, default 0.8 = 8/10).
"""

__all__ = ["__version__"]

__version__ = "1.0.0"
