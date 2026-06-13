---
name: sdd-analyze
description: "spec.md, plan.md, tasks.md 간 교차 일관성 및 품질 분석을 수행한다. 산출물 간 불일치, 커버리지 갭, constitution 위반 등을 검출한다. 설계 검토, 산출물 점검, 품질 분석이 필요할 때 사용한다."
argument-hint: "[분석 초점]"
allowed-tools: Read, Grep, Glob, Bash
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 목표

구현 전에 세 가지 핵심 산출물(`spec.md`, `plan.md`, `tasks.md`) 전반의 불일치, 중복, 모호성, 미지정 항목을 식별합니다. 이 명령은 `/sdd-tasks`가 완전한 `tasks.md`를 성공적으로 생성한 후에만 실행해야 합니다.

## 운영 제약사항

**엄격한 읽기 전용**: 어떤 파일도 수정하지 **마세요**. 구조화된 분석 보고서를 출력합니다.

**constitution 권한**: 프로젝트 constitution(`.specify/memory/constitution.md`)은 이 분석 범위 내에서 **타협할 수 없습니다**. constitution 충돌은 자동으로 CRITICAL입니다.

## 실행 단계

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

### 1. 분석 컨텍스트 초기화

`.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`를 실행하고 FEATURE_DIR과 AVAILABLE_DOCS를 파싱합니다. 절대 경로로 SPEC, PLAN, TASKS를 도출합니다.

### 2. 산출물 로드 (점진적 공개)

각 산출물에서 최소한의 필요 컨텍스트만 로드합니다. 세부 로딩 규칙은 [analysis-rules.md](analysis-rules.md)를 참조하세요.

### 3. 시맨틱 모델 구축

내부 표현을 생성합니다:
- **요구사항 인벤토리**: 각 요구사항에 안정적인 키 부여
- **태스크 커버리지 매핑**: 각 태스크를 요구사항/스토리에 매핑
- **constitution 규칙 세트**: 원칙 이름 및 MUST/SHOULD 규범적 명령문 추출

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 분석기 에이전트 위임(배치별) 진행 상황을 알립니다.

### 4. 탐지 패스 (analyzer 서브에이전트 병렬 위임)

고신호 발견에 집중, 총 50개 발견으로 제한. **독립적인 카테고리는 `analyzer` 서브에이전트에 병렬로 위임**하여 분석 속도를 높입니다.

**병렬 위임 그룹 1** (내용 분석 - 동시 실행):
- Agent(analyzer): "duplicates 탐지 - SPEC={경로}, PLAN={경로}, TASKS={경로}"
- Agent(analyzer): "ambiguity 탐지 - SPEC={경로}, PLAN={경로}"
- Agent(analyzer): "constitution 정렬 - SPEC={경로}, PLAN={경로}, CONSTITUTION={경로}"

**병렬 위임 그룹 2** (구조 분석 - 그룹 1 완료 후):
- Agent(analyzer): "coverage 갭 - SPEC={경로}, TASKS={경로}"
- Agent(analyzer): "inconsistency 탐지 - SPEC={경로}, PLAN={경로}, TASKS={경로}"
- Agent(analyzer): "underspecified 탐지 - SPEC={경로}, TASKS={경로}"

각 에이전트의 결과를 수집하여 통합 보고서를 작성합니다. 세부 탐지 규칙은 [analysis-rules.md](analysis-rules.md)를 참조하세요.

### 5. 심각도 할당

- **CRITICAL**: constitution MUST 위반, 핵심 산출물 누락, 기본 기능 차단
- **HIGH**: 중복/충돌 요구사항, 모호한 보안/성능 속성
- **MEDIUM**: 용어 표류, 비기능 커버리지 누락
- **LOW**: 스타일 개선, 사소한 중복

### 6. 분석 보고서 생성

마크다운 테이블 형식으로 출력 (파일 쓰기 없음):
- 발견 테이블 (ID, 카테고리, 심각도, 위치, 요약, 권장사항)
- 커버리지 요약 테이블
- constitution 정렬 이슈
- 지표 (총 요구사항, 태스크, 커버리지%, 모호성, 중복, Critical 수)

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 분석 보고서 생성 결과를 알립니다.

### 7. 다음 액션

- CRITICAL 시: `/sdd-implement` 전에 해결 권장
- LOW/MEDIUM만: 진행 가능, 개선 제안
- 구체적 명령 제안 제공

### 8. 개선 제안

"상위 N개 이슈에 대해 구체적인 개선 편집을 제안해 드릴까요?" (자동 적용하지 않음)
