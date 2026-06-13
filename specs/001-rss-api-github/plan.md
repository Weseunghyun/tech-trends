---
title: "Implementation Plan: AI·개발/기술 트렌드 종합 대시보드"
type: plan
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Approved
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/plan
---

# Implementation Plan: AI·개발/기술 트렌드 종합 대시보드

**Branch**: `feature/daily-trends-dashboard` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-rss-api-github/spec.md`

## Summary

매일 KST 08:00경 무인 루틴이 무료·무키 공개 소스(GitHub Trending RSS, AI 랩/OpenAI Codex RSS, Hacker News Algolia JSON)에서 항목을 수집하고, 정규화 URL로 중복을 제거(30일 롤링 원장)하며, 교차 출현 + HN engagement 실측치만으로 트렌드 점수를 매기고, 오케스트레이팅 에이전트가 한글로 요약·번역한 뒤, 정적 JSON(`docs/data/*.json`)으로 산출해 공개 GitHub Pages 정적 대시보드(`docs/index.html`, 외부 CDN 0, 동일 출처 fetch)로 보여준다. 개별 소스 실패는 격리되어 부분 성공으로 갱신한다. X는 phase 2(범위 밖).

기술 접근: 단일 프로젝트(파이썬 수집기 `scripts/` + 정적 프론트 `docs/`). 요약은 에이전트 인라인(별도 LLM 키 없음). 자세한 결정 근거는 [research.md](research.md), 스키마는 [data-model.md](data-model.md)·[contracts/](contracts/).

## Technical Context

**Language/Version**: Python 3.11+ (수집기), HTML5 + Vanilla JS/CSS (대시보드, 빌드 스텝·프레임워크 없음)  
**Primary Dependencies**: `feedparser==6.0.11`, `requests==2.33.0` (LLM SDK 없음 — 요약은 에이전트 인라인)  
**Storage**: 정적 JSON 파일(`docs/data/`); DB 없음  
**Testing**: pytest(수집/정규화/점수/중복 제거 단위), `--dry-run` 통합, `impl-python-validate`(ruff/bandit/pip-audit)  
**Target Platform**: GitHub Pages 정적 호스팅 + 스케줄 자동화(claude.ai/code 루틴 1차, GitHub Actions cron 폴백)  
**Project Type**: 단일 프로젝트(정적 사이트 + 배치 수집기)  
**Performance Goals**: 대시보드 첫 표시 5초 이내(SC-001, latest.json 단일 fetch); 수집 루틴 일 1회 수십 피드 순차로 충분  
**Constraints**: 외부 CDN 0·키/CORS 불필요(동일 출처); 시크릿 미노출(SEC-01); 외부 HTTP verify=True·timeout·raise_for_status(SEC-04); 카테고리당 ~10개; 30일 롤링  
**Scale/Scope**: 단일 소유자, 공개 읽기 전용; 일 수십~수백 항목; 4계열·9개 소스 식별자

## Constitution Check

*GATE: Phase 0 전 통과 필수, Phase 1 설계 후 재평가.*

| 원칙 | 게이트 | 평가 |
|---|---|---|
| I. 공개·정적 우선, 시크릿 미노출 (NON-NEGOTIABLE) | 산출물이 공개 가능 데이터만·정적 파일, 키는 env/시크릿로만, 위험 실행 없음, HTTP 안전 | **PASS** — 개인정보 없음. JSON/HTML 정적. `scripts/http.py`가 verify/timeout/raise_for_status 강제. eval/exec 없음. 시크릿은 루틴 env(폴백은 Actions Secret) |
| II. 클라우드 가용 소스만 자동화 | 자동 경로 소스가 클라우드 IP에서 도달 | **PASS** — R1에서 4계열 전부 GitHub Pages/raw/Algolia/OpenAI CDN, 클라우드 도달 확인. 로그인 소스 없음 |
| III. 데이터 무결성·출처 명시 | 출처 링크 필수·요약은 수집 데이터 근거·결측 추정 금지 | **PASS** — FR-003(URL 필수), 점수는 실측만(R2), 결측 null/""(FR-010) |
| IV. 외부 소스 실패 격리 | 개별 실패가 전체 중단 안 함 | **PASS** — SourceStatus 격리(FR-009, US3), `--dry-run` 회귀 |
| V. ToS·예의 준수 | 공개 RSS/공식 API만, 로그인 스크래핑 없음 | **PASS** — 공식/문서화 엔드포인트만. X는 phase 2(FR-016) |
| VI. 최소주의(YAGNI) | 서버·DB·인증 미추가 | **PASS** — 정적 사이트 + 배치. 의존성 2개·핀 고정 |

**위반 없음 → Complexity Tracking 불필요.** (Phase 1 설계 후 재평가: data-model/contracts가 정적 JSON·동일 출처·시크릿 미노출 유지 → 재평가도 PASS.)

## Project Structure

### Documentation (this feature)

```text
specs/001-rss-api-github/
├── plan.md              # 본 파일
├── spec.md              # 명세 (clarify 반영)
├── research.md          # Phase 0 산출
├── data-model.md        # Phase 1 산출
├── quickstart.md        # Phase 1 산출
├── contracts/           # Phase 1 산출
│   ├── data-json-schema.md
│   └── collector-cli.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/sdd-tasks 생성 — 본 단계 산출 아님)
```

### Source Code (repository root)

```text
scripts/                 # 파이썬 수집기 (배치)
├── collect.py           # 오케스트레이션 진입점 (python -m scripts.collect)
├── http.py              # 공통 HTTP (verify/timeout/raise_for_status)
├── normalize.py         # URL 정규화·검증
├── dedup.py             # 정규화-URL 중복 제거 + 30일 원장
├── score.py             # 토픽 그룹핑 + 트렌드 점수
├── render.py            # 스냅샷 작성·포인터 갱신·30일 prune
├── config.py            # 소스 목록·카테고리 매핑·점수 상수(W_SRC 등)
└── sources/
    ├── github_trending.py
    ├── ai_labs.py        # anthropic/openai/deepmind/meta/mistral/xai RSS
    ├── codex.py
    └── hackernews.py

docs/                    # GitHub Pages 정적 대시보드 (퍼블리시 루트 /docs)
├── index.html
├── app.js               # data/latest.json 동일 출처 fetch + 렌더
├── styles.css           # 모바일 반응형, 탭/카드, CDN 0
└── data/
    ├── latest.json       # 당일 스냅샷 복사본 (대시보드가 읽는 유일 파일)
    ├── YYYY-MM-DD.json   # 일자 아카이브 (≤30)
    ├── index.json        # 매니페스트 {dates, generated_at}
    └── seen_urls.json    # 중복 제거 원장 (수집기 전용)

tests/
├── unit/                # normalize/dedup/score 단위
└── integration/         # collect --dry-run, 부분 실패 격리

requirements.txt         # feedparser==6.0.11, requests==2.33.0
.github/workflows/       # (폴백) daily.yml — cron 0 23 * * *
```

**Structure Decision**: 단일 프로젝트. 수집기는 `scripts/`(stock-routine 관행 계승, `impl-python-validate` 적용 범위 `scripts/**/*.py`와 일치), 정적 산출은 `docs/`(GitHub Pages `/docs` 퍼블리시). 프론트는 빌드 스텝 없는 vanilla(헌법 VI). 소스별 어댑터는 `scripts/sources/`로 분리해 실패 격리·테스트 용이.

## Phase 0 — Research

→ [research.md](research.md) 완료. 해소된 항목: 소스 엔드포인트 직접 재확인(R1), 트렌드 점수 산식(R2), 정규화-URL 중복 제거 + 30일 원장(R3), 라이브러리 선정(R4), Pages 데이터 레이아웃(R5), 스케줄링 1차/폴백(R6), 30일 보관·git 이력 트레이드오프(R7). 미해결 "명확화 필요" 없음.

## Phase 1 — Design & Contracts

→ [data-model.md](data-model.md): TrendItem/HotTopic/Category/DashboardSnapshot/SourceStatus + SeenLedger/Manifest, 검증 규칙(SEC-05), 라이프사이클.  
→ [contracts/data-json-schema.md](contracts/data-json-schema.md): 대시보드↔데이터 JSON 계약(동일 출처, 전방 호환).  
→ [contracts/collector-cli.md](contracts/collector-cli.md): 수집기 CLI/모듈 경계 + 보안 계약.  
→ [quickstart.md](quickstart.md): 로컬 실행·검증·배포 절차.  
→ 에이전트 컨텍스트: `update-agent-context.sh claude` 실행으로 갱신.

## Post-Design Constitution Re-Check

설계 산출물 검토 결과 모든 원칙 **PASS 유지**: 정적 JSON·동일 출처(I·VI), 클라우드 가용 소스만(II), 출처 필수·실측 점수·결측 추정 금지(III), SourceStatus 실패 격리(IV), 공식 엔드포인트만·X 제외(V). 신규 위반·복잡도 부채 없음.

## 다음 단계

`/sdd-tasks` — 본 설계 산출물 기반 실행 가능한 태스크 분해.
