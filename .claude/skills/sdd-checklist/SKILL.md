---
name: sdd-checklist
description: "사용자 요구사항에 기반하여 도메인별 맞춤형 체크리스트를 생성한다. UX, API, 보안, 성능 등 특정 관점에서 요구사항의 품질과 완성도를 검증하는 체크리스트가 필요할 때 사용한다."
argument-hint: "[도메인: ux|api|security|performance|...]"
---

## 체크리스트 목적: "영어의 유닛 테스트"

**핵심 개념**: 체크리스트는 **요구사항 작성의 유닛 테스트**입니다 - 주어진 도메인에서 요구사항의 품질, 명확성, 완성도를 검증합니다.

**구현 테스트가 아닙니다**:
- 코드 실행, 사용자 액션, 시스템 동작 검증이 아님
- 요구사항 자체의 품질을 테스트합니다

**올바른 예**: "모든 인터랙티브 요소에 대해 호버 상태 요구사항이 일관되게 정의되어 있는가?" [일관성]

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 실행 단계

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

1. **설정**: `.specify/scripts/bash/check-prerequisites.sh --json`을 실행하고 FEATURE_DIR과 AVAILABLE_DOCS를 파싱합니다.

2. **의도 명확화 (동적)**: 최대 3개의 초기 맥락 명확화 질문을 도출합니다. 세부 알고리즘은 [clarification-algorithm.md](clarification-algorithm.md)를 참조하세요.

3. **사용자 요청 이해**: `$ARGUMENTS` + 명확화 답변 결합하여 체크리스트 테마, 필수 항목, 카테고리 스캐폴딩을 결정합니다.

4. **기능 컨텍스트 로드**: FEATURE_DIR에서 spec.md, plan.md (있는 경우), tasks.md (있는 경우)를 읽습니다. 활성 집중 영역과 관련된 부분만 로드합니다.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 감사 에이전트 위임 및 체크리스트 작성 진행 상황을 알립니다.

5. **체크리스트 생성** (`checklist-auditor` 서브에이전트 활용):
   - `FEATURE_DIR/checklists/` 디렉토리가 없으면 생성
   - 도메인 기반 파일명 (예: `ux.md`, `api.md`, `security.md`)
   - 기존 파일이 있으면 항목 추가 (마지막 CHK ID에서 계속)
   - 기존 콘텐츠를 절대 삭제하지 않음
   - **여러 도메인이 요청된 경우** `checklist-auditor` 서브에이전트에 병렬 위임:
     ```
     Agent(checklist-auditor): "UX 도메인 분석 - SPEC={경로}, PLAN={경로}"
     Agent(checklist-auditor): "API 도메인 분석 - SPEC={경로}, PLAN={경로}"
     ```
   - 각 에이전트의 결과를 수집하여 CHK ID를 부여하고 체크리스트 파일에 작성
   - 세부 작성 규칙은 [checklist-rules.md](checklist-rules.md)를 참조하세요

6. **구조 참조**: `.specify/templates/checklist-template.md`의 정규 템플릿을 따릅니다. **마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다** (특히 템플릿의 후행 공백 2칸 보존).

7. **보고**: 체크리스트 파일 경로, 항목 수, 선택된 집중 영역, 깊이 수준 요약 출력.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.
