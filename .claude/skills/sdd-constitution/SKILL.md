---
name: sdd-constitution
description: "프로젝트 constitution을 생성하거나 업데이트하고 종속 템플릿의 동기화를 보장한다. 프로젝트 원칙, 거버넌스 규칙, 아키텍처 결정 원칙을 정의하거나 변경할 때 사용한다."
argument-hint: "[원칙 설명 또는 업데이트 내용]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 개요

`.specify/memory/constitution.md`의 프로젝트 constitution을 업데이트합니다. 이 파일은 대괄호로 된 플레이스홀더 토큰(예: `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`)을 포함하는 템플릿입니다.

**참고**: `.specify/memory/constitution.md`가 아직 존재하지 않는 경우, `.specify/templates/constitution-template.md`에서 복사하세요.

## 실행 흐름

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

1. **기존 constitution 로드**: `.specify/memory/constitution.md`에서 로드하고 `[ALL_CAPS_IDENTIFIER]` 형식의 플레이스홀더 토큰을 식별합니다.

2. **값 수집/도출**: 사용자 입력이 값을 제공하면 사용, 그렇지 않으면 저장소 컨텍스트에서 추론합니다. 세부 규칙은 [versioning-rules.md](versioning-rules.md)를 참조하세요.

3. **업데이트된 constitution 초안 작성**: 모든 플레이스홀더를 구체적인 텍스트로 교체합니다. 각 원칙 섹션: 간결한 이름, 타협 불가 규칙, 명확하지 않은 경우 명시적 근거.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 동기화 전파 결과를 알립니다.

4. **일관성 전파 체크리스트**: 세부 절차는 [sync-checklist.md](sync-checklist.md)를 참조하세요.
   - plan-template.md: constitution 점검 정렬 확인
   - spec-template.md: 범위/요구사항 정렬 확인
   - tasks-template.md: 태스크 분류 반영 확인
   - 런타임 가이던스 문서 업데이트

5. **동기화 영향 보고서 생성**: constitution 파일 상단에 HTML 주석으로 추가 (버전 변경, 수정된 원칙, 추가/제거된 섹션, 업데이트 필요 템플릿).

6. **최종 출력 전 검증**: 설명되지 않은 대괄호 토큰 없음, 버전 라인 일치, ISO 날짜 형식, 원칙이 선언적이고 테스트 가능한지.

7. `.specify/memory/constitution.md`에 작성 (덮어쓰기).

8. **최종 요약 출력**: 새 버전, 범프 근거, 수동 후속 조치 파일, 커밋 메시지 제안.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.

## 포맷팅 요구사항

- 템플릿과 동일한 마크다운 제목 사용
- 긴 근거 라인은 가독성을 위해 줄바꿈 (<100자)
- 섹션 사이 빈 줄 하나 유지
- 새 템플릿을 만들지 마세요; 항상 기존 파일에서 작업
- **마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다** (특히 템플릿의 후행 공백 2칸 보존)

### 다음 단계 안내
- `/sdd-specify`: 업데이트된 constitution에 기반하여 명세서 작성
