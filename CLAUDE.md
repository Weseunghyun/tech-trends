# tech-trends Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-06-13

## Active Technologies

- Python 3.11+ (수집기), HTML5 + Vanilla JS/CSS (대시보드, 빌드 스텝·프레임워크 없음) + `feedparser==6.0.11`, `requests==2.33.0` (LLM SDK 없음 — 요약은 에이전트 인라인) (feature/daily-trends-dashboard)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+ (수집기), HTML5 + Vanilla JS/CSS (대시보드, 빌드 스텝·프레임워크 없음): Follow standard conventions

## Recent Changes

- feature/daily-trends-dashboard: Added Python 3.11+ (수집기), HTML5 + Vanilla JS/CSS (대시보드, 빌드 스텝·프레임워크 없음) + `feedparser==6.0.11`, `requests==2.33.0` (LLM SDK 없음 — 요약은 에이전트 인라인)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## cladding

**Spec is SSoT** — `spec.yaml` is authoritative; code must satisfy its
`features[]` and `acceptance_criteria`. Run `clad check --strict` before commit.

**Persona separation** — planner writes spec, reviewer audits, developer
implements; whoever authors a unit must not sign off on it (anti-self-cert).

**Feature cycle — one at a time** — One feature end-to-end before the next:
author its shard (`acceptance_criteria` + `modules`) → implement → author tests
in a separate context → `clad done <featureId>` (sets `status: done` only when
`clad check --tier=pre-push --strict` is GREEN). Never author shards ahead of
their code, or hand-write `status: done`. See `docs/feature-cycle.md`.

**Hash-based IDs** — Never hand-author `F-NNN` filenames; use the `clad` CLI
(or `/cladding:init`). Model in `docs/spec-ids-multi-dev.md`.

**Drift detectors** — `clad check --strict` runs them all; don't suppress
findings — fix them or update spec.
