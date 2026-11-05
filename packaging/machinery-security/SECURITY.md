<!--
DRAFT for the public learn-ukrainian/machinery repository. Install it there as
the root SECURITY.md.
-->
# Security Policy

## Scope

This repository holds agent-orchestration and CI tooling: the dispatcher, the
review recorder, guards and hooks, launch scripts and the pre-publication gate.
It is not a website.

In scope:

- **Credential exposure**: a secret or token in a commit, a log, a prompt or a
  tool's output.
- **Guard or hook bypass**: a way to skip a guard, a hook or a required check,
  or to make one pass when it should fail.
- **Unsafe command execution**: command or argument injection, unsafe handling
  of paths or untrusted input, or a sandbox escape.
- **Supply chain**: an unpinned or compromised dependency, action or scanner,
  or a way to change what CI installs and runs.

Out of scope: the Learn Ukrainian website and its curriculum content. Report
those to
[learn-ukrainian/learn-ukrainian.github.io](https://github.com/learn-ukrainian/learn-ukrainian.github.io/security/advisories/new).

## Reporting a Vulnerability

1. **Do not open a public issue** for a security vulnerability.
2. Report it through
   [GitHub private vulnerability reporting](https://github.com/learn-ukrainian/machinery/security/advisories/new).
3. Include a description, the affected file or command, and steps to reproduce.

## Supported Versions

Only the latest `main` is supported.
