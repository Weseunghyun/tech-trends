---
title: "Tasks: AI·개발/기술 트렌드 종합 대시보드"
type: tasks
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Approved
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/tasks
---

# Tasks: AI·개발/기술 트렌드 종합 대시보드

**Input**: Design documents from `specs/001-rss-api-github/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 헌법·PROJECT_BRIEF의 "매 단계 테스트 + dry-run + ruff/bandit" 방침에 따라 핵심 단위/통합 테스트를 포함한다(전수 TDD는 아님).

**Organization**: 사용자 스토리(P1/P2/P3)별로 단계를 묶어 독립 구현·테스트가 가능하게 한다.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 병렬 가능(다른 파일, 미완료 종속 없음)
- **[Story]**: 소속 사용자 스토리(US1/US2/US3)
- 설명에 정확한 파일 경로 포함

## Path Conventions

단일 프로젝트: 수집기 `scripts/`, 정적 프론트 `docs/`, 테스트 `tests/`(plan.md 구조).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 프로젝트 초기화 및 기본 구조

- [X] T001 plan.md 구조대로 디렉토리 생성: `scripts/`, `scripts/sources/`, `docs/`, `docs/data/`, `tests/unit/`, `tests/integration/` (각 패키지에 `__init__.py`)
- [X] T002 `requirements.txt` 작성 — `feedparser==6.0.11`, `requests==2.33.0` (== 핀, SEC-08). LLM SDK 미포함
- [X] T003 [P] ruff·bandit 설정 추가 (`pyproject.toml` 또는 `ruff.toml`/`.bandit`) — ruff S-그룹 활성(SEC 검출)
- [X] T004 [P] `scripts/config.py` 작성 — 소스 목록·엔드포인트(research.md R1), 닫힌 소스 enum(9개: github_trending·anthropic·openai·deepmind·meta_ai·mistral·xai·openai_codex·hackernews) 및 소스→카테고리 매핑(data-model Category, HN→`hot_topics`), 점수 상수 `W_SRC=0.6`/`W_HN=0.4`/`COMMENT_RATIO=0.5`/`JACCARD=0.5`, 길이 컷 상수. 각 소스는 **클라우드 IP 도달·로그인 불필요**(FR-015)임을 주석으로 명시하고, X/Twitter 엔드포인트를 포함하지 않음을 보장(FR-016 가드)
- [X] T005 [P] `.gitignore`에 `.env`·`*.key`·SA JSON 패턴 확인/추가(SEC-09), `docs/data/`는 추적 대상 유지

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 스토리가 의존하는 핵심 인프라

**⚠️ CRITICAL**: 이 단계 완료 전 사용자 스토리 작업 불가

- [X] T006 `scripts/http.py` 구현 — `get(url, timeout=15) -> bytes` (Session + UA, `verify=True` 기본 유지, `raise_for_status()`; SEC-04). 시크릿·URL 토큰 미출력
- [X] T007 [P] `scripts/normalize.py` 구현 — `normalize_url(raw)`(scheme소문자·http→https·www제거·끝슬래시·utm_/추적파라미터제거·정렬·fragment제거, research R3) + `valid_url(u)`(`^https?://[^\s]{1,2048}$`) + `item_id(url)`(정규화 URL의 sha1-hex)
- [X] T008 `scripts/render.py` 구현 — `write_snapshot(snapshot, out)`, `refresh_pointers(out)`(latest.json 복사·index.json 갱신), `prune_files(out, days=30)`; `schema_version=1`, 한국어 JSON `ensure_ascii=False` (data-model·R7)
- [X] T009 `scripts/collect.py` 골격 — argparse(`--dry-run`,`--date`,`--out docs/data`), KST(Asia/Seoul) 기준 일자 계산, 소스 호출→항목 수집→render 호출 파이프라인 배선. (실패 격리·점수·중복 제거는 각 스토리에서 강화)

**Checkpoint**: 공통 인프라 준비 — 사용자 스토리 착수 가능

---

## Phase 3: User Story 1 - 매일 자동 수집·요약된 트렌드를 대시보드에서 본다 (Priority: P1) 🎯 MVP

