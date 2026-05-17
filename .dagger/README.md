# Dagger Local CI Replay

Run the canonical local pytest replay from the repo root:

```bash
DAGGER_NO_NAG=1 dagger call pytest --source=.
```

`DAGGER_CLOUD_TOKEN` is optional. With Dagger CLI v0.20.8, `dagger --help`
and `dagger call --help` do not expose a `--no-cloud` flag. The local
pre-push hook sets `DAGGER_NO_NAG=1` so unauthenticated local runs do not
emit Dagger Cloud setup nags; this does not make Dagger Cloud required.
