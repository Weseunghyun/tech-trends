---
name: sdd-clarify
description: "명세서의 모호한 결정 포인트를 식별하여 최대 5개의 질문으로 명확화하고 spec.md에 직접 반영한다. 명세서 리뷰, 스펙의 모호한 부분 확인, 요구사항 구체화가 필요할 때 사용한다."
argument-hint: "[추가 컨텍스트]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 개요

Goal: 활성 기능 명세서의 모호성 또는 누락된 결정 포인트를 탐지하고, 명확화 결과를 spec 파일에 직접 기록합니다.

이 명확화 워크플로우는 `/sdd-plan` 호출 **전에** 실행(및 완료)되어야 합니다. 사용자가 명시적으로 명확화를 건너뛰겠다고 선언한 경우(예: 탐색적 스파이크) 진행할 수 있지만, 하류 재작업 위험이 증가한다는 경고를 반드시 표시합니다.

## 실행 흐름

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

### 1. 사전 조건 확인

리포 루트에서 `check-prerequisites.sh --json --paths-only`를 **한 번** 실행합니다.

```bash
.specify/scripts/bash/check-prerequisites.sh --json --paths-only
```

최소 JSON 페이로드 필드 파싱:
- `FEATURE_DIR`
- `FEATURE_SPEC`

JSON 파싱 실패 시 중단하고, 사용자에게 `/sdd-specify`를 먼저 실행하거나 기능 브랜치 환경을 확인하도록 안내합니다.

### 2. 커버리지 스캔

spec.md를 로드한 후 [clarify-taxonomy.md](clarify-taxonomy.md) 기반으로 구조화된 모호성 및 커버리지 스캔을 수행합니다.

- 각 카테고리에 대해 **Clear / Partial / Missing** 상태를 판정합니다
- 내부 커버리지 맵을 생성합니다 (질문이 없는 경우에만 출력)

### 3. 질문 생성

내부적으로 우선순위가 매겨진 명확화 질문 큐를 생성합니다 (최대 5개). 모든 질문을 한꺼번에 출력하지 않습니다.

제약 조건:
- 전체 세션에서 **최대 5개** 질문
- 각 질문은 다음 중 하나로 답변 가능해야 합니다:
  - 객관식 선택 (2-5개의 상호 배타적 옵션), 또는
  - 단답형 (5단어 이내)
- 아키텍처, 데이터 모델링, 태스크 분해, 테스트 설계, UX 동작, 운영 준비성, 컴플라이언스 검증에 실질적으로 영향을 주는 질문만 포함
- 카테고리 균형: 미해결된 가장 높은 영향도 카테고리를 우선 처리
- 이미 답변된 질문, 사소한 스타일 선호, 계획 수준 실행 세부사항 제외
- 5개 이상 카테고리가 미해결이면 **(Impact * Uncertainty)** 휴리스틱으로 상위 5개 선택

### 4. 순차 질문 루프 (인터랙티브)

**한 번에 정확히 1개의 질문**을 제시합니다.

#### 객관식 질문:
- 모든 옵션을 분석하고 **가장 적합한 옵션**을 결정합니다:
  - 프로젝트 유형에 대한 베스트 프랙티스
  - 유사 구현의 공통 패턴
  - 리스크 감소 (보안, 성능, 유지보수성)
  - spec에 명시된 프로젝트 목표/제약과의 정합성
- **추천 옵션**을 상단에 표시: `**Recommended:** Option [X] - <근거>`
- 모든 옵션을 마크다운 테이블로 렌더링:

| Option | Description |
|--------|-------------|
| A | 옵션 A 설명 |
| B | 옵션 B 설명 |
| Short | 직접 단답형 입력 (5단어 이내) |

- 안내: `옵션 문자(예: "A"), "yes" 또는 "recommended"로 추천을 수락, 또는 직접 단답형 입력이 가능합니다.`

#### 단답형 질문:
- **제안 답변** 제시: `**Suggested:** <제안 답변> - <간단한 근거>`
- 안내: `형식: 단답형 (5단어 이내). "yes" 또는 "suggested"로 제안을 수락하거나 직접 입력하세요.`

#### 답변 처리:
- "yes", "recommended", "suggested" → 이전 추천/제안을 답변으로 사용
- 그 외 → 옵션 매핑 또는 5단어 제약 충족 검증
- 모호한 경우 → 간단한 명확화 요청 (같은 질문으로 카운트)
- 만족스러운 답변 → 작업 메모리에 기록 후 다음 질문으로 이동

