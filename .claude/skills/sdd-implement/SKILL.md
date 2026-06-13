---
name: sdd-implement
description: "tasks.md에 정의된 태스크를 실행하여 코드를 구현한다. 설계 산출물 기반으로 코드 구현을 시작하거나, 태스크 목록에 따라 개발을 진행할 때 사용한다. '구현 시작', '코드 작성 시작', '태스크 실행' 요청 시 반드시 이 스킬을 사용한다."
argument-hint: "[추가 컨텍스트 또는 시작 태스크 ID]"
---

## 사용자 입력

```text
$ARGUMENTS
```

진행하기 전에 사용자 입력을 **반드시** 확인해야 합니다 (비어있지 않은 경우).

## 사전 실행 검사

**확장 훅 확인 (구현 전)**: `.specify/extensions.yml`의 `hooks.before_implement` 처리. 훅 처리 절차는 [extension-hooks.md](extension-hooks.md)를 참조하세요.

## 개요

### Slack 알림
[slack-notifications.md](../sdd-shared/slack-notifications.md) 참조하여 STARTED 알림을 발송합니다.

1. `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`를 실행하고 FEATURE_DIR과 AVAILABLE_DOCS를 파싱합니다.

2. **체크리스트 상태 확인** (FEATURE_DIR/checklists/가 존재하는 경우): 세부 절차는 [checklist-validation.md](checklist-validation.md)를 참조하세요.

3. **구현 컨텍스트 로드**: tasks.md, plan.md (필수), data-model.md, contracts/, research.md, quickstart.md (선택)를 읽습니다.

4. **프로젝트 설정 검증**: 실제 프로젝트 설정에 기반하여 무시 파일 생성/검증. 세부 규칙은 [project-setup.md](project-setup.md)를 참조하세요.

5. **태스크 파싱**: tasks.md에서 단계, 종속성, 태스크 세부사항, 실행 흐름을 추출합니다.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 MILESTONE 템플릿으로 체크리스트 검증 및 각 Phase 위임 진행 상황을 알립니다.

6. **구현 실행** (`implementer` 서브에이전트 활용):
   - 단계별 실행: 다음 단계로 이동하기 전에 각 단계를 완료
   - **[P] 태스크 병렬 실행**: 같은 단계 내에서 [P] 마커가 있고 서로 다른 파일을 대상으로 하는 태스크들은 `implementer` 서브에이전트에 병렬 위임:
     ```
     Agent(implementer): "T005 [P] 구현 - TASK={태스크 설명}, PLAN={plan.md 경로}, FEATURE_DIR={FEATURE_DIR 경로}"
     Agent(implementer): "T006 [P] 구현 - TASK={태스크 설명}, PLAN={plan.md 경로}, FEATURE_DIR={FEATURE_DIR 경로}"
     ```
   - 순차 태스크는 직접 실행하거나 하나의 implementer에 위임
   - TDD 접근법: 해당 구현 태스크 전에 테스트 태스크 실행
   - 파일 기반 조정: 같은 파일에 영향을 미치는 태스크는 순차 실행
   - **Phase 완료 시 커밋 확인**: 각 Phase(단계)의 모든 태스크가 완료된 시점에 `git status`로 미커밋 변경사항을 확인한다. 스테이징되지 않은 변경이나 스테이징된 변경이 있으면 `commit-rule` 스킬 규칙에 따라 커밋한다. 이는 implementer가 개별 태스크 커밋을 누락했을 때의 안전장치이다.

7. **실행 순서**: 설정 → 테스트(필요시) → 핵심 개발 → 통합 → 마무리

8. **진행 추적**: 완료된 태스크 후 진행 보고, 실패 시 중단/보고, 완료된 태스크는 tasks 파일에서 `[X]`로 표시

9. **모듈별 커밋**: implementer 서브에이전트는 각 태스크(또는 논리적 모듈 단위) 구현 완료 후 `commit-rule` 스킬 규칙에 따라 커밋한다. (push는 하지 않는다)

10. **최종 커밋 확인**: 모든 태스크 완료 후 `git status`로 미커밋 변경사항을 확인한다. 변경된 파일이 있으면 `commit-rule` 스킬 규칙에 따라 커밋한다. tasks.md의 `[X]` 표시 갱신 등 문서 변경도 포함한다.

11. **완료 검증**: 모든 태스크 완료 확인, 명세서 일치, 테스트 통과, 최종 상태 보고

12. **보안/품질 검증**: 태스크를 최종 `[X]`로 확정하기 전, Python 코드(`scripts/**`)가 변경된 경우 `impl-python-validate` 스킬을 실행하여 보안/품질을 검증한다. 도구(ruff/bandit/pip-audit)가 미설치면 graceful skip 후 수동 체크리스트로 대체한다. 보안 규칙은 `.claude/rules/python-security.md`(SEC-01~SEC-09)를 따른다.

13. **사후 확장 훅 확인**: `.specify/extensions.yml`의 `hooks.after_implement` 처리. [extension-hooks.md](extension-hooks.md) 참조.

**Slack 알림**: [slack-notifications.md](../sdd-shared/slack-notifications.md)의 COMPLETED 또는 FAILED 템플릿으로 최종 검증 결과를 알립니다. (개인용 셋업에서는 항상 스킵됩니다.)

**참고**: tasks.md에 완전한 태스크 분해가 존재한다고 가정합니다. 불완전하면 `/sdd-tasks`를 먼저 실행하세요.

### 다음 단계 안내
- 구현 완료된 브랜치는 로컬에서 검토 후 직접 머지하거나 PR을 생성한다(개인 프로젝트, 외부 MR 도구 연동 없음).
