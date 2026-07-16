# AGENTS.md

This project is managed by **cladding** — the Spec-Anchored Agent Harness.

## Single Source of Truth

- `spec.yaml` is the authoritative spec (Tier A). Code must conform.
- `spec/features/<slug>-<hash>.yaml` holds individual feature shards.
  Never hand-author `F-NNN` filenames — ask cladding via the `clad`
  CLI (or, when your host has cladding wired as an MCP server,
  `clad_create_feature`).
- `docs/project-context.md` is the Tier B design SSoT.
- Run `clad check --strict` to verify spec ↔ code drift across every
  drift detector.

## Feature cycle — one at a time

Work ONE feature end-to-end before starting the next: author its shard
**with** `acceptance_criteria` (+ `modules`) → implement → author its
tests in a separate context → mark it done with `clad done <featureId>`
(it sets `status: done` ONLY when `clad check --tier=pre-push --strict`
is GREEN, reverting otherwise) → only then the next feature. Do NOT author
feature shards ahead of the code, and do NOT hand-write `status: done`.
Independent features (no shared `modules`) may run as parallel instances
of this same cycle. Enforced by the `PLANNED_BACKLOG` detector; rationale
in `docs/feature-cycle.md`.

## Persona separation (anti-self-cert)

The agent that writes a unit of work must not be the agent that signs off
on it. planner writes spec, reviewer audits, developer implements.

## More

See `CLAUDE.md` for Claude Code-specific memory, and
`spec/architecture.yaml` for the layer / `forbidden_imports` invariants
enforced by `ARCHITECTURE_FROM_SPEC`.
