# Tasks: overview sheets (V1)

Details, acceptance criteria and verification: `tasks/plan.md`. Spec: `SPEC.md`.

## Phase 1: Script

- [x] Task 0: Fixtures and golden output in `/tmp/vs_smoke` (no commit)
- [x] Task 1: Shared sheet builder for `--scan` (refactor, output unchanged)
- [x] Task 2: `--at A-B/N` (S7, S8)
- [x] Task 3: `-v N` gives exactly N even frames; old selector removed (S5, S6, S12)
- [x] Task 4: Overview sheets by default (S1-S4)

## Phase 2: Docs for agents and users

- [x] Task 5: `docs/usage.md`
- [x] Task 6: `skill/SKILL.md`

## Checkpoint A: before the eval

- [x] S1-S12 pass at the branch head under `/bin/bash` 3.2.57
- [x] Reviewer subagent has read the branch diff; accepted findings fixed
- [x] Stop and report; `SKILL.md` and the bars are frozen

## Phase 3: Eval and decision (each step needs approval)

- [x] Task 7: Eval run, recorded in `docs/measurements.md`, `eval/README.md`, `eval/overview/` (every bar met; Codex agents)
- [x] Task 8: ADR-0007 (only if every bar is met)
- [x] Task 9: README table and intro; `SPEC.md` status (only if every bar is met)

## Checkpoint B: merge

- [x] Merged into master and pushed on 2026-11-15, after the owner's go-ahead. The `post-merge` hook copied the new `skill/SKILL.md` into Claw's memory.
