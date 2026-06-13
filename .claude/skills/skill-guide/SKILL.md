---
name: skill-guide
description: 이 프로젝트(stock-routine)에서 사용 가능한 스킬과 SDD 파이프라인 사용법을 안내한다. 어떤 스킬을 써야 할지, SDD 흐름이 어떻게 되는지 물을 때 사용한다.
disable-model-invocation: true
---

# stock-routine 스킬 가이드

개인용 Python 데이터 수집 프로젝트의 SDD(Spec-Driven Development) 셋업. 보안을 최우선으로 한다.

## SDD 파이프라인 (계획 → 구현)

`/sdd-design`이 전체 설계 흐름을 한 번에 관장하는 오케스트레이터다.

```
/sdd-design <기능 설명>
   └─ sdd-specify → sdd-clarify → sdd-plan → sdd-tasks  (설계 산출물 일괄 생성)

이후 단계(개별 호출):
/sdd-analyze     # spec/plan/tasks 교차 일관성 분석 (읽기 전용)
/sdd-checklist   # 도메인별(security 등) 요구사항 품질 체크리스트
/sdd-implement   # tasks.md 기반 구현 + 보안 검증 + 커밋
```

| 스킬 | 역할 |
|------|------|
| `sdd-design` | **진입점.** specify→clarify→plan→tasks를 자동 연속 실행 |
| `sdd-specify` | 자연어 설명 → 기능 명세서(spec.md) + feature 브랜치 생성 |
| `sdd-clarify` | 명세서의 모호한 결정 포인트를 최대 5개 질문으로 명확화 |
| `sdd-plan` | spec → 구현 계획(plan.md), data-model, contracts, research |
| `sdd-tasks` | 설계 산출물 → 실행 가능한 tasks.md (의존성 순서) |
| `sdd-analyze` | 산출물 간 불일치/갭/constitution 위반 탐지 |
| `sdd-checklist` | 요구사항 자체의 품질을 검증하는 체크리스트 생성 |
| `sdd-implement` | tasks.md 실행 → 구현 → `impl-python-validate` → 커밋 |
| `sdd-constitution` | 프로젝트 불변 원칙(`.specify/memory/constitution.md`) 관리 |
| `impl-python-validate` | 구현 후 ruff/bandit/pip-audit + 보안 수동 체크리스트 |
| `commit-rule` | 커밋 메시지 형식 규칙 |

## 서브에이전트 (`.claude/agents/`)

SDD 스킬이 병렬 위임에 사용한다: `architect`(설계), `researcher`(조사), `spec-reviewer`(명세 검증), `task-breaker`(태스크 분해), `analyzer`(교차 분석), `checklist-auditor`(체크리스트), `implementer`(태스크 구현), `coder`(범용 구현).

## 규칙 / 원칙

- **보안 규칙**: `.claude/rules/python-security.md` (SEC-01~SEC-09) — 시크릿 미노출, 위험 실행 금지, 외부 HTTP 보안, 데이터 미보정 등.
- **불변 원칙**: `.specify/memory/constitution.md` — 모든 SDD 단계가 참조하는 고정 컨텍스트. 보안 우선 원칙은 협상 불가.

## 산출물 위치

- 기능별 산출물: 로컬 `specs/<NNN-slug>/` (spec.md, plan.md, tasks.md, ...)
- 외부 이슈 트래커/메신저/노트 앱 연동 없음. 브랜치는 `feature/<slug>`.
