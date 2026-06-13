---
name: sdd-tasks
description: "설계 산출물(spec.md, plan.md)을 기반으로 실행 가능하고 종속성 순서가 정해진 tasks.md를 생성한다. 구현 계획을 태스크로 분해하거나, 작업 항목을 만들거나, 개발 단계를 정리할 때 사용한다."
argument-hint: "[추가 컨텍스트]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 사전 실행 검사

**확장 훅 확인 (태스크 생성 전)**: 프로젝트 루트에 `.specify/extensions.yml`이 있는지 확인합니다. 세부 훅 처리 절차는 [extension-hooks.md](extension-hooks.md)를 참조하세요.

## 개요

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

1. **설정**: 저장소 루트에서 `.specify/scripts/bash/check-prerequisites.sh --json`을 실행하고 FEATURE_DIR과 AVAILABLE_DOCS 목록을 파싱합니다. 모든 경로는 절대 경로여야 합니다.

2. **설계 문서 로드**: FEATURE_DIR에서 읽기:
   - **필수**: plan.md (기술 스택, 라이브러리, 구조), spec.md (우선순위가 있는 사용자 스토리)
   - **선택**: data-model.md (엔티티), contracts/ (인터페이스 계약), research.md (결정사항), quickstart.md (테스트 시나리오)
   - 참고: 모든 프로젝트에 모든 문서가 있는 것은 아닙니다. 사용 가능한 것에 기반하여 태스크를 생성합니다.

3. **태스크 생성 워크플로우 실행**: 세부 규칙은 [task-rules.md](task-rules.md)를 참조하세요.
   - plan.md를 로드하고 기술 스택, 라이브러리, 프로젝트 구조 추출
   - spec.md를 로드하고 우선순위(P1, P2, P3 등)가 있는 사용자 스토리 추출
   - data-model.md가 있으면: 엔티티 추출 및 사용자 스토리에 매핑
   - contracts/가 있으면: 인터페이스 계약을 사용자 스토리에 매핑
   - research.md가 있으면: 설정 태스크용 결정사항 추출
   - 사용자 스토리별로 조직된 태스크 생성
   - 사용자 스토리 완료 순서를 보여주는 종속성 그래프 생성
   - 사용자 스토리별 병렬 실행 예시 생성
   - 태스크 완성도 검증 (각 사용자 스토리에 필요한 모든 태스크가 있고 독립적으로 테스트 가능)

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 tasks.md 작성 및 포맷 검증 진행 상황을 알립니다.

4. **tasks.md 생성**: `.specify/templates/tasks-template.md`를 구조로 사용하여 채우기. **마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다** (특히 템플릿의 후행 공백 2칸 보존):
   - plan.md의 올바른 기능명
   - 1단계: 설정 태스크 (프로젝트 초기화)
   - 2단계: 기초 태스크 (모든 사용자 스토리의 차단 전제조건)
   - 3단계+: 사용자 스토리당 하나의 단계 (spec.md의 우선순위 순서)
   - 최종 단계: 마무리 및 공통 관심사
   - 모든 태스크는 엄격한 체크리스트 형식을 따라야 함

5. **보고**: 생성된 tasks.md 경로 및 요약 출력:
   - 총 태스크 수, 사용자 스토리별 태스크 수
   - 식별된 병렬 기회
   - MVP 범위 제안 (일반적으로 사용자 스토리 1만)
   - 형식 검증: 모든 태스크가 체크리스트 형식을 따르는지 확인

6. **사후 확장 훅 확인**: tasks.md 생성 후 `.specify/extensions.yml`의 `hooks.after_tasks` 처리. 세부 절차는 [extension-hooks.md](extension-hooks.md)를 참조하세요.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.

태스크 생성 컨텍스트: $ARGUMENTS

tasks.md는 즉시 실행 가능해야 합니다 — 각 태스크는 LLM이 추가 컨텍스트 없이 완료할 수 있을 만큼 구체적이어야 합니다.

### 다음 단계 안내
- `/sdd-analyze`: 산출물 간 일관성 분석
- `/sdd-implement`: 구현 시작
