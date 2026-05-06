# Broker Stays On SQLite

**Date:** 2026-05-06
**Status:** Accepted
**Scope:** agent-bridge broker storage

SQLite stays as broker storage. The performance bottleneck on
`comms.html` was unindexed scans plus unbounded result sets, not the
storage engine.

The broker is a single-user localhost service, with no current
multi-host or multi-user requirement. WAL mode handles concurrent local
readers, and operational backup remains a normal file copy.

Revisit this if multi-host or multi-user broker use emerges, in line
with ADR #1731 Part B's current localhost-only scope.
