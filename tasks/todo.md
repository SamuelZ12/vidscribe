# Tasks: full overview sheets (V1)

Details, acceptance criteria and verification: `tasks/plan.md`. Spec: `SPEC.md`.

## Phase 1: Script

- [ ] Task 0: Fixtures and golden output in `/tmp/vs_smoke/full` (no commit)
- [ ] Task 1: Tile count gives full sheets (`bin/vidscribe`; criteria 1, 3, 4)

## Phase 2: Docs

- [ ] Task 2: `docs/usage.md`
- [ ] Task 3: `skill/SKILL.md`
- [ ] Task 4: ADR-0008, ADR index, pointer in 0007, eval note in `docs/measurements.md`

## Checkpoint: before merge

- [ ] 3:33 test video gives `16 tiles on 1 sheet` (criterion 2)
- [ ] `-a`, an audio file, `--at` and `--scan` match master (criterion 5)
- [ ] No "one per 10 s" statement of the overview count is left in `bin`, `docs/usage.md` or `skill`
- [ ] Stop and report; merge, push and deleting `SPEC.md` and `tasks/` wait for the owner's go-ahead