**Goal**: 수집→검증→산출(JSON)→정적 대시보드 표시의 종단 흐름. 카테고리별 항목 + 한글 요약 + 출처 링크 + 신선도 + 모바일 반응형.

**Independent Test**: `python -m scripts.collect --out docs/data` 1회 실행으로 `latest.json` 생성 후, `docs/`를 로컬 서버로 열어 카테고리별 항목·한글 요약·클릭 가능 출처 링크·갱신 시각이 표시되고 모바일 폭에서 가로 스크롤이 없으면 통과.

### Implementation for User Story 1

- [X] T010 [P] [US1] `scripts/sources/github_trending.py` — `fetch() -> list[dict]` (daily/all.xml, http.py로 bytes→feedparser.parse, title/url/published 추출, category=`github_trending`)
- [X] T011 [P] [US1] `scripts/sources/ai_labs.py` — Anthropic·OpenAI(공식 RSS)·DeepMind(공식 RSS)·Meta·Mistral·xAI 피드 수집, source 식별자·category=`ai_labs` 부여(research R1 엔드포인트)
- [X] T012 [P] [US1] `scripts/sources/codex.py` — OpenAI Codex changelog RSS 수집, category=`codex`
- [X] T013 [P] [US1] `scripts/sources/hackernews.py` — Algolia `search?tags=front_page`·`search_by_date` JSON, `points`/`num_comments`/`created_at_i` → metrics, category=`hot_topics` 원천, 429 백오프
- [X] T014 [US1] `scripts/collect.py`에 항목 정규화·검증 통합 — 각 raw 항목에 `item_id`·정규화 url·`valid_url` 필터(미충족 폐기)·title/summary 길이 컷·`collected_at`(KST)·카테고리당 ~10개 상한(FR-017) 적용 (T010–T013, T007 의존)
- [X] T015 [US1] 요약 주입 계약 구현 — `collect.py`/`render.py`가 `summary_ko`를 받도록(기본 ""), 에이전트가 채울 수 있는 `--summaries <json>` 머지 경로 또는 항목별 빈 필드 산출(FR-004; 결측 시 "" 유지, 추정 금지)
- [X] T016 [US1] `render`로 당일 `DashboardSnapshot` 작성 → `docs/data/YYYY-MM-DD.json`·`latest.json`·`index.json` 생성(contracts/data-json-schema 준수)
- [X] T017 [P] [US1] `docs/index.html` — 카테고리 탭(AI 랩 동향/GitHub Trending/엔지니어링·기술 블로그/OpenAI Codex/핫토픽), 외부 CDN 0
- [X] T018 [P] [US1] `docs/styles.css` — 모바일 반응형(가로 스크롤 없음, SC-005), 카드/탭 룩앤필
- [X] T019 [US1] `docs/app.js` — `data/latest.json?v=<ts>` 동일 출처 fetch(`cache:"no-store"`), 카테고리별 카드 렌더(제목→url 링크, `summary_ko`), `generated_at` 신선도 표시(FR-012), 빈 카테고리 "항목 없음"(T017 의존)
- [X] T020 [P] [US1] `tests/integration/test_collect_smoke.py` — `--dry-run`에서 1개 이상 소스 수집·모든 항목이 `valid_url` 통과·출처 링크 100% 보유(SC-002)·시크릿 미출력 검증; `docs/index.html`이 외부 CDN(절대 URL script/link)을 포함하지 않음 단언(SC-001/외부 CDN 0) (US1 Independent Test)

**Checkpoint**: US1 단독으로 "오늘의 트렌드를 본다" MVP 동작·테스트 가능

---

## Phase 4: User Story 2 - "뜨거운 화두"를 트렌드 점수로 식별한다 (Priority: P2)

**Goal**: 교차 출현 + HN engagement 실측치로 트렌드 점수 산출, 핫토픽 점수 내림차순 표시.

**Independent Test**: 복수 소스에 동일 주제가 있을 때 핫토픽 섹션에 점수·src_count와 함께 상위 노출되고 내림차순 정렬되면 통과.

### Implementation for User Story 2

