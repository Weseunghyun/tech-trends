---
name: sdd-plan
description: "기능 명세서(spec.md) 기반으로 구현 계획(plan.md), 데이터 모델, API 계약 등 설계 산출물을 생성한다. 기술 설계, 아키텍처 결정, 데이터 모델링이 필요할 때 사용한다."
argument-hint: "[추가 컨텍스트]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 개요

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

1. **설정**: 저장소 루트에서 `.specify/scripts/bash/setup-plan.sh --json`을 실행하고 JSON에서 FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH를 파싱합니다. 인수에 작은따옴표가 있는 경우 이스케이프 구문을 사용하세요.

2. **컨텍스트 로드**: FEATURE_SPEC과 `.specify/memory/constitution.md`를 읽습니다. IMPL_PLAN 템플릿을 로드합니다 (이미 복사됨).

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 각 Phase 완료 및 게이트 평가 결과를 알립니다.

3. **계획 워크플로우 실행**: IMPL_PLAN 템플릿의 구조를 따라 수행합니다. **마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다** (특히 템플릿의 후행 공백 2칸 보존):
   - 기술 컨텍스트 채우기 (불명확한 항목은 "명확화 필요"로 표시)
   - constitution(Constitution)에서 constitution 점검 섹션 채우기
   - 게이트 평가 (정당화되지 않은 위반 시 오류)
   - 0단계: research.md 생성 (모든 "명확화 필요" 해결)
   - 1단계: data-model.md, contracts/, quickstart.md 생성
   - 1단계: 에이전트 스크립트를 실행하여 에이전트 컨텍스트 업데이트
   - 설계 후 constitution 점검 재평가

4. **중단 및 보고**: 2단계 계획 후 명령이 종료됩니다. 브랜치, IMPL_PLAN 경로, 생성된 산출물을 보고합니다.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.

세부 단계 설명은 [phases.md](phases.md)를 참조하세요.

## 핵심 규칙

- 절대 경로 사용
- 게이트 실패 또는 미해결 명확화 시 오류 처리

### 다음 단계 안내
- `/sdd-tasks`: 설계 산출물 기반으로 실행 가능한 태스크 생성
- `/sdd-checklist`: 도메인별 체크리스트 생성
