# SDD 마크다운 포맷팅 규칙

이 문서는 모든 sdd-* 스킬에서 문서 생성 시 공유하는 마크다운 포맷팅 규칙을 정의합니다.

## 1. YAML Frontmatter

모든 sdd-* 스킬이 생성하는 마크다운 문서는 파일 최상단에 YAML frontmatter를 포함합니다. (개인 프로젝트라 외부 노트 앱 연동은 없으며, frontmatter는 문서 분류/검색 편의를 위한 것입니다.)

### 속성

| 속성 | 설명 | 예시 |
|------|------|------|
| `title` | 문서 제목 | `"Feature Specification: 환율 갱신"` |
| `type` | 문서 유형 | `spec`, `plan`, `tasks`, `checklist`, `research`, `data-model`, `quickstart`, `contract`, `constitution` |
| `project` | 프로젝트 이름 | `stock-routine` |
| `feature` | 기능 slug | `fetch-jp-prices` |
| `branch` | 기능 브랜치명 | `feature/fetch-jp-prices` |
| `status` | 문서 상태 | `Draft`, `In Review`, `Approved`, `Implemented` |
| `created` | 생성일 (ISO 8601) | `2026-06-03` |
| `updated` | 최종 수정일 (ISO 8601) | `2026-06-03` |
| `tags` | 태그 목록 | `[sdd, sdd/spec]` |

### project 값 결정

`project` 속성은 `.specify/sdd-config.yml` 파일의 `project` 값을 사용합니다.

- 문서 생성 전에 `.specify/sdd-config.yml`을 읽어 `project` 값을 파싱합니다
- 값이 비어있거나 파일이 없으면 `project` 필드를 빈 문자열(`""`)로 설정합니다

### Frontmatter 템플릿

```yaml
---
title: "[문서 제목]"
type: [문서 유형]
project: "[project from .specify/sdd-config.yml]"
feature: "[slug]"
branch: "[feature/slug]"
status: Draft
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
tags:
  - sdd
  - sdd/[type]
---
```

### 태그 규칙

- 모든 SDD 문서에는 공통 태그 `sdd`를 포함합니다
- 문서 유형별 네스티드 태그 `sdd/[type]`을 추가합니다 (예: `sdd/spec`, `sdd/plan`, `sdd/tasks`)
- 체크리스트 문서는 도메인별 태그도 추가합니다 (예: `sdd/checklist`, `sdd/checklist/ux`)

### 적용 규칙

- 새 문서 생성 시: 템플릿의 플레이스홀더를 실제 값으로 치환하여 frontmatter를 작성합니다
- 기존 문서 수정 시: `updated` 날짜를 현재 날짜로 갱신합니다
- `status` 변경 시: 워크플로우에 맞게 자동 업데이트합니다
  - sdd-specify 완료 → `Draft`
  - sdd-clarify 완료 → `In Review`
  - sdd-plan/sdd-tasks 완료 → `Approved`
  - sdd-implement 완료 → `Implemented`
- `project` 값은 `.specify/sdd-config.yml`의 `project`에서 읽어온 값을 사용합니다
- `feature`, `branch` 값은 스크립트 출력(JSON)에서 파싱한 값을 사용합니다

### 비템플릿 문서

`research.md`, `data-model.md`, `quickstart.md`, `contracts/*.md` 등 별도 템플릿 없이 생성되는 문서에도 동일한 frontmatter 규칙을 적용합니다. 각 스킬의 실행 흐름에서 해당 문서 생성 시 frontmatter를 포함하도록 지침이 명시되어 있습니다.

## 2. 후행 공백 2칸 (Trailing Two Spaces) 보존

마크다운에서 줄 끝에 공백 2칸(`  `)은 `<br>` 줄바꿈을 의미합니다.

**규칙**: `.specify/templates/` 의 템플릿 파일에서 줄 끝에 공백 2칸(`  `)이 있는 라인은, 생성되는 문서에서도 **반드시** 동일하게 공백 2칸을 유지해야 합니다.

### 적용 대상 예시

```markdown
# 템플릿 원본 (공백 2칸이 줄 끝에 있음)
**Feature Branch**: `[###-feature-name]`··
**Created**: [DATE]··
**Status**: Draft··

**Language/Version**: [e.g., Python 3.11]··
**Primary Dependencies**: [e.g., FastAPI]··
```

> 위에서 `··`는 공백 2칸을 나타냅니다.

### 생성 시 주의사항

- 템플릿을 로드할 때 각 라인의 후행 공백을 확인합니다
- 메타데이터 라인(예: `**Key**: Value`)이 연속으로 나열되고 템플릿에서 `  `(공백 2칸)으로 끝나는 경우, 생성 문서에서도 동일하게 `  `을 추가합니다
- Write 도구나 Edit 도구로 파일을 작성할 때 해당 라인 끝에 공백 2칸이 포함되어야 합니다
- 공백 2칸이 없는 라인에는 추가하지 않습니다 — 템플릿에 있는 그대로만 적용합니다