"""Lane session canaries for long interactive sessions (Grok/Codex/Claude).

Operational mid-session rot check reuses ``scripts.context_canary`` legacy
scoring (pass-ratio, default 0.8 = 8/10). Production rollover still uses
strict 10/10 snapshot mint via ``context_canary.py mint --snapshot``.
"""

__all__ = ["__version__"]

__version__ = "1.0.0"
