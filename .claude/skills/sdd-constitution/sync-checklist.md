# 일관성 전파 체크리스트

## 확인 대상 파일

Constitution 업데이트 후 다음 파일들을 검토하여 일관성을 보장합니다:

### plan-template.md
- `.specify/templates/plan-template.md`를 읽고 "constitution 점검" 또는 규칙이 업데이트된 원칙과 정렬되는지 확인

### spec-template.md
- `.specify/templates/spec-template.md`에서 범위/요구사항 정렬을 확인
- constitution이 필수 섹션이나 제약사항을 추가/제거하면 업데이트

### tasks-template.md
- `.specify/templates/tasks-template.md`를 읽고 태스크 분류가 새롭거나 제거된 원칙 기반 태스크 유형을 반영하는지 확인

### 명령 파일
- `.specify/templates/commands/*.md`의 각 명령 파일을 읽어 오래된 참조가 남아있지 않은지 확인

### 런타임 가이던스 문서
- `README.md`, `docs/quickstart.md`, 또는 에이전트별 가이던스 파일을 읽음
- 변경된 원칙에 대한 참조를 업데이트

## 동기화 영향 보고서 형식

Constitution 파일 상단에 HTML 주석으로 추가:
- 버전 변경: 이전 → 새
- 수정된 원칙 목록 (이름 변경 시 이전 제목 → 새 제목)
- 추가된 섹션
- 제거된 섹션
- 업데이트가 필요한 템플릿 (✅ 업데이트됨 / ⚠ 대기 중) 파일 경로 포함
- 의도적으로 지연된 플레이스홀더가 있는 경우 후속 TODO
