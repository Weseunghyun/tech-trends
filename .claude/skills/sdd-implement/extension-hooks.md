# 확장 훅 처리 절차

## before_implement 훅

- 프로젝트 루트에 `.specify/extensions.yml`이 있는지 확인
- 존재하면 읽고 `hooks.before_implement` 키 아래 항목을 찾습니다
- YAML을 파싱할 수 없거나 유효하지 않으면 조용히 건너뜁니다
- `enabled: true`인 훅만 필터링
- `condition` 표현식을 해석하거나 평가하려고 시도하지 마세요:
  - condition이 없거나 null/비어있으면 실행 가능으로 처리
  - 비어있지 않은 condition이면 건너뛰기
- **선택적 훅** (`optional: true`): 명령, 설명, 프롬프트를 안내
- **필수 훅** (`optional: false`): 자동 실행 후 결과 대기

## after_implement 훅

- `.specify/extensions.yml`의 `hooks.after_implement` 키 처리
- 동일한 필터링 및 실행 규칙 적용
- 선택적/필수 훅 동일하게 처리
- 등록된 훅이 없으면 조용히 건너뜁니다
