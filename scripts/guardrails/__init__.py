"""Shared guardrail primitives for agent runtime containment.

Modules here answer cross-cutting safety questions that several enforcement
layers (provider hooks, the runtime git shim, pre-dispatch checks, Monitor API
health) must answer identically. Keeping the logic in one place stops
containment bugs from drifting between reimplementations (issue #4444).
"""