- [X] T021 [P] [US2] `scripts/score.py` — `group_topics(items)`(제목 토큰셋 Jaccard≥0.5 또는 동일 정규화 URL 그리디 클러스터, research R2) + `score(topics)`(`log1p`+min-max 정규화, `0.6*src + 0.4*hn`, 0~1)
- [X] T022 [US2] `scripts/collect.py`에 점수 단계 통합 — 수집 항목으로 HotTopic 산출, 점수 내림차순 상위 10(FR-008/FR-017)을 snapshot `hot_topics`에 기록 (T021, T014 의존)
- [X] T023 [US2] `docs/app.js`·`docs/index.html` 핫토픽 탭 — `hot_topics` 렌더(점수·src_count 배지, 근거 항목 출처 링크), 내림차순 정렬 표시 (T019 의존)
- [X] T024 [P] [US2] `tests/unit/test_score.py` — research R2 worked example(Claude 0.96 > Rust 0.70 > DeepMind 0.00) 재현, 결측 HN 항이 0 처리(헌법 III)·정렬 검증

**Checkpoint**: US1 + US2 모두 독립 동작 — 핫토픽 점수 표시

---

## Phase 5: User Story 3 - 개별 소스 실패에도 대시보드가 부분 갱신된다 (Priority: P3)

**Goal**: 소스 실패 격리(부분 성공 갱신) + 정규화 URL 일자 간 중복 제거.

**Independent Test**: 한 소스 엔드포인트를 강제 실패시켜도 나머지로 `latest.json` 갱신·전체 중단 없음, 실패 소스는 "데이터 없음"; 동일 URL 항목이 일자에 걸쳐 1회만 노출.

### Implementation for User Story 3

- [X] T025 [US3] `scripts/collect.py` 실패 격리 강화 — 소스별 `try/except`로 `SourceStatus`(ok/item_count/`error_type=type(e).__name__`만, SEC-02) 집계, 부분 성공으로 진행, 종료코드(0=부분성공/1=전소스실패), 전 소스 실패 시 `latest.json` 미덮어쓰기(엣지 케이스 정책, FR-009)
- [X] T026 [P] [US3] `scripts/dedup.py` — `load_ledger(path)`/`prune(ledger, today, days=30)`/`is_new(url, ledger)` + `docs/data/seen_urls.json` 입출력(research R3)
- [X] T027 [US3] `scripts/collect.py`에 중복 제거 통합 — 정규화 URL로 신규 항목만 통과·원장 갱신·30일 prune, HN 텍스트 글은 item URL 키 폴백(FR-011) (T026, T014 의존)
- [X] T028 [US3] `docs/app.js` — `sources` 중 `ok:false`를 "수집 실패" 표시, 빈 소스/카테고리 추정값 미표시(FR-010) (T019 의존)
- [X] T029 [P] [US3] `tests/integration/test_failure_isolation.py` — 한 소스 강제 실패 시 나머지 적재·종료코드 0·SourceStatus 기록; `tests/unit/test_dedup.py` — 정규화 URL 동일 항목 일자 간 1회·30일 prune 검증

**Checkpoint**: 전 사용자 스토리 독립 동작

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 보안 검증·스케줄·배포·문서

