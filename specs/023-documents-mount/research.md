# Research: Dedicated Documents Mount

## R1 — The mount lives in `MOUNTS`, not a hand-built flag

- **Decision**: add `("~/agentic-rag-docs", "/data/rag-docs")` to the
  `MOUNTS` list in `deploy/docker_ops.py` and refactor
  `recreate_container()` to build ALL `-v` flags from that list
  (today three flags are hand-built — two from MOUNTS, one
  ppt-master from REPO_ROOT).
- **Rationale**: one list = the container spec; every future
  `redeploy`/`all` carries the documents mount automatically (FR-004).
  A hand-added fourth flag would duplicate the pattern that already
  drifted (the MOUNTS list exists but isn't fully used).
- **Alternatives considered**: config.toml-driven mounts — rejected
  (YAGNI; the pair is deployment-constant); manual `docker run` —
  rejected (lost on next redeploy, exactly what FR-004 forbids).

## R2 — The tooling creates the host folder with correct ownership

- **Decision**: `recreate_container()` does `mkdir -p` on the expanded
  host path before `docker run`.
- **Rationale**: Docker auto-creates missing `-v` host paths as
  **root**; a user-managed documents folder owned by root would still
  work (container root reads it) but blocks the operator from cleaning
  it up without sudo. Pre-creating keeps the operator's ownership.
- **Alternatives considered**: relying on Docker's auto-create —
  rejected (wrong ownership class of problem).

## R3 — Unit tests assert the run command, not the running container

- **Decision**: new unit tests assert `recreate_container` emits the
  documents `-v` flag and creates the folder (mock the subprocess
  runner); the live battery covers the real thing.
- **Rationale**: the run-command string IS the spec's FR-004 artifact —
  asserting it in a unit test makes mount survival regression-proof at
  the constitution's test layer, without needing a container in CI.
- **Alternatives considered**: parse `docker inspect` in the unit test —
  rejected (needs a live docker; the battery already does it).

## Error handling (user-requested)

| Condition | Behavior |
|---|---|
| Recreate fails (`docker run` non-zero) | deploy CLI raises with stderr tail — container is gone but config/state live on the mounted volumes; re-run redeploys cleanly (existing fail-fast) |
| Health gate times out after recreate | CLI aborts before any later step; mount is present but unverified — the failure is loud, never half-applied |
| Old source removal fails mid-migration | documents are idempotent: both sources can coexist briefly (old points at a now-empty folder → its next sync deletes the doc from the index; new source has it) — re-run migration completes |
| PDF move lands before source swap | the watcher may re-sync the old source against an empty folder (removing 1 doc) and the new source auto-syncs on add — net state correct after both syncs |
| Host folder deleted while container runs | container keeps its mount of a deleted dir → writes go nowhere user-visible; next recreate re-creates it (mkdir -p) — self-healing on the deploy path |
| Unsupported extensions dropped in the folder | unchanged scanner behavior (silently ignored; audio skipped with reason) — documented, not fixed here |
| Concurrent chat traffic during recreate | in-flight requests fail once (~1 min); `--restart always` + health gate restore service (spec Edge Case) |
