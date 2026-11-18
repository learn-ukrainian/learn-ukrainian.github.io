# Patched picomatch (GHSA-fc5q-39xc-vjpf)

`learn-ukrainian-picomatch-4.0.7-lu.1.tgz` is picomatch 4.0.7 with one fix, packed as
`@learn-ukrainian/picomatch@4.0.7-lu.1`. `site/package.json` and the root `package.json`
install it as `picomatch` and point every `picomatch` in their trees at it with the
override `"picomatch": "$picomatch"`. The lockfiles pin its sha512 integrity.

## Why

GHSA-fc5q-39xc-vjpf (CVE-2026-112366, high) covers every published picomatch release up
to 4.0.7: a repeated extglob such as `+(*a)` compiles to a regular expression that
backtracks exponentially. No fixed release exists and upstream has not merged any of the
open fix proposals, so this copy carries the fix. It replaces both the 4.x copies and the
2.3.2 copy that anymatch used to pull in; anymatch and micromatch only call functions 4.x
still provides.

## The fix

`picomatch-4.0.7-lu.1.patch` changes `lib/parse.js` and `package.json` only. In
`analyzeRepeatedExtglob`, a `+(...)` or `*(...)` extglob is now treated as risky, and so
compiled as literal text (the treatment upstream already gives `*(*|x)`), unless:

- it has one branch of fixed width: literal characters, `?` and bracket expressions only,
  so every repetition consumes the same number of characters; or
- it has several branches that are all non-empty literals forming a uniquely decodable
  set (Sardinas-Patterson test), so no input can be split into branches in two ways.

Repeated extglobs whose body holds `*`, `+`, a nested extglob, braces, quotes or an
ambiguous alternation (`+(a|ab|b)`) now match only their literal text. Upstream's own test
suite passes except for 65 assertions, all of that kind. A numeric `maxExtglobRecursion`
no longer relaxes the guard; `maxExtglobRecursion: false` still turns it off.

## Rebuild and verify

```bash
npm pack picomatch@4.0.7   # integrity sha512-qcJu88Q2IWqJsDD529JKMdwGm/dvInW4HvQnRwiH9JtihJvzGOscDtHE3x1pBKeUOTysQ8kVmLnJ2kJu7yhcGA==
tar xzf picomatch-4.0.7.tgz
patch -p1 < site/vendor/picomatch/picomatch-4.0.7-lu.1.patch
chmod -R u=rwX,go=rX package
(cd package && npm pack --pack-destination ..)
```

The result is byte-identical to the committed tarball: integrity
`sha512-wxG+7WV8klxi0ISaa2DuID1CZB2uwE1cRtzuoIwqJFiLDjGdQ0zwuBXBWuCtN3pFgyFVL5RNJ06cYRQhE8qTrg==`,
the value of the `node_modules/picomatch` entry in both lockfiles. When you change the
patch, bump the `-lu.N` suffix, rebuild, and update both lockfiles.

## Removal condition

Remove this copy when either holds:

- a picomatch release newer than 4.0.7 fixes GHSA-fc5q-39xc-vjpf (the advisory then names
  a first patched version): point the `picomatch` dependency in both `package.json` files
  at that registry release, keeping the override so the 2.x consumers get it too; or
- the advisory is withdrawn: drop the `picomatch` dependency and override from both
  `package.json` files.

Then regenerate both lockfiles and delete this directory.