#### 중단 조건:
- 모든 중요 모호성이 조기 해결됨
- 사용자가 완료 신호 ("done", "good", "no more")
- 5개 질문 도달

미래 질문을 미리 공개하지 않습니다.
유효한 질문이 없으면 즉시 "No critical ambiguities detected"를 보고합니다.

### 5. 답변 통합 (각 수락된 답변 후 즉시)

- spec의 인메모리 표현과 원본 파일 내용을 유지합니다
- 첫 번째 통합 답변 시:
  - `## Clarifications` 섹션이 존재하는지 확인 (없으면 생성)
  - `### Session YYYY-MM-DD` 하위 제목 생성 (없는 경우)
- 수락 직후 불릿 라인 추가: `- Q: <질문> → A: <최종 답변>`
- 명확화를 가장 적절한 섹션에 즉시 적용:
  - 기능적 모호성 → Functional Requirements 업데이트
  - 사용자 상호작용 / 액터 구분 → User Stories 또는 Actors 업데이트
  - 데이터 형태 / 엔티티 → Data Model 업데이트
  - 비기능 제약 → Non-Functional / Quality Attributes 업데이트
  - 엣지 케이스 / 부정적 흐름 → Edge Cases / Error Handling 추가
  - 용어 충돌 → spec 전체에서 용어 정규화
- 이전 모호한 서술을 무효화하는 경우, 중복이 아닌 **교체**
- 각 통합 후 spec 파일을 **저장** (atomic overwrite)
- 포맷팅 보존: 관련 없는 섹션 재정렬 금지, 제목 계층 유지
- 각 삽입된 명확화는 최소한이고 테스트 가능하게 유지

**마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다.**

### 6. 검증 (각 쓰기 + 최종 패스 후)

- Clarifications 세션에 수락된 답변당 정확히 1개 불릿 (중복 없음)
- 총 질문 수 ≤ 5
- 업데이트된 섹션에 새 답변이 해결하려 한 모호한 플레이스홀더가 남아있지 않음
- 모순되는 이전 서술이 남아있지 않음
- 마크다운 구조 유효; 허용된 새 제목: `## Clarifications`, `### Session YYYY-MM-DD`
- 용어 일관성: 동일한 표준 용어가 모든 업데이트된 섹션에서 사용됨

### 7. spec 저장

업데이트된 spec을 `FEATURE_SPEC`에 기록합니다.

### 8. 완료 보고

질문 루프 종료 또는 조기 종료 후:

- 질문 수 및 답변 수
- 업데이트된 spec 경로
- 수정된 섹션 목록
- 커버리지 요약 테이블:

| Category | Status |
|----------|--------|
| ... | Resolved / Deferred / Clear / Outstanding |

상태 정의:
- **Resolved**: Partial/Missing였으나 이번 세션에서 해결됨
- **Deferred**: 질문 할당량 초과 또는 계획 단계에서 처리가 더 적합
- **Clear**: 이미 충분
- **Outstanding**: 여전히 Partial/Missing이지만 낮은 영향도

Outstanding 또는 Deferred가 남아있으면 `/sdd-plan` 진행 또는 나중에 `/sdd-clarify` 재실행을 권장합니다.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.

### 다음 단계 안내
- `/sdd-plan`: 명세서 기반으로 구현 계획 생성

## 동작 규칙

- 의미 있는 모호성이 없으면 (또는 모든 잠재 질문이 낮은 영향도): "No critical ambiguities detected worth formal clarification." 응답 후 진행 제안
- spec 파일 누락 시 `/sdd-specify`를 먼저 실행하도록 안내 (여기서 새 spec 생성 금지)
- 총 질문 5개 초과 금지 (단일 질문의 명확화 재시도는 새 질문으로 카운트하지 않음)
- spec에 보이는 프로젝트 목표/제약과 무관한 추측적 기술 스택 질문 회피
- 사용자 조기 종료 신호 ("stop", "done", "proceed") 존중
- 전체 커버리지로 질문이 없는 경우 간결한 커버리지 요약 (모든 카테고리 Clear) 출력 후 진행 제안
- 할당량 도달 시 미해결 고영향 카테고리가 남아있으면 Deferred로 명시적 플래그 및 근거 제공