- [X] T030 `impl-python-validate` 실행 — `scripts/**` ruff(S그룹)/bandit/pip-audit + SEC-01~09 수동 체크리스트. `.claude/rules/python-security.md` 준수 확인(외부 HTTP·시크릿 취급 태스크 T006/T009/T025 완료 조건). 추가: 커밋 대상 `docs/data/*` diff에 토큰/키 패턴이 없음을 스캔(SEC-01/09, 헌법 I)
- [X] T031 [P] `.github/workflows/daily.yml` (폴백) — cron `0 23 * * *`(=KST 08:00), `workflow_dispatch`, `permissions: contents: write`, 내장 `GITHUB_TOKEN`로 `docs/data` 커밋·푸시. LLM 키 사용 시 Actions Secret만(커밋·출력 금지, SEC-01/09)
- [X] T032 [P] `README.md` 갱신 — 공개 URL·아키텍처·스케줄 루틴(1차)/Actions(폴백)·GitHub Pages `/docs` 설정 절차
- [X] T033 quickstart.md 검증 절차 전체 1회 수행(로컬 dry-run→산출→대시보드 미리보기→검증 체크리스트), 결과 기록. 포함: `latest.json` 단일 fetch로 대시보드 첫 표시 5초 이내(SC-001) 및 외부 CDN 0 확인
- [X] T034 스케줄 루틴 등록 — `/schedule`로 `tech-trends-daily`(cron `0 8 * * *`, KST 08:00) 등록: 로컬 repo clone→수집→에이전트 한글 요약→commit·push. 요약 주입 경로(T015) 연결됨. 주의: 데스크톱 앱이 켜져 있을 때 실행(꺼져 있으면 다음 실행 시 보충)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup(P1)**: 종속 없음, 즉시 시작
- **Foundational(P2)**: Setup 완료 후 — 모든 스토리 차단(BLOCKS)
- **User Stories(P3+)**: Foundational 완료 후. 우선순위순(P1→P2→P3) 또는 병렬
- **Polish(P6)**: 원하는 스토리 완료 후

### User Story Dependencies

- **US1(P1)**: Foundational 후 착수, 타 스토리 무종속 — MVP
- **US2(P2)**: Foundational 후. 수집 항목(T014) 위에 점수 추가, 독립 테스트 가능
- **US3(P3)**: Foundational 후. 수집 파이프라인(T014) 위에 실패 격리·중복 제거 추가, 독립 테스트 가능

### Within Each User Story

- 소스 어댑터(모델 격) → collect 통합(서비스 격) → 대시보드 렌더(UI 격) → 테스트
- 핵심 구현 후 통합, 스토리 완료 후 다음 우선순위

### Parallel Opportunities

- Setup의 T003/T004/T005 [P] 병렬
- Foundational의 T007 [P]는 T006과 병렬(다른 파일)
- US1 소스 어댑터 T010–T013 [P] 병렬(서로 다른 파일)
- US1 프론트 T017/T018 [P] 병렬(app.js T019는 index.html 의존)
- 각 스토리 테스트([P] 표기) 병렬

---

## Parallel Example: User Story 1

```bash
# US1 소스 어댑터 병렬 착수:
Task: "scripts/sources/github_trending.py fetch 구현"
Task: "scripts/sources/ai_labs.py fetch 구현"
Task: "scripts/sources/codex.py fetch 구현"
Task: "scripts/sources/hackernews.py fetch 구현"

# US1 프론트 골격 병렬:
Task: "docs/index.html 탭 구조"
Task: "docs/styles.css 반응형"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup → 2. Phase 2 Foundational(차단) → 3. Phase 3 US1 → 4. **STOP & VALIDATE**(US1 단독 테스트) → 5. 배포/데모(MVP)

### Incremental Delivery

1. Setup + Foundational → 기반 준비
2. US1 → 독립 테스트 → 배포(MVP: 오늘의 트렌드 표시)
3. US2 → 독립 테스트 → 배포(핫토픽 점수)
4. US3 → 독립 테스트 → 배포(실패 격리·중복 제거)

---

## Notes

- [P] = 다른 파일·무종속. [Story] = 추적성 라벨
- 각 스토리는 독립 완료·테스트 가능
- 외부 HTTP/시크릿/외부 입력 취급 태스크(T006/T009/T014/T025/T027)는 `.claude/rules/python-security.md`(SEC-01~09) 준수를 완료 조건에 포함
- 태스크 또는 논리 그룹 단위 커밋(commit-rule, Claude 꼬리말 금지). 개인 프로젝트라 push까지 수행
- 결측·실패는 빈 값/"데이터 없음"으로 — 추정 금지(헌법 III)

## 총괄

- **총 태스크**: 34개 (Setup 5, Foundational 4, US1 11, US2 4, US3 5, Polish 5)
- **사용자 스토리**: 3개 (P1 MVP / P2 / P3)
- **병렬 기회**: 소스 어댑터 4개·프론트 골격·스토리별 테스트
- **MVP 범위**: Phase 1+2+3 (US1) — "매일 자동 수집된 트렌드를 대시보드에서 본다"
