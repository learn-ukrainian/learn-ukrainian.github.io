# Design red flags

Screen a candidate shape before choosing it. A flag is a reason to revise or reject that shape.

## Shallow module

A shallow module exposes a large interface and hides little. Prefer a small interface with real behavior behind it. A deep module is not a deep call chain. A deep call chain scatters the story.

Signs: callers must coordinate several methods for one operation. Public options expose internal stages. Learning the interface does not save the caller from learning the implementation.

## Information leakage

Several modules depend on the same internal decision, so one change needs coordinated edits. Parsing external data into a domain type behind the interface stops this. Do not re-export transport or wire types.

## Temporal decomposition

Modules named only for execution order (load, validate, transform, save) repeat one representation across boundaries. Group code by the knowledge it owns.

## Pass-through

A method that forwards the same arguments adds a layer and hides nothing. Remove it, or move the work to the module that can finish the operation.

## Split ownership

More than one module writes the same state. Give that state one owner. Others read it or ask the owner to change it.

## Two ways

One task has two supported paths. Keep one. Move callers and delete the other in the same change.

## Importable internals

If a caller can import a module's internals, that import becomes the interface. Make the internal import fail the build.

## Hand-synced list

Two places list the same items. Keep one list and derive the other. If you cannot derive it, fail the build when the lists disagree.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
