---
title: "Contract: 수집기 CLI / 모듈 인터페이스"
type: contract
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Draft
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/contract
---

# Contract: 수집기 CLI / 모듈 인터페이스

파이썬 수집기의 실행 계약. 스케줄 루틴(또는 폴백 Actions)이 이 진입점을 호출하고, 에이전트가 요약 단계를 인라인으로 채운다.

## 진입점

```bash
python -m scripts.collect [--dry-run] [--date YYYY-MM-DD] [--out docs/data]
```

| 플래그 | 기본 | 의미 |
|---|---|---|
| `--dry-run` | off | 수집·점수까지 수행하되 파일 쓰기·커밋 안 함. stdout에 요약 통계만(시크릿 미출력) |
| `--date` | KST 오늘 | 기준 일자 지정(테스트용) |
| `--out` | `docs/data` | 산출 디렉토리 |

종료 코드: `0` = 부분 성공 포함 정상(최소 1개 소스 성공), `1` = 전 소스 실패 또는 치명 오류. 전 소스 실패 시 직전 `latest.json`을 덮어쓰지 않는다(엣지 케이스 정책).

## 모듈 경계 (단일 프로젝트, scripts/)

| 모듈 | 책임 | 핵심 함수(계약) |
|---|---|---|
| `scripts/sources/*.py` | 소스별 수집 | `fetch() -> list[RawItem]` (예외는 호출측에서 격리) |
| `scripts/http.py` | 공통 HTTP | `get(url, timeout=15) -> bytes` (verify=True, raise_for_status) |
| `scripts/normalize.py` | URL 정규화·검증 | `normalize_url(raw:str) -> str`, `valid_url(u:str) -> bool` |
| `scripts/dedup.py` | 중복 제거·원장 | `load_ledger(path)`, `prune(ledger, today, days=30)`, `is_new(url, ledger)` |
| `scripts/score.py` | 그룹핑·점수 | `group_topics(items) -> list[Topic]`, `score(topics) -> list[HotTopic]` |
| `scripts/render.py` | 산출물 작성 | `write_snapshot(snapshot, out)`, `refresh_pointers(out)`, `prune_files(out, days=30)` |
| `scripts/collect.py` | 오케스트레이션 | 위 단계 순차 호출, SourceStatus 집계 |

요약(`summary_ko`) 생성은 **에이전트 인라인 단계**로, 수집기는 신규 항목 목록을 산출하고 에이전트가 한글 요약을 채운 뒤 `render`로 넘긴다(별도 LLM 키 없음, R6). 폴백(Actions)에서는 요약 생략 또는 외부 LLM 키 사용.

## 보안 계약 (SEC-01~09, 헌법 I)

- 어떤 경로(stdout/stderr/로그/산출물)로도 시크릿·자격증명·`info` dict를 출력하지 않는다.
- 개별 소스 실패: `SourceStatus.error_type`에 `type(e).__name__`만 기록 후 `continue`(SEC-02, FR-009).
- 외부 HTTP: `verify=True`·`timeout` 명시·`raise_for_status()`(SEC-04). feedparser엔 URL이 아닌 **bytes** 전달.
- `eval/exec/os.system/shell=True` 금지(SEC-03). 동적 실행 없음.
- ticker류 자유 입력은 없으나, 외부 URL·제목은 정규식/길이 검증 후 사용(SEC-05).
- 의존성 `==` 핀, 추가 시 `pip-audit`(SEC-08).

## 검증 게이트

- `impl-python-validate`(ruff → bandit → pip-audit)를 구현 후 실행.
- `--dry-run`으로 시크릿 미출력·부분 성공 격리·점수 정렬을 회귀 검증.
