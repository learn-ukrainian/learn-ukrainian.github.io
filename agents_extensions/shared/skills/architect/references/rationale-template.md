# Rationale template

One page beside the type sketch. Replace the notes with the actual design.

## Problem

What we are doing, and which constraint makes the shape non-obvious.

## Usage

The caller's view, written first. Two or three realistic call sites: what they import, what they call, what comes back. The type sketch is derived from this. When they disagree, change the sketch.

## Shape

Data structures first, then how data moves through the signatures. Name what the public surface hides, what it still exposes, and where validation lives. Cite a principle by name. Do not restate it.

## Choice

Which candidate is the base, what was taken from the others, and what was rejected. At least one concrete alternative, with why it lost. If constraints left only one viable shape, say why.

## Tradeoffs

One bullet each: we accept X in exchange for Y. Name anything a later reader might think was an oversight.

## Open questions

Questions for the operator, not assertions. Risks to flag before implementation.

## First implementation step

The first thing to build against the sketch, in one sentence.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
