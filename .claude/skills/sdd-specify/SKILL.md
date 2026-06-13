---
name: sdd-specify
description: "자연어 기능 설명으로부터 기능 명세서(spec.md)를 생성하거나 업데이트한다. 새 기능 개발을 시작할 때, 기능 스펙을 정의하거나, 요구사항을 분석하거나, 사용자 시나리오를 작성할 때 사용한다. '스펙 작성', '명세서 만들어', '기능 정의', '요구사항 정리' 요청 시 반드시 이 스킬을 사용한다."
argument-hint: "[작업-ID(선택)] [기능 설명]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 개요

사용자가 트리거 메시지에서 `/sdd-specify` 뒤에 입력한 텍스트가 **기능 설명**입니다. `$ARGUMENTS`가 아래에 문자 그대로 나타나더라도 이 대화에서 항상 사용 가능하다고 가정하세요. 사용자가 빈 명령어를 제공한 경우에만 다시 물어보세요.

### 브랜치/slug 규칙 (개인 프로젝트)
- 외부 이슈 트래커(Jira/GitLab) 연동은 없습니다.
- 기능 설명에서 **2~4단어 slug**를 만듭니다 (동작-명사, 예: `fetch-jp-prices`, `add-rsi-screener`).
- 브랜치 이름은 **`feature/{slug}`** 형식으로 생성합니다.
- 사용자가 별도 작업 ID(예: `JP-12`)를 인자로 주면 `feature/{id}`도 허용합니다.

## 실행 흐름

해당 기능 설명이 주어지면 다음을 수행하세요:

1. **slug 생성**: 기능 설명을 분석하여 2~4단어 slug를 만듭니다 (동작-명사, 예: `add-user-auth`, `fetch-jp-prices`). 사용자가 작업 ID를 줬으면 그것을 brnach/slug에 사용합니다.

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다. (개인용 셋업에서는 항상 스킵됩니다.)

2. **기능 브랜치 생성**: 위 slug로 `feature/{slug}` 브랜치를 생성합니다:
    ```bash
    .specify/scripts/bash/create-new-feature.sh "$ARGUMENTS" --json --branch "feature/{slug}"
    ```
   - `--branch "feature/{slug}"`: Git 브랜치명을 지정합니다.
   - `--number`와 `--short-name`을 전달하지 마세요
   - JSON 출력에서 BRANCH_NAME, SPEC_FILE, SPEC_DIR_NAME을 파싱합니다
   - `BRANCH_NAME`은 git 브랜치명 (`feature/{slug}`), `SPEC_DIR_NAME`은 spec 디렉토리명 (`NNN-{slug}`)

3. **템플릿 로드**: `.specify/templates/spec-template.md`를 읽어 필수 섹션을 이해합니다.

4. **명세서 생성**: 실행 흐름에 따라 spec.md를 작성합니다. 세부 규칙은 [guidelines.md](guidelines.md)를 참조하세요. **마크다운 포맷팅 규칙은 [formatting-rules.md](../sdd-shared/formatting-rules.md)를 반드시 준수합니다** (특히 템플릿의 후행 공백 2칸 보존).

5. **명세서 품질 검증**: 작성 후 `spec-reviewer` 서브에이전트에 위임하여 품질을 검증합니다:
    ```
    Agent(spec-reviewer): "spec.md 품질 검증 - SPEC={spec.md 경로}"
    ```
   에이전트 결과에서 실패 항목이 있으면 [quality-checklist.md](quality-checklist.md)의 절차에 따라 처리합니다.

6. **완료 보고**: 브랜치 이름, 명세서 파일 경로, 체크리스트 결과, 다음 단계 준비 상태를 보고합니다.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 결과를 알립니다.

**참고:** 스크립트는 작성 전에 새 브랜치를 생성하고 체크아웃하며 명세서 파일을 초기화합니다.

### 다음 단계 안내
- `/sdd-clarify`: 명세서의 모호한 결정 포인트 명확화 (권장)
- `/sdd-plan`: 명세서 기반으로 구현 계획 생성
- `/sdd-checklist`: 도메인별 체크리스트 생성