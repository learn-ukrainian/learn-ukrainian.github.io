# Curriculum lifecycle module contract

Operate on the manifest target `a1/introductions` in phase `build` from
derived state `unbuilt`. Treat evidence identity
`aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` as immutable input, and stop if any consumed dependency
does not match it.

Return only JSON conforming to the registered
`curriculum-lifecycle-output.v1` schema. Findings must name the owning phase;
never repair content from inside a read-only gate.

---

# CORE family policy

Apply the registered CORE profile for family `core`. Preserve the active
level's progression and immersion policy: A1 English scaffolding is intentional,
while A2 and later levels must not gain English. Do not borrow a seminar-specific
source or framing rule unless the profile registers it.
