# Clarify Taxonomy

명세서의 모호성 및 커버리지를 스캔하기 위한 분류 체계입니다.
각 카테고리에 대해 **Clear / Partial / Missing** 상태를 판정합니다.

## 1. Functional Scope & Behavior

- 핵심 사용자 목표 및 성공 기준
- 명시적 범위 외(out-of-scope) 선언
- 사용자 역할 / 페르소나 구분

## 2. Domain & Data Model

- 엔티티, 속성, 관계
- 식별자 및 고유성 규칙
- 라이프사이클 / 상태 전이
- 데이터 볼륨 / 스케일 가정

## 3. Interaction & UX Flow

- 핵심 사용자 여정 / 시퀀스
- 에러 / 빈 상태 / 로딩 상태
- 접근성 또는 지역화 관련 사항

## 4. Non-Functional Quality Attributes

- 성능 (지연 시간, 처리량 목표)
- 확장성 (수평/수직, 한계)
- 신뢰성 및 가용성 (업타임, 복구 기대치)
- 관측성 (로깅, 메트릭, 트레이싱)
- 보안 및 개인정보 (인증/인가, 데이터 보호, 위협 가정)
- 컴플라이언스 / 규제 제약 (해당 시)

## 5. Integration & External Dependencies

- 외부 서비스/API 및 장애 모드
- 데이터 import/export 형식
- 프로토콜 / 버전 관리 가정

## 6. Edge Cases & Failure Handling

- 부정적 시나리오
- Rate limiting / throttling
- 충돌 해결 (예: 동시 편집)

## 7. Constraints & Tradeoffs

- 기술적 제약 (언어, 스토리지, 호스팅)
- 명시적 트레이드오프 또는 거부된 대안

## 8. Terminology & Consistency

- 표준 용어 정의
- 회피해야 할 동의어 / 폐기된 용어

## 9. Completion Signals

- 인수 기준의 테스트 가능성
- 측정 가능한 Definition of Done 지표

## 10. Misc / Placeholders

- TODO 마커 / 미결정 사항
- 정량화 없는 모호한 형용사 ("robust", "intuitive" 등)

---

## 판정 기준

| 상태 | 기준 |
|------|------|
| **Clear** | 해당 카테고리의 모든 항목이 구체적이고 측정 가능하게 기술됨 |
| **Partial** | 일부 항목만 기술되었거나 모호한 표현이 포함됨 |
| **Missing** | 해당 카테고리에 대한 언급이 없거나 극히 부족함 |

## 질문 생성 규칙

Partial 또는 Missing 상태인 카테고리에 대해 질문 후보를 생성하되, 다음 경우는 제외:
- 명확화가 구현이나 검증 전략에 실질적 영향을 주지 않는 경우
- 계획 단계(sdd-plan)에서 결정하는 것이 더 적절한 정보인 경우 (내부 메모)