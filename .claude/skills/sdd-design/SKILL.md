---
name: sdd-design
description: "자연어 기능 설명으로부터 sdd-specify → sdd-clarify → sdd-plan → sdd-tasks 파이프라인을 자동 실행하여 설계 전체를 한 번에 완료한다. 기능 설계를 처음부터 끝까지 한 번에 진행하고 싶을 때 사용한다."
disable-model-invocation: true
argument-hint: "[작업-ID(선택)] [기능 설명]"
---

## 사용자 입력

```text
$ARGUMENTS
```

## 개요

이 스킬은 SDD(Specification-Driven Development) 설계 파이프라인을 자동으로 실행합니다.
사용자가 기능 설명을 전달하면 다음 4단계를 순차적으로 수행합니다:

1. **sdd-specify**: 자연어 기능 설명으로부터 기능 명세서(spec.md) 생성
2. **sdd-clarify**: 명세서의 모호한 결정 포인트 명확화 (자동 스킵 가능)
3. **sdd-plan**: 명세서를 기반으로 구현 계획(plan.md) 및 설계 산출물 생성
4. **sdd-tasks**: 설계 산출물을 기반으로 실행 가능한 작업 계획(tasks.md) 생성

## 실행 규칙

### 입력 검증

- `$ARGUMENTS`가 비어있으면 사용자에게 기능 설명을 요청합니다.
- 외부 이슈 트래커 연동은 없습니다. 작업 ID는 선택입니다.
- 기능 설명에서 2~4단어 slug를 만들고(예: `fetch-jp-prices`), 브랜치는 `feature/{slug}`로 진행합니다. 사용자가 작업 ID를 줬으면 `feature/{id}`도 허용합니다.
- 기능 설명이 확인되면 파이프라인을 시작합니다.

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다. sdd-design은 파이프라인 수준 알림만 발송하고, 내부 sub-skill이 각자 알림을 발송하므로 MILESTONE은 생략합니다.

### 파이프라인 실행

각 단계는 반드시 이전 단계가 성공적으로 완료된 후에 실행합니다.
각 단계의 결과를 확인하고 문제가 있으면 사용자에게 보고합니다.

**자동 연속 실행 원칙**: 각 하위 스킬(sdd-specify, sdd-clarify 등)은 단독 실행을 가정하고 "다음 단계 안내"를 출력하지만, sdd-design 파이프라인 내에서는 이 안내를 **무시**하고 즉시 다음 단계의 Skill 호출로 진행해야 합니다. 하위 스킬의 완료 보고가 출력되더라도 사용자 입력을 기다리지 않고, 완료 확인 조건만 충족되면 바로 다음 Skill을 호출합니다. 단, sdd-clarify의 인터랙티브 질문 루프처럼 사용자 응답이 필수인 경우에만 사용자 입력을 대기합니다.

#### 1단계: 요구사항 스펙 정의 (sdd-specify)

Skill 도구를 사용하여 `sdd-specify`를 호출합니다.

```
Skill: sdd-specify
Args: $ARGUMENTS
```

**완료 확인**:
- spec.md 파일이 생성되었는지 확인
- 체크리스트 검증이 통과했는지 확인

**중요**: sdd-specify가 완료 보고와 "다음 단계 안내"를 출력하더라도 멈추지 마세요. spec.md가 정상 생성되었으면 즉시 2단계 sdd-clarify Skill 호출로 진행합니다.

#### 2단계: 명세서 명확화 (sdd-clarify)

1단계가 완료되면 **지체 없이** Skill 도구를 사용하여 `sdd-clarify`를 호출합니다.

```
Skill: sdd-clarify
Args: $ARGUMENTS
```

**완료 확인**:
- 커버리지 스캔 결과 확인
- "No critical ambiguities detected" 반환 시 자동으로 다음 단계로 스킵
- 명확화 질문이 있는 경우 사용자 응답을 받은 후 다음 단계로 진행
- spec.md에 Clarifications 섹션이 추가되었는지 확인

**중요**: sdd-clarify가 완료 보고와 "다음 단계 안내"를 출력하더라도 멈추지 마세요. 즉시 3단계 sdd-plan Skill 호출로 진행합니다.

#### 3단계: 구조 설계 (sdd-plan)

2단계가 완료되면 **지체 없이** Skill 도구를 사용하여 `sdd-plan`을 호출합니다.

```
Skill: sdd-plan
Args: $ARGUMENTS
```

**완료 확인**:
- plan.md 파일이 생성되었는지 확인
- research.md, data-model.md 등 설계 산출물 생성 여부 확인
- 게이트 평가를 통과했는지 확인

**중요**: sdd-plan이 완료 보고와 "다음 단계 안내"를 출력하더라도 멈추지 마세요. 즉시 4단계 sdd-tasks Skill 호출로 진행합니다.

#### 4단계: 작업 계획 세분화 (sdd-tasks)

3단계가 완료되면 **지체 없이** Skill 도구를 사용하여 `sdd-tasks`를 호출합니다.

```
Skill: sdd-tasks
Args: $ARGUMENTS
```

**완료 확인**:
- tasks.md 파일이 생성되었는지 확인
- 태스크 형식이 체크리스트 형식(체크박스, ID, 라벨, 파일 경로)을 따르는지 확인

### 파이프라인 완료 보고

모든 단계가 완료되면 다음을 요약하여 보고합니다:

```markdown
## SDD 설계 파이프라인 완료

### 생성된 산출물
- **명세서**: [spec.md 경로]
- **구현 계획**: [plan.md 경로]
- **작업 계획**: [tasks.md 경로]
- **추가 산출물**: [research.md, data-model.md, contracts/ 등]

### 요약
- **기능명**: [기능명]
- **브랜치**: [브랜치명]
- **총 태스크 수**: [N]개
- **사용자 스토리 수**: [N]개

### 다음 단계
- `/sdd-analyze`: 산출물 간 일관성 분석
- `/sdd-implement`: 구현 시작
- `/sdd-checklist`: 도메인별 체크리스트 생성
```

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 파이프라인 완료 결과를 알립니다.

### 에러 처리

- 각 단계에서 실패 시 해당 단계의 에러를 보고하고 파이프라인을 중단합니다.
- 사용자에게 실패한 단계와 원인을 명확하게 전달합니다.
- 사용자가 문제를 해결한 후 실패한 단계부터 재시작할 수 있도록 안내합니다:
  - 1단계 실패: `/sdd-design [전체 인수]`로 재시작
  - 2단계 실패: `/sdd-clarify`로 해당 단계부터 수동 실행
  - 3단계 실패: `/sdd-plan`으로 해당 단계부터 수동 실행
  - 4단계 실패: `/sdd-tasks`로 해당 단계부터 수동 실행