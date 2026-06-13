# sdd-plan 상세 단계 설명

## 0단계: 개요 및 리서치

1. **기술 컨텍스트에서 불명확한 항목 추출**:
   - 각 "명확화 필요" 항목 → 리서치 태스크
   - 각 의존성 → 모범 사례 태스크
   - 각 통합 → 패턴 태스크

2. **리서치 에이전트 생성 및 배정**:

   `researcher` 에이전트 (`.claude/agents/researcher.md`)를 사용하여 각 불명확 항목을 병렬로 조사합니다.

   ```text
   기술 컨텍스트의 각 불명확한 항목에 대해:
     Agent(researcher): "{기능 컨텍스트}에 대한 {불명확 항목} 리서치"
   각 기술 선택에 대해:
     Agent(researcher): "{도메인}에서 {기술}의 모범 사례 찾기"
   각 통합 대상에 대해:
     Agent(researcher): "{통합 대상}의 통합 패턴 조사"
   ```

   **에이전트 호출 규칙**:
   - 독립적인 조사 항목은 병렬로 실행
   - 의존성이 있는 항목은 순차 실행
   - 각 에이전트에 기능 명세서 경로와 프로젝트 컨텍스트 전달

3. **결과 통합** `research.md`에 다음 형식으로 작성:
   - **frontmatter 포함** ([formatting-rules.md](../sdd-shared/formatting-rules.md) 참조):
     ```yaml
     ---
     title: "Research: [FEATURE NAME]"
     type: research
     feature: "[slug]"
     branch: "[feature/slug]"
     status: Draft
     created: [YYYY-MM-DD]
     updated: [YYYY-MM-DD]
     tags:
       - sdd
       - sdd/research
     ---
     ```
   - 결정: [선택된 사항]
   - 근거: [선택 이유]
   - 고려된 대안: [평가된 다른 옵션]

**산출물**: 모든 "명확화 필요"가 해결된 research.md

## 1단계: 설계 및 계약

**전제조건:** `research.md` 완료

1. **기능 명세서에서 엔티티 추출** → `data-model.md`:
   - **frontmatter 포함** ([formatting-rules.md](../sdd-shared/formatting-rules.md) 참조, `type: data-model`, 태그: `sdd/data-model`)
   - 엔티티 이름, 필드, 관계
   - 요구사항에서 도출된 유효성 검증 규칙
   - 해당되는 경우 상태 전이
   - 외부에서 받는 입력 필드는 검증 규칙(형식/범위)을 명시한다(보안: SEC-05)

2. **인터페이스 계약 정의** (프로젝트에 외부 인터페이스가 있는 경우) → `/contracts/`:
   - **각 계약 문서에 frontmatter 포함** ([formatting-rules.md](../sdd-shared/formatting-rules.md) 참조, `type: contract`, 태그: `sdd/contract`)
   - 프로젝트가 사용자나 다른 시스템에 노출하는 인터페이스 식별
   - 프로젝트 유형에 적합한 계약 형식 문서화
   - 예시: 라이브러리의 공개 API, CLI 도구의 명령 스키마, 웹 서비스의 엔드포인트, 파서의 문법, 애플리케이션의 UI 계약
   - 순수 내부용 프로젝트인 경우 건너뜁니다 (빌드 스크립트, 일회용 도구 등)

3. **에이전트 컨텍스트 업데이트**:
   - `.specify/scripts/bash/update-agent-context.sh claude` 실행
   - 이 스크립트는 사용 중인 AI 에이전트를 감지합니다
   - 해당 에이전트별 컨텍스트 파일을 업데이트합니다
   - 현재 계획의 새로운 기술만 추가합니다
   - 마커 사이의 수동 추가 사항을 보존합니다

4. **quickstart.md 생성 시**: frontmatter를 포함합니다 ([formatting-rules.md](../sdd-shared/formatting-rules.md) 참조, `type: quickstart`, 태그: `sdd/quickstart`)

**산출물**: data-model.md, /contracts/*, quickstart.md, 에이전트별 파일
