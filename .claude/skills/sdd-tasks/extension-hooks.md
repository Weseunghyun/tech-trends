# 확장 훅 처리 절차

## before_tasks 훅 (태스크 생성 전)

- 프로젝트 루트에 `.specify/extensions.yml`이 있는지 확인합니다.
- 존재하면 읽고 `hooks.before_tasks` 키 아래 항목을 찾습니다
- YAML을 파싱할 수 없거나 유효하지 않으면 조용히 훅 검사를 건너뛰고 정상 진행합니다
- `enabled: true`인 훅만 필터링합니다
- 나머지 각 훅에 대해 훅 `condition` 표현식을 해석하거나 평가하려고 시도하지 **마세요**:
  - 훅에 `condition` 필드가 없거나 null/비어있으면 실행 가능으로 처리
  - 훅이 비어있지 않은 `condition`을 정의하면 훅을 건너뛰고 조건 평가는 HookExecutor 구현에 맡깁니다
- 실행 가능한 각 훅에 대해 `optional` 플래그에 따라 다음을 출력합니다:
  - **선택적 훅** (`optional: true`):
    ```
    ## 확장 훅

    **선택적 사전 훅**: {extension}
    명령: `/{command}`
    설명: {description}

    프롬프트: {prompt}
    실행하려면: `/{command}`
    ```
  - **필수 훅** (`optional: false`):
    ```
    ## 확장 훅

    **자동 사전 훅**: {extension}
    실행 중: `/{command}`
    EXECUTE_COMMAND: {command}

    개요로 진행하기 전에 훅 명령의 결과를 기다립니다.
    ```
- 등록된 훅이 없거나 `.specify/extensions.yml`이 존재하지 않으면 조용히 건너뜁니다

## after_tasks 훅 (태스크 생성 후)

- 프로젝트 루트에 `.specify/extensions.yml`이 있는지 확인합니다.
- 존재하면 읽고 `hooks.after_tasks` 키 아래 항목을 찾습니다
- YAML을 파싱할 수 없거나 유효하지 않으면 조용히 훅 검사를 건너뛰고 정상 진행합니다
- `enabled: true`인 훅만 필터링합니다
- 나머지 각 훅에 대해 훅 `condition` 표현식을 해석하거나 평가하려고 시도하지 **마세요**:
  - 훅에 `condition` 필드가 없거나 null/비어있으면 실행 가능으로 처리
  - 훅이 비어있지 않은 `condition`을 정의하면 훅을 건너뛰고 조건 평가는 HookExecutor 구현에 맡깁니다
- 실행 가능한 각 훅에 대해 `optional` 플래그에 따라 다음을 출력합니다:
  - **선택적 훅** (`optional: true`):
    ```
    ## 확장 훅

    **선택적 훅**: {extension}
    명령: `/{command}`
    설명: {description}

    프롬프트: {prompt}
    실행하려면: `/{command}`
    ```
  - **필수 훅** (`optional: false`):
    ```
    ## 확장 훅

    **자동 훅**: {extension}
    실행 중: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- 등록된 훅이 없거나 `.specify/extensions.yml`이 존재하지 않으면 조용히 건너뜁니다
